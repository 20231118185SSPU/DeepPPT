#!/usr/bin/env python3
"""PPT Master — Office Source Repair (Copy-Only)

Opt-in DOCX/XLSX repair on temporary copies. Never modifies the user's original
source file. Produces timestamped repaired copies in ``sources/repaired/`` and
re-runs the format-appropriate converter to produce a new Markdown.

Usage:
    python3 scripts/office_source_repair.py scaffold <project> --source <relative-path>
    python3 scripts/office_source_repair.py check-plan <project>
    python3 scripts/office_source_repair.py apply <project>

Dependencies:
    ``officecli_bridge.py`` (same directory).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from officecli_bridge import (  # noqa: E402
    run_officecli,
    run_atomic_batch,
    validate_office_file,
    probe_officecli,
    OFFICECLI_NOT_INSTALLED,
    OFFICECLI_BATCH_ROLLED_BACK,
    OFFICECLI_VALIDATION_FAILED,
    OFFICECLI_COMMAND_FAILED,
    OFFICECLI_PLAN_INVALID,
    OFFICECLI_PLAN_STALE,
)

# Best-effort trace import
try:
    from dashboard.trace_writer import trace_event as _trace_event
except ImportError:
    def _trace_event(*args: Any, **kwargs: Any) -> None:  # type: ignore[no-redef]
        pass

_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent
REPAIR_PLAN_SCHEMA = "ppt_master.office_source_repair_plan.v1"
REPAIR_RESULT_SCHEMA = "ppt_master.office_source_repair_result.v1"

ALLOWED_FORMATS = {"docx", "xlsx"}
ALLOWED_COMMANDS = {"set", "add", "remove", "move", "swap"}


def _sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _count_issues(path: Path) -> int:
    """Count issues reported by OfficeCLI for a file (-1 when unreportable)."""
    result = run_officecli(["view", str(path), "issues", "--json"], timeout_s=30.0)
    if not result.success:
        return -1
    envelope = result.data or {}
    inner = envelope.get("data", {})
    if isinstance(inner, dict):
        count = inner.get("count")
        if isinstance(count, int):
            return count
        issues = inner.get("issues")
        if isinstance(issues, list):
            return len(issues)
    elif isinstance(inner, list):
        return len(inner)
    return 0


def _resolve_source(project: Path, relative_path: str) -> Path:
    """Resolve a relative source path within a project."""
    source_path = (project / relative_path).resolve()
    if not source_path.exists():
        raise SystemExit(f"Source not found: {source_path}")
    fmt = source_path.suffix.lstrip(".").lower()
    if fmt not in ALLOWED_FORMATS:
        raise SystemExit(
            f"Repair only supports {', '.join(ALLOWED_FORMATS)}. "
            f"Got: {fmt}"
        )
    return source_path


# ---------------------------------------------------------------------------
# scaffold — create a repair plan
# ---------------------------------------------------------------------------
def _cmd_scaffold(project_path: str, source_rel: str) -> int:
    project = Path(project_path).resolve()
    source_path = _resolve_source(project, source_rel)
    source_hash = _sha256(source_path)

    plan: dict[str, object] = {
        "schema": REPAIR_PLAN_SCHEMA,
        "status": "draft",
        "officecli_version": "1.0.143",
        "source": {
            "path": source_rel,
            "sha256": source_hash,
            "format": source_path.suffix.lstrip(".").lower(),
        },
        "operations": [],
        "invariants": {
            "preserve_original": True,
            "copy_only": True,
        },
        "confirmation": {
            "confirmed_at": None,
            "confirmed_by": None,
        },
    }

    analysis_dir = project / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    plan_path = analysis_dir / "source_repair_plan.json"
    with open(plan_path, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"Repair plan scaffolded at {plan_path}")
    print(f"  Source: {source_rel} ({source_path.suffix.lstrip('.')})")
    print(f"  SHA-256: {source_hash[:16]}...")
    print(f"  Add operations to the 'operations' list, then confirm and apply.")
    return 0


# ---------------------------------------------------------------------------
# Plan validation (shared by check-plan and apply)
# ---------------------------------------------------------------------------
def _resolve_get_node(result) -> dict[str, object]:
    """Return the first matched node from a ``get`` result envelope."""
    if not result.success:
        return {}
    envelope = result.data or {}
    inner = envelope.get("data", {})
    if not isinstance(inner, dict):
        return {}
    results = inner.get("results", [])
    if isinstance(results, list) and results and isinstance(results[0], dict):
        return results[0]
    return {}


def _repair_plan_errors(project: Path, plan: dict[str, object]) -> list[str]:
    """Validate a repair plan against the current source; return a list of errors.

    Covers plan schema/status, source hash freshness, command allowlist,
    required fields, and — against the live document — target/parent existence
    plus ``expect`` fingerprints.
    """
    errors: list[str] = []

    if plan.get("schema") != REPAIR_PLAN_SCHEMA:
        errors.append(f"Unknown plan schema: {plan.get('schema')}")
    status = plan.get("status", "")
    if status not in {"draft", "confirmed", "applied", "failed"}:
        errors.append(f"Invalid plan status: {status}")

    source_rel = str(plan.get("source", {}).get("path", ""))
    source_path = (project / source_rel).resolve()
    if not source_path.exists():
        errors.append(f"Source not found: {source_path}")
        return errors
    current_hash = _sha256(source_path)
    plan_hash = plan.get("source", {}).get("sha256", "")
    if plan_hash and plan_hash != current_hash:
        errors.append(
            f"Source hash mismatch (plan is stale): "
            f"plan={plan_hash[:16]}... current={current_hash[:16]}..."
        )

    operations = plan.get("operations", [])
    if not isinstance(operations, list):
        errors.append("'operations' must be a list")
        return errors

    for i, op in enumerate(operations):
        if not isinstance(op, dict):
            errors.append(f"op[{i}]: not an object")
            continue
        op_id = op.get("id", f"op[{i}]")
        cmd = op.get("command", "")
        if cmd not in ALLOWED_COMMANDS:
            errors.append(
                f"{op_id}: command '{cmd}' not in allowlist "
                f"{sorted(ALLOWED_COMMANDS)}"
            )
            continue
        path = op.get("path", "")
        parent = op.get("parent", "")
        if cmd != "add" and not path:
            errors.append(f"{op_id}: missing 'path'")
        if cmd == "add" and not parent:
            errors.append(f"{op_id}: missing 'parent'")
        if "reason" not in op:
            errors.append(f"{op_id}: missing 'reason'")
        if cmd != "add" and "expect" not in op:
            errors.append(f"{op_id}: missing 'expect' fingerprint for non-add operation")

        # Target / parent existence + expect fingerprint against the live document
        targets = [parent] if cmd == "add" else [path]
        if cmd == "swap":
            targets.append(op.get("path2", ""))
        for target in targets:
            if not target:
                continue
            get_result = run_officecli(
                ["get", str(source_path), target, "--json"],
                timeout_s=15.0,
            )
            if not get_result.success:
                errors.append(f"{op_id}: target not found: {target}")
                continue
            if cmd != "add":
                expect = op.get("expect")
                node = _resolve_get_node(get_result)
                if not isinstance(expect, dict):
                    errors.append(f"{op_id}: expect must be an object")
                    continue
                for key, value in expect.items():
                    if key not in node:
                        errors.append(f"{op_id}: expect key '{key}' not present on target node")
                    elif node.get(key) != value:
                        errors.append(
                            f"{op_id}: expect '{key}' mismatch: want {value!r}, "
                            f"got {node.get(key)!r}"
                        )
    return errors


# ---------------------------------------------------------------------------
# check-plan
# ---------------------------------------------------------------------------
def _cmd_check_plan(project_path: str) -> int:
    project = Path(project_path).resolve()

    plan_path = project / "analysis" / "source_repair_plan.json"
    if not plan_path.exists():
        raise SystemExit(f"No repair plan found at {plan_path}")

    plan = _load_json(plan_path)
    errors = _repair_plan_errors(project, plan)
    if errors:
        print("Plan errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    source_rel = str(plan.get("source", {}).get("path", ""))
    current_hash = _sha256((project / source_rel).resolve())
    operations = plan.get("operations", [])
    print("Repair plan check passed.")
    print(f"  Status: {plan.get('status')}")
    print(f"  Operations: {len(operations) if isinstance(operations, list) else 0}")
    print(f"  Source: {source_rel}")
    print(f"  Hash: {current_hash[:16]}...")
    return 0


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------
def _cmd_apply(project_path: str) -> int:
    project = Path(project_path).resolve()
    t0 = time.perf_counter()

    # Probe OfficeCLI
    runtime = probe_officecli()
    if runtime.status != "ready":
        print(f"ERROR: OfficeCLI not ready (status={runtime.status})")
        return 1
    _trace_event(
        project,
        "officecli_probe",
        f"Runtime ready (v{runtime.actual_version}, {runtime.platform})",
        status="PASS",
        runtime_version=runtime.actual_version,
        platform=runtime.platform,
        duration_ms=int((time.perf_counter() - t0) * 1000),
    )

    # Load plan
    plan_path = project / "analysis" / "source_repair_plan.json"
    plan = _load_json(plan_path)

    if plan.get("status") != "confirmed":
        print(f"ERROR: Plan must be 'confirmed', got '{plan.get('status')}'")
        return 1

    # Gate 2: re-run plan validation (schema, hash freshness, targets, expect)
    plan_errors = _repair_plan_errors(project, plan)
    if plan_errors:
        print("Repair plan validation failed (apply aborted):")
        for e in plan_errors:
            print(f"  - {e}")
        return 1

    # Resolve source
    source_rel = str(plan.get("source", {}).get("path", ""))
    source_path = (project / source_rel).resolve()
    source_hash = _sha256(source_path)
    plan_hash = plan.get("source", {}).get("sha256", "")
    if plan_hash != source_hash:
        print("ERROR: Source hash mismatch. Plan is stale.")
        return 1

    operations = plan.get("operations", [])
    if not operations:
        print("No operations in plan — nothing to do.")
        return 0

    fmt = source_path.suffix.lstrip(".").lower()

    # Create temp copy
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = _REPO_ROOT / ".tmp" / f"officecli-repair-{run_id}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    candidate = tmp_dir / source_path.name
    shutil.copy2(source_path, candidate)

    # Verify original untouched
    assert _sha256(source_path) == source_hash, "Original source modified!"

    # Apply atomic batch
    batch_commands = []
    for op in operations:
        cmd_entry: dict[str, object] = {"command": op["command"]}
        if "path" in op:
            cmd_entry["path"] = op["path"]
        if "parent" in op:
            cmd_entry["parent"] = op["parent"]
        if "props" in op:
            cmd_entry["props"] = op["props"]
        batch_commands.append(cmd_entry)

    print(f"Applying {len(batch_commands)} repair operations to temp copy...")
    result = run_atomic_batch(candidate, batch_commands, timeout_s=120.0)

    if not result.success:
        rolled_back = _sha256(candidate) == _sha256(source_path)
        print(f"Repair batch failed: {result.message}")
        print(f"Rolled back: {rolled_back}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return 1

    # Validate repaired copy + issues readback
    t_validate = time.perf_counter()
    val_result = validate_office_file(candidate)
    issues_before = _count_issues(source_path)
    issues_after = _count_issues(candidate)
    _trace_event(
        project,
        "officecli_validate",
        f"Source issues={issues_before}, repaired issues={issues_after}",
        status="PASS",
        source_issue_count=issues_before,
        candidate_issue_count=issues_after,
        duration_ms=int((time.perf_counter() - t_validate) * 1000),
    )

    # Publish repaired copy
    repaired_dir = project / "sources" / "repaired"
    repaired_dir.mkdir(parents=True, exist_ok=True)
    stem = source_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    repaired_name = f"{stem}_repaired_{timestamp}.{fmt}"
    repaired_path = repaired_dir / repaired_name
    shutil.copy2(candidate, repaired_path)
    repaired_hash = _sha256(repaired_path)

    # Re-run converter
    converter_output = ""
    converter_warning = ""
    markdown_hash = ""
    if fmt == "docx":
        converter_script = _SCRIPT_DIR / "source_to_md" / "doc_to_md.py"
    elif fmt == "xlsx":
        converter_script = _SCRIPT_DIR / "source_to_md" / "excel_to_md.py"
    else:
        converter_script = None

    if converter_script and converter_script.exists():
        md_name = f"{stem}_repaired_{timestamp}.md"
        md_path = project / "sources" / md_name
        import subprocess
        conv_result = subprocess.run(
            [sys.executable, str(converter_script), str(repaired_path), "-o", str(md_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if conv_result.returncode == 0:
            converter_output = str(md_path)
            if md_path.is_file():
                markdown_hash = _sha256(md_path)
        else:
            converter_warning = conv_result.stderr[:500]

    # Operation digest (no props/replacement text)
    operations = plan.get("operations", [])
    op_digest = hashlib.sha256(
        json.dumps(
            [{"command": o.get("command"), "path": o.get("path") or o.get("parent")}
             for o in operations if isinstance(o, dict)],
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    # Write result
    result_data: dict[str, object] = {
        "schema": REPAIR_RESULT_SCHEMA,
        "success": True,
        "source": {
            "original_path": source_rel,
            "original_sha256": source_hash,
        },
        "repaired": {
            "path": str(repaired_path.relative_to(project)),
            "sha256": repaired_hash,
            "validate_passed": val_result.success,
            "issues_before": issues_before,
            "issues_after": issues_after,
        },
        "converter": {
            "output": converter_output,
            "markdown_sha256": markdown_hash or None,
            "warning": converter_warning or None,
        },
        "operation_digest": op_digest,
        "applied_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    result_path = project / "analysis" / "source_repair_result.json"
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result_data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # Update plan status
    plan["status"] = "applied"
    with open(plan_path, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # Clean up temp
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # Verify original still unchanged
    assert _sha256(source_path) == source_hash, "Original source was modified!"

    print(f"Repair applied successfully.")
    print(f"  Repaired: {repaired_path}")
    print(f"  Converter: {converter_output or 'skipped'}")
    print(f"  Issues: {issues_before} -> {issues_after}")
    if issues_after > issues_before:
        print(f"  WARNING: repaired copy reports {issues_after - issues_before} new issue(s); "
              f"review before using it as the pipeline source.")
    if converter_warning:
        print(f"  Warning: {converter_warning[:200]}")

    _trace_event(
        project,
        "office_source_repair",
        f"Repaired {source_rel} ({len(operations)} ops) → {repaired_name}",
        status="PASS",
        format=fmt,
        operation_count=len(operations),
        converter_output=converter_output or None,
        duration_ms=int((time.perf_counter() - t0) * 1000),
    )
    return 0


def _load_json(path: Path) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy-only Office source repair (DOCX/XLSX)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scaffold = sub.add_parser("scaffold", help="Create repair plan")
    p_scaffold.add_argument("project", help="Project directory")
    p_scaffold.add_argument("--source", required=True, help="Relative path to source file")

    p_check = sub.add_parser("check-plan", help="Validate repair plan")
    p_check.add_argument("project", help="Project directory")

    p_apply = sub.add_parser("apply", help="Apply confirmed repair plan")
    p_apply.add_argument("project", help="Project directory")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "scaffold":
        return _cmd_scaffold(args.project, args.source)
    elif args.command == "check-plan":
        return _cmd_check_plan(args.project)
    elif args.command == "apply":
        return _cmd_apply(args.project)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
