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
_DASHBOARD_DIR = Path(__file__).resolve().parent
if str(_DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD_DIR))

from project_utils import CANVAS_FORMATS, get_project_info  # noqa: E402
from update_spec import parse_lock  # noqa: E402

from artifact_registry import latest_pptx  # noqa: E402
from bridge import dashboard_status, confirm_ui_status, live_preview_status  # noqa: E402
from health_reader import health_summary  # noqa: E402
from officecli_reader import (  # noqa: E402
    officecli_runtime_state,
    office_sources_state,
    native_revision_state,
)
from quality_reader import page_expression_summary, quality_summary  # noqa: E402

_SKILL_DIR = Path(__file__).resolve().parents[2]
_TEMPLATE_INDEXES = {
    "brand": _SKILL_DIR / "templates" / "brands" / "brands_index.json",
    "layout": _SKILL_DIR / "templates" / "layouts" / "layouts_index.json",
    "deck": _SKILL_DIR / "templates" / "decks" / "decks_index.json",
}
_TEMPLATE_DIRS = {
    "brand": "templates/brands",
    "layout": "templates/layouts",
    "deck": "templates/decks",
}


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

_STEP_NAMES_ZH = {
    1: "源内容处理",
    2: "项目初始化",
    3: "模板选择",
    4: "设计确认",
    5: "图片获取",
    6: "页面执行",
    7: "后处理与导出",
    8: "规格复盘",
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


def _read_text_head(path: Path, max_chars: int = 4096) -> str:
    try:
        return path.read_text(encoding="utf-8")[:max_chars]
    except OSError:
        return ""


def _yaml_frontmatter_value(text: str, key: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    prefix = f"{key}:"
    for line in text[3:end].splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip().strip("\"'")
    return None


def _template_kind_from_project(project: Path) -> str | None:
    spec = project / "templates" / "design_spec.md"
    kind = _yaml_frontmatter_value(_read_text_head(spec), "kind")
    if kind in _TEMPLATE_INDEXES:
        return kind
    return None


def _template_index_entries(limit_per_kind: int = 20) -> dict:
    entries_by_kind: dict[str, list[dict]] = {}
    counts: dict[str, int] = {}
    for kind, index_path in _TEMPLATE_INDEXES.items():
        data = _read_json(index_path) or {}
        items = []
        for template_id, meta in sorted(data.items(), key=lambda item: str(item[0]).lower()):
            if not isinstance(meta, dict):
                meta = {}
            base_dir = _TEMPLATE_DIRS[kind]
            entry = {
                "id": str(template_id),
                "name": str(meta.get("name") or template_id),
                "name_zh": str(meta.get("name_zh") or meta.get("name") or template_id),
                "kind": kind,
                "path": f"skills/ppt-master/{base_dir}/{template_id}/",
                "description": str(meta.get("summary") or meta.get("description") or ""),
                "description_zh": str(
                    meta.get("summary_zh")
                    or meta.get("description_zh")
                    or meta.get("summary")
                    or meta.get("description")
                    or ""
                ),
                "scope": str(meta.get("scope") or meta.get("canvas_format") or ""),
                "preview_files": _template_preview_files(kind, str(template_id)),
            }
            if meta.get("page_count") is not None:
                entry["scope"] = (entry["scope"] + f"; {meta.get('page_count')} pages").strip("; ")
            items.append(entry)
        counts[kind] = len(items)
        entries_by_kind[kind] = items[:limit_per_kind]
    return {
        "entries": entries_by_kind,
        "counts": counts,
        "total": sum(counts.values()),
        "note": (
            "Discovery only. Selecting a template records a pending Step 3 action; "
            "templates are applied only after the explicit path is rerun through Step 3/4."
        ),
    }


def _template_preview_files(kind: str, template_id: str, limit: int = 6) -> list[dict]:
    """Return existing SVG preview candidates for a template library entry."""
    base_dir = _SKILL_DIR / _TEMPLATE_DIRS.get(kind, "") / template_id
    if not base_dir.is_dir():
        return []
    previews = []
    for path in sorted(base_dir.glob("*.svg"))[:limit]:
        rel = path.relative_to(_SKILL_DIR).as_posix()
        previews.append({
            "name": path.name,
            "path": f"skills/ppt-master/{rel}",
            "url": f"/template-file/{kind}/{template_id}/{path.name}",
        })
    return previews


def template_route_state(project: Path) -> dict:
    """Return Step 3 template route, discovery, and any pending UI choice."""
    templates_dir = project / "templates"
    has_template_files = _dir_has_files(templates_dir)
    kind = _template_kind_from_project(project)
    pending_selection = None
    result = _read_json(project / "confirm_ui" / "result.json") or {}
    raw_selection = result.get("template_selection")
    if isinstance(raw_selection, dict) and raw_selection.get("action") == "apply_template":
        pending_selection = raw_selection

    if has_template_files and kind:
        route = "template_applied"
        label = "Template applied"
        reason = "Project templates/design_spec.md declares an explicit template kind."
        applied = {
            "kind": kind,
            "path": str(templates_dir.resolve()),
            "source": "project/templates/design_spec.md",
        }
    elif has_template_files:
        route = "template_expected_missing"
        label = "Template expected but missing"
        reason = "templates/ contains files but no readable design_spec.md kind; Step 3 may be incomplete."
        applied = {
            "kind": None,
            "path": str(templates_dir.resolve()),
            "source": "project/templates/",
        }
    else:
        route = "free_design"
        label = "Free design"
        reason = "No explicit template directory path has been applied; this is the normal default path."
        applied = None

    return {
        "route": route,
        "label": label,
        "reason": reason,
        "applied": applied,
        "pending_selection": pending_selection,
        "library": _template_index_entries(),
    }


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


def _page_expression_state(project: Path) -> dict:
    """Return lightweight page-expression contract observability for Dashboard."""
    summary = page_expression_summary(project)
    summary["modified_at"] = summary.pop("updated_at")
    return summary


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


_SUB_STEP_LABELS_ZH = {
    "sources": "源文件",
    "project_dir": "项目目录",
    "readme": "README",
    "templates": "模板文件",
    "recommendations": "确认建议",
    "confirmation": "用户确认",
    "design_spec": "设计规格",
    "spec_lock": "规格锁",
    "image_prompts": "图片提示词",
    "images": "图片池",
    "svg_generate": "SVG 生成",
    "notes_total": "讲稿备注",
    "notes_split": "拆分备注",
    "svg_final": "SVG 后处理",
    "pptx_export": "PPTX 导出",
    "spec_review": "规格复盘",
}

_GATE_LABELS_ZH = {
    "Source material exists": "源材料已存在",
    "Project directory exists": "项目目录已存在",
    "Template applied or default free-design path is valid": "模板已应用或自由设计路线有效",
    "Step 3 complete or skipped": "Step 3 已完成或已跳过",
    "Strategist artifacts ready": "策略阶段产物已就绪",
    "spec_lock.md exists": "spec_lock.md 已存在",
    "SVG output exists": "SVG 输出已存在",
    "notes/total.md exists": "notes/total.md 已存在",
    "PPTX export exists": "PPTX 导出已存在",
    "Spec review completed or optional review is not applicable": "规格复盘已完成或可跳过",
}


def _sub_step(id_: str, label: str, state: str, detail: str | None = None, progress: float | None = None) -> dict:
    return {
        "id": id_,
        "label": label,
        "label_en": label,
        "label_zh": _SUB_STEP_LABELS_ZH.get(id_, label),
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
            {
                "label": label,
                "label_en": label,
                "label_zh": _GATE_LABELS_ZH.get(label, label),
                "met": met,
                "detail": detail,
            }
            for label, met, detail in requirements
        ],
    }


def _step(step: int, state: str, *, sub_steps: list[dict] | None = None, gate: dict | None = None,
          started_at: str | None = None, completed_at: str | None = None, error: str | None = None) -> dict:
    return {
        "step": step,
        "name": _STEP_NAMES[step],
        "name_en": _STEP_NAMES[step],
        "name_zh": _STEP_NAMES_ZH[step],
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


# Staged flow recommendation files (newest first) plus the legacy single file.
_RECOMMENDATION_FILE_NAMES = (
    "recommendations.stage3.json",
    "recommendations.stage2.json",
    "recommendations.stage1.json",
    "recommendations.json",
)


def _latest_recommendations_file(project: Path) -> Path | None:
    """Return the newest existing recommendation file (staged or legacy)."""
    confirm_dir = project / "confirm_ui"
    existing = [confirm_dir / name for name in _RECOMMENDATION_FILE_NAMES if (confirm_dir / name).is_file()]
    if not existing:
        return None
    return max(existing, key=lambda path: path.stat().st_mtime)


def _template_option_state(project: Path, has_templates: bool) -> tuple[str, str, bool]:
    route = template_route_state(project)
    if route["route"] == "template_applied":
        applied = route.get("applied") or {}
        return (
            "completed",
            f"Template applied ({applied.get('kind') or 'unknown'}): {applied.get('path')}",
            True,
        )
    if route["route"] == "template_expected_missing":
        return (
            "failed",
            route["reason"],
            False,
        )
    templates_dir = project / "templates"
    if has_templates:
        return (
            "failed",
            "templates/ exists but no valid template kind was detected.",
            False,
        )
    if templates_dir.is_dir():
        return (
            "failed",
            "templates/ exists but contains no files; template application may be incomplete.",
            False,
        )
    return (
        "skipped",
        "Free design: no explicit template path was applied; this is the normal default route.",
        True,
    )


def _spec_review_state(has_spec_review: bool, has_export: bool) -> tuple[str, str, bool]:
    if has_spec_review:
        return (
            "completed",
            "Post-export spec review artifact found.",
            True,
        )
    if has_export:
        return (
            "skipped",
            "Optional post-export Step 8a was not run; no spec_review.md artifact exists.",
            True,
        )
    return (
        "pending",
        "Available after PPTX export; optional unless a post-generation review is requested.",
        False,
    )


def _manifest_items(value: dict | None) -> list[dict]:
    if not isinstance(value, dict):
        return []
    raw = value.get("items") or value.get("sources") or value.get("assets") or []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _image_provenance_summary(project: Path) -> dict | None:
    """Summarize image_sources provenance for dashboard/API visibility."""
    manifest_path = project / "images" / "image_sources.json"
    manifest = _read_json(manifest_path)
    items = _manifest_items(manifest)
    if not items:
        return None

    by_source_pack: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    pending_review: list[dict] = []
    discovery_items = 0
    missing_provenance = 0
    required = {
        "source_pack",
        "selection_reason",
        "copyright_risk",
        "manual_review_status",
        "discovery_source",
        "source_page_url",
    }

    for item in items:
        source_pack = str(item.get("source_pack") or "legacy_unspecified")
        by_source_pack[source_pack] = by_source_pack.get(source_pack, 0) + 1

        risk = str(item.get("copyright_risk") or "unknown").split(":", 1)[0].strip().lower()
        risk = risk or "unknown"
        by_risk[risk] = by_risk.get(risk, 0) + 1

        provider = str(item.get("provider") or "").lower()
        discovery_source = str(item.get("discovery_source") or "").lower()
        if provider == "browser" or any(
            token in discovery_source for token in ("google", "bing", "yandex", "browser")
        ):
            discovery_items += 1

        missing = [field for field in required if not str(item.get(field) or "").strip()]
        if missing:
            missing_provenance += 1

        review_status = str(item.get("manual_review_status") or "").lower()
        needs_review = bool(item.get("needs_manual_review")) or risk in {"high", "unknown"}
        if needs_review and review_status not in {"approved", "reviewed", "cleared", "accepted"}:
            pending_review.append({
                "filename": item.get("filename") or "",
                "slide": item.get("slide") or "",
                "source_pack": source_pack,
                "copyright_risk": item.get("copyright_risk") or "unknown",
                "manual_review_status": item.get("manual_review_status") or "missing",
                "source_page_url": item.get("source_page_url") or "",
                "selection_reason": item.get("selection_reason") or "",
            })

    return {
        "manifest": manifest_path.relative_to(project).as_posix(),
        "total": len(items),
        "by_source_pack": by_source_pack,
        "by_copyright_risk": by_risk,
        "discovery_items": discovery_items,
        "missing_provenance": missing_provenance,
        "pending_manual_review": pending_review[:20],
        "pending_manual_review_count": len(pending_review),
    }


def _build_steps(project: Path, page_count: int | None, svg_count: int) -> list[dict]:
    sources_ready = _dir_has_files(project / "sources") or any(
        (project / name).is_file() for name in ("research_report.md", "来源文档.md")
    )
    initialized = project.is_dir() and (project / "README.md").is_file()
    has_templates = _dir_has_files(project / "templates")
    latest_recommendations = _latest_recommendations_file(project)
    has_recommendations = latest_recommendations is not None
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
    step3_state, step3_detail, step3_gate_met = _template_option_state(project, has_templates)
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

    step8_state, step8_detail, step8_gate_met = _spec_review_state(has_spec_review, has_export)

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
                _sub_step("templates", "Template files", step3_state, step3_detail),
            ],
            gate=_gate([("Template applied or default free-design path is valid", step3_gate_met, step3_detail)]),
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
            started_at=_file_time(latest_recommendations) if latest_recommendations else None,
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
                _sub_step("spec_review", "Spec review", step8_state, step8_detail),
            ],
            gate=_gate([
                ("PPTX export exists", has_export, None),
                ("Spec review completed or optional review is not applicable", step8_gate_met, step8_detail),
            ]),
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
    quality = quality_summary(project)
    digest_status = quality.get("spec_lock_digest") if quality else None
    if digest_status == "PASS":
        spec_lock_verified = True
    elif digest_status == "FAIL":
        spec_lock_verified = False
    else:
        spec_lock_verified = None
    payload = {
        "project_name": info.get("name") or project.name,
        "project_path": str(project.resolve()),
        "canvas_format": canvas_id,
        "canvas_info": _canvas_info(canvas_id),
        "current_step": _current_step(steps),
        "steps": steps,
        "generation_mode": generation_mode,
        "confirm_status": confirm_status,
        "template_route": template_route_state(project),
        "spec_lock_digest": _spec_digest(project),
        "spec_lock_verified": spec_lock_verified,
        "page_expression": _page_expression_state(project),
        "quality_summary": quality,
        "image_provenance": _image_provenance_summary(project),
        "page_count": page_count,
        "svg_count": svg_count,
        "export_path": latest_pptx(project),
        "dashboard": dashboard_status(project),
        "live_preview": live_preview_status(project),
        "confirm_ui": confirm_ui_status(project),
        "officecli_runtime": officecli_runtime_state(project),
        "office_sources": office_sources_state(project),
        "native_revision": native_revision_state(project),
        "derived_at": _now(),
    }
    payload["health_summary"] = health_summary(project, payload)
    return payload
