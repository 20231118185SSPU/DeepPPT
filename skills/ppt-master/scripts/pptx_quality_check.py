#!/usr/bin/env python3
"""
PPT Master - PPTX Quality Check

Checks exported PPTX files for structure, editable text, image-area risks,
placeholder text, font-size floor, and slide-bound geometry.

Usage:
    python3 scripts/pptx_quality_check.py <pptx_path> [options]
    python3 scripts/pptx_quality_check.py <pptx_path> --json-out report.json

Examples:
    python3 scripts/pptx_quality_check.py projects/my_deck/exports/deck.pptx
    python3 scripts/pptx_quality_check.py projects/my_deck/exports/deck.pptx --json-out projects/my_deck/quality/pptx_quality.json

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
}

SLIDE_RE = re.compile(r"ppt/slides/slide(\d+)\.xml$")
PLACEHOLDER_RE = re.compile(
    r"\b(?:TODO|TBD|PLACEHOLDER|LOREM IPSUM)\b|Click to add|单击此处添加",
    re.IGNORECASE,
)

DEFAULT_MIN_FONT_PT = 6.5
DEFAULT_MIN_TEXT_SHAPES = 1
DEFAULT_LARGE_IMAGE_RATIO = 0.40
DEFAULT_FULL_IMAGE_RATIO = 0.90
DEFAULT_EXPECTED_ASPECT = 16 / 9
DEFAULT_ASPECT_TOLERANCE = 0.03
INPUT_ERROR_CODES = {
    "FILE_NOT_FOUND",
    "INVALID_PPTX_ZIP",
    "MISSING_PACKAGE_PART",
    "MISSING_SLIDE_SIZE",
    "INVALID_SLIDE_SIZE",
    "INVALID_PACKAGE_XML",
}


def make_issue(code: str, message: str, *, slide: int | None = None) -> dict[str, Any]:
    """Build a report issue."""
    issue: dict[str, Any] = {"code": code, "message": message}
    if slide is not None:
        issue["slide"] = slide
    return issue


def read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    """Read an XML part from a PPTX archive."""
    return ET.fromstring(archive.read(name))


def find_slide_names(archive: zipfile.ZipFile) -> list[str]:
    """Return slide XML part names ordered by slide number."""
    slides: list[tuple[int, str]] = []
    for name in archive.namelist():
        match = SLIDE_RE.fullmatch(name)
        if match:
            slides.append((int(match.group(1)), name))
    return [name for _, name in sorted(slides)]


def shape_bounds(element: ET.Element) -> tuple[int, int, int, int] | None:
    """Return ``(x, y, cx, cy)`` bounds in EMUs for a slide element."""
    xfrm = element.find(".//a:xfrm", NS)
    if xfrm is None:
        return None
    offset = xfrm.find("a:off", NS)
    extent = xfrm.find("a:ext", NS)
    if offset is None or extent is None:
        return None
    try:
        return (
            int(offset.get("x", "0")),
            int(offset.get("y", "0")),
            int(extent.get("cx", "0")),
            int(extent.get("cy", "0")),
        )
    except ValueError:
        return None


def text_content(element: ET.Element) -> str:
    """Return visible text stored in DrawingML text runs."""
    return "".join(node.text or "" for node in element.findall(".//a:t", NS)).strip()


def font_sizes_pt(element: ET.Element) -> list[float]:
    """Extract run and default run font sizes in points."""
    sizes: list[float] = []
    for node in element.findall(".//a:rPr", NS) + element.findall(".//a:defRPr", NS):
        raw_size = node.get("sz")
        if raw_size is None:
            continue
        try:
            size = int(raw_size) / 100
        except ValueError:
            continue
        if size > 0:
            sizes.append(size)
    return sizes


def empty_report(path: Path) -> dict[str, Any]:
    """Create an empty report shell."""
    return {
        "schema": "ppt_master.pptx_quality_check.v1",
        "file": str(path),
        "summary": {
            "slide_count": 0,
            "width_emu": 0,
            "height_emu": 0,
            "aspect_ratio": 0.0,
            "native_text_shapes": 0,
            "native_graphic_shapes": 0,
            "pictures": 0,
            "charts": 0,
            "tables": 0,
            "min_font_size_pt": None,
            "max_picture_area_ratio": 0.0,
        },
        "errors": [],
        "warnings": [],
        "slides": [],
    }


def inspect_slide(
    root: ET.Element,
    slide_number: int,
    width: int,
    height: int,
    *,
    min_font_pt: float,
    min_text_shapes: int,
    large_image_ratio: float,
    full_image_ratio: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Inspect one slide and return metrics, errors, and warnings."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    shapes = root.findall(".//p:sp", NS)
    pictures = root.findall(".//p:pic", NS)
    graphic_frames = root.findall(".//p:graphicFrame", NS)
    charts = root.findall(".//c:chart", NS)
    tables = root.findall(".//a:tbl", NS)

    measurable_elements = [*shapes, *pictures, *graphic_frames]
    slide_area = max(width * height, 1)
    text_shapes = [shape for shape in shapes if text_content(shape)]
    native_text_shapes = len(text_shapes)
    all_font_sizes = [size for shape in text_shapes for size in font_sizes_pt(shape)]
    picture_area_ratios: list[float] = []

    for element in measurable_elements:
        bounds = shape_bounds(element)
        if bounds is None:
            continue
        x, y, cx, cy = bounds
        if cx <= 0 or cy <= 0:
            errors.append(
                make_issue(
                    "ZERO_OR_NEGATIVE_SHAPE_SIZE",
                    "Element has zero or negative dimensions.",
                    slide=slide_number,
                )
            )
        if x < 0 or y < 0:
            errors.append(
                make_issue(
                    "NEGATIVE_SHAPE_COORDINATE",
                    "Element has negative coordinates.",
                    slide=slide_number,
                )
            )
        if x + cx > width or y + cy > height:
            errors.append(
                make_issue(
                    "SHAPE_OUTSIDE_SLIDE",
                    "Element extends beyond the slide canvas.",
                    slide=slide_number,
                )
            )

    for picture in pictures:
        bounds = shape_bounds(picture)
        if bounds is None:
            continue
        _, _, cx, cy = bounds
        area_ratio = max(0.0, (cx * cy) / slide_area)
        picture_area_ratios.append(area_ratio)
        if area_ratio >= full_image_ratio:
            errors.append(
                make_issue(
                    "FULL_SLIDE_IMAGE_RISK",
                    "A single picture covers most of the slide; verify this is not a rasterized page.",
                    slide=slide_number,
                )
            )
        elif area_ratio >= large_image_ratio:
            warnings.append(
                make_issue(
                    "LARGE_IMAGE_ASSET",
                    "A single picture covers a large part of the slide; verify key text/data remains editable.",
                    slide=slide_number,
                )
            )

    combined_text = " ".join(text_content(shape) for shape in text_shapes)
    if PLACEHOLDER_RE.search(combined_text):
        errors.append(
            make_issue(
                "PLACEHOLDER_TEXT",
                "Possible authoring placeholder text remains on the slide.",
                slide=slide_number,
            )
        )

    if native_text_shapes < min_text_shapes:
        errors.append(
            make_issue(
                "LOW_NATIVE_TEXT_SHAPE_COUNT",
                f"Slide has {native_text_shapes} native text shape(s); expected at least {min_text_shapes}.",
                slide=slide_number,
            )
        )

    min_font_size = min(all_font_sizes) if all_font_sizes else None
    max_font_size = max(all_font_sizes) if all_font_sizes else None
    if min_font_size is not None and min_font_size < min_font_pt:
        errors.append(
            make_issue(
                "FONT_SIZE_BELOW_MINIMUM",
                f"Native text run is {min_font_size:.1f}pt; minimum is {min_font_pt:.1f}pt.",
                slide=slide_number,
            )
        )

    total_picture_area = round(min(sum(picture_area_ratios), 1.0), 4)
    max_picture_area = round(max(picture_area_ratios, default=0.0), 4)
    if total_picture_area >= large_image_ratio:
        warnings.append(
            make_issue(
                "HIGH_TOTAL_IMAGE_AREA",
                "Pictures cover a large part of the slide in total; verify asset use is intentional.",
                slide=slide_number,
            )
        )

    metrics = {
        "slide": slide_number,
        "native_text_shapes": native_text_shapes,
        "native_graphic_shapes": len(shapes) + len(graphic_frames),
        "pictures": len(pictures),
        "charts": len(charts),
        "tables": len(tables),
        "element_count": len(measurable_elements),
        "picture_area_ratio": total_picture_area,
        "max_picture_area_ratio": max_picture_area,
        "min_font_size_pt": round(min_font_size, 2) if min_font_size is not None else None,
        "max_font_size_pt": round(max_font_size, 2) if max_font_size is not None else None,
        "text_characters": len(combined_text),
    }
    return metrics, errors, warnings


def validate_pptx(
    path: Path,
    *,
    expected_aspect: float,
    aspect_tolerance: float,
    min_font_pt: float,
    min_text_shapes: int,
    large_image_ratio: float,
    full_image_ratio: float,
) -> dict[str, Any]:
    """Validate a PPTX file and return a structured report."""
    report = empty_report(path)
    if not path.is_file():
        report["errors"].append(make_issue("FILE_NOT_FOUND", f"PPTX file not found: {path}"))
        return report

    try:
        with zipfile.ZipFile(path) as archive:
            required_parts = {"[Content_Types].xml", "ppt/presentation.xml"}
            missing = sorted(required_parts - set(archive.namelist()))
            if missing:
                report["errors"].append(
                    make_issue("MISSING_PACKAGE_PART", f"Missing required PPTX parts: {', '.join(missing)}")
                )
                return report

            presentation = read_xml(archive, "ppt/presentation.xml")
            slide_size = presentation.find("p:sldSz", NS)
            if slide_size is None:
                report["errors"].append(
                    make_issue("MISSING_SLIDE_SIZE", "ppt/presentation.xml has no p:sldSz element.")
                )
                return report

            width = int(slide_size.get("cx", "0"))
            height = int(slide_size.get("cy", "0"))
            if width <= 0 or height <= 0:
                report["errors"].append(
                    make_issue("INVALID_SLIDE_SIZE", f"Invalid slide size: {width} x {height} EMU.")
                )
                return report

            aspect_ratio = width / height
            report["summary"].update(
                {
                    "width_emu": width,
                    "height_emu": height,
                    "aspect_ratio": round(aspect_ratio, 4),
                }
            )
            if expected_aspect > 0 and abs(aspect_ratio - expected_aspect) > aspect_tolerance:
                report["warnings"].append(
                    make_issue(
                        "UNEXPECTED_ASPECT_RATIO",
                        f"Slide aspect ratio is {aspect_ratio:.4f}; expected {expected_aspect:.4f} +/- {aspect_tolerance:.4f}.",
                    )
                )

            slide_names = find_slide_names(archive)
            if not slide_names:
                report["errors"].append(make_issue("NO_SLIDES", "No ppt/slides/slideN.xml parts found."))
                return report

            for slide_number, slide_name in enumerate(slide_names, start=1):
                try:
                    slide_root = read_xml(archive, slide_name)
                except (ET.ParseError, KeyError) as exc:
                    report["errors"].append(
                        make_issue(
                            "INVALID_SLIDE_XML",
                            f"Cannot parse {slide_name}: {exc}",
                            slide=slide_number,
                        )
                    )
                    continue
                metrics, errors, warnings = inspect_slide(
                    slide_root,
                    slide_number,
                    width,
                    height,
                    min_font_pt=min_font_pt,
                    min_text_shapes=min_text_shapes,
                    large_image_ratio=large_image_ratio,
                    full_image_ratio=full_image_ratio,
                )
                report["slides"].append(metrics)
                report["errors"].extend(errors)
                report["warnings"].extend(warnings)

            report["summary"]["slide_count"] = len(slide_names)
            for field in ("native_text_shapes", "native_graphic_shapes", "pictures", "charts", "tables"):
                report["summary"][field] = sum(slide[field] for slide in report["slides"])
            font_sizes = [
                slide["min_font_size_pt"]
                for slide in report["slides"]
                if slide["min_font_size_pt"] is not None
            ]
            report["summary"]["min_font_size_pt"] = min(font_sizes) if font_sizes else None
            report["summary"]["max_picture_area_ratio"] = round(
                max((slide["max_picture_area_ratio"] for slide in report["slides"]), default=0.0),
                4,
            )
    except zipfile.BadZipFile:
        report["errors"].append(make_issue("INVALID_PPTX_ZIP", "File is not a readable PPTX ZIP package."))
    except (ET.ParseError, KeyError, ValueError) as exc:
        report["errors"].append(make_issue("INVALID_PACKAGE_XML", str(exc)))

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check exported PPTX structure and editability risks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pptx_path", help="Path to the PPTX file to inspect")
    parser.add_argument("--json-out", help="Optional path for a UTF-8 JSON report")
    parser.add_argument(
        "--expected-aspect",
        type=float,
        default=DEFAULT_EXPECTED_ASPECT,
        help="Expected slide aspect ratio. Use 0 to disable aspect warning. Default: 16:9.",
    )
    parser.add_argument(
        "--aspect-tolerance",
        type=float,
        default=DEFAULT_ASPECT_TOLERANCE,
        help="Allowed aspect-ratio delta before warning.",
    )
    parser.add_argument(
        "--min-font-pt",
        type=float,
        default=DEFAULT_MIN_FONT_PT,
        help="Minimum native text font size before error.",
    )
    parser.add_argument(
        "--min-text-shapes",
        type=int,
        default=DEFAULT_MIN_TEXT_SHAPES,
        help="Minimum native text shapes per slide before error.",
    )
    parser.add_argument(
        "--large-image-ratio",
        type=float,
        default=DEFAULT_LARGE_IMAGE_RATIO,
        help="Single/total picture area ratio that emits a warning.",
    )
    parser.add_argument(
        "--full-image-ratio",
        type=float,
        default=DEFAULT_FULL_IMAGE_RATIO,
        help="Single picture area ratio that emits an error.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    pptx_path = Path(args.pptx_path)
    report = validate_pptx(
        pptx_path,
        expected_aspect=args.expected_aspect,
        aspect_tolerance=args.aspect_tolerance,
        min_font_pt=args.min_font_pt,
        min_text_shapes=args.min_text_shapes,
        large_image_ratio=args.large_image_ratio,
        full_image_ratio=args.full_image_ratio,
    )

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_out:
        output_path = Path(args.json_out)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(payload + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"Error: cannot write JSON report: {exc}", file=sys.stderr)
            return 2

    print(payload)
    if report["errors"]:
        error_codes = {error.get("code") for error in report["errors"]}
        if error_codes and error_codes.issubset(INPUT_ERROR_CODES):
            return 2
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
