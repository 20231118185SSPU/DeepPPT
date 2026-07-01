#!/usr/bin/env python3
"""
PPT Master - Script Smoke Check

Verifies that all top-level scripts under scripts/ plus selected nested
entry points can be imported and that their CLI entry points respond to
--help without crashing.

Usage:
    python3 skills/ppt-master/scripts/smoke_check.py
    python3 skills/ppt-master/scripts/smoke_check.py --scripts-dir <path>
    python3 skills/ppt-master/scripts/smoke_check.py --skip-help

Examples:
    python3 skills/ppt-master/scripts/smoke_check.py
    python3 skills/ppt-master/scripts/smoke_check.py --skip-help

Dependencies:
    None for import checks (--help checks may need project deps)

Notes:
    - Import check: verifies the module loads without ImportError
    - --help check: invokes each script's CLI with --help, catches crashes
    - Scripts that require interactive input or long startup are skipped
    - Selected nested entry points are included when they are workflow-facing
    - Exit 0 = all pass; exit 1 = failures found
"""

import os
import sys
import argparse
import importlib
import importlib.util
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

# Scripts that need interactive input or a running server — skip --help check.
_SKIP_HELP: set[str] = {
    "confirm_ui/server.py",
    "svg_editor/server.py",
    "server_common.py",
}

# Nested entry points that are directly exposed in SKILL.md / AGENTS.md.
_EXTRA_ENTRYPOINTS: set[str] = {
    "dashboard/server.py",
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
    """Return smoke-covered script entry points."""
    scripts = [
        p for p in scripts_dir.glob("*.py")
        if p.name != "__init__.py" and p.name != "smoke_check.py"
    ]
    for rel in _EXTRA_ENTRYPOINTS:
        path = scripts_dir / rel
        if path.is_file():
            scripts.append(path)
    return sorted(scripts, key=lambda p: p.relative_to(scripts_dir).as_posix())


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


def dashboard_e2e_smoke(scripts_dir: Path) -> tuple[bool, str]:
    """Create a temporary project, start Dashboard, read state, then shut down."""
    repo_root = scripts_dir.parents[2]
    projects_dir = repo_root / "projects"
    project = None
    stage = "init"
    try:
        from project_manager import ProjectManager
        from dashboard_launcher import launch_dashboard_daemon

        projects_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"_smoke_dashboard_{stamp}_{uuid.uuid4().hex[:6]}"
        manager = ProjectManager(projects_dir)
        project = Path(manager.init_project(name, "ppt169")).resolve()

        stage = "launch"
        result = launch_dashboard_daemon(project, port=8765, no_browser=True)
        if result != 0:
            return False, f"launch returned {result}; project={project}"

        stage = "lock"
        lock = _wait_for_lock(project / ".dashboard.lock")
        if not lock:
            return False, f"dashboard lock not found; project={project}; log={_dashboard_log(project)}"
        port = int(lock.get("port", 0) or 0)
        url = str(lock.get("url") or f"http://127.0.0.1:{port}/")
        if not port:
            return False, f"dashboard lock missing port; project={project}; log={_dashboard_log(project)}"

        stage = "state"
        state = _get_json(f"{url.rstrip('/')}/api/state")
        missing = [
            key for key in (
                "project_name",
                "project_path",
                "canvas_format",
                "steps",
                "current_step",
                "confirm_ui",
                "live_preview",
            )
            if key not in state
        ]
        if missing:
            return False, f"/api/state missing {missing}; url={url}; log={_dashboard_log(project)}"

        stage = "shutdown"
        _post_json(f"{url.rstrip('/')}/api/shutdown")
        if not _wait_for_down(f"{url.rstrip('/')}/api/state"):
            return False, f"dashboard still responds after shutdown; url={url}; log={_dashboard_log(project)}"

        stage = "cleanup"
        if project.name.startswith("_smoke_dashboard_"):
            shutil.rmtree(project)
        return True, f"PASS dashboard-e2e url={url} log={_dashboard_log(project)}"
    except Exception as exc:
        return False, f"dashboard-e2e failed at {stage}: {type(exc).__name__}: {exc}; project={project}"


def _wait_for_lock(lock_path: Path, timeout: float = 10.0) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            time.sleep(0.2)
            continue
        if isinstance(data, dict):
            return data
    return None


def _get_json(url: str, timeout: float = 3.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return data


def _post_json(url: str, timeout: float = 3.0) -> None:
    request = urllib.request.Request(
        url,
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout):
        pass


def _wait_for_down(url: str, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=0.5).close()
        except (urllib.error.URLError, TimeoutError, OSError):
            return True
        time.sleep(0.2)
    return False


def _dashboard_log(project: Path) -> Path:
    return project / "dashboard" / "dashboard.log"


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
    parser.add_argument(
        "--dashboard-e2e",
        action="store_true",
        help="Run opt-in Dashboard daemon/API/shutdown smoke check",
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

    if args.dashboard_e2e:
        print("\nDashboard e2e")
        print("-" * 50)
        ok, msg = dashboard_e2e_smoke(scripts_dir)
        if ok:
            print(f"  [PASS] {msg}")
            passed += 1
        else:
            print(f"  [FAIL] {msg}")
            failed += 1

    total = passed + failed + skipped
    print(f"\n{'=' * 50}")
    print(f"Result: {passed} passed, {failed} failed, {skipped} skipped / {total} checks")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    configure_utf8_stdio()
    raise SystemExit(main())
