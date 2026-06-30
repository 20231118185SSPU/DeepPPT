"""
Estimate whether planned slide copy can fit standard layout zones.

Lightweight pre-check: reads detailed_outline.json and spec_lock.md,
estimates text load against layout slot dimensions, flags overfull/tight pages
BEFORE Executor begins SVG generation.

Adapted from PPT Hell's estimate_layout_capacity.py for DeepPPT's schema.

Usage:
  python layout_capacity_check.py <project_path> [--output <path>] [--format json|text]
"""

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LINE_HEIGHT = 1.4
DEFAULT_BODY_SIZE = 22
DEFAULT_CANVAS = (1280, 720)

LAYOUT_ZONES = {
    "03_content_image_text": [
        {"zone": "text_left", "x": 40, "y": 100, "w": 580, "h": 540},
        {"zone": "image_right", "x": 660, "y": 100, "w": 580, "h": 540},
    ],
    "03_content_image_hero": [
        {"zone": "title_top", "x": 40, "y": 40, "w": 1200, "h": 80},
        {"zone": "image_center", "x": 40, "y": 140, "w": 1200, "h": 500},
    ],
    "03_content_bullet_cards": [
        {"zone": "title_top", "x": 40, "y": 40, "w": 1200, "h": 80},
        {"zone": "cards_area", "x": 40, "y": 140, "w": 1200, "h": 500},
    ],
    "03_content_three_columns": [
        {"zone": "title_top", "x": 40, "y": 40, "w": 1200, "h": 80},
        {"zone": "col_1", "x": 40, "y": 140, "w": 370, "h": 500},
        {"zone": "col_2", "x": 435, "y": 140, "w": 370, "h": 500},
        {"zone": "col_3", "x": 830, "y": 140, "w": 370, "h": 500},
    ],
    "03_content_data_cards": [
        {"zone": "title_top", "x": 40, "y": 40, "w": 1200, "h": 80},
        {"zone": "cards_area", "x": 40, "y": 140, "w": 1200, "h": 500},
    ],
    "_default": [
        {"zone": "title_top", "x": 40, "y": 40, "w": 1200, "h": 80},
        {"zone": "content_main", "x": 40, "y": 140, "w": 1160, "h": 500},
    ],
}


def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def parse_spec_lock(project_path):
    """Extract body font size and canvas from spec_lock.md."""
    spec_path = Path(project_path) / "spec_lock.md"
    body_size = DEFAULT_BODY_SIZE
    canvas_w, canvas_h = DEFAULT_CANVAS

    if not spec_path.exists():
        return body_size, canvas_w, canvas_h

    text = spec_path.read_text(encoding="utf-8")
    m = re.search(r"^- body:\s*(\d+)", text, re.MULTILINE)
    if m:
        body_size = int(m.group(1))
    m = re.search(r"^- viewBox:\s*0\s+0\s+(\d+)\s+(\d+)", text, re.MULTILINE)
    if m:
        canvas_w, canvas_h = int(m.group(1)), int(m.group(2))
    return body_size, canvas_w, canvas_h


def visual_chars(text):
    """Estimate visual character width (CJK=1.0, Latin=0.55, space=0.25)."""
    total = 0.0
    for ch in str(text or ""):
        if ch.isspace():
            total += 0.25
        elif ord(ch) < 128:
            total += 0.55
        else:
            total += 1.0
    return total


def font_size_for_zone(zone_name, body_size):
    z = zone_name.lower()
    if "title" in z:
        return int(body_size * 1.6)
    if "footer" in z or "annotation" in z:
        return int(body_size * 0.7)
    return body_size


def chars_per_line(zone_width, font_size, padding=24):
    usable = max(1.0, float(zone_width) - 2 * padding)
    avg_char_w = font_size * 0.78
    return max(1, math.floor(usable / avg_char_w))


def max_lines(zone_height, font_size):
    usable = max(1.0, float(zone_height) - 40.0)
    return max(1, math.floor(usable / (font_size * DEFAULT_LINE_HEIGHT)))


def classify(utilization, est_chars, zone_name):
    if est_chars <= 0:
        if "image" in zone_name.lower():
            return "ok"
        return "too_empty"
    if utilization > 1.15:
        return "overfull"
    if utilization > 0.85:
        return "tight"
    if utilization < 0.2:
        return "too_empty"
    return "ok"


def extract_page_text(page):
    """Extract text content from a detailed_outline.json page entry."""
    parts = []
    title = page.get("core_argument", "")
    if title:
        parts.append(("title", title))

    hierarchy = page.get("text_hierarchy", {})
    if isinstance(hierarchy, dict):
        for key in ("title", "subtitle"):
            v = hierarchy.get(key, "")
            if v and v != title:
                parts.append(("title", str(v)))
        body_items = hierarchy.get("body", [])
        if isinstance(body_items, list):
            parts.append(("body", "\n".join(str(x) for x in body_items)))
        elif body_items:
            parts.append(("body", str(body_items)))
        ann = hierarchy.get("annotation", "")
        if ann:
            parts.append(("annotation", str(ann)))

    bullets = page.get("content_bullets", [])
    if bullets and not any(k == "body" for k, _ in parts):
        parts.append(("body", "\n".join(str(b) for b in bullets)))

    return parts


def get_zones(layout_suggestion):
    """Get zone definitions for a layout template."""
    if not layout_suggestion:
        return LAYOUT_ZONES["_default"]
    for key, zones in LAYOUT_ZONES.items():
        if key != "_default" and key in layout_suggestion:
            return zones
    return LAYOUT_ZONES["_default"]


def check_page(page, body_size):
    """Check capacity for a single page."""
    page_type = page.get("page_type", "content")
    if page_type in ("cover", "ending", "toc"):
        return {"status": "ok", "summary": "Structural page — capacity check skipped.", "regions": [], "recommendations": []}

    layout = page.get("layout_suggestion", "")
    zones = get_zones(layout)
    text_parts = extract_page_text(page)

    title_text = " ".join(t for role, t in text_parts if role == "title")
    body_text = "\n".join(t for role, t in text_parts if role == "body")
    annotation_text = " ".join(t for role, t in text_parts if role == "annotation")

    status_rank = {"ok": 0, "too_empty": 1, "tight": 2, "overfull": 3}
    worst = "ok"
    regions_out = []

    for zone in zones:
        zone_name = zone["zone"]
        if "image" in zone_name.lower():
            regions_out.append({
                "zone": zone_name, "status": "ok",
                "estimated_chars": 0, "font_size": 0,
                "estimated_lines": 0, "max_lines": 0, "utilization": 0.0,
            })
            continue

        fs = font_size_for_zone(zone_name, body_size)
        if "title" in zone_name.lower():
            text = title_text
        elif "footer" in zone_name.lower() or "annotation" in zone_name.lower():
            text = annotation_text
        else:
            text = body_text

        est_chars = visual_chars(text)
        cpl = chars_per_line(zone["w"], fs)
        lines = int(math.ceil(est_chars / max(cpl, 1))) if est_chars else 0
        ml = max_lines(zone["h"], fs)
        utilization = lines / max(ml, 1)
        status = classify(utilization, est_chars, zone_name)

        if status_rank.get(status, 0) > status_rank.get(worst, 0):
            worst = status

        regions_out.append({
            "zone": zone_name,
            "estimated_chars": round(est_chars, 1),
            "font_size": fs,
            "estimated_lines": lines,
            "max_lines": ml,
            "utilization": round(utilization, 2),
            "status": status,
        })

    recommendations = []
    if worst == "overfull":
        recommendations.append("Text likely exceeds layout zone. Shorten content_bullets, split page, or choose a larger template before Executor starts.")
    elif worst == "tight":
        recommendations.append("Text may fit but needs careful line breaks. Avoid solving by shrinking below body font size.")

    summaries = {
        "ok": "Planned copy is likely to fit.",
        "tight": "Copy may fit but zone is near capacity.",
        "overfull": "Copy likely cannot fit without layout or content changes.",
        "too_empty": "Some zones appear underused.",
    }

    return {
        "status": worst,
        "summary": summaries.get(worst, worst),
        "regions": regions_out,
        "recommendations": recommendations,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Estimate layout copy capacity for DeepPPT projects (pre-Executor check)."
    )
    parser.add_argument("project_path", help="Project root directory")
    parser.add_argument("--output", default="", help="Output JSON path (default: <project>/layout_capacity_report.json)")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")
    args = parser.parse_args()

    root = Path(args.project_path)
    outline = load_json(root / "detailed_outline.json")
    if not outline:
        raise SystemExit(f"Cannot find or parse: {root / 'detailed_outline.json'}")

    body_size, canvas_w, canvas_h = parse_spec_lock(root)

    pages_data = outline if isinstance(outline, list) else outline.get("pages", outline.get("detailed_outline", []))
    if not isinstance(pages_data, list):
        raise SystemExit("Cannot find pages array in detailed_outline.json")

    results = {}
    issues = {"overfull": 0, "tight": 0, "too_empty": 0, "ok": 0}

    for page in pages_data:
        if not isinstance(page, dict):
            continue
        pnum = page.get("page_number", 0)
        key = f"P{pnum:02d}" if pnum else page.get("page_key", "unknown")
        result = check_page(page, body_size)
        results[key] = result
        issues[result["status"]] = issues.get(result["status"], 0) + 1

    report = {
        "project": root.name,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "canvas": {"w": canvas_w, "h": canvas_h},
        "body_font_size": body_size,
        "summary": issues,
        "pages": results,
    }

    if args.format == "text":
        print(f"Layout Capacity Check: {root.name}")
        print(f"Canvas: {canvas_w}x{canvas_h}, Body font: {body_size}px")
        print(f"Pages: {len(results)} checked")
        print(f"  ok: {issues['ok']}  tight: {issues['tight']}  overfull: {issues['overfull']}  too_empty: {issues['too_empty']}")
        print()
        for key, res in results.items():
            if res["status"] in ("overfull", "tight"):
                print(f"  ⚠ {key}: {res['status']} — {res['summary']}")
                for rec in res.get("recommendations", []):
                    print(f"    → {rec}")
        if issues["overfull"] == 0 and issues["tight"] == 0:
            print("  ✓ All pages within capacity.")

    output_path = Path(args.output) if args.output else root / "layout_capacity_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.format == "text":
        print(f"\nReport written to: {output_path}")

    return 1 if issues["overfull"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
