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
import time
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from server_common import process_alive, read_lock  # noqa: E402


def _mtime_iso(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return None


def _file_info(project: Path, rel_path: str) -> dict:
    path = project / rel_path
    return {
        "path": rel_path,
        "exists": path.is_file(),
        "mtime": _mtime_iso(path),
    }


def _latest_file(project: Path, rel_paths: list[str]) -> dict | None:
    existing = [_file_info(project, rel_path) for rel_path in rel_paths]
    existing = [item for item in existing if item["exists"]]
    if not existing:
        return None
    return max(existing, key=lambda item: item.get("mtime") or "")


def _project_matches(project: Path, lock: dict | None) -> bool | None:
    if not lock:
        return None
    raw_path = lock.get("project_path") or lock.get("project") or lock.get("root")
    if not raw_path:
        return None
    try:
        return Path(str(raw_path)).resolve() == project.resolve()
    except OSError:
        return False


def _status_from_lock(project: Path, lock_path: Path, lock: dict | None, bridge: str) -> dict:
    pid = int((lock or {}).get("pid", 0) or 0)
    port = int((lock or {}).get("port", 0) or 0)
    alive = bool(pid and process_alive(pid))
    running = bool(pid and port and alive)
    lock_exists = lock_path.is_file()
    lock_mtime = _mtime_iso(lock_path)
    lock_age_seconds = None
    if lock_exists:
        try:
            lock_age_seconds = max(0, int(time.time() - lock_path.stat().st_mtime))
        except OSError:
            lock_age_seconds = None
    project_matches = _project_matches(project, lock)
    stale_lock = bool(lock_exists and pid and not alive)
    return {
        "bridge": bridge,
        "running": running,
        "url": f"http://localhost:{port}" if running else None,
        "port": port if running else None,
        "pid": pid if running else None,
        "lock_path": str(lock_path) if lock_exists else None,
        "lock_mtime": lock_mtime,
        "lock_age_seconds": lock_age_seconds,
        "stale_lock": stale_lock,
        "project_matches": project_matches,
        "lock_project_path": (
            str((lock or {}).get("project_path") or (lock or {}).get("project") or "")
            or None
        ),
    }


def _confirm_next_action(status: dict, result_file: dict | None, recommendations_file: dict | None) -> str:
    if status.get("running"):
        return "open_confirm_ui"
    if result_file:
        return "review_confirm_result"
    if recommendations_file:
        return "start_confirm_ui"
    if status.get("stale_lock"):
        return "restart_confirm_ui"
    return "prepare_confirm_recommendations"


def _preview_next_action(status: dict, annotation_file: dict | None, edit_file: dict | None) -> str:
    if annotation_file or edit_file:
        return "review_live_preview_changes_after_export"
    if status.get("running"):
        return "open_live_preview"
    if status.get("stale_lock"):
        return "restart_live_preview"
    return "start_live_preview"


def confirm_ui_status(project: Path) -> dict:
    """Return existing Confirm UI status from ``.confirm_ui.lock``."""
    lock_path = project / ".confirm_ui.lock"
    status = _status_from_lock(project, lock_path, read_lock(lock_path), "confirm")
    result_file = _latest_file(project, ["confirm_ui/result.json"])
    recommendations_file = _latest_file(project, ["confirm_ui/recommendations.json"])
    status.update({
        "last_result_file": result_file,
        "last_result_mtime": result_file.get("mtime") if result_file else None,
        "last_recommendations_file": recommendations_file,
        "last_recommendations_mtime": (
            recommendations_file.get("mtime") if recommendations_file else None
        ),
    })
    status["next_action"] = _confirm_next_action(status, result_file, recommendations_file)
    return status


def live_preview_status(project: Path) -> dict:
    """Return existing Live Preview status from the new or legacy lock."""
    new_lock = project / "live_preview" / "lock.json"
    legacy_lock = project / ".live_preview.lock"
    status = _status_from_lock(project, new_lock, read_lock(new_lock), "live-preview")
    if status["running"]:
        status["lock_kind"] = "live_preview/lock.json"
    else:
        legacy_status = _status_from_lock(
            project,
            legacy_lock,
            read_lock(legacy_lock),
            "live-preview",
        )
        if legacy_status["running"] or not status.get("lock_path"):
            status = legacy_status
            status["lock_kind"] = ".live_preview.lock"
        else:
            status["lock_kind"] = "live_preview/lock.json"

    annotation_file = _latest_file(project, ["live_preview/annotations.jsonl"])
    edit_file = _latest_file(project, ["live_preview/edits.jsonl", "live_preview/edit_log.jsonl"])
    status.update({
        "last_annotation_file": annotation_file,
        "last_annotation_mtime": annotation_file.get("mtime") if annotation_file else None,
        "last_update_file": edit_file,
        "last_update_mtime": edit_file.get("mtime") if edit_file else None,
    })
    status["next_action"] = _preview_next_action(status, annotation_file, edit_file)
    return status
