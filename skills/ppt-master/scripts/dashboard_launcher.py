#!/usr/bin/env python3
"""
PPT Master - Dashboard Launcher

Best-effort background launcher for the unified Dashboard. It reuses an
existing per-project dashboard lock when present, otherwise starts the
Dashboard server detached and returns quickly.

Usage:
    python3 scripts/dashboard_launcher.py <project_path> [--port 8765]

Examples:
    python3 scripts/dashboard_launcher.py projects/my_deck

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from server_common import process_alive, read_lock  # noqa: E402

DEFAULT_PORT = 8765
LOCK_FILE_NAME = ".dashboard.lock"
DASHBOARD_DIR_NAME = "dashboard"
DASHBOARD_LOG_NAME = "dashboard.log"
UNSAFE_PORTS = {5060}
READY_TIMEOUT_SECONDS = 8.0


def find_safe_port(preferred: int, host: str = "127.0.0.1", span: int = 50) -> int:
    """Return a bindable local port, skipping Chrome's unsafe port 5060."""
    upper = min(65536, preferred + span)
    for port in range(preferred, upper):
        if port in UNSAFE_PORTS:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, port))
                return port
            except OSError:
                continue
    if preferred in UNSAFE_PORTS:
        return preferred + 1
    return preferred


def launch_dashboard_daemon(
    project: Path,
    *,
    port: int = DEFAULT_PORT,
    host: str = "127.0.0.1",
    no_browser: bool = False,
) -> int:
    """Start or reuse a detached Dashboard service for a project."""
    project = project.resolve()
    if not project.is_dir():
        print(f"Error: project directory not found: {project}", file=sys.stderr)
        return 2

    lock_file = project / LOCK_FILE_NAME
    existing = read_lock(lock_file)
    if existing and process_alive(int(existing.get("pid", 0) or 0)):
        url = _lock_url(existing)
        print(f"Dashboard already running: {url}")
        if not no_browser:
            _open_browser(url)
        return 0
    if existing:
        _remove_stale_lock(lock_file)

    dashboard_dir = project / DASHBOARD_DIR_NAME
    try:
        dashboard_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Warning: cannot create dashboard runtime directory: {dashboard_dir} ({exc})")
        return 0

    launch_port = find_safe_port(port, host)
    display_host = "127.0.0.1" if host in {"127.0.0.1", "0.0.0.0"} else host
    expected_url = f"http://{display_host}:{launch_port}/"
    log_path = dashboard_dir / DASHBOARD_LOG_NAME
    cmd = [
        sys.executable,
        str(_SCRIPTS_DIR / "dashboard" / "server.py"),
        str(project),
        "--host",
        host,
        "--port",
        str(launch_port),
        "--no-browser",
    ]

    popen_kwargs: dict = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    else:
        popen_kwargs["start_new_session"] = True

    try:
        with log_path.open("a", encoding="utf-8") as log:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                **popen_kwargs,
            )
    except OSError as exc:
        print(f"Warning: Dashboard failed to launch: {exc}")
        print(f"Warning: Dashboard log path: {log_path}")
        return 0

    url = _wait_for_dashboard(lock_file, proc, expected_url)
    if proc.poll() is not None:
        print(
            f"Warning: Dashboard process exited during startup "
            f"(code {proc.returncode}); see {log_path}"
        )
        return 0
    if not _url_ready(url):
        print(f"Warning: Dashboard may still be starting: {url} (log: {log_path})")
    else:
        print(f"Dashboard: {url}")
    print(f"Dashboard log: {log_path}")
    if not no_browser:
        _open_browser(url)
    return 0


def _wait_for_dashboard(lock_file: Path, proc: subprocess.Popen, fallback_url: str) -> str:
    deadline = time.time() + READY_TIMEOUT_SECONDS
    last_url = fallback_url
    while time.time() < deadline:
        if proc.poll() is not None:
            return last_url
        current = read_lock(lock_file)
        if current:
            last_url = _lock_url(current)
            if _url_ready(last_url):
                return last_url
        elif _url_ready(last_url):
            return last_url
        time.sleep(0.2)
    return last_url


def _url_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=0.8) as response:
            return response.status < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _lock_url(lock: dict) -> str:
    raw_url = str(lock.get("url") or "").strip()
    if raw_url:
        return _with_trailing_slash(raw_url)
    port = lock.get("port")
    return _with_trailing_slash(f"http://127.0.0.1:{port}")


def _with_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else f"{url}/"


def _remove_stale_lock(lock_file: Path) -> None:
    try:
        lock_file.unlink(missing_ok=True)
    except OSError:
        pass


def _open_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except webbrowser.Error:
        print(f"Warning: browser did not auto-open; open {url} manually")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start the PPT Master Dashboard in the background.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Preferred port")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return launch_dashboard_daemon(
        Path(args.project_path),
        port=args.port,
        host=args.host,
        no_browser=args.no_browser,
    )


if __name__ == "__main__":
    raise SystemExit(main())
