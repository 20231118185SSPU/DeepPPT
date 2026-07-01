#!/usr/bin/env python3
"""
PPT Master - Dashboard Trace Writer

Best-effort JSONL event writer for production scripts. Trace writes must never
block the main PPT workflow.

Usage:
    from trace_writer import trace_event
    trace_event(Path("projects/example"), "step_start", "Step 2 started")

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def trace_event(project: str | Path, event_type: str, detail: str = "", **extra: Any) -> None:
    """Append one normalized event to ``<project>/trace.jsonl``."""
    project_path = Path(project)
    event = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "type": event_type,
        "detail": detail,
    }
    for key, value in extra.items():
        if value is not None:
            event[key] = _json_safe(value)

    try:
        with (project_path / "trace.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        pass


def artifact_created(
    project: str | Path,
    path: str | Path,
    artifact_type: str,
    *,
    step: int | None = None,
    detail: str = "",
    producer: str = "",
) -> None:
    """Record a created artifact with basic file metadata."""
    project_path = Path(project)
    artifact_path = Path(path)
    if artifact_path.is_absolute():
        try:
            rel_path = artifact_path.resolve().relative_to(project_path.resolve()).as_posix()
        except ValueError:
            rel_path = str(artifact_path)
    else:
        rel_path = artifact_path.as_posix()
        artifact_path = project_path / artifact_path

    size_bytes = None
    try:
        size_bytes = artifact_path.stat().st_size
    except OSError:
        pass

    trace_event(
        project_path,
        "artifact_created",
        detail or f"{artifact_type} created",
        path=rel_path,
        artifact_type=artifact_type,
        step=step,
        size_bytes=size_bytes,
        producer=producer,
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
