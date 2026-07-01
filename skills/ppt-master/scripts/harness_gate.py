#!/usr/bin/env python3
"""
PPT Master - Harness Gate (Aggregated Quality Gate)

Runs three upstream check scripts and produces a unified PASS/FAIL report.
Designed to be called before Step 7 Post-process to block不合格 output.

Usage:
    python3 scripts/harness_gate.py <project_path>
    python3 scripts/harness_gate.py <project_path> --quick
    python3 scripts/harness_gate.py <project_path> --quick --read-only
    python3 scripts/harness_gate.py <project_path> --json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR / "dashboard") not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR / "dashboard"))

from trace_writer import trace_event  # noqa: E402


def _run_check(cmd: list[str], label: str) -> dict:
    """Run a check script and return {label, passed, skipped, stdout, stderr, returncode}."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        return {
            "label": label,
            "passed": result.returncode == 0,
            "skipped": False,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "command": cmd,
        }
    except FileNotFoundError:
        return {
            "label": label,
            "passed": False,
            "skipped": False,
            "stdout": "",
            "stderr": f"Script not found: {cmd[1]}",
            "returncode": -1,
            "command": cmd,
        }
    except subprocess.TimeoutExpired:
        return {
            "label": label,
            "passed": False,
            "skipped": False,
            "stdout": "",
            "stderr": "Check timed out (120s)",
            "returncode": -2,
            "command": cmd,
        }


def run_harness_gate(project_path: str, quick: bool = False) -> dict:
    """
    Run all three gate checks and return a unified report.

    Returns:
        {
            "spec_compliance": "PASS" | "FAIL",
            "svg_quality": "PASS" | "FAIL",
            "e2e": "PASS" | "FAIL" | "SKIP",
            "overall": "PASS" | "FAIL",
            "details": [...]
        }
    """
    project = Path(project_path)
    python = sys.executable

    checks = []

    # 1. spec_compliance_check.py
    spec_cmd = [python, str(SCRIPTS_DIR / "spec_compliance_check.py"), str(project)]
    checks.append(_run_check(spec_cmd, "spec_compliance"))

    # 2. svg_quality_checker.py
    svg_cmd = [python, str(SCRIPTS_DIR / "svg_quality_checker.py"), str(project / "svg_output")]
    checks.append(_run_check(svg_cmd, "svg_quality"))

    # 3. e2e_validate.py (optional in quick mode)
    if quick:
        checks.append({
            "label": "e2e",
            "passed": True,
            "skipped": True,
            "stdout": "Skipped (--quick mode)",
            "stderr": "",
            "returncode": 0,
            "command": [],
        })
    else:
        e2e_cmd = [python, str(SCRIPTS_DIR / "e2e_validate.py"), str(project)]
        checks.append(_run_check(e2e_cmd, "e2e"))

    # Aggregate
    report = {}
    for check in checks:
        if check.get("skipped"):
            report[check["label"]] = "SKIP"
        else:
            report[check["label"]] = "PASS" if check["passed"] else "FAIL"

    report["overall"] = "PASS" if all(c["passed"] for c in checks) else "FAIL"
    report["details"] = checks
    report["checked_at"] = datetime.now(tz=timezone.utc).isoformat()

    return report


def set_write_mode(report: dict, read_only: bool) -> None:
    """Annotate whether the current invocation writes dashboard artifacts."""
    report["write_mode"] = "read-only" if read_only else "dashboard-artifacts"


def write_report(project: Path, report: dict) -> None:
    """Best-effort write of the dashboard-readable harness report."""
    try:
        quality_dir = project / "quality"
        quality_dir.mkdir(parents=True, exist_ok=True)
        (quality_dir / "harness.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass


def trace_report(project: Path, report: dict) -> None:
    """Best-effort trace event for the aggregate quality gate."""
    failed = [
        item.get("label")
        for item in report.get("details", [])
        if isinstance(item, dict) and not item.get("passed", False)
    ]
    trace_event(
        project,
        "gate_result",
        f"Harness gate {report.get('overall')}",
        step=6,
        gate="harness",
        status=report.get("overall"),
        failed_scripts=failed,
        report_path="quality/harness.json",
        producer="harness_gate.py",
    )


def print_report(report: dict) -> None:
    """Pretty-print the harness gate report."""
    print("=" * 60)
    print("  HARNESS GATE REPORT")
    print("=" * 60)

    for label in ["spec_compliance", "svg_quality", "e2e"]:
        status = report.get(label, "N/A")
        if status == "PASS":
            icon = "✅"
        elif status == "SKIP":
            icon = "⏭"
        else:
            icon = "❌"
        print(f"  {icon} {label:<20s} {status}")

    print("-" * 60)
    overall = report["overall"]
    icon = "✅" if overall == "PASS" else "❌"
    print(f"  {icon} {'OVERALL':<20s} {overall}")
    print("=" * 60)

    # Print details for any failures
    for check in report.get("details", []):
        if not check["passed"]:
            print(f"\n--- {check['label']} FAILED ---")
            if check["stdout"]:
                print(check["stdout"])
            if check["stderr"]:
                print(check["stderr"], file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="PPT Master Harness Gate — aggregated quality gate."
    )
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--quick", action="store_true", help="Skip e2e validation")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument(
        "--read-only",
        "--no-write",
        action="store_true",
        help=(
            "Do not write quality/harness.json or append trace.jsonl. "
            "Use for regression checks that must leave the project tree unchanged."
        ),
    )
    args = parser.parse_args(argv)

    project = Path(args.project_path)
    if not project.is_dir():
        print(f"Error: {project} is not a directory", file=sys.stderr)
        return 1

    report = run_harness_gate(str(project), quick=args.quick)
    set_write_mode(report, args.read_only)
    if not args.read_only:
        write_report(project, report)
        trace_report(project, report)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)

    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
