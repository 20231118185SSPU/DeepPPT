#!/usr/bin/env python3
"""
PPT Master - Confirm UI Gate

Validates that Step 4 Eight Confirmations were explicitly confirmed before
design_spec.md / spec_lock.md are written.

Usage:
    python3 scripts/confirm_ui_gate.py <project_path>

Examples:
    python3 skills/ppt-master/scripts/confirm_ui_gate.py projects/my_deck

Dependencies:
    None (only uses standard library)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


CONFIRM_DIR = "confirm_ui"
RECOMMENDATIONS_NAME = "recommendations.json"
RESULT_NAME = "result.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] Cannot read valid JSON: {path}", file=sys.stderr)
        print(f"       Fix: rewrite this file as valid JSON. Detail: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"[FAIL] {path} must contain a JSON object.", file=sys.stderr)
        print("       Fix: rewrite it as an object with status/confirmed_at fields.", file=sys.stderr)
        return None
    return data


def _parse_time(value: Any) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Eight Confirmations output before writing design_spec.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help="Accept result.json with fallback_confirmed=true for chat fallback confirmations.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project = Path(args.project_path).resolve()
    confirm_dir = project / CONFIRM_DIR
    rec_path = confirm_dir / RECOMMENDATIONS_NAME
    result_path = confirm_dir / RESULT_NAME

    print("=" * 72)
    print("PPT Master Confirm UI Gate")
    print("=" * 72)

    if not project.is_dir():
        print("FAIL")
        print(f"[FAIL] Project directory not found: {project}")
        print("       Fix: pass the canonical project folder created by project_manager.py.")
        return 2
    if not rec_path.exists():
        print("FAIL")
        print(f"[FAIL] Missing {rec_path}")
        print("       Fix: write confirm_ui/recommendations.json before launching or using chat fallback.")
        return 1
    if not result_path.exists():
        print("FAIL")
        print(f"[FAIL] Missing {result_path}")
        print("       Fix: wait for browser confirmation, or record an equivalent chat fallback result.json.")
        return 1

    rec = _load_json(rec_path)
    result = _load_json(result_path)
    if rec is None or result is None:
        print("FAIL")
        return 1

    errors: list[str] = []
    if result.get("status") != "confirmed":
        errors.append("result.json status must be 'confirmed'. Fix: confirm in the UI or write chat fallback status=confirmed.")

    confirmed_at = _parse_time(result.get("confirmed_at"))
    if confirmed_at is None:
        errors.append("result.json confirmed_at is missing or invalid ISO time. Fix: add confirmed_at after user confirmation.")
    else:
        try:
            rec_mtime = rec_path.stat().st_mtime
        except OSError:
            rec_mtime = 0
        try:
            result_mtime = result_path.stat().st_mtime
        except OSError:
            result_mtime = 0
        if result_mtime < rec_mtime or confirmed_at < rec_mtime:
            errors.append(
                "result.json is older than recommendations.json. Fix: re-confirm after the latest recommendations were written."
            )

    if result.get("fallback_confirmed") and not args.allow_fallback:
        errors.append(
            "result.json records chat fallback confirmation. Fix: rerun with --allow-fallback only when the user confirmed in chat."
        )

    if errors:
        print("FAIL")
        for error in errors:
            print(f"[FAIL] {error}")
        print("Return to: SKILL.md Step 4 Eight Confirmations")
        return 1

    print("PASS")
    if result.get("fallback_confirmed"):
        print("Chat fallback confirmation accepted.")
    else:
        print("Browser confirmation accepted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
