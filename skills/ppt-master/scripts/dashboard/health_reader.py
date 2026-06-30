#!/usr/bin/env python3
"""
PPT Master - Dashboard Health Reader

Derive a conservative project health summary from the already-read dashboard
state. The reader never runs generation, export, or quality commands.

Usage:
    summary = health_summary(project, pipeline_state)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import json
from pathlib import Path


_FAIL_STATUSES = {"FAIL", "BLOCKED", "ERROR", "FAILED"}
_WARN_STATUSES = {"WARN", "WARNING", "PASS_WITH_WARNINGS"}
_PASS_STATUSES = {"PASS", "CLEAN", "OK"}
_IMAGE_TERMINAL_MANUAL = {"Needs-Manual", "Needs Manual", "needs-manual"}


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _step_state(pipeline_state: dict, step_id: int) -> str | None:
    for step in pipeline_state.get("steps", []):
        if isinstance(step, dict) and step.get("step") == step_id:
            return str(step.get("state") or "")
    return None


def _quality_statuses(quality: dict | None) -> list[str]:
    if not quality:
        return []
    statuses = []
    for key in ("overall", "spec_compliance", "svg_quality", "e2e"):
        value = quality.get(key)
        if value:
            statuses.append(str(value).upper())
    return statuses


def _missing_manual_images(project: Path) -> list[str]:
    manifest = _read_json(project / "images" / "image_prompts.json")
    if not manifest:
        return []
    items = manifest.get("items", [])
    if not isinstance(items, list):
        return []
    missing = []
    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "")
        filename = Path(str(item.get("filename") or "")).name
        if not filename or status not in _IMAGE_TERMINAL_MANUAL:
            continue
        if not (project / "images" / filename).is_file():
            missing.append(filename)
    return missing


def _latest_error_trace(project: Path) -> str | None:
    trace_file = project / "trace.jsonl"
    if not trace_file.is_file():
        return None
    try:
        lines = trace_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines[-200:]):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "").lower()
        if event_type not in {"error", "failed", "failure"}:
            continue
        return str(event.get("detail") or event.get("message") or "Trace contains an error event.")
    return None


def health_summary(project: Path, pipeline_state: dict) -> dict:
    """Return ``healthy``, ``warn``, ``blocked``, or ``unknown`` with reasons."""
    reasons: list[str] = []
    warnings: list[str] = []
    evidence = 0

    current_step = pipeline_state.get("current_step")
    step4_state = _step_state(pipeline_state, 4)
    if step4_state:
        evidence += 1
    if step4_state in {"active", "pending"} and current_step == 4:
        reasons.append("Step 4 is waiting for user confirmation or Strategist artifacts.")

    quality_statuses = _quality_statuses(pipeline_state.get("quality_summary"))
    if quality_statuses:
        evidence += 1
    if any(status in _FAIL_STATUSES for status in quality_statuses):
        reasons.append("Quality summary contains a failing gate.")
    elif any(status in _WARN_STATUSES for status in quality_statuses):
        warnings.append("Quality summary contains warnings.")

    step6_state = _step_state(pipeline_state, 6)
    step7_state = _step_state(pipeline_state, 7)
    if step6_state:
        evidence += 1
    if current_step in {6, 7} and step6_state == "completed" and not quality_statuses:
        warnings.append("Step 6 appears complete, but no quality summary was found.")

    missing_images = _missing_manual_images(project)
    if missing_images:
        evidence += 1
    if missing_images and (current_step == 7 or step7_state in {"active", "completed"}):
        shown = ", ".join(missing_images[:5])
        suffix = "" if len(missing_images) <= 5 else f" (+{len(missing_images) - 5} more)"
        reasons.append(f"Step 7 is blocked by missing manual image files: {shown}{suffix}.")

    export_path = pipeline_state.get("export_path")
    if export_path:
        evidence += 1
    if step7_state == "active" and not export_path:
        warnings.append("Step 7 has started, but no PPTX export is available yet.")

    live_preview = pipeline_state.get("live_preview") or {}
    if current_step == 6 and not live_preview.get("running"):
        warnings.append("Live preview is not running while Step 6 is current.")

    latest_error = _latest_error_trace(project)
    if latest_error:
        evidence += 1
        warnings.append(f"Latest trace error: {latest_error}")

    has_progress_evidence = bool(
        pipeline_state.get("spec_lock_digest")
        or pipeline_state.get("svg_count")
        or export_path
        or quality_statuses
    )

    if reasons:
        status = "blocked"
    elif warnings:
        status = "warn"
        reasons = warnings
    elif has_progress_evidence and evidence >= 2 and current_step is not None and (
        not quality_statuses or any(status in _PASS_STATUSES for status in quality_statuses)
    ):
        status = "healthy"
        reasons = ["No blocking conditions detected from available dashboard state."]
    else:
        status = "unknown"
        reasons = ["Not enough state has been collected to determine project health."]

    return {
        "status": status,
        "reasons": reasons,
    }