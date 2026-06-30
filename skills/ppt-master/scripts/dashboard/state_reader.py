#!/usr/bin/env python3
"""
PPT Master - Dashboard State Reader

Derive a read-only PipelineState snapshot from a PPT Master project folder.

Usage:
    state = read_pipeline_state(Path("projects/example"))

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from project_utils import CANVAS_FORMATS, get_project_info  # noqa: E402
from update_spec import parse_lock  # noqa: E402

from artifact_registry import latest_pptx  # noqa: E402
from bridge import confirm_ui_status, live_preview_status  # noqa: E402
from health_reader import health_summary  # noqa: E402
from quality_reader import quality_summary  # noqa: E402


_STEP_NAMES = {
    1: "Source Content Processing",
    2: "Project Initialization",
    3: "Template Option",
    4: "Strategist Phase",
    5: "Image Acquisition",
    6: "Executor Phase",
    7: "Post-processing & Export",
    8: "Spec Review",
}


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _file_time(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return None


def _dir_has_files(path: Path, pattern: str = "*") -> bool:
    return path.is_dir() and any(p.is_file() for p in path.glob(pattern))


def _count_files(path: Path, pattern: str) -> int:
    return len(list(path.glob(pattern))) if path.is_dir() else 0


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _parse_spec_lock(project: Path) -> dict:
    lock_path = project / "spec_lock.md"
    if not lock_path.is_file():
        return {}
    try:
        data = parse_lock(lock_path)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _spec_digest(project: Path) -> str | None:
    lock_path = project / "spec_lock.md"
    if not lock_path.is_file():
        return None
    try:
        return hashlib.sha256(lock_path.read_bytes()).hexdigest()
    except OSError:
        return None


def _canvas_info(canvas_id: str | None) -> dict | None:
    if not canvas_id or canvas_id not in CANVAS_FORMATS:
        return None
    fmt = CANVAS_FORMATS[canvas_id]
    dim = str(fmt.get("dimensions", "")).replace("×", "x")
    return {
        "id": canvas_id,
        "label": fmt.get("name", canvas_id),
        "label_zh": fmt.get("name", canvas_id),
        "label_en": fmt.get("name", canvas_id),
        "dim": dim,
        "viewbox": fmt.get("viewbox", ""),
        "use_zh": None,
        "use_en": None,
    }


def _canvas_from_spec_lock(spec_lock: dict) -> str | None:
    canvas = spec_lock.get("canvas", {}) if isinstance(spec_lock.get("canvas"), dict) else {}
    raw_viewbox = str(canvas.get("viewBox") or canvas.get("viewbox") or "")
    for canvas_id, fmt in CANVAS_FORMATS.items():
        if raw_viewbox and raw_viewbox == fmt.get("viewbox"):
            return canvas_id
    raw_format = str(canvas.get("format") or "").lower()
    for canvas_id, fmt in CANVAS_FORMATS.items():
        if canvas_id in raw_format or str(fmt.get("name", "")).lower() in raw_format:
            return canvas_id
    return None


def _sub_step(id_: str, label: str, state: str, detail: str | None = None, progress: float | None = None) -> dict:
    return {
        "id": id_,
        "label": label,
        "state": state,
        "progress": progress,
        "detail": detail,
        "started_at": None,
        "completed_at": None,
    }


def _gate(requirements: list[tuple[str, bool, str | None]]) -> dict:
    return {
        "satisfied": all(item[1] for item in requirements),
        "requirements": [
            {"label": label, "met": met, "detail": detail}
            for label, met, detail in requirements
        ],
    }


def _step(step: int, state: str, *, sub_steps: list[dict] | None = None, gate: dict | None = None,
          started_at: str | None = None, completed_at: str | None = None, error: str | None = None) -> dict:
    return {
        "step": step,
        "name": _STEP_NAMES[step],
        "state": state,
        "blocking": step == 4,
        "started_at": started_at,
        "completed_at": completed_at,
        "sub_steps": sub_steps or [],
        "gate": gate,
        "error": error,
    }


def _confirmation_status(project: Path) -> tuple[str | None, str | None, bool | None]:
    result = _read_json(project / "confirm_ui" / "result.json")
    if not result:
        return None, None, None
    return (
        result.get("status"),
        result.get("generation_mode"),
        result.get("refine_spec"),
    )


def _build_steps(project: Path, page_count: int | None, svg_count: int) -> list[dict]:
    sources_ready = _dir_has_files(project / "sources") or any(
        (project / name).is_file() for name in ("research_report.md", "来源文档.md")
    )
    initialized = project.is_dir() and (project / "README.md").is_file()
    has_templates = _dir_has_files(project / "templates")
    has_recommendations = (project / "confirm_ui" / "recommendations.json").is_file()
    confirm_status, _, _ = _confirmation_status(project)
    has_design = (project / "design_spec.md").is_file()
    has_lock = (project / "spec_lock.md").is_file()
    has_image_prompts = (project / "images" / "image_prompts.json").is_file()
    has_images = _dir_has_files(project / "images")
    has_notes_total = (project / "notes" / "total.md").is_file()
    has_notes_split = _dir_has_files(project / "notes", "*.md")
    has_svg_final = _dir_has_files(project / "svg_final", "*.svg")
    has_export = bool(latest_pptx(project))
    has_spec_review = any((project / name).is_file() for name in ("spec_review.md", "spec-review.md"))

    upstream_complete = has_design or has_lock or svg_count > 0 or has_export

    step1_state = "completed" if sources_ready or upstream_complete else "pending"
    step2_state = "completed" if initialized or upstream_complete else "pending"
    step3_state = "completed" if has_templates else "skipped"
    if has_design and has_lock:
        step4_state = "completed"
    elif has_recommendations and confirm_status != "confirmed":
        step4_state = "active"
    else:
        step4_state = "pending" if step2_state == "completed" else "pending"

    if has_image_prompts or has_images:
        step5_state = "completed" if has_images else "active"
    else:
        step5_state = "skipped" if step4_state == "completed" else "pending"

    if page_count and svg_count >= page_count and has_notes_total:
        step6_state = "completed"
    elif svg_count > 0:
        step6_state = "active"
    else:
        step6_state = "pending" if step4_state == "completed" else "pending"

    if has_export:
        step7_state = "completed"
    elif has_notes_split or has_svg_final:
        step7_state = "active"
    else:
        step7_state = "pending" if step6_state == "completed" else "pending"

    step8_state = "completed" if has_spec_review else ("pending" if has_export else "pending")

    svg_progress = (svg_count / page_count) if page_count else None
    return [
        _step(
            1,
            step1_state,
            sub_steps=[
                _sub_step("sources", "Source files", "completed" if sources_ready else "pending"),
            ],
            gate=_gate([("Source material exists", sources_ready or upstream_complete, None)]),
        ),
        _step(
            2,
            step2_state,
            sub_steps=[
                _sub_step("project_dir", "Project directory", "completed" if project.is_dir() else "pending"),
                _sub_step("readme", "README", "completed" if initialized else "pending"),
            ],
            gate=_gate([("Project directory exists", project.is_dir(), str(project))]),
        ),
        _step(
            3,
            step3_state,
            sub_steps=[
                _sub_step("templates", "Template files", "completed" if has_templates else "skipped"),
            ],
            gate=_gate([("Explicit template path was applied", has_templates, None)]),
        ),
        _step(
            4,
            step4_state,
            sub_steps=[
                _sub_step("recommendations", "Recommendations", "completed" if has_recommendations else "pending"),
                _sub_step("confirmation", "User confirmation", "completed" if confirm_status == "confirmed" else ("active" if has_recommendations else "pending")),
                _sub_step("design_spec", "Design spec", "completed" if has_design else "pending"),
                _sub_step("spec_lock", "Spec lock", "completed" if has_lock else "pending"),
            ],
            gate=_gate([("Step 3 complete or skipped", step3_state in {"completed", "skipped"}, None)]),
            started_at=_file_time(project / "confirm_ui" / "recommendations.json"),
            completed_at=_file_time(project / "spec_lock.md") if has_lock else None,
        ),
        _step(
            5,
            step5_state,
            sub_steps=[
                _sub_step("image_prompts", "Image prompts", "completed" if has_image_prompts else "skipped"),
                _sub_step("images", "Image pool", "completed" if has_images else "skipped"),
            ],
            gate=_gate([("Strategist artifacts ready", has_design and has_lock, None)]),
        ),
        _step(
            6,
            step6_state,
            sub_steps=[
                _sub_step("svg_generate", "SVG generation", "completed" if step6_state == "completed" else ("active" if svg_count else "pending"),
                          f"{svg_count}/{page_count or '?'} SVG files", svg_progress),
                _sub_step("notes_total", "Speaker notes", "completed" if has_notes_total else "pending"),
            ],
            gate=_gate([("spec_lock.md exists", has_lock, None)]),
        ),
        _step(
            7,
            step7_state,
            sub_steps=[
                _sub_step("notes_split", "Split notes", "completed" if has_notes_split else "pending"),
                _sub_step("svg_final", "Finalize SVG", "completed" if has_svg_final else "pending"),
                _sub_step("pptx_export", "PPTX export", "completed" if has_export else "pending"),
            ],
            gate=_gate([("SVG output exists", svg_count > 0, None), ("notes/total.md exists", has_notes_total, None)]),
        ),
        _step(
            8,
            step8_state,
            sub_steps=[
                _sub_step("spec_review", "Spec review", "completed" if has_spec_review else "pending"),
            ],
            gate=_gate([("Export exists", has_export, None)]),
        ),
    ]


def _current_step(steps: list[dict]) -> int | None:
    for step in steps:
        if step["state"] == "active":
            return step["step"]
    for step in steps:
        if step["state"] == "pending":
            return step["step"]
    return steps[-1]["step"] if steps else None


def read_pipeline_state(project: Path) -> dict:
    """Return the full PipelineState payload."""
    info = get_project_info(str(project))
    spec_lock = _parse_spec_lock(project)
    rhythm = spec_lock.get("page_rhythm", {}) if isinstance(spec_lock.get("page_rhythm"), dict) else {}
    page_count = len(rhythm) if rhythm else None
    svg_count = _count_files(project / "svg_output", "*.svg")
    steps = _build_steps(project, page_count, svg_count)
    confirm_status, generation_mode, _ = _confirmation_status(project)
    canvas_id = info.get("format")
    if canvas_id == "unknown":
        canvas_id = _canvas_from_spec_lock(spec_lock)
    payload = {
        "project_name": info.get("name") or project.name,
        "project_path": str(project.resolve()),
        "canvas_format": canvas_id,
        "canvas_info": _canvas_info(canvas_id),
        "current_step": _current_step(steps),
        "steps": steps,
        "generation_mode": generation_mode,
        "confirm_status": confirm_status,
        "spec_lock_digest": _spec_digest(project),
        "spec_lock_verified": None,
        "quality_summary": quality_summary(project),
        "page_count": page_count,
        "svg_count": svg_count,
        "export_path": latest_pptx(project),
        "live_preview": live_preview_status(project),
        "confirm_ui": confirm_ui_status(project),
        "derived_at": _now(),
    }
    payload["health_summary"] = health_summary(project, payload)
    return payload


