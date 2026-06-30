#!/usr/bin/env python3
"""
PPT Master - Dashboard Trace Store

Read and filter ``trace.jsonl`` events for dashboard log views.

Usage:
    events = query_trace(Path("projects/example"), limit=100)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _event_step(event: dict) -> int | None:
    raw = event.get("step")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _matches_query(event: dict, query: str) -> bool:
    needle = query.strip().lower()
    if not needle:
        return True
    haystacks: list[str] = []
    for key, value in event.items():
        if isinstance(value, (str, int, float, bool)):
            haystacks.append(str(value))
        elif key in {"detail", "message", "path", "file", "error"}:
            haystacks.append(str(value))
    return any(needle in value.lower() for value in haystacks)


def load_trace(project: Path) -> list[dict]:
    """Return parsed trace events, skipping malformed lines."""
    trace_file = project / "trace.jsonl"
    if not trace_file.is_file():
        return []
    events: list[dict] = []
    try:
        lines = trace_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def query_trace(
    project: Path,
    *,
    type_filter: Optional[str] = None,
    step: Optional[int] = None,
    query: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    order: str = "desc",
) -> dict:
    """Return a filtered trace payload for ``GET /api/log``."""
    events = load_trace(project)
    types = {part.strip() for part in type_filter.split(",")} if type_filter else set()
    types = {item for item in types if item}
    since_dt = _parse_time(since)
    until_dt = _parse_time(until)
    query_text = query or ""

    filtered = []
    for event in events:
        if types and event.get("type") not in types:
            continue
        if step is not None and _event_step(event) != step:
            continue
        if query_text and not _matches_query(event, query_text):
            continue
        event_dt = _parse_time(str(event.get("ts") or ""))
        if since_dt and event_dt and event_dt < since_dt:
            continue
        if until_dt and event_dt and event_dt > until_dt:
            continue
        filtered.append(event)

    normalized_order = "asc" if str(order).lower() == "asc" else "desc"
    reverse = normalized_order == "desc"
    filtered.sort(key=lambda e: str(e.get("ts") or ""), reverse=reverse)
    total = len(filtered)
    limit = max(1, min(limit, 1000))
    offset = max(0, offset)
    page = filtered[offset:offset + limit]
    return {
        "events": page,
        "total": total,
        "has_more": offset + limit < total,
        "offset": offset,
        "limit": limit,
        "order": normalized_order,
    }

