#!/usr/bin/env python3
"""
PPT Master - Dashboard Layout Preview

Build a read-only per-page layout preview payload for the dashboard.

Usage:
    from layout_preview import layout_preview
    payload = layout_preview(Path("projects/example"))

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from update_spec import parse_lock  # noqa: E402

_SKILL_DIR = Path(__file__).resolve().parents[2]
_LAYOUT_TEMPLATE_DIRS = (
    _SKILL_DIR / "templates" / "layouts",
    _SKILL_DIR / "templates" / "decks",
)
_CHART_TEMPLATE_DIR = _SKILL_DIR / "templates" / "charts"
_PAGE_RE = re.compile(r"^P?(\d{1,3})$", re.IGNORECASE)
_PAGE_FILE_RE = re.compile(r"^(\d{1,3})(?:[_\-.]|$)")


def _read_spec_lock(project: Path) -> dict[str, dict[str, str]]:
    lock_path = project / "spec_lock.md"
    if not lock_path.is_file():
        return {}
    try:
        data = parse_lock(lock_path)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _page_key(value: str) -> str | None:
    token = str(value or "").strip().strip("|").strip()
    match = _PAGE_RE.match(token)
    if not match:
        return None
    return f"P{int(match.group(1)):02d}"


def _page_number(key: str) -> int:
    match = _PAGE_RE.match(key)
    return int(match.group(1)) if match else 0


def _layout_basename(value: str) -> str:
    basename = str(value or "").strip().strip("`")
    if basename.lower().endswith(".svg"):
        basename = basename[:-4]
    return basename


def _project_file_source(project: Path, path: Path, kind: str, label: str) -> dict[str, str]:
    rel = path.relative_to(project).as_posix()
    return {
        "kind": kind,
        "label": label,
        "path": rel,
        "url": f"/artifact-file/{rel}",
    }


def _template_url(path: Path) -> str | None:
    try:
        rel = path.relative_to(_SKILL_DIR)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 3 or parts[0] != "templates":
        return None
    if parts[1] == "layouts":
        kind = "layout"
    elif parts[1] == "decks":
        kind = "deck"
    else:
        return None
    if len(parts) == 3:
        return f"/template-file/{kind}/__root__/{parts[2]}"
    template_id = parts[2]
    filename = "/".join(parts[3:])
    return f"/template-file/{kind}/{template_id}/{filename}"


def _chart_url(path: Path) -> str | None:
    try:
        rel = path.relative_to(_CHART_TEMPLATE_DIR)
    except ValueError:
        return None
    return f"/chart-template-file/{rel.as_posix()}"


def _find_template_svg(basename: str) -> tuple[Path | None, str | None]:
    clean = _layout_basename(basename)
    if not clean:
        return None, None
    filename = f"{clean}.svg"
    for root in _LAYOUT_TEMPLATE_DIRS:
        direct = root / filename
        if direct.is_file():
            return direct, _template_url(direct)
        matches = sorted(root.glob(f"*/{filename}"))
        if matches:
            return matches[0], _template_url(matches[0])
    return None, None


def _find_chart_svg(name: str) -> tuple[Path | None, str | None]:
    clean = _layout_basename(name)
    if not clean:
        return None, None
    path = _CHART_TEMPLATE_DIR / f"{clean}.svg"
    if path.is_file():
        return path, _chart_url(path)
    return None, None


def _preview_pngs(project: Path) -> dict[str, Path]:
    result = {}
    for preview_dir in (project / "quality" / "screenshots", project / ".preview"):
        if not preview_dir.is_dir():
            continue
        for path in sorted(preview_dir.glob("*.png")):
            match = _PAGE_FILE_RE.match(path.name)
            if match:
                result[f"P{int(match.group(1)):02d}"] = path
    return result


def _page_svgs(project: Path, folder: str) -> dict[str, Path]:
    svg_dir = project / folder
    if not svg_dir.is_dir():
        return {}
    result = {}
    for path in sorted(svg_dir.glob("*.svg")):
        match = _PAGE_FILE_RE.match(path.name)
        if match:
            result[f"P{int(match.group(1)):02d}"] = path
    return result


def _rows_from_page_rhythm(raw: dict[str, str]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        page = _page_key(key)
        if page:
            rows[page] = {"rhythm": str(value or "")}
    return rows


def _table_rows_from_spec_lock(project: Path) -> dict[str, dict[str, str]]:
    lock_path = project / "spec_lock.md"
    if not lock_path.is_file():
        return {}
    rows: dict[str, dict[str, str]] = {}
    in_page_rhythm = False
    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for raw in lines:
        line = raw.strip()
        if line.startswith("## "):
            in_page_rhythm = line[3:].strip() == "page_rhythm"
            continue
        if not in_page_rhythm or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or cells[0].lower() == "page" or set(cells[0]) <= {"-"}:
            continue
        page = _page_key(cells[0])
        if not page:
            continue
        rows[page] = {
            "type": cells[1] if len(cells) > 1 else "",
            "rhythm": cells[2] if len(cells) > 2 else "",
            "layout": cells[3] if len(cells) > 3 else "",
            "notes": cells[4] if len(cells) > 4 else "",
        }
    return rows


def _normalized_page_map(raw: dict[str, str]) -> dict[str, str]:
    result = {}
    for key, value in raw.items():
        page = _page_key(key)
        if page:
            result[page] = _layout_basename(value)
    return result


def _page_keys(
    rhythm_rows: dict[str, dict[str, str]],
    layouts: dict[str, str],
    charts: dict[str, str],
    draft_svgs: dict[str, Path],
    final_svgs: dict[str, Path],
    preview_pngs: dict[str, Path],
) -> list[str]:
    keys = set(rhythm_rows) | set(layouts) | set(charts) | set(draft_svgs) | set(final_svgs) | set(preview_pngs)
    return sorted(keys, key=_page_number)


def _source_for_page(
    page: str,
    project: Path,
    layout_name: str,
    chart_name: str,
    draft_svgs: dict[str, Path],
    final_svgs: dict[str, Path],
    pngs: dict[str, Path],
) -> dict[str, str]:
    if page in pngs:
        return _project_file_source(project, pngs[page], "rendered_png", "Rendered screenshot")
    if page in final_svgs:
        return _project_file_source(project, final_svgs[page], "svg_final", "Final SVG")
    if page in draft_svgs:
        return _project_file_source(project, draft_svgs[page], "svg_output", "Generated SVG")

    template_path, template_url = _find_template_svg(layout_name)
    if template_path and template_url:
        return {
            "kind": "layout_template",
            "label": "Layout template",
            "path": template_path.relative_to(_SKILL_DIR).as_posix(),
            "url": template_url,
        }

    chart_path, chart_url = _find_chart_svg(chart_name)
    if chart_path and chart_url:
        return {
            "kind": "chart_template",
            "label": "Chart template",
            "path": chart_path.relative_to(_SKILL_DIR).as_posix(),
            "url": chart_url,
        }

    return {"kind": "free_design", "label": "Free design", "path": "", "url": ""}


def layout_preview(project: Path) -> dict[str, Any]:
    """Return the dashboard layout preview payload."""
    lock = _read_spec_lock(project)
    rhythm_rows = _rows_from_page_rhythm(lock.get("page_rhythm", {}))
    table_rows = _table_rows_from_spec_lock(project)
    rhythm_rows.update({key: {**rhythm_rows.get(key, {}), **value} for key, value in table_rows.items()})

    layouts = _normalized_page_map(lock.get("page_layouts", {}) or {})
    charts = _normalized_page_map(lock.get("page_charts", {}) or {})
    draft_svgs = _page_svgs(project, "svg_output")
    final_svgs = _page_svgs(project, "svg_final")
    pngs = _preview_pngs(project)
    pages = []

    for page in _page_keys(rhythm_rows, layouts, charts, draft_svgs, final_svgs, pngs):
        row = rhythm_rows.get(page, {})
        layout_name = layouts.get(page) or _layout_basename(row.get("layout") or "")
        chart_name = charts.get(page) or ""
        source = _source_for_page(page, project, layout_name, chart_name, draft_svgs, final_svgs, pngs)
        pages.append({
            "page": page,
            "page_number": _page_number(page),
            "type": row.get("type", ""),
            "rhythm": row.get("rhythm", ""),
            "layout": layout_name,
            "chart": chart_name,
            "notes": row.get("notes", ""),
            "source": source,
        })

    return {
        "available": bool(pages),
        "source": "spec_lock.md" if lock else "",
        "page_count": len(pages),
        "generated_count": sum(
            1
            for page in pages
            if page["source"]["kind"] in {"rendered_png", "svg_final", "svg_output"}
        ),
        "template_count": sum(1 for page in pages if page["source"]["kind"] in {"layout_template", "chart_template"}),
        "pages": pages,
    }
