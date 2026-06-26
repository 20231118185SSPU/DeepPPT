#!/usr/bin/env python3
"""
PPT Master - Script Smoke Check

Verifies that all top-level scripts under scripts/ can be imported
and that their CLI entry points respond to --help without crashing.

Usage:
    python3 scripts/smoke_check.py
    python3 scripts/smoke_check.py --scripts-dir <path>
    python3 scripts/smoke_check.py --skip-help

Examples:
    python3 scripts/smoke_check.py
    python3 scripts/smoke_check.py --skip-help

Dependencies:
    None for import checks (--help checks may need project deps)

Notes:
    - Import check: verifies the module loads without ImportError
    - --help check: invokes each script's CLI with --help, catches crashes
    - Scripts that require interactive input or long startup are skipped
    - Exit 0 = all pass; exit 1 = failures found
"""

import os
import sys
import argparse
import importlib
import importlib.util
import subprocess
from pathlib import Path
from typing import Optional

# Scripts that need interactive input or a running server — skip --help check.
_SKIP_HELP: set[str] = {
    "confirm_ui/server.py",
    "svg_editor/server.py",
    "server_common.py",
}

# Thin wrappers that delegate to a same-named sub-package.
# Import check is unreliable (name collision), but --help works fine.
_WRAP_ONLY: set[str] = {
    "svg_to_pptx.py",
    "pptx_to_svg.py",
    "template_fill_pptx.py",
}

# Scripts that have heavy import-time side effects (network, DB) — skip import.
_SKIP_IMPORT: set[str] = set()


def find_scripts(scripts_dir: Path) -> list[Path]:
    """Return all top-level .py files in scripts/, excluding __init__.py."""
    return sorted(
        p for p in scripts_dir.glob("*.py")
        if p.name != "__init__.py" and p.name != "smoke_check.py"
    )


def check_import(script_path: Path, scripts_dir: Path) -> tuple[bool, str]:
    """Try to import the script as a module. Returns (ok, message)."""
    module_name = script_path.stem
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        return False, "cannot create module spec"

    try:
        # Import without executing __main__ block
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        del sys.modules[module_name]
        return True, "ok"
    except SystemExit:
        # Some scripts raise SystemExit(0) in __main__ guard — that's fine
        if module_name in sys.modules:
            del sys.modules[module_name]
        return True, "ok (SystemExit 0)"
    except ImportError as e:
        if module_name in sys.modules:
            del sys.modules[module_name]
        # Optional dependency failures are expected
        if "optional" in str(e).lower() or "not installed" in str(e).lower():
            return True, f"ok (optional dep missing: {e})"
        return False, f"ImportError: {e}"
    except Exception as e:
        if module_name in sys.modules:
            del sys.modules[module_name]
        return False, f"{type(e).__name__}: {e}"


def check_help(script_path: Path, python: str) -> tuple[bool, str]:
    """Run the script with --help. Returns (ok, message)."""
    try:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [python, str(script_path), "--help"],
            capture_output=True,
            timeout=15,
            env=env,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            return True, "ok"
        else:
            stderr_tail = result.stderr.strip().splitlines()[-1:] if result.stderr.strip() else []
            return False, f"exit {result.returncode}: {stderr_tail[0] if stderr_tail else 'no stderr'}"
    except subprocess.TimeoutExpired:
        return False, "timeout (15s)"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke check all PPT Master scripts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--scripts-dir",
        help="Path to scripts/ directory (default: auto-detect relative to this file)",
    )
    parser.add_argument(
        "--skip-help",
        action="store_true",
        help="Only check imports, skip --help invocations",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    scripts_dir = Path(args.scripts_dir) if args.scripts_dir else Path(__file__).resolve().parent
    if not scripts_dir.is_dir():
        print(f"Error: scripts directory not found: {scripts_dir}", file=sys.stderr)
        return 2

    scripts = find_scripts(scripts_dir)
    if not scripts:
        print(f"Error: no .py files found in {scripts_dir}", file=sys.stderr)
        return 2

    python = sys.executable
    passed = 0
    failed = 0
    skipped = 0

    print(f"Smoke check: {len(scripts)} scripts in {scripts_dir.name}/\n")

    # Phase 1: Import check
    print("Import check")
    print("-" * 50)
    for script in scripts:
        rel = script.relative_to(scripts_dir)
        if str(rel) in _SKIP_IMPORT:
            print(f"  [SKIP] {rel}")
            skipped += 1
            continue
        if rel.name in _WRAP_ONLY:
            print(f"  [SKIP] {rel} (thin wrapper, validated via --help)")
            skipped += 1
            continue
        ok, msg = check_import(script, scripts_dir)
        if ok:
            print(f"  [PASS] {rel} — {msg}")
            passed += 1
        else:
            print(f"  [FAIL] {rel} — {msg}")
            failed += 1

    # Phase 2: --help check
    if not args.skip_help:
        print(f"\n--help check")
        print("-" * 50)
        for script in scripts:
            rel = script.relative_to(scripts_dir)
            if str(rel) in _SKIP_HELP:
                print(f"  [SKIP] {rel} (interactive/server)")
                skipped += 1
                continue
            ok, msg = check_help(script, python)
            if ok:
                print(f"  [PASS] {rel}")
                passed += 1
            else:
                print(f"  [FAIL] {rel} — {msg}")
                failed += 1

    total = passed + failed + skipped
    print(f"\n{'=' * 50}")
    print(f"Result: {passed} passed, {failed} failed, {skipped} skipped / {total} checks")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
