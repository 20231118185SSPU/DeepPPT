#!/usr/bin/env python3
"""
PPT Master - Rendered Layout Check

Checks rendered-slide reliability after SVG static validation. It combines
local PNG screenshot signals with deterministic SVG layout heuristics and
emits a gate report for issues that structural XML checks cannot represent.

Usage:
    python3 scripts/rendered_layout_check.py <project_path>
    python3 scripts/rendered_layout_check.py <project_path> --render
    python3 scripts/rendered_layout_check.py <project_path> --accept-current-render

Examples:
    python3 scripts/rendered_layout_check.py projects/demo_deck
    python3 scripts/rendered_layout_check.py projects/demo_deck --render --server-url http://localhost:5050

Dependencies:
    Pillow for PNG analysis. Playwright is required only when --render is used
    through visual_review.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from console_encoding import configure_utf8_stdio
except ImportError:
    def configure_utf8_stdio() -> None:
        return None

SAFE_MARGIN_X = 56
SAFE_TOP = 130
SAFE_BOTTOM = 660
TEXT_LINE_PAD = 4.0
TEXT_CONTAINER_PAD = 6.0
TEXT_CONTAINER_HARD_OVERFLOW = 18.0
CROSS_COLUMN_MARGIN = 18.0


@dataclass
class BBox:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return max(0.0, self.right - self.left)

    @property
    def height(self) -> float:
        return max(0.0, self.bottom - self.top)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def cx(self) -> float:
        return (self.left + self.right) / 2

    @property
    def cy(self) -> float:
        return (self.top + self.bottom) / 2

    def overlaps_y(self, other: "BBox") -> float:
        return max(0.0, min(self.bottom, other.bottom) - max(self.top, other.top))

    def overlaps_x(self, other: "BBox") -> float:
        return max(0.0, min(self.right, other.right) - max(self.left, other.left))

    def contains_point(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom

    def expanded(self, pad: float) -> "BBox":
        return BBox(self.left - pad, self.top - pad, self.right + pad, self.bottom + pad)


@dataclass
class ElementBox:
    kind: str
    bbox: BBox
    element_id: str
    text: str = ""
    font_size: float = 0.0


@dataclass
class Issue:
    issue_id: str
    severity: str
    category: str
    page: str
    message: str
    evidence: dict[str, Any]


def _now_utc() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _parse_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(str(value).strip().replace("px", ""))
    except ValueError:
        return default


def _mat_identity() -> tuple[float, float, float, float, float, float]:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _mat_mul(
    a: tuple[float, float, float, float, float, float],
    b: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    a1, b1, c1, d1, e1, f1 = a
    a2, b2, c2, d2, e2, f2 = b
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _parse_transform(value: str | None) -> tuple[float, float, float, float, float, float]:
    if not value:
        return _mat_identity()
    matrix = _mat_identity()
    for name, raw_args in re.findall(r"(matrix|translate|scale)\(([^)]*)\)", value):
        nums = [_parse_float(part, 0.0) for part in re.split(r"[,\s]+", raw_args.strip()) if part]
        if name == "matrix" and len(nums) == 6:
            step = tuple(nums)  # type: ignore[assignment]
        elif name == "translate" and nums:
            tx = nums[0]
            ty = nums[1] if len(nums) > 1 else 0.0
            step = (1.0, 0.0, 0.0, 1.0, tx, ty)
        elif name == "scale" and nums:
            sx = nums[0]
            sy = nums[1] if len(nums) > 1 else sx
            step = (sx, 0.0, 0.0, sy, 0.0, 0.0)
        else:
            continue
        matrix = _mat_mul(matrix, step)
    return matrix


def _apply_matrix(
    matrix: tuple[float, float, float, float, float, float],
    x: float,
    y: float,
) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    return (a * x + c * y + e, b * x + d * y + f)


def _transform_bbox(
    bbox: BBox,
    matrix: tuple[float, float, float, float, float, float],
) -> BBox:
    points = [
        _apply_matrix(matrix, bbox.left, bbox.top),
        _apply_matrix(matrix, bbox.right, bbox.top),
        _apply_matrix(matrix, bbox.right, bbox.bottom),
        _apply_matrix(matrix, bbox.left, bbox.bottom),
    ]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return BBox(min(xs), min(ys), max(xs), max(ys))


def _text_width(text: str, font_size: float) -> float:
    width = 0.0
    for char in text:
        if char.isspace():
            width += 0.34
        elif "\u4e00" <= char <= "\u9fff":
            width += 1.0
        elif char.isupper():
            width += 0.64
        elif char.isdigit():
            width += 0.56
        elif char in ".:/\\|-_`'(),":
            width += 0.34
        else:
            width += 0.53
    return width * font_size


def _text_bbox(
    x: float,
    y: float,
    text: str,
    font_size: float,
    anchor: str,
    matrix: tuple[float, float, float, float, float, float],
) -> BBox:
    width = _text_width(text, font_size)
    if anchor == "middle":
        left = x - width / 2
    elif anchor == "end":
        left = x - width
    else:
        left = x
    raw = BBox(left, y - font_size * 0.88, left + width, y + font_size * 0.24)
    return _transform_bbox(raw, matrix)


def _extract_text_boxes(
    elem: ET.Element,
    inherited_matrix: tuple[float, float, float, float, float, float],
    current_group: str,
) -> list[ElementBox]:
    matrix = _mat_mul(inherited_matrix, _parse_transform(elem.attrib.get("transform")))
    x = _parse_float(elem.attrib.get("x"), 0.0)
    y = _parse_float(elem.attrib.get("y"), 0.0)
    font_size = _parse_float(elem.attrib.get("font-size"), 20.0)
    anchor = elem.attrib.get("text-anchor", "start")
    element_id = elem.attrib.get("id") or current_group or "text"
    boxes: list[ElementBox] = []

    direct = (elem.text or "").strip()
    if direct:
        bbox = _text_bbox(x, y, direct, font_size, anchor, matrix)
        boxes.append(ElementBox("text", bbox, element_id, direct, font_size))

    cursor_y = y
    for child in elem:
        if _local_name(child.tag) != "tspan":
            continue
        child_size = _parse_float(child.attrib.get("font-size"), font_size)
        child_x = _parse_float(child.attrib.get("x"), x)
        if "y" in child.attrib:
            cursor_y = _parse_float(child.attrib.get("y"), cursor_y)
        else:
            cursor_y += _parse_float(child.attrib.get("dy"), 0.0)
        text = "".join(child.itertext()).strip()
        if not text:
            continue
        bbox = _text_bbox(child_x, cursor_y, text, child_size, anchor, matrix)
        boxes.append(ElementBox("text", bbox, element_id, text, child_size))
    return boxes


def _extract_boxes(svg_path: Path) -> tuple[list[ElementBox], tuple[float, float]]:
    root = ET.parse(svg_path).getroot()
    view_box = root.attrib.get("viewBox", "0 0 1280 720").split()
    canvas = (1280.0, 720.0)
    if len(view_box) == 4:
        canvas = (_parse_float(view_box[2], 1280.0), _parse_float(view_box[3], 720.0))

    boxes: list[ElementBox] = []

    def walk(
        elem: ET.Element,
        matrix: tuple[float, float, float, float, float, float],
        group_id: str,
    ) -> None:
        tag = _local_name(elem.tag)
        elem_matrix = _mat_mul(matrix, _parse_transform(elem.attrib.get("transform")))
        elem_id = elem.attrib.get("id") or group_id or tag

        if tag == "g":
            for child in elem:
                walk(child, elem_matrix, elem_id)
            return

        if tag == "text":
            boxes.extend(_extract_text_boxes(elem, matrix, group_id))
        elif tag in {"rect", "image"}:
            x = _parse_float(elem.attrib.get("x"), 0.0)
            y = _parse_float(elem.attrib.get("y"), 0.0)
            w = _parse_float(elem.attrib.get("width"), 0.0)
            h = _parse_float(elem.attrib.get("height"), 0.0)
            if w > 0 and h > 0:
                boxes.append(ElementBox(tag, _transform_bbox(BBox(x, y, x + w, y + h), elem_matrix), elem_id))
        elif tag in {"line"}:
            x1 = _parse_float(elem.attrib.get("x1"), 0.0)
            y1 = _parse_float(elem.attrib.get("y1"), 0.0)
            x2 = _parse_float(elem.attrib.get("x2"), 0.0)
            y2 = _parse_float(elem.attrib.get("y2"), 0.0)
            stroke = _parse_float(elem.attrib.get("stroke-width"), 1.0) / 2
            bbox = BBox(min(x1, x2) - stroke, min(y1, y2) - stroke,
                        max(x1, x2) + stroke, max(y1, y2) + stroke)
            boxes.append(ElementBox(tag, _transform_bbox(bbox, elem_matrix), elem_id))
        elif tag in {"circle", "ellipse"}:
            cx = _parse_float(elem.attrib.get("cx"), 0.0)
            cy = _parse_float(elem.attrib.get("cy"), 0.0)
            rx = _parse_float(elem.attrib.get("r"), _parse_float(elem.attrib.get("rx"), 0.0))
            ry = _parse_float(elem.attrib.get("r"), _parse_float(elem.attrib.get("ry"), rx))
            if rx > 0 and ry > 0:
                boxes.append(ElementBox(tag, _transform_bbox(BBox(cx - rx, cy - ry, cx + rx, cy + ry), elem_matrix), elem_id))

        for child in elem:
            walk(child, elem_matrix, elem_id)

    walk(root, _mat_identity(), "")
    return boxes, canvas


def _is_background_rect(box: ElementBox, canvas: tuple[float, float]) -> bool:
    return (
        box.kind == "rect"
        and box.bbox.left <= 1
        and box.bbox.top <= 1
        and box.bbox.right >= canvas[0] - 1
        and box.bbox.bottom >= canvas[1] - 1
    )


def _add_issue(issues: list[Issue], issue: Issue) -> None:
    issues.append(issue)


def _check_svg_geometry(svg_path: Path) -> list[Issue]:
    boxes, canvas = _extract_boxes(svg_path)
    page = svg_path.name
    issues: list[Issue] = []
    texts = [b for b in boxes if b.kind == "text" and b.text]
    lines = [b for b in boxes if b.kind == "line"]
    rects = [b for b in boxes if b.kind == "rect" and not _is_background_rect(b, canvas)]

    vertical_rules = [b for b in lines if b.bbox.height > 120 and b.bbox.width <= 8]
    horizontal_rules = [b for b in lines if b.bbox.width > 250 and b.bbox.height <= 8]

    for text in texts:
        for rule in vertical_rules:
            if text.bbox.left < rule.bbox.cx - CROSS_COLUMN_MARGIN and text.bbox.right > rule.bbox.cx + CROSS_COLUMN_MARGIN:
                if text.bbox.overlaps_y(rule.bbox) > max(10.0, text.bbox.height * 0.3):
                    _add_issue(issues, Issue(
                        "cross_column_text_intrusion",
                        "must_fix",
                        "layout_heuristic",
                        page,
                        f"Text crosses a vertical column divider near x={rule.bbox.cx:.0f}: '{text.text[:48]}'.",
                        {
                            "text_bbox": asdict(text.bbox),
                            "divider_bbox": asdict(rule.bbox),
                            "text": text.text,
                        },
                    ))

        containing_rects = [
            rect for rect in rects
            if rect.bbox.contains_point(text.bbox.cx, text.bbox.cy)
            and rect.bbox.area > text.bbox.area * 1.4
            and rect.bbox.width < canvas[0] * 0.95
            and rect.bbox.height < canvas[1] * 0.9
        ]

        for rule in horizontal_rules:
            # Process-flow connector lines often sit behind cards in source SVG.
            # If the text is inside a local container, rendered z-order and the
            # card fill decide visibility; do not treat that as a deterministic
            # collision. Standalone labels near page-wide rules are still checked.
            if containing_rects:
                continue
            if text.bbox.overlaps_x(rule.bbox) > min(40.0, text.bbox.width * 0.5):
                vertical_gap = max(rule.bbox.top - text.bbox.bottom, text.bbox.top - rule.bbox.bottom, 0.0)
                if text.bbox.overlaps_y(rule.bbox) > 0 or vertical_gap <= TEXT_LINE_PAD:
                    _add_issue(issues, Issue(
                        "text_line_collision",
                        "must_fix",
                        "layout_heuristic",
                        page,
                        f"Text overlaps or touches a long rule: '{text.text[:48]}'.",
                        {
                            "text_bbox": asdict(text.bbox),
                            "line_bbox": asdict(rule.bbox),
                            "vertical_gap_px": round(vertical_gap, 2),
                            "text": text.text,
                        },
                    ))

        containers = containing_rects
        if containers:
            container = min(containers, key=lambda r: r.bbox.area)
            padded = BBox(
                container.bbox.left + TEXT_CONTAINER_PAD,
                container.bbox.top + TEXT_CONTAINER_PAD,
                container.bbox.right - TEXT_CONTAINER_PAD,
                container.bbox.bottom - TEXT_CONTAINER_PAD,
            )
            over = {
                "left": round(max(0.0, padded.left - text.bbox.left), 2),
                "top": round(max(0.0, padded.top - text.bbox.top), 2),
                "right": round(max(0.0, text.bbox.right - padded.right), 2),
                "bottom": round(max(0.0, text.bbox.bottom - padded.bottom), 2),
            }
            max_overflow = max(over.values())
            vertical_overflow = max(over["top"], over["bottom"])
            horizontal_overflow = max(over["left"], over["right"])
            severe_horizontal = horizontal_overflow > max(45.0, text.bbox.width * 0.22)
            if vertical_overflow > TEXT_CONTAINER_HARD_OVERFLOW or severe_horizontal:
                _add_issue(issues, Issue(
                    "text_container_edge_contact",
                    "must_fix",
                    "layout_heuristic",
                    page,
                    f"Text is too close to or outside its containing box: '{text.text[:48]}'.",
                    {
                        "text_bbox": asdict(text.bbox),
                        "container_bbox": asdict(container.bbox),
                        "padding_px": TEXT_CONTAINER_PAD,
                        "overflow_px": over,
                        "text": text.text,
                    },
                ))
            elif max_overflow > 0:
                _add_issue(issues, Issue(
                    "text_container_close_fit",
                    "needs_human_review",
                    "layout_heuristic",
                    page,
                    f"Text nearly touches its containing box; inspect rendered fit: '{text.text[:48]}'.",
                    {
                        "text_bbox": asdict(text.bbox),
                        "container_bbox": asdict(container.bbox),
                        "padding_px": TEXT_CONTAINER_PAD,
                        "overflow_px": over,
                        "text": text.text,
                    },
                ))

    for issue in _check_svg_whitespace(page, boxes, rects, canvas):
        _add_issue(issues, issue)

    for issue in _check_card_density(page, boxes, rects, canvas):
        _add_issue(issues, issue)

    return _dedupe_issues(issues)


def _check_svg_whitespace(
    page: str,
    boxes: list[ElementBox],
    rects: list[ElementBox],
    canvas: tuple[float, float],
) -> list[Issue]:
    issues: list[Issue] = []
    content = [
        box for box in boxes
        if box.kind != "rect" or not _is_background_rect(box, canvas)
    ]
    meaningful = [
        box for box in content
        if box.kind in {"text", "image", "circle", "ellipse", "line"}
        or (box.kind == "rect" and box.bbox.area < canvas[0] * canvas[1] * 0.25)
    ]

    # Wide status strips frequently hide visual failure: text is crammed against
    # a line or left edge while the right half is empty. Flag for review instead
    # of forcing an automatic rewrite.
    for rect in rects:
        if rect.bbox.width < canvas[0] * 0.58 or rect.bbox.height > canvas[1] * 0.26:
            continue
        if rect.bbox.top < SAFE_TOP or rect.bbox.bottom > canvas[1] - 28:
            continue
        inside_texts = [
            box for box in boxes
            if box.kind == "text" and rect.bbox.expanded(2).contains_point(box.bbox.cx, box.bbox.cy)
        ]
        if not inside_texts:
            continue
        rel_centers = [(box.bbox.cx - rect.bbox.left) / max(rect.bbox.width, 1.0) for box in inside_texts]
        has_right_text = any(center > 0.66 for center in rel_centers)
        has_left_text = any(center < 0.45 for center in rel_centers)
        if has_left_text and not has_right_text:
            issues.append(Issue(
                "wide_container_sparse_right",
                "needs_human_review",
                "layout_heuristic",
                page,
                "Wide horizontal container has text concentrated on the left; inspect for excessive right-side whitespace.",
                {
                    "container_bbox": asdict(rect.bbox),
                    "text_count": len(inside_texts),
                    "relative_text_centers": [round(v, 3) for v in rel_centers],
                },
            ))

    lower_left = BBox(SAFE_MARGIN_X, canvas[1] * 0.56, canvas[0] * 0.44, canvas[1] * 0.86)
    upper_left = BBox(SAFE_MARGIN_X, SAFE_TOP, canvas[0] * 0.44, canvas[1] * 0.44)
    right_body = BBox(canvas[0] * 0.48, SAFE_TOP, canvas[0] - SAFE_MARGIN_X, canvas[1] * 0.86)

    def area_in_region(region: BBox) -> float:
        area = 0.0
        for box in meaningful:
            ox = box.bbox.overlaps_x(region)
            oy = box.bbox.overlaps_y(region)
            # Full-width footer/status bands should not hide a dead content
            # zone above them.
            if box.bbox.width > canvas[0] * 0.75 and box.bbox.top > canvas[1] * 0.82:
                continue
            area += ox * oy
        return area

    lower_left_area = area_in_region(lower_left)
    upper_left_area = area_in_region(upper_left)
    right_area = area_in_region(right_body)
    if lower_left_area < 700 and upper_left_area > 7000 and right_area > 14000:
        issues.append(Issue(
            "large_blank_region",
            "needs_human_review",
            "layout_heuristic",
            page,
            "Lower-left content region is nearly empty while upper-left and right-side regions carry content.",
            {
                "lower_left_region": asdict(lower_left),
                "lower_left_area": round(lower_left_area, 2),
                "upper_left_area": round(upper_left_area, 2),
                "right_area": round(right_area, 2),
            },
        ))

    return issues


def _text_density_units(text: str) -> float:
    units = 0.0
    for char in text:
        if char.isspace():
            continue
        if "\u4e00" <= char <= "\u9fff":
            units += 1.0
        elif char.isalnum():
            units += 0.55
        else:
            units += 0.25
    return units


def _check_card_density(
    page: str,
    boxes: list[ElementBox],
    rects: list[ElementBox],
    canvas: tuple[float, float],
) -> list[Issue]:
    issues: list[Issue] = []
    candidate_cards = [
        rect for rect in rects
        if rect.bbox.top >= SAFE_TOP
        and rect.bbox.bottom <= SAFE_BOTTOM
        and rect.bbox.width >= 220
        and rect.bbox.width <= canvas[0] * 0.56
        and rect.bbox.height >= 280
        and rect.bbox.area <= canvas[0] * canvas[1] * 0.36
    ]
    if len(candidate_cards) < 2:
        return issues

    text_boxes = [box for box in boxes if box.kind == "text" and box.text]
    grid_card_count = len(candidate_cards)
    for card in candidate_cards:
        inside = [
            text for text in text_boxes
            if card.bbox.expanded(2).contains_point(text.bbox.cx, text.bbox.cy)
        ]
        if len(inside) < 2:
            continue

        min_font = min(text.font_size for text in inside if text.font_size > 0)
        text_top = min(text.bbox.top for text in inside)
        text_bottom = max(text.bbox.bottom for text in inside)
        text_span_ratio = (text_bottom - text_top) / max(card.bbox.height, 1.0)
        lower_blank_ratio = (card.bbox.bottom - text_bottom) / max(card.bbox.height, 1.0)

        long_small_texts = [
            text.text for text in inside
            if text.font_size < 18 and _text_density_units(text.text) >= 14
        ]
        if long_small_texts or (grid_card_count >= 3 and min_font < 18):
            issues.append(Issue(
                "card_text_too_small",
                "must_fix",
                "card_density",
                page,
                "Large card grid uses undersized text; enlarge type or recompose the card hierarchy.",
                {
                    "card_bbox": asdict(card.bbox),
                    "card_count": grid_card_count,
                    "min_font_size": round(min_font, 2),
                    "small_text_samples": [text[:48] for text in long_small_texts[:4]],
                },
            ))

        if text_span_ratio < 0.45 or lower_blank_ratio > 0.36:
            issues.append(Issue(
                "card_sparse_content",
                "needs_human_review",
                "card_density",
                page,
                "Large card has low text density or excessive lower whitespace; inspect for tiny-text card layout.",
                {
                    "card_bbox": asdict(card.bbox),
                    "card_count": grid_card_count,
                    "text_count": len(inside),
                    "text_span_ratio": round(text_span_ratio, 3),
                    "lower_blank_ratio": round(lower_blank_ratio, 3),
                    "min_font_size": round(min_font, 2),
                },
            ))

    return issues


def _dedupe_issues(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, str, str]] = set()
    out: list[Issue] = []
    for issue in issues:
        text = str(issue.evidence.get("text", ""))[:48]
        key = (issue.page, issue.issue_id, text)
        if key in seen:
            continue
        seen.add(key)
        out.append(issue)
    return out


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _analyze_png(png_path: Path, page: str) -> tuple[list[Issue], dict[str, Any]]:
    try:
        from PIL import Image
    except ImportError:
        return (
            [Issue(
                "png_analysis_unavailable",
                "needs_human_review",
                "rendered_screenshot",
                page,
                "Pillow is not installed; rendered PNG could not be analyzed.",
                {"fix": "Install Pillow or perform manual visual review."},
            )],
            {},
        )

    img = Image.open(png_path).convert("RGB")
    width, height = img.size
    pixels = img.load()
    bg = pixels[0, 0]
    xs: list[int] = []
    ys: list[int] = []

    def is_content(x: int, y: int) -> bool:
        r, g, b = pixels[x, y]
        return abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 34

    for y in range(height):
        for x in range(width):
            if is_content(x, y):
                xs.append(x)
                ys.append(y)

    meta: dict[str, Any] = {
        "path": str(png_path),
        "sha256": _hash_file(png_path),
        "size": [width, height],
        "background_rgb": list(bg),
    }
    issues: list[Issue] = []
    if not xs:
        issues.append(Issue(
            "blank_render",
            "must_fix",
            "rendered_screenshot",
            page,
            "Rendered PNG has no visible non-background content.",
            meta,
        ))
        return issues, meta

    bbox = BBox(min(xs), min(ys), max(xs), max(ys))
    meta["content_bbox"] = asdict(bbox)
    meta["content_pixel_ratio"] = round(len(xs) / (width * height), 4)

    safe_left = min(SAFE_MARGIN_X, width // 10)
    safe_right = width - safe_left
    safe_top = min(SAFE_TOP, height // 4)
    safe_bottom = min(SAFE_BOTTOM, height - 40)
    mid_x = width // 2
    y1 = safe_top
    y2 = int(safe_top + (safe_bottom - safe_top) * 0.36)
    y3 = int(safe_top + (safe_bottom - safe_top) * 0.72)
    bands = [
        ("top_left", safe_left, mid_x, y1, y2),
        ("mid_left", safe_left, mid_x, y2, y3),
        ("lower_left", safe_left, mid_x, y3, safe_bottom),
        ("top_right", mid_x, safe_right, y1, y2),
        ("mid_right", mid_x, safe_right, y2, y3),
        ("lower_right", mid_x, safe_right, y3, safe_bottom),
    ]
    occupancy: dict[str, float] = {}
    for label, left, right, top, bottom in bands:
        total = max(1, (right - left) * (bottom - top))
        count = 0
        # Sample every second pixel to keep the gate cheap on large decks.
        sampled_total = 0
        for y in range(top, bottom, 2):
            for x in range(left, right, 2):
                sampled_total += 1
                if is_content(x, y):
                    count += 1
        occupancy[label] = round(count / max(1, sampled_total), 5)
    meta["region_occupancy"] = occupancy

    left_occ = occupancy["top_left"] + occupancy["mid_left"] + occupancy["lower_left"]
    right_occ = occupancy["top_right"] + occupancy["mid_right"] + occupancy["lower_right"]
    if min(left_occ, right_occ) / max(left_occ, right_occ, 0.00001) < 0.18:
        issues.append(Issue(
            "content_balance_outlier",
            "needs_human_review",
            "rendered_screenshot",
            page,
            "Rendered content is strongly one-sided; inspect for excessive whitespace.",
            {"left_occupancy": round(left_occ, 5), "right_occupancy": round(right_occ, 5), **meta},
        ))

    if (
        occupancy["lower_left"] < 0.0015
        and occupancy["top_left"] > 0.003
        and (occupancy["mid_right"] + occupancy["lower_right"]) > 0.006
    ):
        issues.append(Issue(
            "large_blank_region",
            "needs_human_review",
            "rendered_screenshot",
            page,
            "Lower-left safe-area region is nearly empty while adjacent page regions carry content.",
            meta,
        ))

    return issues, meta


def _run_renderer(project: Path, pages: list[str] | None, server_url: str) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "visual_review.py"),
        str(project),
        "--server-url",
        server_url,
    ]
    if pages:
        cmd.extend(["--pages", *pages])
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    return {
        "command": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _snapshot_issues(project: Path, svg_files: list[Path]) -> list[Issue]:
    snapshots_path = project / ".revision" / "snapshots.json"
    snapshots = _load_json(snapshots_path)
    if not snapshots:
        return []

    accepted_path = project / "quality" / "rendered_visual_acceptance.json"
    accepted = _load_json(accepted_path)
    current_svg_hashes = {path.name: _hash_file(path) for path in svg_files}
    changed = {
        name: {"snapshot": old_hash, "current": current_svg_hashes.get(name)}
        for name, old_hash in snapshots.items()
        if current_svg_hashes.get(name) and current_svg_hashes.get(name) != old_hash
    }
    if not changed:
        return []

    if accepted and accepted.get("svg_hashes") == current_svg_hashes:
        return []

    return [Issue(
        "rendered_regression_review_required",
        "needs_human_review",
        "human_review_gate",
        "deck",
        "SVGs changed after a revision snapshot; current rendered screenshots need explicit visual confirmation.",
        {
            "snapshot_file": str(snapshots_path),
            "acceptance_file": str(accepted_path),
            "changed_pages": changed,
        },
    )]


def _build_acceptance(project: Path, svg_files: list[Path], png_files: dict[str, Path]) -> dict[str, Any]:
    return {
        "accepted_at": _now_utc(),
        "method": "rendered_layout_check --accept-current-render",
        "svg_hashes": {path.name: _hash_file(path) for path in svg_files},
        "png_hashes": {name: _hash_file(path) for name, path in png_files.items() if path.exists()},
        "note": "Human accepted current rendered screenshots for visual-regression gate.",
    }


def _print_report(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("=" * 72)
    print("RENDERED VISUAL GATE")
    print("=" * 72)
    print(f"status: {summary['gate_status']}")
    print(f"must_fix: {summary['must_fix']} | needs_human_review: {summary['needs_human_review']} | info: {summary['info']}")
    for page, page_report in report["pages"].items():
        issues = page_report.get("issues", [])
        if not issues:
            continue
        print(f"\n{page}")
        for issue in issues:
            print(f"  [{issue['severity']}] {issue['issue_id']}: {issue['message']}")
    print("=" * 72)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rendered screenshot and layout heuristic gate for PPT Master projects.",
    )
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument(
        "--svg-dir",
        default=None,
        help="Override SVG directory (default: <project>/svg_output).",
    )
    parser.add_argument(
        "--preview-dir",
        default=None,
        help="Override preview PNG directory (default: <project>/.preview).",
    )
    parser.add_argument(
        "--pages",
        nargs="+",
        default=None,
        help="Optional page tokens to check, e.g. 01 04_takeaways.svg.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Run visual_review.py first to refresh local PNG screenshots.",
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:5050",
        help="Live-preview server URL for --render.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON report instead of text summary.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Report path (default: <project>/quality/rendered_visual_gate.json).",
    )
    parser.add_argument(
        "--read-only",
        "--no-write",
        action="store_true",
        help="Do not write the report file.",
    )
    parser.add_argument(
        "--accept-current-render",
        action="store_true",
        help="Write quality/rendered_visual_acceptance.json for current SVG+PNG hashes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project = Path(args.project_path).resolve()
    if not project.is_dir():
        print(f"project path not found: {project}", file=sys.stderr)
        return 2

    svg_dir = Path(args.svg_dir).resolve() if args.svg_dir else project / "svg_output"
    preview_dir = Path(args.preview_dir).resolve() if args.preview_dir else project / ".preview"
    if not svg_dir.is_dir():
        print(f"SVG directory not found: {svg_dir}", file=sys.stderr)
        return 2

    all_svgs = sorted(svg_dir.glob("*.svg"))
    if args.pages:
        selected: list[Path] = []
        for token in args.pages:
            match = next((p for p in all_svgs if p.name == token or p.stem == token or p.name.startswith(token)), None)
            if match is None:
                print(f"no SVG matches page token: {token}", file=sys.stderr)
                return 2
            selected.append(match)
        svg_files = selected
    else:
        svg_files = all_svgs

    render_result = None
    if args.render:
        render_result = _run_renderer(project, [p.name for p in svg_files], args.server_url)
        if render_result["returncode"] != 0:
            print(render_result["stderr"], file=sys.stderr)

    png_files = {p.name: preview_dir / f"{p.stem}.png" for p in svg_files}
    if args.accept_current_render:
        missing = [str(path) for path in png_files.values() if not path.exists()]
        if missing:
            print("cannot accept current render; missing PNG files:", file=sys.stderr)
            for path in missing:
                print(f"  {path}", file=sys.stderr)
            return 2
        acceptance = _build_acceptance(project, svg_files, png_files)
        out = project / "quality" / "rendered_visual_acceptance.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(acceptance, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Accepted current rendered visual state: {out}")
        return 0

    deck_issues = _snapshot_issues(project, svg_files)
    pages: dict[str, dict[str, Any]] = {}
    all_issues: list[Issue] = [*deck_issues]

    for svg_path in svg_files:
        page_issues = _check_svg_geometry(svg_path)
        png_meta: dict[str, Any] = {}
        png_path = png_files[svg_path.name]
        if png_path.exists():
            png_issues, png_meta = _analyze_png(png_path, svg_path.name)
            page_issues.extend(png_issues)
        else:
            page_issues.append(Issue(
                "rendered_png_missing",
                "needs_human_review",
                "rendered_screenshot",
                svg_path.name,
                "Rendered PNG is missing; run visual_review.py or rendered_layout_check.py --render before export.",
                {"expected_png": str(png_path)},
            ))

        all_issues.extend(page_issues)
        pages[svg_path.name] = {
            "svg_path": str(svg_path),
            "png_path": str(png_path) if png_path.exists() else None,
            "png": png_meta,
            "issues": [asdict(issue) for issue in _dedupe_issues(page_issues)],
        }

    if deck_issues:
        pages["_deck"] = {
            "issues": [asdict(issue) for issue in deck_issues],
        }

    must_fix = sum(1 for issue in all_issues if issue.severity == "must_fix")
    needs_human = sum(1 for issue in all_issues if issue.severity == "needs_human_review")
    info = sum(1 for issue in all_issues if issue.severity == "info")
    gate_status = "BLOCKED" if must_fix or needs_human else "PASS"

    report = {
        "checked_at": _now_utc(),
        "method": "rendered_layout_check",
        "project": str(project),
        "svg_dir": str(svg_dir),
        "preview_dir": str(preview_dir),
        "render": render_result,
        "summary": {
            "gate_status": gate_status,
            "must_fix": must_fix,
            "needs_human_review": needs_human,
            "info": info,
            "page_count": len(svg_files),
        },
        "pages": pages,
        "role_boundaries": {
            "svg_quality_checker.py": "static SVG/XML/spec compliance; not a visual acceptance gate",
            "rendered_layout_check.py": "local screenshots plus layout heuristics; blocks on must-fix and human-review-required findings",
            "visual-review.md": "rubric or human visual review for subjective quality decisions",
            "harness_gate.py --quick": "aggregates static checks only; e2e is skipped",
            "e2e_validate.py": "PPTX structure/page/notes integrity; not a visual checker",
        },
    }

    output_path = Path(args.output).resolve() if args.output else project / "quality" / "rendered_visual_gate.json"
    if not args.read_only:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_report(report)
        if not args.read_only:
            print(f"report: {output_path}")

    return 1 if gate_status == "BLOCKED" else 0


if __name__ == "__main__":
    configure_utf8_stdio()
    raise SystemExit(main())
