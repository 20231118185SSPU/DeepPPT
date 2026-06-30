#!/usr/bin/env python3
"""
PPT Master - Dashboard File Watcher

Poll notable project files and publish dashboard events on changes.

Usage:
    watcher = ProjectWatcher(project, bus, state_callback)
    watcher.start()

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from artifact_registry import iter_artifact_files
from event_bus import EventBus, utc_now


_WATCH_DIRS = {
    "sources",
    "templates",
    "analysis",
    "images",
    "icons",
    "svg_output",
    "svg_final",
    "notes",
    "exports",
    "backup",
    "confirm_ui",
    "live_preview",
}

_WATCH_ROOT_FILES = {
    "README.md",
    "design_spec.md",
    "spec_lock.md",
    "animations.json",
    "trace.jsonl",
    ".confirm_ui.lock",
    ".live_preview.lock",
}


class ProjectWatcher:
    """Lightweight polling watcher for project state changes."""

    def __init__(
        self,
        project: Path,
        bus: EventBus,
        state_callback: Callable[[], dict],
        *,
        interval: float = 1.0,
    ) -> None:
        self.project = project
        self.bus = bus
        self.state_callback = state_callback
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._snapshot: dict[str, int] = {}

    def start(self) -> None:
        """Start the background watcher thread."""
        if self._thread and self._thread.is_alive():
            return
        self._snapshot = self._scan()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the watcher thread."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _scan(self) -> dict[str, int]:
        snapshot: dict[str, int] = {}
        if not self.project.is_dir():
            return snapshot
        for name in _WATCH_ROOT_FILES:
            path = self.project / name
            if path.exists():
                snapshot[path.relative_to(self.project).as_posix()] = _stamp(path)
        for dirname in _WATCH_DIRS:
            root = self.project / dirname
            if not root.exists():
                continue
            if root.is_file():
                snapshot[root.relative_to(self.project).as_posix()] = _stamp(root)
                continue
            for path in root.rglob("*"):
                if path.is_file():
                    snapshot[path.relative_to(self.project).as_posix()] = _stamp(path)
        return snapshot

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            current = self._scan()
            added = [path for path in current if path not in self._snapshot]
            changed = [
                path for path, stamp in current.items()
                if path in self._snapshot and self._snapshot[path] != stamp
            ]
            removed = [path for path in self._snapshot if path not in current]
            if added or changed or removed:
                self._publish_changes(added, changed, removed)
                self._snapshot = current

    def _publish_changes(self, added: list[str], changed: list[str], removed: list[str]) -> None:
        for rel in added:
            path = self.project / rel
            if path.is_file():
                self.bus.publish(
                    "artifact:new",
                    {
                        "path": rel,
                        "name": path.name,
                        "type": _rough_type(rel),
                        "step": _rough_step(rel),
                        "size_bytes": path.stat().st_size if path.exists() else None,
                        "metadata": None,
                        "ts": utc_now(),
                    },
                )
        for rel in added + changed:
            if rel == "confirm_ui/recommendations.json":
                self.bus.publish(
                    "confirm:needed",
                    {
                        "tier": 1,
                        "confirm_url": None,
                        "fallback": False,
                        "recommendations_summary": None,
                        "ts": utc_now(),
                    },
                )
            elif rel == "confirm_ui/result.json":
                self.bus.publish(
                    "confirm:done",
                    {
                        "stage": "final",
                        "status": "confirmed",
                        "confirmed_at": utc_now(),
                        "fallback_confirmed": False,
                        "confirmed_values": None,
                        "ts": utc_now(),
                    },
                )
        self.bus.publish("pipeline:state", self.state_callback())


def _stamp(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def _rough_type(rel: str) -> str:
    top = rel.split("/", 1)[0]
    if top == "svg_output":
        return "svg"
    if top == "svg_final":
        return "svg_final"
    if top == "exports":
        return "pptx"
    if top == "notes":
        return "notes"
    if top == "images":
        return "image"
    if top == "sources":
        return "source"
    if top == "templates":
        return "template"
    if top == "analysis":
        return "analysis"
    if top == "backup":
        return "backup"
    if top == "confirm_ui":
        return "confirm"
    return "config"


def _rough_step(rel: str) -> int:
    top = rel.split("/", 1)[0]
    mapping = {
        "sources": 1,
        "analysis": 2,
        "templates": 3,
        "confirm_ui": 4,
        "images": 5,
        "svg_output": 6,
        "notes": 6,
        "svg_final": 7,
        "exports": 7,
        "backup": 7,
    }
    return mapping.get(top, 1)

