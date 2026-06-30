#!/usr/bin/env python3
"""
PPT Master - Dashboard Safe Actions

Whitelisted, explicitly confirmed backend actions for the local dashboard.
This module starts only auxiliary UI/check commands; it does not run generation,
export, annotation application, or any arbitrary user-provided command.

Usage:
    from actions import get_action, run_action

Examples:
    run_action(Path("projects/my_deck"), "start-preview", {"confirm": True})

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bridge import confirm_ui_status, live_preview_status


_DASHBOARD_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _DASHBOARD_DIR.parent
_REPO_ROOT = _DASHBOARD_DIR.parents[3]

ACTION_DIR = Path("dashboard") / "actions"
ACTION_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
ALLOWED_ACTIONS = {"start-confirm", "start-preview", "run-quality"}
ALLOWED_QUALITY_CHECKS = {"spec", "svg", "harness"}
QUALITY_CHECK_ORDER = ("spec", "svg", "harness")
MAX_TAIL_CHARS = 6000
START_TIMEOUT = 90
QUALITY_TIMEOUT = 300


def run_action(project: Path, action: str, payload: dict[str, Any] | None) -> tuple[dict, int]:
    """Validate and start a whitelisted dashboard action."""
    payload = payload or {}
    if action not in ALLOWED_ACTIONS:
        return {"error": "Unknown action."}, 404
    if payload.get("confirm") is not True:
        return {"error": "Request must include confirm: true."}, 400

    try:
        project = _resolve_project(project)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    if action == "start-confirm":
        existing = confirm_ui_status(project)
        if existing.get("running"):
            return _record_existing(project, action, existing), 200
        command = _start_confirm_command(project)
        return _start_background_action(project, action, [command], START_TIMEOUT), 202

    if action == "start-preview":
        existing = live_preview_status(project)
        if existing.get("running"):
            return _record_existing(project, action, existing), 200
        command = _start_preview_command(project)
        return _start_background_action(project, action, [command], START_TIMEOUT), 202

    commands_or_error = _quality_commands(project, payload)
    if isinstance(commands_or_error, dict):
        return commands_or_error, 400
    return _start_background_action(project, action, commands_or_error, QUALITY_TIMEOUT), 202


def get_action(project: Path, action_id: str) -> tuple[dict, int]:
    """Return a previously recorded action status."""
    if not ACTION_ID_RE.fullmatch(action_id):
        return {"error": "Invalid action id."}, 400
    try:
        project = _resolve_project(project)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    record_path = _action_record_path(project, action_id)
    if not record_path.is_file():
        return {"error": "Action not found."}, 404
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"error": "Action record is unreadable."}, 500
    if not isinstance(record, dict):
        return {"error": "Action record is invalid."}, 500
    return _public_record(record), 200


def command_preview(project: Path, action: str, payload: dict[str, Any] | None = None) -> tuple[dict, int]:
    """Return the fixed command preview for a valid action without executing it."""
    if action not in ALLOWED_ACTIONS:
        return {"error": "Unknown action."}, 404
    try:
        project = _resolve_project(project)
    except ValueError as exc:
        return {"error": str(exc)}, 400
    payload = payload or {}
    if action == "start-confirm":
        commands = [_start_confirm_command(project)]
    elif action == "start-preview":
        commands = [_start_preview_command(project)]
    else:
        commands_or_error = _quality_commands(project, payload)
        if isinstance(commands_or_error, dict):
            return commands_or_error, 400
        commands = commands_or_error
    return {
        "action": action,
        "project_path": str(project),
        "commands": [_preview_command(command) for command in commands],
    }, 200


def _resolve_project(project: Path) -> Path:
    resolved = project.resolve()
    if not resolved.is_dir():
        raise ValueError("Project not found or not initialized.")
    if not _is_relative_to(resolved, _REPO_ROOT):
        raise ValueError("Project path must stay inside the repository workspace.")
    return resolved


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _start_confirm_command(project: Path) -> list[str]:
    return [
        sys.executable,
        str(_SCRIPTS_DIR / "confirm_ui" / "server.py"),
        str(project),
        "--daemon",
        "--no-browser",
    ]


def _start_preview_command(project: Path) -> list[str]:
    return [
        sys.executable,
        str(_SCRIPTS_DIR / "svg_editor" / "server.py"),
        str(project),
        "--daemon",
        "--live",
        "--no-browser",
    ]


def _quality_commands(project: Path, payload: dict[str, Any]) -> list[list[str]] | dict:
    mode = str(payload.get("mode") or "quick")
    if mode != "quick":
        return {"error": "run-quality currently allows only mode: quick."}

    raw_checks = payload.get("checks") or ["harness"]
    if not isinstance(raw_checks, list) or not all(isinstance(item, str) for item in raw_checks):
        return {"error": "checks must be a list of strings."}
    checks = [item for item in QUALITY_CHECK_ORDER if item in set(raw_checks)]
    unknown = sorted(set(raw_checks) - ALLOWED_QUALITY_CHECKS)
    if unknown:
        return {"error": f"Unsupported quality check: {', '.join(unknown)}."}
    if not checks:
        return {"error": "At least one quality check is required."}

    quality_dir = project / "quality"
    return [_quality_command(project, quality_dir, check) for check in checks]


def _quality_command(project: Path, quality_dir: Path, check: str) -> list[str]:
    if check == "spec":
        return [
            sys.executable,
            str(_SCRIPTS_DIR / "spec_compliance_check.py"),
            str(project),
            "--json",
        ]
    if check == "svg":
        return [
            sys.executable,
            str(_SCRIPTS_DIR / "svg_quality_checker.py"),
            str(project),
            "--integrated-review",
            "--ir-output",
            str(quality_dir / "integrated_review.json"),
        ]
    return [
        sys.executable,
        str(_SCRIPTS_DIR / "harness_gate.py"),
        str(project),
        "--quick",
        "--json",
    ]


def _start_background_action(
    project: Path,
    action: str,
    commands: list[list[str]],
    timeout_seconds: int,
) -> dict:
    action_id = _new_action_id(action)
    record = {
        "action_id": action_id,
        "action": action,
        "status": "running",
        "project_path": str(project),
        "command_preview": "\n".join(_preview_command(command) for command in commands),
        "commands": [_preview_command(command) for command in commands],
        "started_at": _now(),
        "updated_at": _now(),
        "stdout_tail": "",
        "stderr_tail": "",
    }
    _write_record(project, record)
    thread = threading.Thread(
        target=_run_commands,
        args=(project, action_id, commands, timeout_seconds),
        daemon=True,
    )
    thread.start()
    return _public_record(record)


def _record_existing(project: Path, action: str, status: dict) -> dict:
    action_id = _new_action_id(action)
    record = {
        "action_id": action_id,
        "action": action,
        "status": "existing",
        "project_path": str(project),
        "url": status.get("url"),
        "port": status.get("port"),
        "pid": status.get("pid"),
        "command_preview": "",
        "commands": [],
        "started_at": _now(),
        "updated_at": _now(),
        "stdout_tail": "",
        "stderr_tail": "",
    }
    _write_record(project, record)
    return _public_record(record)


def _run_commands(
    project: Path,
    action_id: str,
    commands: list[list[str]],
    timeout_seconds: int,
) -> None:
    record = _read_record(project, action_id)
    stdout_all: list[str] = []
    stderr_all: list[str] = []
    results: list[dict] = []
    status = "done"

    if record.get("action") == "run-quality":
        (project / "quality").mkdir(parents=True, exist_ok=True)

    for command in commands:
        result = _run_one_command(project, action_id, command, timeout_seconds)
        results.append({
            "command": _preview_command(command),
            "returncode": result["returncode"],
        })
        stdout_all.append(result["stdout"])
        stderr_all.append(result["stderr"])
        _persist_quality_stdout(project, command, result["stdout"])
        if result["returncode"] != 0:
            status = "failed"

    if record.get("action") == "start-confirm":
        service = confirm_ui_status(project)
        if service.get("running"):
            record["url"] = service.get("url")
    elif record.get("action") == "start-preview":
        service = live_preview_status(project)
        if service.get("running"):
            record["url"] = service.get("url")

    record.update({
        "status": status,
        "finished_at": _now(),
        "updated_at": _now(),
        "results": results,
        "stdout_tail": _tail("\n".join(stdout_all)),
        "stderr_tail": _tail("\n".join(stderr_all)),
    })
    _write_text(_stdout_path(project, action_id), "\n".join(stdout_all))
    _write_text(_stderr_path(project, action_id), "\n".join(stderr_all))
    _write_record(project, record)


def _run_one_command(
    project: Path,
    action_id: str,
    command: list[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    try:
        proc = subprocess.Popen(
            command,
            cwd=str(_REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        return {"returncode": proc.returncode, "stdout": stdout, "stderr": stderr}
    except subprocess.TimeoutExpired:
        _terminate_process(proc)
        stdout, stderr = proc.communicate()
        return {
            "returncode": -2,
            "stdout": stdout,
            "stderr": stderr + f"\nAction command timed out after {timeout_seconds}s.",
        }
    except OSError as exc:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Failed to start command for {action_id}: {exc}",
        }


def _terminate_process(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
    except OSError:
        return
    try:
        proc.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        try:
            proc.kill()
        except OSError:
            pass


def _persist_quality_stdout(project: Path, command: list[str], stdout: str) -> None:
    if not stdout.strip():
        return
    script_name = Path(command[1]).name if len(command) > 1 else ""
    targets = {
        "spec_compliance_check.py": "spec_compliance.json",
        "harness_gate.py": "harness.json",
    }
    filename = targets.get(script_name)
    if not filename:
        return
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return
    if not isinstance(parsed, dict):
        return
    quality_dir = project / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    _write_json(quality_dir / filename, parsed)


def _new_action_id(action: str) -> str:
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{action}-{uuid.uuid4().hex[:8]}"


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _preview_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def _public_record(record: dict) -> dict:
    return {
        key: value
        for key, value in record.items()
        if key not in {"stdout", "stderr"}
    }


def _tail(text: str) -> str:
    return text[-MAX_TAIL_CHARS:]


def _action_dir(project: Path) -> Path:
    return project / ACTION_DIR


def _action_record_path(project: Path, action_id: str) -> Path:
    return _action_dir(project) / f"{action_id}.json"


def _stdout_path(project: Path, action_id: str) -> Path:
    return _action_dir(project) / f"{action_id}.stdout.log"


def _stderr_path(project: Path, action_id: str) -> Path:
    return _action_dir(project) / f"{action_id}.stderr.log"


def _read_record(project: Path, action_id: str) -> dict:
    try:
        data = json.loads(_action_record_path(project, action_id).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"action_id": action_id, "status": "failed"}
    return data if isinstance(data, dict) else {"action_id": action_id, "status": "failed"}


def _write_record(project: Path, record: dict) -> None:
    action_dir = _action_dir(project)
    action_dir.mkdir(parents=True, exist_ok=True)
    _write_json(_action_record_path(project, record["action_id"]), record)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


