#!/usr/bin/env python3
"""
PPT Master - Consulting Content Lock

Build an optional slide_content_lock sidecar for dense consulting decks from a
confirmed detailed outline or a parseable spec_lock.md.

Usage:
    python3 scripts/consulting_content_lock.py <project_path> [--outline path] [--out path]

Examples:
    python3 scripts/consulting_content_lock.py projects/strategy_deck_ppt169_20260702
    python3 scripts/consulting_content_lock.py projects/strategy_deck_ppt169_20260702 --outline analysis/detailed_outline.json

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from update_spec import parse_lock  # noqa: E402

SCHEMA_ID = "ppt_master.slide_content_lock.v1"
DEFAULT_OUTPUT = Path("analysis") / "slide_content_lock.json"
PAGE_ID_RE = re.compile(r"P?(\d{1,3})", re.IGNORECASE)
KPI_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:\d+(?:[.,]\d+)?\s*(?:%|x|倍|点|天|年|月|万|亿|u/L|SP|px)|[A-Z]{2,6})"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Generate optional consulting slide_content_lock.json sidecar.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", type=Path, help="Project root directory")
    parser.add_argument(
        "--outline",
        type=Path,
        help="Explicit detailed_outline.json path. Overrides auto-discovery.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output JSON path (default: <project>/analysis/slide_content_lock.json)",
    )
    return parser


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_source(project: Path, explicit_outline: Path | None) -> tuple[Path | None, str, str]:
    """Resolve the input source using the documented priority order."""
    if explicit_outline is not None:
        outline = explicit_outline
        if not outline.is_absolute() and not outline.is_file():
            outline = project / outline
        return outline, "detailed_outline_json", "explicit --outline"

    candidates = [
        (project / "analysis" / "detailed_outline.json", "detailed_outline_json", "analysis/detailed_outline.json"),
        (project / "detailed_outline.json", "detailed_outline_json", "detailed_outline.json"),
        (project / "spec_lock.md", "spec_lock_md", "spec_lock.md"),
    ]
    for path, source_type, reason in candidates:
        if path.is_file():
            return path, source_type, reason
    return None, "", ""


def load_outline(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load a detailed outline JSON file and return its pages."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if isinstance(raw, list):
        pages = raw
    elif isinstance(raw, dict):
        pages = raw.get("pages", raw.get("detailed_outline", []))
    else:
        pages = []

    if not isinstance(pages, list):
        pages = []
    return [page for page in pages if isinstance(page, dict)], raw if isinstance(raw, dict) else {}


def _page_sort_key(page_id: str) -> tuple[int, str]:
    match = PAGE_ID_RE.search(page_id)
    if match:
        return int(match.group(1)), page_id
    return 9999, page_id


def _page_id_from_value(value: Any, fallback_index: int) -> str:
    if isinstance(value, str) and value.strip():
        raw = value.strip().upper()
        match = PAGE_ID_RE.search(raw)
        if match:
            return f"P{int(match.group(1)):02d}"
        return raw
    if isinstance(value, int):
        return f"P{value:02d}"
    return f"P{fallback_index + 1:02d}"


def _page_id(page: dict[str, Any], fallback_index: int) -> str:
    for key in ("page_id", "slide_id", "page_key", "id"):
        value = page.get(key)
        if value:
            return _page_id_from_value(value, fallback_index)
    return _page_id_from_value(page.get("page_number"), fallback_index)


def _page_number(page_id: str, page: dict[str, Any]) -> int | None:
    value = page.get("page_number")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    match = PAGE_ID_RE.search(page_id)
    if match:
        return int(match.group(1))
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _as_text_list(value: Any) -> list[str]:
    return [str(item).strip() for item in _as_list(value) if str(item).strip()]


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _text_hierarchy(page: dict[str, Any]) -> dict[str, Any]:
    hierarchy = page.get("text_hierarchy")
    return hierarchy if isinstance(hierarchy, dict) else {}


def _extract_kpis(page: dict[str, Any]) -> tuple[list[str], bool]:
    explicit = []
    for key in ("kpis", "kpi", "kpi_items", "metrics"):
        explicit.extend(_as_text_list(page.get(key)))
    if explicit:
        return explicit, True

    candidates: list[str] = []
    hierarchy = _text_hierarchy(page)
    for item in _as_text_list(page.get("content_bullets")) + _as_text_list(hierarchy.get("body")):
        if KPI_RE.search(item):
            candidates.append(item)
    return candidates, False


def _extract_charts(page: dict[str, Any], evidence_ids: list[str]) -> tuple[list[dict[str, Any]], bool]:
    explicit = _as_list(page.get("charts") or page.get("chart"))
    if explicit:
        charts = [
            item if isinstance(item, dict) else {"description": str(item)}
            for item in explicit
        ]
        return charts, True

    visual_need = page.get("visual_need") if isinstance(page.get("visual_need"), dict) else {}
    element_hits = [
        item for item in _as_text_list(page.get("element_list"))
        if "chart" in item.lower()
    ]
    image_type = str(visual_need.get("image_type", "")).lower()
    if image_type == "chart" or element_hits:
        return [
            {
                "description": _first_text(
                    visual_need.get("image_description"),
                    page.get("core_argument"),
                ),
                "source": _first_text(_text_hierarchy(page).get("annotation")),
                "layout_suggestion": _first_text(page.get("layout_suggestion")),
                "elements": element_hits,
                "evidence_ids": evidence_ids,
            }
        ], False
    return [], False


def _extract_tables(page: dict[str, Any], evidence_ids: list[str]) -> tuple[list[dict[str, Any]], bool]:
    explicit = _as_list(page.get("tables") or page.get("table"))
    if explicit:
        tables = [
            item if isinstance(item, dict) else {"description": str(item)}
            for item in explicit
        ]
        return tables, True

    layout = _first_text(page.get("layout_suggestion")).lower()
    element_hits = [
        item for item in _as_text_list(page.get("element_list"))
        if "table" in item.lower()
    ]
    if "table" in layout or element_hits:
        return [
            {
                "description": _first_text(page.get("core_argument")),
                "layout_suggestion": page.get("layout_suggestion", ""),
                "elements": element_hits,
                "evidence_ids": evidence_ids,
            }
        ], False
    return [], False


def build_slide_from_outline(page: dict[str, Any], index: int, source_hash: str) -> dict[str, Any]:
    """Normalize one detailed outline page into a content-lock slide record."""
    hierarchy = _text_hierarchy(page)
    page_id = _page_id(page, index)
    evidence_ids = (
        _as_text_list(page.get("evidence_ids"))
        or _as_text_list(page.get("evidence_refs"))
        or _as_text_list(page.get("source_ids"))
    )
    title = _first_text(page.get("title"), hierarchy.get("title"), page.get("core_argument"))
    subtitle = _first_text(page.get("subtitle"), hierarchy.get("subtitle"))
    annotations = _as_text_list(page.get("annotations"))
    annotation = _first_text(hierarchy.get("annotation"), page.get("annotation"), page.get("source_annotation"))
    if annotation:
        annotations.append(annotation)
    caveats = _as_text_list(page.get("caveats") or page.get("caveat") or page.get("risks"))
    so_what = _first_text(page.get("so_what"), page.get("so what"), page.get("takeaway"), page.get("core_argument"))
    explicit_so_what = any(page.get(key) for key in ("so_what", "so what", "takeaway"))
    kpis, explicit_kpis = _extract_kpis(page)
    charts, explicit_charts = _extract_charts(page, evidence_ids)
    tables, explicit_tables = _extract_tables(page, evidence_ids)

    missing_fields = []
    if not title:
        missing_fields.append("title")
    if not subtitle:
        missing_fields.append("subtitle")
    if not kpis:
        missing_fields.append("kpis")
    if charts and not explicit_charts:
        missing_fields.append("charts.explicit")
    if tables and not explicit_tables:
        missing_fields.append("tables.explicit")
    if not annotations:
        missing_fields.append("annotations")
    if not caveats:
        missing_fields.append("caveats")
    if not explicit_so_what:
        missing_fields.append("so_what")
    if not evidence_ids:
        missing_fields.append("evidence_ids")
    if kpis and not explicit_kpis:
        missing_fields.append("kpis.explicit")

    return {
        "page_id": page_id,
        "slide_id": page_id,
        "page_number": _page_number(page_id, page),
        "page_type": page.get("page_type", ""),
        "title": title,
        "subtitle": subtitle,
        "so_what": so_what,
        "kpis": kpis,
        "charts": charts,
        "tables": tables,
        "annotations": annotations,
        "caveats": caveats,
        "evidence_ids": evidence_ids,
        "content_density": page.get("content_density", page.get("content_mode", "")),
        "layout_suggestion": page.get("layout_suggestion", ""),
        "visual_need": page.get("visual_need", {}),
        "missing_fields": sorted(set(missing_fields)),
        "source_file_hash": source_hash,
    }


def slides_from_spec_lock(path: Path, source_hash: str) -> list[dict[str, Any]]:
    """Build sparse slide records from spec_lock.md."""
    lock = parse_lock(path)
    page_ids: set[str] = set()
    for section_name in ("page_rhythm", "page_layouts", "page_charts"):
        for raw_id in lock.get(section_name, {}):
            page_ids.add(_page_id_from_value(raw_id, len(page_ids)))
    for raw_id in lock.get("images", {}):
        match = PAGE_ID_RE.search(raw_id)
        if match:
            page_ids.add(f"P{int(match.group(1)):02d}")

    slides = []
    charts = lock.get("page_charts", {})
    layouts = lock.get("page_layouts", {})
    rhythm = lock.get("page_rhythm", {})
    for page_id in sorted(page_ids, key=_page_sort_key):
        chart_name = charts.get(page_id, "")
        table_expected = "table" in layouts.get(page_id, "").lower()
        missing_fields = [
            "title",
            "subtitle",
            "kpis",
            "annotations",
            "caveats",
            "so_what",
            "evidence_ids",
        ]
        slide = {
            "page_id": page_id,
            "slide_id": page_id,
            "page_number": _page_sort_key(page_id)[0],
            "page_type": "",
            "title": "",
            "subtitle": "",
            "so_what": "",
            "kpis": [],
            "charts": [{"template": chart_name}] if chart_name else [],
            "tables": [{"layout_suggestion": layouts.get(page_id, "")}] if table_expected else [],
            "annotations": [],
            "caveats": [],
            "evidence_ids": [],
            "content_density": rhythm.get(page_id, ""),
            "layout_suggestion": layouts.get(page_id, ""),
            "visual_need": {},
            "missing_fields": missing_fields,
            "source_file_hash": source_hash,
        }
        slides.append(slide)
    return slides


def build_report(project: Path, source_path: Path, source_type: str, reason: str) -> dict[str, Any]:
    """Build the slide content lock report."""
    source_hash = sha256_file(source_path)
    if source_type == "detailed_outline_json":
        pages, raw = load_outline(source_path)
        slides = [
            build_slide_from_outline(page, index, source_hash)
            for index, page in enumerate(pages)
        ]
        total_pages = raw.get("total_pages", len(slides)) if isinstance(raw, dict) else len(slides)
    else:
        slides = slides_from_spec_lock(source_path, source_hash)
        total_pages = len(slides)

    return {
        "schema": SCHEMA_ID,
        "project": project.name,
        "project_path": str(project),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": {
            "path": str(source_path),
            "type": source_type,
            "resolution": reason,
            "sha256": source_hash,
        },
        "total_pages": total_pages,
        "slides": slides,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project = args.project_path.resolve()
    if not project.exists() or not project.is_dir():
        print(f"error: project directory not found: {project}", file=sys.stderr)
        return 1

    source_path, source_type, reason = resolve_source(project, args.outline)
    if source_path is None:
        print(
            "error: no input found. Expected --outline, analysis/detailed_outline.json, "
            "detailed_outline.json, or spec_lock.md.",
            file=sys.stderr,
        )
        return 1

    source_path = source_path.resolve()
    if not source_path.is_file():
        print(f"error: input file not found: {source_path}", file=sys.stderr)
        return 1

    try:
        report = build_report(project, source_path, source_type, reason)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output_path = (args.out or (project / DEFAULT_OUTPUT)).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    slide_count = len(report["slides"])
    missing_count = sum(1 for slide in report["slides"] if slide.get("missing_fields"))
    print(
        f"wrote {output_path} ({slide_count} slides, {missing_count} with missing_fields)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
