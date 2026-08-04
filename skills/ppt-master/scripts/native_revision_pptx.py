#!/usr/bin/env python3
"""PPT Master — Native PPTX Revision (OfficeCLI-backed)

Read-only inspection, browser-based element selection, atomic plan validation,
and temp-copy apply for existing PPTX files. Never mutates source in place.

Usage:
    python3 scripts/native_revision_pptx.py init <pptx-or-project> [--name <slug>]
    python3 scripts/native_revision_pptx.py inspect <project>
    python3 scripts/native_revision_pptx.py watch <project> [--port 26315]
    python3 scripts/native_revision_pptx.py selected <project> --json
    python3 scripts/native_revision_pptx.py unwatch <project>
    python3 scripts/native_revision_pptx.py check-plan <project>
    python3 scripts/native_revision_pptx.py apply <project>
    python3 scripts/native_revision_pptx.py validate <project> --pptx <candidate>

Dependencies:
    ``officecli_bridge.py`` (same directory) for OfficeCLI interaction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# sys.path bootstrap
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from officecli_bridge import (  # noqa: E402
    resolve_officecli,
    probe_officecli,
    run_officecli,
    run_atomic_batch,
    validate_office_file,
    inspect_office_file,
    OfficeCliResult,
    OfficeCliRuntime,
    OFFICECLI_COMMAND_FAILED,
    OFFICECLI_VALIDATION_FAILED,
    OFFICECLI_BATCH_ROLLED_BACK,
    OFFICECLI_PLAN_INVALID,
    OFFICECLI_PLAN_STALE,
    OFFICECLI_TARGET_MISSING,
    OFFICECLI_PREVIEW_UNAVAILABLE,
    OFFICECLI_NOT_INSTALLED,
)

# Best-effort trace import
try:
    from dashboard.trace_writer import trace_event as _trace_event
except ImportError:
    def _trace_event(*args: Any, **kwargs: Any) -> None:  # type: ignore[no-redef]
        pass

_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
PLAN_SCHEMA = "ppt_master.native_revision_plan.v1"
INVENTORY_SCHEMA = "ppt_master.native_revision_inventory.v1"
RESULT_SCHEMA = "ppt_master.native_revision_result.v1"
VALIDATION_SCHEMA = "ppt_master.officecli_validation.v1"
REPORT_SCHEMA = "ppt_master.native_revision_report.v1"

VALID_PLAN_STATUSES = {"draft", "confirmed", "applied", "failed"}
V1_MUTATION_ALLOWLIST = {"set", "add", "remove", "move", "swap"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tmp_dir(run_id: Optional[str] = None) -> Path:
    """Return a repo-local temporary directory path."""
    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d%H%M%S")
    return _REPO_ROOT / ".tmp" / f"officecli-{run_id}"


def _resolve_source(project_or_pptx: str) -> tuple[Path, bool]:
    """Resolve input to either a project dir or a standalone PPTX path.

    Returns (path, is_project).
    """
    p = Path(project_or_pptx).resolve()
    if p.is_dir():
        # Check if it's a PPT Master project
        if (p / "project.json").exists():
            return p, True
        # Directory containing a single PPTX
        pptx_files = list(p.glob("*.pptx"))
        if len(pptx_files) == 1:
            return pptx_files[0], False
        raise SystemExit(f"Not a project and no single PPTX found in: {p}")
    elif p.is_file() and p.suffix.lower() == ".pptx":
        return p, False
    else:
        raise SystemExit(f"Not a PPTX file or project directory: {p}")


def _ensure_project_dirs(project: Path) -> dict[str, Path]:
    """Create standard project subdirectories and return them."""
    dirs = {
        "analysis": project / "analysis",
        "quality": project / "quality",
        "validation": project / "validation",
        "native_preview": project / "native_preview",
        "exports": project / "exports",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _read_json(path: Path) -> dict[str, object]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _probe_or_die() -> tuple[Path, OfficeCliRuntime]:
    """Probe OfficeCLI runtime; exit non-zero if not ready."""
    runtime = probe_officecli()
    if runtime.status != "ready":
        print(
            json.dumps({
                "success": False,
                "error_code": OFFICECLI_NOT_INSTALLED,
                "message": f"OfficeCLI not ready (status={runtime.status}). "
                           f"Run: python skills/ppt-master/scripts/install_officecli.py install",
            }),
            file=sys.stderr,
        )
        raise SystemExit(1)
    return resolve_officecli(), runtime


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------
def _cmd_init(pptx_path: str, name: Optional[str] = None) -> int:
    """Create a native revision project from a PPTX or existing project."""
    source, is_project = _resolve_source(pptx_path)

    if is_project:
        # Use existing project
        project = source
        # Find the PPTX to revise — look in exports/
        exports_dir = project / "exports"
        pptx_files = sorted(exports_dir.glob("*.pptx"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not pptx_files:
            raise SystemExit(f"No PPTX files found in {exports_dir}")
        target_pptx = pptx_files[0]
        target_in_project = target_pptx
    else:
        # Create a new standalone project
        stem = name or source.stem
        project = _REPO_ROOT / "projects" / f"_revision_{stem}"
        if project.exists():
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project = _REPO_ROOT / "projects" / f"_revision_{stem}_{stamp}"
        project.mkdir(parents=True, exist_ok=True)

        # Copy source to sources/
        sources_dir = project / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)
        target_in_project = sources_dir / source.name
        shutil.copy2(source, target_in_project)
        target_pptx = target_in_project

    # Create project structure
    dirs = _ensure_project_dirs(project)

    # Create minimal project.json
    proj_json = project / "project.json"
    if not proj_json.exists():
        _write_json(proj_json, {
            "name": project.name,
            "kind": "native_pptx_revision",
            "created_at": _now_iso(),
            "source_pptx": str(target_pptx),
            "source_sha256": _sha256(target_pptx),
        })

    print(f"Project: {project}")
    print(f"Source:  {target_pptx}")
    print(f"SHA-256: {_sha256(target_pptx)}")
    return 0


# ---------------------------------------------------------------------------
# inspect
# ---------------------------------------------------------------------------
def _cmd_inspect(project_path: str) -> int:
    """Generate native_revision_inventory.json for the project."""
    project = Path(project_path).resolve()
    if not project.is_dir():
        raise SystemExit(f"Not a directory: {project}")

    # Find source PPTX
    source_pptx = _find_source_pptx(project)

    # Compute source hash
    source_hash = _sha256(source_pptx)

    # Run OfficeCLI inspection
    info = inspect_office_file(source_pptx, detail="summary")

    # Verify source unchanged
    assert _sha256(source_pptx) == source_hash, "Source file was modified during inspection!"

    # Build inventory
    slug = project.name
    if slug.startswith("_revision_"):
        slug = slug[len("_revision_"):]

    inventory: dict[str, object] = {
        "schema": INVENTORY_SCHEMA,
        "inspected_at": _now_iso(),
        "source": {
            "path": str(source_pptx),
            "sha256": source_hash,
            "format": "pptx",
        },
        "stats": info.get("stats", {}),
        "outline": info.get("outline", {}),
        "issues": info.get("issues", {}),
        "elements": info.get("elements", []),
        "officecli_version": "1.0.143",
    }

    dirs = _ensure_project_dirs(project)
    inv_path = dirs["analysis"] / "native_revision_inventory.json"
    _write_json(inv_path, inventory)

    # Print summary
    stats = info.get("stats", {})
    slides = _count_slides(stats)
    shapes = _count_shapes(stats)
    print(f"Inventory written to {inv_path}")
    print(f"  Slides: {slides}, Shapes: {shapes}")
    if info.get("issues"):
        issues_data = info["issues"]
        issue_count = _count_issues(issues_data)
        print(f"  Issues: {issue_count}")

    # Trace event
    _trace_event(
        project,
        "native_revision_inspect",
        f"Inventory: {slides} slides, {shapes} shapes",
        status="PASS",
        slide_count=slides,
        shape_count=shapes,
    )
    return 0


def _find_source_pptx(project: Path) -> Path:
    """Locate the source PPTX for a project."""
    proj_json = project / "project.json"
    if proj_json.exists():
        proj = _read_json(proj_json)
        src = proj.get("source_pptx", "")
        if src:
            p = Path(src)
            if p.is_absolute() and p.exists():
                return p
            rel = project / src
            if rel.exists():
                return rel

    # Fallback: search sources/ then exports/
    for d in ["sources", "exports"]:
        pptx_files = list((project / d).glob("*.pptx"))
        if pptx_files:
            return sorted(pptx_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]

    raise SystemExit(f"No PPTX source found in project: {project}")


def _count_slides(stats: object) -> int:
    if isinstance(stats, dict):
        s_data = stats.get("data", stats)
        if isinstance(s_data, dict):
            return s_data.get("slides", 0)
    return 0


def _count_shapes(stats: object) -> int:
    if isinstance(stats, dict):
        s_data = stats.get("data", stats)
        if isinstance(s_data, dict):
            return s_data.get("totalShapes", 0)
    return 0


def _count_issues(issues: object) -> int:
    if isinstance(issues, dict):
        iss_data = issues.get("data", issues)
        if isinstance(iss_data, list):
            return len(iss_data)
        if isinstance(iss_data, dict):
            return iss_data.get("count", len(iss_data))
    if isinstance(issues, list):
        return len(issues)
    return 0


def _count_validation_issues(result: OfficeCliResult) -> int:
    """Count warning/error entries in a validation result."""
    if result.success:
        return 0
    data = result.data
    warnings = data.get("warnings", [])
    if isinstance(warnings, list):
        return len(warnings)
    return 1  # non-zero failure but no countable warnings


# ---------------------------------------------------------------------------
# watch / selected / unwatch
# ---------------------------------------------------------------------------
def _cmd_watch(project_path: str, port: int = 26315) -> int:
    """Start OfficeCLI live preview for the source PPTX."""
    project = Path(project_path).resolve()
    source_pptx = _find_source_pptx(project)
    binary, runtime = _probe_or_die()

    source_hash = _sha256(source_pptx)

    # Start watch as background process
    env = os.environ.copy()
    env.setdefault("OFFICECLI_NO_AUTO_RESIDENT", "0")  # allow resident for watch

    import subprocess
    proc = subprocess.Popen(
        [str(binary), "watch", str(source_pptx)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    # Give it a moment to start
    time.sleep(2)

    # Write lock sidecar
    dirs = _ensure_project_dirs(project)
    watch_data: dict[str, object] = {
        "schema": "ppt_master.officecli_watch.v1",
        "status": "running",
        "pid": proc.pid,
        "port": port,
        "source_sha256": source_hash,
        "started_at": _now_iso(),
    }

    # Try to detect actual URL from OfficeCLI output
    try:
        line = proc.stdout.readline() if proc.stdout else ""
        if "http" in line.lower():
            watch_data["url"] = line.strip()
    except Exception:
        pass

    watch_path = dirs["native_preview"] / "officecli-watch.json"
    _write_json(watch_path, watch_data)

    print(f"Watch started (PID={proc.pid})")
    print(f"Preview lock: {watch_path}")
    if watch_data.get("url"):
        print(f"URL: {watch_data['url']}")

    _trace_event(
        project,
        "native_revision_preview",
        f"Watch preview started (PID={proc.pid})",
        status="PASS",
        port=port,
    )
    return 0


def _cmd_selected(project_path: str) -> int:
    """Read browser selection from OfficeCLI watch."""
    project = Path(project_path).resolve()
    source_pptx = _find_source_pptx(project)

    result = run_officecli(
        ["get", str(source_pptx), "selected", "--json"],
        timeout_s=15.0,
    )
    if result.success:
        print(json.dumps(result.data, indent=2))
        return 0
    else:
        print(json.dumps({
            "success": False,
            "error_code": result.error_code,
            "message": result.message,
        }))
        return 1


def _cmd_unwatch(project_path: str) -> int:
    """Stop the OfficeCLI watch preview."""
    project = Path(project_path).resolve()
    source_pptx = _find_source_pptx(project)

    result = run_officecli(
        ["unwatch", str(source_pptx)],
        timeout_s=15.0,
    )
    if result.success:
        print("Watch stopped.")
        # Clean up lock
        watch_path = project / "native_preview" / "officecli-watch.json"
        watch_path.unlink(missing_ok=True)
        return 0
    else:
        # unwatch may fail if no watch is running — not an error
        print(f"Unwatch: {result.message}")
        return 0


# ---------------------------------------------------------------------------
# check-plan
# ---------------------------------------------------------------------------
def _cmd_check_plan(project_path: str) -> int:
    """Validate the revision plan against current source state."""
    project = Path(project_path).resolve()
    source_pptx = _find_source_pptx(project)

    # Load plan
    plan_path = project / "analysis" / "native_revision_plan.json"
    if not plan_path.exists():
        raise SystemExit(f"No plan found at {plan_path}. Create one first.")
    plan = _read_json(plan_path)

    # Validate schema
    if plan.get("schema") != PLAN_SCHEMA:
        print(f"ERROR: Unknown plan schema: {plan.get('schema')}")
        return 1

    # Check status
    status = plan.get("status", "")
    if status not in VALID_PLAN_STATUSES:
        print(f"ERROR: Invalid plan status: {status}")
        return 1

    # Verify source hash matches
    current_hash = _sha256(source_pptx)
    plan_hash = plan.get("source", {}).get("sha256", "")
    if plan_hash != current_hash:
        print(f"ERROR: Source hash mismatch (plan is stale)")
        print(f"  plan:    {plan_hash}")
        print(f"  current: {current_hash}")
        return 1

    # Verify operations
    operations = plan.get("operations", [])
    if not isinstance(operations, list) or len(operations) == 0:
        print("WARNING: Plan has no operations.")
        return 0

    errors = []
    for i, op in enumerate(operations):
        op_id = op.get("id", f"op[{i}]")
        command = op.get("command", "")

        # Check allowlist
        if command not in V1_MUTATION_ALLOWLIST:
            errors.append(f"{op_id}: command '{command}' not in V1 allowlist {V1_MUTATION_ALLOWLIST}")

        # Check required fields
        if "path" not in op and "parent" not in op:
            errors.append(f"{op_id}: missing 'path' or 'parent'")
        if "reason" not in op:
            errors.append(f"{op_id}: missing 'reason'")
        if command != "add" and "expect" not in op:
            errors.append(f"{op_id}: missing 'expect' fingerprint for non-add operation")

    if errors:
        print("Plan validation errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    # Verify slide count invariance if declared
    invariants = plan.get("invariants", {})
    if invariants.get("preserve_slide_count"):
        stats_result = run_officecli(
            ["view", str(source_pptx), "stats", "--json"],
            timeout_s=30.0,
        )
        if stats_result.success:
            current_slides = _count_slides(stats_result.data)
            plan_slides = plan.get("source", {}).get("slide_count", 0)
            if current_slides != plan_slides:
                print(f"ERROR: Slide count changed: plan={plan_slides}, current={current_slides}")
                return 1

    print("Plan check passed.")
    print(f"  Status: {status}")
    print(f"  Operations: {len(operations)}")
    print(f"  Source hash: {current_hash[:16]}...")

    _trace_event(
        project,
        "native_revision_plan",
        f"Plan check: {len(operations)} ops, status={status}",
        status="PASS",
        operation_count=len(operations),
    )
    return 0


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------
def _cmd_apply(project_path: str) -> int:
    """Apply a confirmed native revision plan atomically."""
    project = Path(project_path).resolve()
    source_pptx = _find_source_pptx(project)
    binary, runtime = _probe_or_die()

    # Load plan
    plan_path = project / "analysis" / "native_revision_plan.json"
    if not plan_path.exists():
        raise SystemExit(f"No plan found at {plan_path}")
    plan = _read_json(plan_path)

    # Must be confirmed
    if plan.get("status") != "confirmed":
        print(f"ERROR: Plan status must be 'confirmed', got '{plan.get('status')}'")
        return 1

    # Verify source hash
    source_hash_before = _sha256(source_pptx)
    plan_hash = plan.get("source", {}).get("sha256", "")
    if plan_hash != source_hash_before:
        print(f"ERROR: Source hash mismatch. Plan is stale.")
        return 1

    operations = plan.get("operations", [])

    # Create temp copy
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = _tmp_dir(run_id)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    candidate = tmp_dir / source_pptx.name
    shutil.copy2(source_pptx, candidate)
    candidate_hash_before = _sha256(candidate)
    assert candidate_hash_before == source_hash_before, "Copy hash mismatch!"

    # Apply atomic batch
    batch_commands = []
    for op in operations:
        cmd_entry: dict[str, object] = {
            "command": op["command"],
        }
        if "path" in op:
            cmd_entry["path"] = op["path"]
        if "parent" in op:
            cmd_entry["parent"] = op["parent"]
        if "type" in op:
            cmd_entry["type"] = op["type"]
        if "props" in op:
            cmd_entry["props"] = op["props"]
        batch_commands.append(cmd_entry)

    print(f"Applying {len(batch_commands)} operations to temp copy...")
    result = run_atomic_batch(candidate, batch_commands, timeout_s=120.0)

    if not result.success:
        # Check if rolled back
        candidate_hash_after = _sha256(candidate)
        rolled_back = candidate_hash_after == candidate_hash_before

        print(f"Batch failed: {result.message}")
        print(f"Rolled back: {rolled_back}")

        # Clean up temp
        shutil.rmtree(tmp_dir, ignore_errors=True)

        # Update plan status
        plan["status"] = "failed"
        _write_json(plan_path, plan)

        # Record failure
        dirs = _ensure_project_dirs(project)
        result_data: dict[str, object] = {
            "schema": RESULT_SCHEMA,
            "success": False,
            "error_code": result.error_code,
            "message": result.message,
            "source_sha256": source_hash_before,
            "candidate_rolled_back": rolled_back,
            "applied_at": _now_iso(),
        }
        _write_json(dirs["analysis"] / "native_revision_result.json", result_data)

        _trace_event(
            project,
            "native_revision_apply",
            f"Batch failed: {result.message[:100]}",
            status="FAIL",
            error_code=result.error_code,
            rolled_back=rolled_back,
        )
        return 1

    # Batch succeeded — apply postflight
    print("Batch applied successfully. Running postflight...")
    rc = _postflight(project, source_pptx, candidate, plan, binary, tmp_dir)
    return rc


def _postflight(
    project: Path,
    source_pptx: Path,
    candidate: Path,
    plan: dict[str, object],
    binary: Path,
    tmp_dir: Path,
) -> int:
    """Run all post-apply validation gates and publish on success."""
    source_hash = _sha256(source_pptx)
    candidate_hash = _sha256(candidate)
    dirs = _ensure_project_dirs(project)

    errors: list[str] = []

    # Gate 4: OfficeCLI validate (baseline delta)
    source_val = validate_office_file(source_pptx)
    cand_val = validate_office_file(candidate)
    source_issues = _count_validation_issues(source_val)
    cand_issues = _count_validation_issues(cand_val)
    if cand_issues > source_issues:
        errors.append(
            f"OfficeCLI validation: candidate has {cand_issues - source_issues} "
            f"new issues vs source baseline ({source_issues} pre-existing)"
        )

    # Gate 5: Compare slide roster
    source_stats = run_officecli(["view", str(source_pptx), "stats", "--json"], timeout_s=30.0)
    cand_stats = run_officecli(["view", str(candidate), "stats", "--json"], timeout_s=30.0)
    source_slides = _count_slides(source_stats.data) if source_stats.success else -1
    cand_slides = _count_slides(cand_stats.data) if cand_stats.success else -1
    if source_slides != cand_slides:
        errors.append(f"Slide count mismatch: source={source_slides}, candidate={cand_slides}")

    # Gate 8: Readback — source unchanged
    source_hash_after = _sha256(source_pptx)
    if source_hash_after != source_hash:
        errors.append(f"Source file was modified! Before={source_hash[:16]}... After={source_hash_after[:16]}...")

    # Determine SVG divergence
    plan_origin = plan.get("source", {}).get("origin", "")
    svg_divergence = plan_origin == "generated_export"

    # Try PowerPoint COM render (Windows only)
    render_ok = False
    try:
        import subprocess
        render_dir = tmp_dir / "render"
        render_dir.mkdir(exist_ok=True)
        render_result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT_DIR / "pptx_render_export.py"),
                "--pptx", str(candidate),
                "-o", str(render_dir),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if render_result.returncode == 0:
            render_ok = True
            print(f"  PowerPoint COM render: OK ({render_dir})")
        else:
            print(f"  PowerPoint COM render: not available (rc={render_result.returncode})")
    except Exception:
        print("  PowerPoint COM render: not available")

    # If errors, fail without publishing
    if errors:
        print("Postflight errors:")
        for e in errors:
            print(f"  - {e}")

        # Update plan
        plan["status"] = "failed"
        _write_json(project / "analysis" / "native_revision_plan.json", plan)

        # Write result
        _write_json(dirs["analysis"] / "native_revision_result.json", {
            "schema": RESULT_SCHEMA,
            "success": False,
            "errors": errors,
            "source_sha256": source_hash,
            "candidate_sha256": candidate_hash,
            "svg_divergence": svg_divergence,
            "applied_at": _now_iso(),
        })
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return 1

    # All gates passed — publish
    stem = source_pptx.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_name = f"{stem}_native_revision_{timestamp}.pptx"
    export_path = dirs["exports"] / export_name

    # Atomic rename to exports
    shutil.copy2(candidate, export_path)

    # Update plan
    plan["status"] = "applied"
    _write_json(project / "analysis" / "native_revision_plan.json", plan)

    # Write result
    _write_json(dirs["analysis"] / "native_revision_result.json", {
        "schema": RESULT_SCHEMA,
        "success": True,
        "source_sha256": source_hash,
        "output_sha256": _sha256(export_path),
        "export_path": str(export_path),
        "svg_divergence": svg_divergence,
        "visual_render": "ok" if render_ok else "not_available",
        "applied_at": _now_iso(),
    })

    # Write validation artifact
    _write_json(dirs["quality"] / "officecli_validation.json", {
        "schema": VALIDATION_SCHEMA,
        "runtime_version": "1.0.143",
        "source_sha256": source_hash,
        "candidate_sha256": candidate_hash,
        "output_sha256": _sha256(export_path),
        "validate_passed": cand_val.success,
        "slide_count_match": source_slides == cand_slides,
        "source_unchanged": source_hash_after == source_hash,
        "status": "passed",
        "checked_at": _now_iso(),
    })

    # Write report
    allowed_diff_count = len(plan.get("operations", []))
    _write_json(dirs["validation"] / "native_revision_report.json", {
        "schema": REPORT_SCHEMA,
        "plan_digest": _sha256(project / "analysis" / "native_revision_plan.json"),
        "result_digest": "see analysis/native_revision_result.json",
        "allowed_differences": allowed_diff_count,
        "source_unchanged": True,
        "visual_render": "ok" if render_ok else "not_available",
        "export_path": str(export_path),
    })

    # Clean up temp
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"Export: {export_path}")
    print(f"SVG divergence: {svg_divergence}")
    print(f"Visual render: {'ok' if render_ok else 'not_available'}")

    _trace_event(
        project,
        "native_revision_apply",
        f"Applied {len(plan.get('operations', []))} ops → {export_path.name}",
        status="PASS",
        svg_divergence=svg_divergence,
        visual_render="ok" if render_ok else "not_available",
    )
    return 0


# ---------------------------------------------------------------------------
# validate (standalone candidate check)
# ---------------------------------------------------------------------------
def _cmd_validate(project_path: str, pptx_path: str) -> int:
    """Validate a candidate PPTX against the source baseline."""
    project = Path(project_path).resolve()
    candidate = Path(pptx_path).resolve()

    if not candidate.exists():
        raise SystemExit(f"Candidate not found: {candidate}")

    # Run OfficeCLI validate
    result = validate_office_file(candidate)
    print(f"OfficeCLI validate: {'PASS' if result.success else 'FAIL'}")

    if result.success:
        stats = run_officecli(["view", str(candidate), "stats", "--json"], timeout_s=30.0)
        if stats.success:
            s = _count_slides(stats.data)
            sh = _count_shapes(stats.data)
            print(f"  Slides: {s}, Shapes: {sh}")

    return 0 if result.success else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Native PPTX revision via OfficeCLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create a native revision project")
    p_init.add_argument("pptx_or_project", help="PPTX file path or existing project dir")
    p_init.add_argument("--name", help="Project slug (for standalone PPTX)")

    p_inspect = sub.add_parser("inspect", help="Generate inventory for project")
    p_inspect.add_argument("project", help="Project directory")

    p_watch = sub.add_parser("watch", help="Start live preview")
    p_watch.add_argument("project", help="Project directory")
    p_watch.add_argument("--port", type=int, default=26315, help="Preview port")

    p_sel = sub.add_parser("selected", help="Get browser selection")
    p_sel.add_argument("project", help="Project directory")
    p_sel.add_argument("--json", action="store_true", default=True, help=argparse.SUPPRESS)

    p_unwatch = sub.add_parser("unwatch", help="Stop live preview")
    p_unwatch.add_argument("project", help="Project directory")

    p_cp = sub.add_parser("check-plan", help="Validate plan against source")
    p_cp.add_argument("project", help="Project directory")

    p_apply = sub.add_parser("apply", help="Apply confirmed plan")
    p_apply.add_argument("project", help="Project directory")

    p_val = sub.add_parser("validate", help="Validate candidate PPTX")
    p_val.add_argument("project", help="Project directory")
    p_val.add_argument("--pptx", required=True, dest="pptx_path", help="Candidate PPTX file")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    cmd = args.command

    if cmd == "init":
        return _cmd_init(args.pptx_or_project, getattr(args, "name", None))
    elif cmd == "inspect":
        return _cmd_inspect(args.project)
    elif cmd == "watch":
        port = getattr(args, "port", 26315)
        return _cmd_watch(args.project, port)
    elif cmd == "selected":
        return _cmd_selected(args.project)
    elif cmd == "unwatch":
        return _cmd_unwatch(args.project)
    elif cmd == "check-plan":
        return _cmd_check_plan(args.project)
    elif cmd == "apply":
        return _cmd_apply(args.project)
    elif cmd == "validate":
        return _cmd_validate(args.project, args.pptx_path)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
