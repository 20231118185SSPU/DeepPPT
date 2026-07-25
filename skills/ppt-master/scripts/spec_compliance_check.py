#!/usr/bin/env python3
"""
PPT Master - spec_lock Compliance Checker

Semantic compliance validation between spec_lock.md and generated SVGs.
Complements svg_quality_checker.py (XML/structural/drift) and
e2e_validate.py (project-level structural consistency) by checking
the inverse direction: are all declared spec_lock entries properly
reflected in the project output?

Checks:
    1. Unused colors — declared in spec_lock colors but absent from all SVGs
    2. Layout template existence — page_layouts entries resolve to real files
    3. Chart template existence — page_charts entries resolve to real files
    4. Rhythm vocabulary — page_rhythm values are exactly anchor/dense/breathing
    5. Icon library validity — library is one of the four known values
    6. Inventory cross-check — SVG data-icon attrs use declared library + inventory
    7. Cross-section consistency — page_layouts/chart/rhythm keys exist in page_rhythm
    8. Image usage — images declared in spec_lock referenced by at least one SVG
    9. Page expression — Strategist contract completeness and visible assertions

Usage:
    python3 scripts/spec_compliance_check.py <project_path> [options]

Examples:
    python3 scripts/spec_compliance_check.py projects/my_deck_ppt169_20260626
    python3 scripts/spec_compliance_check.py projects/my_deck --json
    python3 scripts/spec_compliance_check.py projects/my_deck --strict

Dependencies:
    None (only uses standard library)

References:
    See ../references/strategist.md and ../templates/design_spec_reference.md for
    the page-expression contract mirrored by this runtime checker.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# sys.path injection for sibling module
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from update_spec import parse_lock  # noqa: E402
from console_encoding import configure_utf8_stdio  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SUPPORTED_RHYTHMS = {"anchor", "dense", "breathing"}
SUPPORTED_ICON_LIBRARIES = {
    "chunk-filled",
    "tabler-filled",
    "tabler-outline",
    "phosphor-duotone",
}
COLOR_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_DATA_ICON_RE = re.compile(r'data-icon="([^"]+)"')

PAGE_EXPRESSION_FILENAME = "page_expression.json"
PAGE_EXPRESSION_FIELDS = (
    "question",
    "assertion",
    "evidence",
    "visual_act",
    "takeaway",
    "next_beat",
)
CONTENT_TEXT_FIELDS = {
    "question",
    "assertion",
    "visual_act",
    "takeaway",
    "next_beat",
}
STRUCTURAL_PAGE_KINDS = {
    "cover",
    "toc",
    "chapter",
    "transition",
    "closing",
    "ending",
}
CONTENT_RELATIONS = {
    "single_claim",
    "parallel_set",
    "weighted_set",
    "compare",
    "sequence",
    "hierarchy",
    "evidence_chain",
    "matrix",
    "summary",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class ComplianceIssue:
    severity: str  # "error" | "warn" | "info"
    check: str
    message: str
    detail: str = ""


@dataclass
class ComplianceReport:
    project: str
    issues: list[ComplianceIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warn_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warn")

    @property
    def passed(self) -> bool:
        return self.error_count == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _find_svg_dir(project: Path) -> Optional[Path]:
    """Return svg_output/ if it contains SVGs, else svg_final/, else None."""
    for name in ("svg_output", "svg_final"):
        d = project / name
        if d.is_dir() and any(d.glob("*.svg")):
            return d
    return None


def _iter_svg_files(svg_dir: Path) -> list[Path]:
    """Return SVG files in deterministic order, including legacy NN_* names."""
    return sorted(svg_dir.glob("*.svg"))


def _collect_svg_colors(svg_dir: Path) -> set[str]:
    """Return all lowercase HEX color values found in SVG fill/stroke/stop-color."""
    colors: set[str] = set()
    hex_re = re.compile(r'(?:fill|stroke|stop-color)\s*=\s*"(#[0-9A-Fa-f]{6})"')
    for svg in _iter_svg_files(svg_dir):
        text = svg.read_text(encoding="utf-8", errors="replace")
        for m in hex_re.finditer(text):
            colors.add(m.group(1).lower())
    return colors


def _collect_svg_data_icons(svg_dir: Path) -> set[str]:
    """Return all data-icon attribute values across SVGs."""
    icons: set[str] = set()
    for svg in _iter_svg_files(svg_dir):
        text = svg.read_text(encoding="utf-8", errors="replace")
        for m in _DATA_ICON_RE.finditer(text):
            icons.add(m.group(1))
    return icons


def _collect_svg_image_refs(svg_dir: Path) -> set[str]:
    """Return all image href paths referenced in SVGs."""
    refs: set[str] = set()
    href_re = re.compile(r'href="([^"]+)"')
    for svg in _iter_svg_files(svg_dir):
        text = svg.read_text(encoding="utf-8", errors="replace")
        for m in href_re.finditer(text):
            val = m.group(1)
            # skip url() references (gradients, filters)
            if val.startswith("url("):
                continue
            refs.add(val)
    return refs


def _parse_page_ids(spec_lock: dict[str, dict[str, str]]) -> list[str]:
    """Extract page IDs (P01, P02, …) from page_rhythm keys."""
    rhythm = spec_lock.get("page_rhythm", {})
    ids = []
    for key in rhythm:
        # normalize: strip slug suffix (P01_cover → P01)
        pid = key.split("_")[0] if "_" in key else key
        ids.append(pid)
    return ids


def _normalize_contract_text(value: object) -> str:
    """Collapse XML/JSON whitespace for exact visible-text comparisons."""
    return " ".join(str(value).split())


def _svg_page_id(stem: str) -> Optional[str]:
    """Map a supported SVG filename stem to its canonical page ID."""
    prefixed = re.match(r"^(P\d+)(?:_|$)", stem)
    if prefixed:
        return prefixed.group(1)
    numeric = re.match(r"^(\d+)(?:_|$)", stem)
    if numeric:
        return f"P{int(numeric.group(1)):02d}"
    return None


def _expected_page_ids(project: Path, spec_lock: dict[str, dict[str, str]]) -> list[str]:
    """Return the union of locked and rendered project page IDs."""
    page_ids = set(_parse_page_ids(spec_lock))
    for directory_name in ("svg_output", "svg_final"):
        svg_dir = project / directory_name
        if not svg_dir.is_dir():
            continue
        for svg_path in svg_dir.glob("*.svg"):
            page_id = _svg_page_id(svg_path.stem)
            if page_id:
                page_ids.add(page_id)
    return sorted(page_ids, key=lambda value: int(value[1:]))


def _preservation_route(project: Path) -> Optional[str]:
    """Detect the existing direct-PPTX preservation routes."""
    analysis = project / "analysis"
    if (analysis / "fill_plan.json").is_file() or any(
        analysis.glob("*fill_plan.json")
    ):
        return "template-fill"
    if (analysis / "beautify_layout_analysis.json").is_file():
        return "beautify"
    return None


def _contract_severity(route: Optional[str]) -> str:
    return "warn" if route else "error"


def _contract_detail(route: Optional[str]) -> str:
    if route:
        return f"{route} is a standalone preservation route; page-expression compatibility is warning-only."
    return "Main-pipeline projects must satisfy the page-expression contract."


def _valid_content_field(field_name: str, value: object) -> bool:
    """Return whether a content-page field has the supported contract shape."""
    if field_name in CONTENT_TEXT_FIELDS:
        return isinstance(value, str) and bool(value.strip())
    if field_name == "evidence":
        if isinstance(value, str):
            return bool(value.strip())
        return (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and bool(item.strip()) for item in value)
        )
    return False


def _is_structural_exception(value: object) -> bool:
    """Return whether a field is the exact allowed structural-page exception."""
    return (
        isinstance(value, dict)
        and set(value) == {"applicable", "reason"}
        and value.get("applicable") is False
        and isinstance(value.get("reason"), str)
        and bool(value["reason"].strip())
    )


def _font_sizes_from_element(element: ET.Element) -> list[float]:
    """Read numeric font-size values from SVG attributes and inline style."""
    values: list[float] = []
    raw_values = [element.attrib.get("font-size", "")]
    style = element.attrib.get("style", "")
    style_match = re.search(r"(?:^|;)\s*font-size\s*:\s*([^;]+)", style)
    if style_match:
        raw_values.append(style_match.group(1))
    for raw in raw_values:
        match = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", raw)
        if match:
            values.append(float(match.group(1)))
    return values


def _effective_style_property(
    element: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
    name: str,
) -> str:
    """Resolve the nearest inherited SVG presentation property."""
    current: Optional[ET.Element] = element
    while current is not None:
        value = _style_property(current, name)
        if value:
            return value
        current = parent_map.get(current)
    return ""


def _effective_font_size(
    element: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> Optional[float]:
    """Resolve the nearest font-size declaration for a text-bearing node."""
    current: Optional[ET.Element] = element
    while current is not None:
        sizes = _font_sizes_from_element(current)
        if sizes:
            # Inline style wins over a presentation attribute on the same node.
            return sizes[-1]
        current = parent_map.get(current)
    return None


def _text_font_sizes(
    text_element: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> list[Optional[float]]:
    """Return effective sizes for every visible text run in an assertion node."""
    values: list[Optional[float]] = []
    for element in text_element.iter():
        if not _svg_element_visible(element, parent_map):
            continue
        if element.text and element.text.strip():
            values.append(_effective_font_size(element, parent_map))
        if element is not text_element and element.tail and element.tail.strip():
            parent = parent_map.get(element)
            if parent is not None and _svg_element_visible(parent, parent_map):
                values.append(_effective_font_size(parent, parent_map))
    return values


def _find_svg_for_page(project: Path, page_id: str) -> Optional[Path]:
    """Find the first SVG page matching a canonical page ID."""
    for directory_name in ("svg_output", "svg_final"):
        svg_dir = project / directory_name
        if not svg_dir.is_dir():
            continue
        for svg_path in sorted(svg_dir.glob("*.svg")):
            if _svg_page_id(svg_path.stem) == page_id:
                return svg_path
    return None


def _typography_body_size(spec_lock: dict[str, dict[str, str]]) -> Optional[float]:
    typography = spec_lock.get("typography", {})
    if not isinstance(typography, dict):
        return None
    raw = str(typography.get("body") or "")
    match = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)", raw)
    return float(match.group(1)) if match else None


def _style_property(element: ET.Element, name: str) -> str:
    """Return an SVG presentation attribute or inline-style value."""
    direct = element.attrib.get(name, "").strip()
    if direct:
        return direct
    style = element.attrib.get("style", "")
    match = re.search(rf"(?:^|;)\s*{re.escape(name)}\s*:\s*([^;]+)", style)
    return match.group(1).strip() if match else ""


def _svg_element_visible(
    element: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> bool:
    """Reject elements hidden by presentation attributes or inline style."""
    current: Optional[ET.Element] = element
    while current is not None:
        if _style_property(current, "display").lower() == "none":
            return False
        if _style_property(current, "visibility").lower() in {"hidden", "collapse"}:
            return False
        opacity = _style_property(current, "opacity")
        if opacity:
            try:
                if float(opacity) <= 0:
                    return False
            except ValueError:
                pass
        current = parent_map.get(current)

    # A text run with no visible fill or stroke is not an observable assertion.
    # Resolve inherited paint from the leaf so a child override does not get
    # hidden by a group-level placeholder fill.
    tag = element.tag.rsplit("}", 1)[-1]
    if tag in {"text", "tspan"}:
        fill = _effective_style_property(element, parent_map, "fill").lower()
        stroke = _effective_style_property(element, parent_map, "stroke").lower()
        fill_opacity = _effective_style_property(element, parent_map, "fill-opacity")
        stroke_opacity = _effective_style_property(element, parent_map, "stroke-opacity")
        fill_visible = fill not in {"none", "transparent"}
        stroke_visible = stroke not in {"", "none", "transparent"}
        if fill_opacity:
            try:
                fill_visible = fill_visible and float(fill_opacity) > 0
            except ValueError:
                pass
        if stroke_opacity:
            try:
                stroke_visible = stroke_visible and float(stroke_opacity) > 0
            except ValueError:
                pass
        if not fill_visible and not stroke_visible:
            return False
    return True


def _visible_element_text(
    element: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> str:
    """Return rendered text while excluding hidden descendant runs."""
    if not _svg_element_visible(element, parent_map):
        return ""
    chunks = [element.text or ""]
    for child in element:
        chunks.append(_visible_element_text(child, parent_map))
        # A tail belongs to the parent, so it remains visible when only the
        # preceding child is hidden.
        chunks.append(child.tail or "")
    return "".join(chunks)


def _check_assertion_visibility(
    project: Path,
    page_id: str,
    page: dict,
    body_size: Optional[float],
    route: Optional[str],
) -> list[ComplianceIssue]:
    """Check that an applicable assertion is editable and visibly prominent."""
    issues: list[ComplianceIssue] = []
    assertion = page.get("assertion")
    if not isinstance(assertion, str) or not assertion.strip():
        issues.append(ComplianceIssue(
            severity=_contract_severity(route),
            check="page-expression-assertion-invalid",
            message=f"{page_id}: applicable assertion must be a non-empty string",
            detail=_contract_detail(route),
        ))
        return issues
    severity = _contract_severity(route)
    detail = _contract_detail(route)
    svg_path = _find_svg_for_page(project, page_id)
    if svg_path is None:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-svg-missing",
            message=f"{page_id}: no SVG page is available to verify assertion visibility",
            detail=detail,
        ))
        return issues

    try:
        root = ET.parse(svg_path).getroot()
    except (ET.ParseError, OSError) as exc:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-svg-parse",
            message=f"{page_id}: cannot parse SVG for assertion visibility: {exc}",
            detail=detail,
        ))
        return issues

    parent_map = {child: parent for parent in root.iter() for child in parent}
    role_groups = [
        child for child in list(root)
        if child.tag.rsplit("}", 1)[-1] == "g"
        and child.attrib.get("id") in {"lead", "subtitle"}
    ]
    visible_role_groups = [
        group for group in role_groups if _svg_element_visible(group, parent_map)
    ]
    assertion_text = _normalize_contract_text(assertion)
    visible_groups = [
        group for group in visible_role_groups
        if assertion_text in _normalize_contract_text(
            _visible_element_text(group, parent_map)
        )
    ]
    if not role_groups:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-role-missing",
            message=f"{page_id}: SVG has no top-level lead or subtitle semantic group",
            detail=detail,
        ))
        return issues
    if not visible_role_groups:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-role-hidden",
            message=f"{page_id}: lead/subtitle semantic group is hidden",
            detail=detail,
        ))
        return issues
    if not visible_groups:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-assertion-not-visible",
            message=f"{page_id}: assertion is not verbatim in a top-level lead/subtitle group",
            detail=detail,
        ))
        return issues

    matching_texts = [
        (element, group)
        for group in visible_groups
        for element in group.iter()
        if element.tag.rsplit("}", 1)[-1] == "text"
        and _svg_element_visible(element, parent_map)
        and assertion_text == _normalize_contract_text(
            _visible_element_text(element, parent_map)
        )
    ]
    if not matching_texts:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-assertion-not-editable",
            message=f"{page_id}: assertion is not present in an editable SVG text element",
            detail=detail,
        ))
        return issues

    if body_size is None:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-body-size-missing",
            message=f"{page_id}: typography.body is unavailable for assertion-size verification",
            detail=detail,
        ))
        return issues

    for text_element, group in matching_texts:
        sizes = _text_font_sizes(text_element, parent_map)
        if not sizes:
            issues.append(ComplianceIssue(
                severity=severity,
                check="page-expression-assertion-size-missing",
                message=f"{page_id}: assertion text has no readable font-size",
                detail=detail,
            ))
            continue
        if any(size is None for size in sizes):
            issues.append(ComplianceIssue(
                severity=severity,
                check="page-expression-assertion-size-missing",
                message=f"{page_id}: assertion text has a run without a readable font-size",
                detail=detail,
            ))
            continue
        minimum = min(size for size in sizes if size is not None)
        if minimum < body_size:
            issues.append(ComplianceIssue(
                severity=severity,
                check="page-expression-assertion-too-small",
                message=(
                    f"{page_id}: assertion font-size {minimum:g}px is below "
                    f"typography.body {body_size:g}px"
                ),
                detail=detail,
            ))
    return issues


def check_page_expression(
    project_path: Path,
    spec_lock: dict[str, dict[str, str]],
) -> list[ComplianceIssue]:
    """Validate the Strategist-owned page-expression contract and SVG assertions."""
    route = _preservation_route(project_path)
    severity = _contract_severity(route)
    detail = _contract_detail(route)
    issues: list[ComplianceIssue] = []
    lock_path = project_path / "spec_lock.md"
    try:
        lock_text = lock_path.read_text(encoding="utf-8")
    except OSError:
        lock_text = ""
    if re.search(r"(?mi)^##\s+page_expression\s*$", lock_text):
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-duplicate-lock-section",
            message="spec_lock.md must not contain a ## page_expression section",
            detail=detail,
        ))

    contract_path = project_path / PAGE_EXPRESSION_FILENAME
    if not contract_path.is_file():
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-missing",
            message=f"{PAGE_EXPRESSION_FILENAME} not found in project root",
            detail=detail,
        ))
        return issues
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-parse-error",
            message=f"Failed to parse {PAGE_EXPRESSION_FILENAME}: {exc}",
            detail=detail,
        ))
        return issues
    if not isinstance(contract, dict):
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-root",
            message=f"{PAGE_EXPRESSION_FILENAME} must contain a JSON object",
            detail=detail,
        ))
        return issues
    schema_version = contract.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != 1:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-schema-version",
            message="page_expression.json schema_version must be 1",
            detail=detail,
        ))
    if contract.get("owner") != "Strategist":
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-owner",
            message="page_expression.json owner must be Strategist",
            detail=detail,
        ))

    pages = contract.get("pages")
    if not isinstance(pages, dict):
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-pages",
            message="page_expression.json pages must be an object keyed by page ID",
            detail=detail,
        ))
        return issues
    expected_ids = _expected_page_ids(project_path, spec_lock)
    actual_ids = set(str(page_id) for page_id in pages)
    missing_ids = [page_id for page_id in expected_ids if page_id not in actual_ids]
    extra_ids = sorted(actual_ids - set(expected_ids))
    if missing_ids:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-page-coverage",
            message=f"page_expression.json is missing project pages: {', '.join(missing_ids)}",
            detail=detail,
        ))
    if extra_ids:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-page-coverage",
            message=f"page_expression.json contains pages not in the project: {', '.join(extra_ids)}",
            detail=detail,
        ))
    if not pages:
        issues.append(ComplianceIssue(
            severity=severity,
            check="page-expression-pages-empty",
            message="page_expression.json pages must not be empty",
            detail=detail,
        ))

    body_size = _typography_body_size(spec_lock)
    for page_id, page in pages.items():
        page_label = str(page_id)
        if not isinstance(page, dict):
            issues.append(ComplianceIssue(
                severity=severity,
                check="page-expression-page-object",
                message=f"{page_label}: page entry must be an object",
                detail=detail,
            ))
            continue
        raw_page_kind = page.get("page_kind")
        if not isinstance(raw_page_kind, str) or not raw_page_kind.strip():
            issues.append(ComplianceIssue(
                severity=severity,
                check="page-expression-page-kind",
                message=f"{page_label}: page_kind must be a non-empty string",
                detail=detail,
            ))
            page_kind = ""
        else:
            page_kind = raw_page_kind.strip().lower()
        is_structural = page_kind in STRUCTURAL_PAGE_KINDS
        if not is_structural:
            relation = page.get("content_relation")
            if not isinstance(relation, str) or relation not in CONTENT_RELATIONS:
                issues.append(ComplianceIssue(
                    severity=severity,
                    check="page-expression-content-relation",
                    message=(
                        f"{page_label}: content_relation must be one of "
                        f"{', '.join(sorted(CONTENT_RELATIONS))}"
                    ),
                    detail=detail,
                ))
            anchor = page.get("information_anchor")
            if not isinstance(anchor, str) or not anchor.strip():
                issues.append(ComplianceIssue(
                    severity=severity,
                    check="page-expression-information-anchor",
                    message=f"{page_label}: information_anchor must be non-empty",
                    detail=detail,
                ))

        for field_name in PAGE_EXPRESSION_FIELDS:
            if field_name not in page:
                issues.append(ComplianceIssue(
                    severity=severity,
                    check="page-expression-field-missing",
                    message=f"{page_label}: missing required field '{field_name}'",
                    detail=detail,
                ))
                continue
            value = page[field_name]
            if is_structural:
                if not (
                    _valid_content_field(field_name, value)
                    or _is_structural_exception(value)
                ):
                    issues.append(ComplianceIssue(
                        severity=severity,
                        check="page-expression-structural-exception",
                        message=(
                            f"{page_label}: structural field '{field_name}' must be a "
                            "non-empty applicable value or "
                            "'{\"applicable\": false, \"reason\": \"...\"}'"
                        ),
                        detail=detail,
                    ))
            elif field_name == "assertion" and not _valid_content_field(field_name, value):
                issues.append(ComplianceIssue(
                    severity=severity,
                    check="page-expression-assertion-invalid",
                    message=f"{page_label}: content assertion must be a non-empty string",
                    detail=detail,
                ))
            elif not _valid_content_field(field_name, value):
                issues.append(ComplianceIssue(
                    severity=severity,
                    check="page-expression-field-invalid",
                    message=(
                        f"{page_label}: content field '{field_name}' must be a non-empty "
                        "string (or a non-empty list of strings for evidence)"
                    ),
                    detail=detail,
                ))

        if isinstance(page.get("assertion"), str):
            issues.extend(_check_assertion_visibility(
                project_path,
                page_label,
                page,
                body_size,
                route,
            ))
    return issues


_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def check_unused_colors(
    spec_lock: dict[str, dict[str, str]],
    svg_colors: set[str],
) -> list[ComplianceIssue]:
    """Check for declared colors not used in any SVG."""
    issues: list[ComplianceIssue] = []
    colors_section = spec_lock.get("colors", {})
    skip_keys = {"image_rendering", "image_palette", "image_rendering_behavior",
                 "image_palette_behavior"}
    for key, val in colors_section.items():
        if key in skip_keys:
            continue
        if not _HEX_RE.match(val):
            continue
        if val.lower() not in svg_colors:
            issues.append(ComplianceIssue(
                severity="warn",
                check="unused-color",
                message=f"Declared color {key}: {val} not found in any SVG",
                detail="This color is locked in spec_lock but unused. "
                       "Consider removing it to keep the lock tight.",
            ))
    return issues


def check_layout_templates(
    spec_lock: dict[str, dict[str, str]],
    project: Path,
) -> list[ComplianceIssue]:
    """Check that page_layouts entries resolve to real template SVGs."""
    issues: list[ComplianceIssue] = []
    layouts = spec_lock.get("page_layouts", {})
    templates_dir = _scripts_templates_dir()
    if not templates_dir:
        issues.append(ComplianceIssue(
            severity="info",
            check="layout-templates",
            message="Cannot locate templates/ directory — skipping layout existence check",
        ))
        return issues
    layouts_dir = templates_dir / "layouts"
    for page_id, tpl_name in layouts.items():
        svg_name = f"{tpl_name}.svg"
        # Search recursively in templates/layouts/ (organized by theme)
        matches = list(layouts_dir.rglob(svg_name)) if layouts_dir.is_dir() else []
        if not matches:
            issues.append(ComplianceIssue(
                severity="warn",
                check="layout-template-missing",
                message=f"{page_id}: template '{svg_name}' not found in templates/layouts/",
            ))
    return issues


def check_chart_templates(
    spec_lock: dict[str, dict[str, str]],
    project: Path,
) -> list[ComplianceIssue]:
    """Check that page_charts entries exist in charts_index.json."""
    issues: list[ComplianceIssue] = []
    charts = spec_lock.get("page_charts", {})
    if not charts:
        return issues
    templates_dir = _scripts_templates_dir()
    if not templates_dir:
        return issues
    index_path = templates_dir / "charts" / "charts_index.json"
    valid_names: set[str] = set()
    if index_path.exists():
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(index_data, dict) and isinstance(index_data.get("charts"), dict):
                valid_names = set(index_data["charts"].keys())
            elif isinstance(index_data, dict):
                valid_names = set(index_data.keys())
            elif isinstance(index_data, list):
                valid_names = {
                    e.get("name", "") for e in index_data if isinstance(e, dict)
                }
        except (json.JSONDecodeError, OSError):
            issues.append(ComplianceIssue(
                severity="warn",
                check="chart-index-unreadable",
                message="charts_index.json exists but could not be parsed",
            ))
            return issues
    for page_id, chart_name in charts.items():
        if valid_names and chart_name not in valid_names:
            issues.append(ComplianceIssue(
                severity="error",
                check="chart-template-missing",
                message=f"{page_id}: chart template '{chart_name}' not in charts_index.json",
            ))
    return issues


def check_rhythm_vocabulary(
    spec_lock: dict[str, dict[str, str]],
) -> list[ComplianceIssue]:
    """Check that all page_rhythm values are valid."""
    issues: list[ComplianceIssue] = []
    rhythm = spec_lock.get("page_rhythm", {})
    for page_id, val in rhythm.items():
        if val not in SUPPORTED_RHYTHMS:
            issues.append(ComplianceIssue(
                severity="error",
                check="rhythm-invalid",
                message=f"{page_id}: rhythm '{val}' is not valid",
                detail=f"Must be one of: {', '.join(sorted(SUPPORTED_RHYTHMS))}",
            ))
    return issues


def check_icon_library(
    spec_lock: dict[str, dict[str, str]],
) -> list[ComplianceIssue]:
    """Check that icon library is a known value."""
    issues: list[ComplianceIssue] = []
    icons = spec_lock.get("icons", {})
    lib = icons.get("library", "")
    if lib and lib not in SUPPORTED_ICON_LIBRARIES:
        issues.append(ComplianceIssue(
            severity="error",
            check="icon-library-invalid",
            message=f"Icon library '{lib}' is not recognized",
            detail=f"Must be one of: {', '.join(sorted(SUPPORTED_ICON_LIBRARIES))}",
        ))
    return issues


def check_icon_inventory(
    spec_lock: dict[str, dict[str, str]],
    svg_icons: set[str],
) -> list[ComplianceIssue]:
    """Check that SVG data-icon values match declared library and inventory."""
    issues: list[ComplianceIssue] = []
    icons_section = spec_lock.get("icons", {})
    lib = icons_section.get("library", "")
    inv_raw = icons_section.get("inventory", "")
    inventory = {n.strip() for n in inv_raw.split(",") if n.strip()} if inv_raw else set()

    for icon_ref in sorted(svg_icons):
        # icon_ref format: "library/name" or just "name"
        if "/" in icon_ref:
            icon_lib, icon_name = icon_ref.split("/", 1)
            if lib and icon_lib != lib:
                issues.append(ComplianceIssue(
                    severity="error",
                    check="icon-library-mismatch",
                    message=f"SVG uses icon '{icon_ref}' from library '{icon_lib}', "
                            f"but spec_lock declares '{lib}'",
                ))
            if inventory and icon_name not in inventory:
                issues.append(ComplianceIssue(
                    severity="warn",
                    check="icon-not-in-inventory",
                    message=f"Icon '{icon_name}' used in SVG but not in spec_lock inventory",
                ))
        else:
            # bare name — can't check library
            if inventory and icon_ref not in inventory:
                issues.append(ComplianceIssue(
                    severity="warn",
                    check="icon-not-in-inventory",
                    message=f"Icon '{icon_ref}' used in SVG but not in spec_lock inventory",
                ))
    return issues


def check_cross_section_consistency(
    spec_lock: dict[str, dict[str, str]],
) -> list[ComplianceIssue]:
    """Check that page_layouts/chart keys exist in page_rhythm."""
    issues: list[ComplianceIssue] = []
    rhythm_ids = set(_parse_page_ids(spec_lock))

    for section_name in ("page_layouts", "page_charts"):
        section = spec_lock.get(section_name, {})
        for page_id in section:
            pid = page_id.split("_")[0] if "_" in page_id else page_id
            if pid not in rhythm_ids:
                issues.append(ComplianceIssue(
                    severity="warn",
                    check="cross-ref-missing",
                    message=f"{section_name} references {page_id}, "
                            f"but {pid} not in page_rhythm",
                ))
    return issues


def check_image_usage(
    spec_lock: dict[str, dict[str, str]],
    svg_image_refs: set[str],
) -> list[ComplianceIssue]:
    """Check that each declared image is referenced by at least one SVG."""
    issues: list[ComplianceIssue] = []
    images = spec_lock.get("images", {})
    if not images:
        return issues
    for label, raw_val in images.items():
        # value may be "images/foo.png" or "images/foo.png | no-crop"
        img_path = raw_val.split("|")[0].strip()
        # normalize for comparison — SVGs may use relative or absolute paths
        found = any(img_path in ref or ref.endswith(Path(img_path).name)
                    for ref in svg_image_refs)
        if not found:
            issues.append(ComplianceIssue(
                severity="warn",
                check="image-declared-unused",
                message=f"Image '{label}: {img_path}' declared in spec_lock "
                        f"but not referenced in any SVG",
            ))
    return issues


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
def _scripts_templates_dir() -> Optional[Path]:
    """Locate the templates/ directory relative to scripts/."""
    candidates = [
        _SCRIPTS_DIR.parent / "templates",
        _SCRIPTS_DIR.parent.parent / "templates",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return None


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def run_compliance(project_path: Path, *, strict: bool = False) -> ComplianceReport:
    """Run all compliance checks and return a report."""
    report = ComplianceReport(project=str(project_path))

    # Locate spec_lock.md
    lock_path = project_path / "spec_lock.md"
    if not lock_path.exists():
        report.issues.append(ComplianceIssue(
            severity="error",
            check="spec-lock-missing",
            message="spec_lock.md not found in project root",
        ))
        return report

    # Parse spec_lock
    try:
        spec_lock = parse_lock(lock_path)
    except Exception as exc:
        report.issues.append(ComplianceIssue(
            severity="error",
            check="spec-lock-parse-error",
            message=f"Failed to parse spec_lock.md: {exc}",
        ))
        return report

    # Page expression is a Strategist-owned main-pipeline contract. Preservation
    # routes are detected from their existing workflow artifacts and retain only
    # an explicit compatibility warning.
    report.issues.extend(check_page_expression(project_path, spec_lock))

    # Locate SVGs
    svg_dir = _find_svg_dir(project_path)
    has_svgs = svg_dir is not None

    # Collect SVG data (empty sets if no SVGs yet)
    svg_colors = _collect_svg_colors(svg_dir) if has_svgs else set()
    svg_icons = _collect_svg_data_icons(svg_dir) if has_svgs else set()
    svg_image_refs = _collect_svg_image_refs(svg_dir) if has_svgs else set()

    # Run checks — spec-only (no SVGs needed)
    report.issues.extend(check_rhythm_vocabulary(spec_lock))
    report.issues.extend(check_icon_library(spec_lock))
    report.issues.extend(check_cross_section_consistency(spec_lock))
    report.issues.extend(check_layout_templates(spec_lock, project_path))
    report.issues.extend(check_chart_templates(spec_lock, project_path))

    # Run checks — require SVGs
    if has_svgs:
        report.issues.extend(check_unused_colors(spec_lock, svg_colors))
        report.issues.extend(check_icon_inventory(spec_lock, svg_icons))
        report.issues.extend(check_image_usage(spec_lock, svg_image_refs))
    else:
        report.issues.append(ComplianceIssue(
            severity="info",
            check="no-svgs",
            message="No SVG output found — SVG-dependent checks skipped",
        ))

    # In strict mode, promote warns to errors
    if strict:
        for issue in report.issues:
            if issue.severity == "warn":
                issue.severity = "error"

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate spec_lock.md and page_expression.json compliance against SVG output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path",
        help="Path to the project directory (e.g. projects/my_deck_ppt169_20260626)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote warnings to errors (exit 1 on any warning)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for programmatic use)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project = Path(args.project_path)
    if not project.is_dir():
        print(f"Error: project directory not found: {project}", file=sys.stderr)
        return 2

    report = run_compliance(project, strict=args.strict)

    # --json mode
    if args.json:
        out = {
            "project": report.project,
            "passed": report.passed,
            "errors": report.error_count,
            "warnings": report.warn_count,
            "issues": [
                {
                    "severity": i.severity,
                    "check": i.check,
                    "message": i.message,
                    "detail": i.detail,
                }
                for i in report.issues
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if report.passed else 1

    # Human-readable output
    print(f"=== spec + page-expression Compliance: {project.name} ===\n")

    if not report.issues:
        print("All checks passed — no issues found.")
        return 0

    for issue in report.issues:
        tag = {"error": "ERROR", "warn": "WARN", "info": "INFO"}[issue.severity]
        icon = {"error": "[X]", "warn": "[!]", "info": "[i]"}[issue.severity]
        print(f"  {icon} {tag} ({issue.check}) {issue.message}")
        if issue.detail:
            print(f"      {issue.detail}")

    # Summary
    print()
    print(f"  Errors: {report.error_count}  |  Warnings: {report.warn_count}  |  "
          f"Total issues: {len(report.issues)}")

    if report.passed:
        print("\n  Result: PASS")
    else:
        print("\n  Result: FAIL")

    return 0 if report.passed else 1


if __name__ == "__main__":
    configure_utf8_stdio()
    raise SystemExit(main())
