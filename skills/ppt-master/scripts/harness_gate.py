#!/usr/bin/env python3
"""
PPT Master - Harness Gate (Aggregated Quality Gate)

Runs three upstream check scripts and produces a unified PASS/FAIL report.
Designed to be called before Step 7 Post-process to block不合格 output.

Usage:
    python3 scripts/harness_gate.py <project_path>
    python3 scripts/harness_gate.py <project_path> --quick
    python3 scripts/harness_gate.py <project_path> --json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent


def _run_check(cmd: list[str], label: str) -> dict:
    """Run a check script and return {label, passed, stdout, stderr, returncode}."""
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
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {
            "label": label,
            "passed": False,
            "stdout": "",
            "stderr": f"Script not found: {cmd[1]}",
            "returncode": -1,
        }
    except subprocess.TimeoutExpired:
        return {
            "label": label,
            "passed": False,
            "stdout": "",
            "stderr": "Check timed out (120s)",
            "returncode": -2,
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
            "stdout": "Skipped (--quick mode)",
            "stderr": "",
            "returncode": 0,
        })
    else:
        e2e_cmd = [python, str(SCRIPTS_DIR / "e2e_validate.py"), str(project), "--quick"]
        checks.append(_run_check(e2e_cmd, "e2e"))

    # Aggregate
    report = {}
    for check in checks:
        report[check["label"]] = "PASS" if check["passed"] else "FAIL"

    report["overall"] = "PASS" if all(c["passed"] for c in checks) else "FAIL"
    report["details"] = checks

    return report


def print_report(report: dict) -> None:
    """Pretty-print the harness gate report."""
    print("=" * 60)
    print("  HARNESS GATE REPORT")
    print("=" * 60)

    for label in ["spec_compliance", "svg_quality", "e2e"]:
        status = report.get(label, "N/A")
        icon = "✅" if status == "PASS" else "❌"
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
    args = parser.parse_args(argv)

    project = Path(args.project_path)
    if not project.is_dir():
        print(f"Error: {project} is not a directory", file=sys.stderr)
        return 1

    report = run_harness_gate(str(project), quick=args.quick)

    if args.json:
        # Strip details for clean JSON output
        compact = {k: v for k, v in report.items() if k != "details"}
        print(json.dumps(compact, indent=2, ensure_ascii=False))
    else:
        print_report(report)

    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
