#!/usr/bin/env python3
"""
PPT Master - Dashboard UI Bridges

Read the existing Confirm UI and Live Preview lock files and expose their
runtime status to the dashboard.

Usage:
    from bridge import confirm_ui_status, live_preview_status

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from server_common import process_alive, read_lock  # noqa: E402


def _status_from_lock(lock: dict | None) -> dict:
    pid = int((lock or {}).get("pid", 0) or 0)
    port = int((lock or {}).get("port", 0) or 0)
    running = bool(pid and port and process_alive(pid))
    return {
        "running": running,
        "url": f"http://localhost:{port}" if running else None,
        "port": port if running else None,
        "pid": pid if running else None,
    }


def confirm_ui_status(project: Path) -> dict:
    """Return existing Confirm UI status from ``.confirm_ui.lock``."""
    return _status_from_lock(read_lock(project / ".confirm_ui.lock"))


def live_preview_status(project: Path) -> dict:
    """Return existing Live Preview status from the new or legacy lock."""
    new_lock = project / "live_preview" / "lock.json"
    legacy_lock = project / ".live_preview.lock"
    status = _status_from_lock(read_lock(new_lock))
    if status["running"]:
        return status
    return _status_from_lock(read_lock(legacy_lock))

