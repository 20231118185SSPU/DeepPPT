#!/usr/bin/env python3
"""
PPT Master - Unified Dashboard Server

Read-only local dashboard for a PPT Master project. Serves pipeline state,
artifacts, quality summaries, trace events, and an SSE event stream.

Usage:
    python3 scripts/dashboard/server.py <project_path> [--port 8765]

Examples:
    python3 scripts/dashboard/server.py projects/my_deck
    python3 scripts/dashboard/server.py examples/ppt169_swiss_grid_systems --no-browser

Dependencies:
    flask>=3.0.0
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

from flask import Flask, Response, jsonify, request, send_from_directory

_DASHBOARD_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _DASHBOARD_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
if str(_DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from dashboard_launcher import find_safe_port, launch_dashboard_daemon  # noqa: E402
from server_common import (  # noqa: E402
    claim_lock,
    process_alive,
    read_lock,
    release_lock,
)

from artifact_registry import list_artifacts  # noqa: E402
from actions import command_preview, get_action, run_action  # noqa: E402
from bridge import confirm_ui_status, live_preview_status  # noqa: E402
from content_viewer import artifact_detail, resolve_project_file  # noqa: E402
from event_bus import EventBus, stream_events  # noqa: E402
from quality_reader import load_check, quality_report  # noqa: E402
from state_reader import read_pipeline_state  # noqa: E402
from trace_store import query_trace  # noqa: E402
from watcher import ProjectWatcher  # noqa: E402

configure_utf8_stdio()

logger = logging.getLogger("dashboard")
DEFAULT_PORT = 8765
LOCK_FILE_NAME = ".dashboard.lock"


def create_app(project_path: Path, bus: EventBus) -> Flask:
    """Create the Flask dashboard app."""
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    project = project_path.resolve()

    def state() -> dict:
        return read_pipeline_state(project)

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/api/state")
    def api_state():
        if not project.is_dir():
            return jsonify({"error": "Project not found or not initialized."}), 404
        return jsonify(state())

    @app.route("/api/step/<int:n>")
    def api_step(n: int):
        if n < 1 or n > 8:
            return jsonify({"error": "Invalid step number. Must be 1-8."}), 400
        include_artifacts = _bool_arg("include_artifacts", True)
        include_quality = _bool_arg("include_quality", True)
        include_trace = _bool_arg("include_trace", False)
        trace_limit = _int_arg("trace_limit", 50, 1, 500)

        pipeline = state()
        step = next((item for item in pipeline["steps"] if item["step"] == n), None)
        if not step:
            return jsonify({"error": "Invalid step number. Must be 1-8."}), 400
        detail = dict(step)
        detail["artifacts"] = (
            list_artifacts(project, step_filter=n)["artifacts"] if include_artifacts else []
        )
        detail["quality"] = quality_report(project) if include_quality and n in {6, 7} else None
        detail["trace_events"] = (
            query_trace(project, step=n, limit=trace_limit)["events"] if include_trace else []
        )
        return jsonify(detail)

    @app.route("/api/quality")
    def api_quality():
        report = quality_report(project)
        if report is None:
            return jsonify({"error": "No quality checks have been run yet."}), 404
        return jsonify(report)

    @app.route("/api/quality/<check>")
    def api_quality_check(check: str):
        item = load_check(project, check)
        if item is None:
            return jsonify({"error": f"Check '{check}' has not been run yet."}), 404
        return jsonify(item)

    @app.route("/api/artifacts")
    def api_artifacts():
        type_filter = request.args.get("type") or None
        step_filter = request.args.get("step") or None
        step_int = None
        if step_filter not in (None, ""):
            try:
                step_int = int(step_filter)
            except ValueError:
                return jsonify({"error": "step must be an integer"}), 400
        return jsonify(list_artifacts(project, type_filter=type_filter, step_filter=step_int))

    @app.route("/api/artifacts/<artifact_type>")
    def api_artifacts_type(artifact_type: str):
        return jsonify(list_artifacts(project, type_filter=artifact_type))

    @app.route("/api/artifact")
    def api_artifact_detail():
        rel_path = request.args.get("path") or ""
        if not rel_path:
            return jsonify({"error": "path is required"}), 400
        try:
            return jsonify(artifact_detail(project, rel_path))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except FileNotFoundError:
            return jsonify({"error": "artifact not found"}), 404

    @app.route("/artifact-file/<path:rel_path>")
    def artifact_file(rel_path: str):
        try:
            path = resolve_project_file(project, rel_path)
        except ValueError:
            return jsonify({"error": "path escapes project directory"}), 400
        except FileNotFoundError:
            return jsonify({"error": "artifact not found"}), 404
        return send_from_directory(path.parent, path.name)
    @app.route("/api/log")
    def api_log():
        step = request.args.get("step")
        step_int = int(step) if step and step.isdigit() else None
        return jsonify(query_trace(
            project,
            type_filter=request.args.get("type") or None,
            step=step_int,
            query=request.args.get("query") or None,
            since=request.args.get("since") or None,
            until=request.args.get("until") or None,
            limit=_int_arg("limit", 100, 1, 1000),
            offset=_int_arg("offset", 0, 0, 1000000),
            order=request.args.get("order") or "desc",
        ))

    @app.route("/api/config")
    def api_config():
        pipeline = state()
        return jsonify({
            "project_name": pipeline["project_name"],
            "project_path": pipeline["project_path"],
            "canvas_format": pipeline["canvas_format"],
            "canvas_info": pipeline["canvas_info"],
            "theme": {
                "header_bg": "#051C2C",
                "content_bg": "#FFFFFF",
                "ok": "#007A53",
                "warn": "#D46A00",
                "danger": "#E60012",
                "text_primary": "#1A1A1A",
                "text_secondary": "#666666",
            },
            "sse_url": "/api/events",
            "refresh_interval": 5000,
            "catalogs": None,
        })

    @app.route("/api/events")
    def api_events():
        last_id = request.headers.get("Last-Event-ID") or request.args.get("last_event_id")
        try:
            last_event_id = int(last_id) if last_id else None
        except ValueError:
            last_event_id = None
        client_id, client_queue, replay = bus.connect(last_event_id=last_event_id)
        client_queue.put(bus.publish("pipeline:state", state()))
        return Response(
            stream_events(bus, client_id, client_queue, replay),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.route("/api/bridges/confirm")
    def api_bridge_confirm():
        return jsonify(confirm_ui_status(project))

    @app.route("/api/bridges/live-preview")
    def api_bridge_live_preview():
        return jsonify(live_preview_status(project))

    @app.route("/api/actions/<action>", methods=["POST"])
    def api_run_action(action: str):
        payload = request.get_json(silent=True)
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return jsonify({"error": "JSON body must be an object."}), 400
        result, status = run_action(project, action, payload)
        return jsonify(result), status

    @app.route("/api/actions/<action>/preview")
    def api_action_preview(action: str):
        payload = {}
        if action == "run-quality":
            checks = request.args.get("checks")
            if checks:
                payload["checks"] = [item for item in checks.split(",") if item]
            mode = request.args.get("mode")
            if mode:
                payload["mode"] = mode
        result, status = command_preview(project, action, payload)
        return jsonify(result), status

    @app.route("/api/actions/<action_id>", methods=["GET"])
    @app.route("/api/actions/status/<action_id>")
    def api_action_status(action_id: str):
        result, status = get_action(project, action_id)
        return jsonify(result), status

    @app.route("/api/shutdown", methods=["POST"])
    def api_shutdown():
        lock_file = project / LOCK_FILE_NAME
        release_lock(lock_file)
        threading.Thread(target=_delayed_exit, daemon=True).start()
        return jsonify({"ok": True})

    return app


def _bool_arg(name: str, default: bool) -> bool:
    raw = request.args.get(name)
    if raw is None:
        return default
    return raw.lower() not in {"0", "false", "no"}


def _int_arg(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(value, maximum))


def _delayed_exit() -> None:
    time.sleep(0.2)
    os._exit(0)


def _shutdown_existing(lock_file: Path) -> int:
    existing = read_lock(lock_file)
    if not existing:
        return 0
    pid = int(existing.get("pid", 0) or 0)
    port = existing.get("port")
    if not process_alive(pid):
        try:
            lock_file.unlink(missing_ok=True)
        except OSError:
            pass
        return 0
    if port:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/shutdown",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except OSError:
            pass
    for _ in range(20):
        if not process_alive(pid):
            break
        time.sleep(0.1)
    if process_alive(pid):
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=5)
            else:
                os.kill(pid, signal.SIGTERM)
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        lock_file.unlink(missing_ok=True)
    except OSError:
        pass
    return 0


def _open_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except webbrowser.Error:
        pass


def _write_runtime_lock(lock_file: Path, project: Path, port: int, url: str) -> None:
    try:
        lock_file.write_text(
            json.dumps({
                "pid": os.getpid(),
                "port": port,
                "url": url,
                "project_path": str(project),
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }),
            encoding="utf-8",
        )
    except OSError:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the PPT Master unified dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Preferred port")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Start the dashboard in the background and return quickly",
    )
    parser.add_argument("--shutdown", action="store_true", help="Stop a running dashboard for this project")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] dashboard: %(message)s")
    args = build_parser().parse_args(argv)
    project = Path(args.project_path).resolve()
    lock_file = project / LOCK_FILE_NAME

    if args.shutdown:
        return _shutdown_existing(lock_file)
    if not project.is_dir():
        print(f"Error: project directory not found: {project}", file=sys.stderr)
        return 2
    if args.daemon:
        return launch_dashboard_daemon(
            project,
            port=args.port,
            host=args.host,
            no_browser=args.no_browser,
        )

    port = find_safe_port(args.port, args.host)
    existing = claim_lock(lock_file, port)
    if existing:
        running_port = existing.get("port")
        running_url = existing.get("url") or f"http://127.0.0.1:{running_port}/"
        print(f"Dashboard already running: {running_url}", file=sys.stderr)
        return 1

    bus = EventBus()
    app = create_app(project, bus)
    watcher = ProjectWatcher(project, bus, lambda: read_pipeline_state(project))
    watcher.start()
    display_host = "127.0.0.1" if args.host in {"127.0.0.1", "0.0.0.0"} else args.host
    url = f"http://{display_host}:{port}/"
    _write_runtime_lock(lock_file, project, port, url)
    print(f"Dashboard: {url}")
    if not args.no_browser:
        _open_browser(url)
    try:
        app.run(host=args.host, port=port, debug=False, threaded=True, use_reloader=False)
    finally:
        watcher.stop()
        release_lock(lock_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())








