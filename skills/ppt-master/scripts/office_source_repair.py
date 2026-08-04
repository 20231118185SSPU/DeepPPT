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
# check-plan
# ---------------------------------------------------------------------------
def _cmd_check_plan(project_path: str) -> int:
    project = Path(project_path).resolve()

    plan_path = project / "analysis" / "source_repair_plan.json"
    if not plan_path.exists():
        raise SystemExit(f"No repair plan found at {plan_path}")

    plan = _load_json(plan_path)
    if plan.get("schema") != REPAIR_PLAN_SCHEMA:
        print(f"ERROR: Unknown plan schema: {plan.get('schema')}")
        return 1

    # Verify source hash
    source_rel = str(plan.get("source", {}).get("path", ""))
    source_path = (project / source_rel).resolve()
    if not source_path.exists():
        print(f"ERROR: Source not found: {source_path}")
        return 1
    current_hash = _sha256(source_path)
    plan_hash = plan.get("source", {}).get("sha256", "")
    if plan_hash != current_hash:
        print(f"ERROR: Source hash mismatch (plan is stale)")
        print(f"  plan:    {plan_hash}")
        print(f"  current: {current_hash}")
        return 1

    # Validate operations
    operations = plan.get("operations", [])
    if not isinstance(operations, list):
        print("ERROR: 'operations' must be a list")
        return 1

    errors = []
    for i, op in enumerate(operations):
        op_id = op.get("id", f"op[{i}]")
        cmd = op.get("command", "")
        if cmd not in ALLOWED_COMMANDS:
            errors.append(f"{op_id}: command '{cmd}' not in allowlist")
        if "reason" not in op:
            errors.append(f"{op_id}: missing 'reason'")
        if "expect" not in op:
            errors.append(f"{op_id}: missing 'expect'")

    if errors:
        print("Plan errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("Repair plan check passed.")
    print(f"  Status: {plan.get('status')}")
    print(f"  Operations: {len(operations)}")
    print(f"  Source: {source_rel}")
    print(f"  Hash: {current_hash[:16]}...")
    return 0


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------
def _cmd_apply(project_path: str) -> int:
    project = Path(project_path).resolve()

    # Probe OfficeCLI
    runtime = probe_officecli()
    if runtime.status != "ready":
        print(f"ERROR: OfficeCLI not ready (status={runtime.status})")
        return 1

    # Load plan
    plan_path = project / "analysis" / "source_repair_plan.json"
    plan = _load_json(plan_path)

    if plan.get("status") != "confirmed":
        print(f"ERROR: Plan must be 'confirmed', got '{plan.get('status')}'")
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

    # Validate repaired copy
    val_result = validate_office_file(candidate)

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
        else:
            converter_warning = conv_result.stderr[:500]

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
        },
        "converter": {
            "output": converter_output,
            "warning": converter_warning or None,
        },
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
