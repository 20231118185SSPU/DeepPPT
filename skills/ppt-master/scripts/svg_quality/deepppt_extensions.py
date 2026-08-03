"""DeepPPT2-specific review checks, migrated from the pre-refactor checker.

These heuristics predate the upstream DrawingML refactor and are not part of
the upstream ``svg_quality`` contract: WCAG contrast, narrative consistency,
element spacing / vertical distribution / overlap / image-text gap / whitespace
balance, the legacy safe-margin layout check, and the three-tier
must_fix / should_fix / accepted_risks classification used by
``--integrated-review``.

They are intentionally review-oriented: messages prefixed with "Review only:"
must never be satisfied by adding filler — the composition itself is the
judgement. The new checker's own contract checks (real text metrics,
transform-aware bounds, syntax contracts) remain the authoritative gate; this
module only appends advisory findings to the same result dict.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: F401  (kept for parity with callers)

# Safe margins from executor-base.md §14.1 (legacy heuristic; the new checker's
# transform-aware bounds contract supersedes these for strict gating).
SAFE_MARGIN_LR = 50   # left/right
SAFE_MARGIN_TB = 40   # top/bottom
OVERFLOW_TOLERANCE = 10  # px grace to avoid false positives

MIN_H_GAP = 15        # px between same-row text elements
MIN_V_GAP_RATIO = 0.3  # fraction of font-size for vertical gap

_EMOJI_RE = re.compile(
    '['
    '\U0001F600-\U0001F64F'  # emoticons
    '\U0001F300-\U0001F5FF'  # misc symbols & pictographs
    '\U0001F680-\U0001F6FF'  # transport & map
    '\U0001F900-\U0001F9FF'  # supplemental symbols
    '\U0001FA00-\U0001FA6F'  # chess symbols
    '\U0001FA70-\U0001FAFF'  # symbols extended-A
    '\U00002702-\U000027B0'  # dingbats
    '\U00002600-\U000026FF'  # misc symbols
    '\U00002700-\U000027BF'  # dingbats
    '\U0000FE00-\U0000FE0F'  # variation selectors
    ']'
)

_MUST_FIX_KEYWORDS = (
    'Invalid XML', 'viewBox', 'Forbidden element', 'Layout overflow',
    'TEXT_OVERFLOW_MAJOR', 'FONT_TOO_SMALL', 'Emoji', 'missing xmlns',
    'width/height mismatch', 'banned', 'not well-formed',
)
_SHOULD_FIX_KEYWORDS = (
    'spec_lock drift', 'Font not PPT-safe', 'Element overlap', 'Spacing',
    'WCAG contrast', 'font-family', 'vertical distribution', 'safe margin',
)


def _wcag_contrast(hex1: str, hex2: str) -> float:
    """Calculate WCAG 2.0 contrast ratio between two #RRGGBB colors."""

    def _luminance(hex_color: str) -> float:
        r = int(hex_color[1:3], 16) / 255.0
        g = int(hex_color[3:5], 16) / 255.0
        b = int(hex_color[5:7], 16) / 255.0

        def _linearize(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)

    l1 = _luminance(hex1)
    l2 = _luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _extract_global_font_size(content: str) -> float | None:
    """Extract the dominant font-size from the SVG (first text element)."""
    m = re.search(r'font-size="([^"]+)"', content)
    if m:
        try:
            return float(m.group(1).replace('px', '').strip())
        except ValueError:
            pass
    return None


def _is_cjk(text: str) -> bool:
    """Heuristic: if >30% of characters are CJK, treat as CJK text."""
    if not text:
        return False
    cjk = sum(1 for c in text if '一' <= c <= '鿿'
              or '　' <= c <= '〿'
              or '＀' <= c <= '￯')
    return cjk / max(len(text), 1) > 0.3


def _viewbox_dimensions(content: str) -> tuple[float, float] | None:
    """Return (width, height) of the root viewBox, or None."""
    vb_match = re.search(r'viewBox="([^"]+)"', content)
    if not vb_match:
        return None
    parts = vb_match.group(1).split()
    if len(parts) != 4:
        return None
    try:
        return float(parts[2]), float(parts[3])
    except ValueError:
        return None


def _spec_lock_bg_color(svg_path: Path) -> str | None:
    """Read spec_lock.md colors.bg near the SVG (best-effort regex parse)."""
    for candidate in (svg_path.parent / 'spec_lock.md',
                      svg_path.parent.parent / 'spec_lock.md'):
        if not candidate.exists():
            continue
        try:
            text = candidate.read_text(encoding='utf-8')
        except OSError:
            return None
        section = re.search(r'##\s+colors\b(.*?)(?=\n##\s|\Z)', text, re.DOTALL)
        if not section:
            return None
        bg = re.search(r'-\s*bg\s*:\s*([#\w]+)', section.group(1))
        if bg:
            return bg.group(1)
    return None


def check_dimensions(content: str, result: dict) -> None:
    """Check root SVG width/height presence and consistency with viewBox."""
    root_match = re.search(r'<svg\b([^>]*)>', content, re.IGNORECASE)
    if not root_match:
        result['errors'].append("Missing root <svg> element")
        return

    root_attrs = root_match.group(1)
    width_match = re.search(r'\bwidth="(\d+)"', root_attrs)
    height_match = re.search(r'\bheight="(\d+)"', root_attrs)

    if width_match and height_match:
        width = width_match.group(1)
        height = height_match.group(1)
        result['info']['dimensions'] = f"{width}x{height}"

        if 'viewbox' in result['info']:
            viewbox_parts = result['info']['viewbox'].split()
            if len(viewbox_parts) == 4:
                vb_width, vb_height = viewbox_parts[2], viewbox_parts[3]
                if width != vb_width or height != vb_height:
                    result['warnings'].append(
                        f"width/height ({width}x{height}) does not match viewBox "
                        f"({vb_width}x{vb_height})"
                    )
    else:
        result['errors'].append(
            "SVG root element missing width/height attributes - "
            "add width and height matching the viewBox dimensions "
            "(e.g. width=1280 height=720)."
        )


def check_layout_bounds(content: str, result: dict) -> None:
    """Legacy safe-margin heuristic: text/image overflow vs the viewBox.

    Superseded for strict gating by the new transform-aware bounds contract,
    but kept as an advisory signal that reads the same vocabulary as the
    Executor's safe-area rules.
    """
    dims = _viewbox_dimensions(content)
    if dims is None:
        return
    vb_w, vb_h = dims

    right_bound = vb_w - SAFE_MARGIN_LR + OVERFLOW_TOLERANCE
    bottom_bound = vb_h - SAFE_MARGIN_TB + OVERFLOW_TOLERANCE
    left_bound = SAFE_MARGIN_LR - OVERFLOW_TOLERANCE
    top_bound = SAFE_MARGIN_TB - OVERFLOW_TOLERANCE

    text_pat = re.compile(
        r'<text\b[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"[^>]*>([^<]+)</text>',
        re.DOTALL,
    )
    tspan_pat = re.compile(
        r'<tspan\b[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"[^>]*>([^<]+)</tspan>',
        re.DOTALL,
    )

    global_fs = _extract_global_font_size(content)
    overflow_count = 0
    for m in text_pat.finditer(content):
        overflow_count += _check_single_text_bounds(
            m.group(1), m.group(2), m.group(3), global_fs,
            right_bound, bottom_bound, left_bound, top_bound, result,
            m.group(0)[:60],
        )
    for m in tspan_pat.finditer(content):
        overflow_count += _check_single_text_bounds(
            m.group(1), m.group(2), m.group(3), global_fs,
            right_bound, bottom_bound, left_bound, top_bound, result,
            m.group(0)[:60],
        )

    if overflow_count > 0:
        result['info']['layout_overflow_count'] = overflow_count

    img_pat = re.compile(
        r'<image\b[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"'
        r'[^>]*\bwidth="([^"]+)"[^>]*\bheight="([^"]+)"',
        re.IGNORECASE,
    )
    for m in img_pat.finditer(content):
        try:
            ix, iy = float(m.group(1)), float(m.group(2))
            iw, ih = float(m.group(3)), float(m.group(4))
        except ValueError:
            continue
        if ix + iw > vb_w + OVERFLOW_TOLERANCE:
            result['warnings'].append(
                f"Layout: image at x={ix} width={iw} exceeds viewBox width {vb_w}")
        if iy + ih > vb_h + OVERFLOW_TOLERANCE:
            result['warnings'].append(
                f"Layout: image at y={iy} height={ih} exceeds viewBox height {vb_h}")


def _check_single_text_bounds(x_str, y_str, text, global_fs,
                              right_bound, bottom_bound, left_bound,
                              top_bound, result, snippet) -> int:
    """Check one text element against the legacy safe-margin bounds."""
    try:
        x = float(x_str)
        y = float(y_str)
    except ValueError:
        return 0

    fs = global_fs if global_fs else 20
    char_width = fs * 1.0 if _is_cjk(text) else fs * 0.55
    est_width = len(text.strip()) * char_width
    anchor = 'start'
    if 'text-anchor="middle"' in snippet:
        anchor = 'middle'
    elif 'text-anchor="end"' in snippet:
        anchor = 'end'

    if anchor == 'middle':
        right_edge = x + est_width / 2
        left_edge = x - est_width / 2
    elif anchor == 'end':
        right_edge = x
        left_edge = x - est_width
    else:
        right_edge = x + est_width
        left_edge = x

    if right_edge > right_bound:
        result['warnings'].append(
            f"Layout overflow: text '{text[:30]}...' right edge ~{right_edge:.0f} "
            f"exceeds safe area bound {right_bound:.0f}")
        return 1
    if left_edge < left_bound:
        result['warnings'].append(
            f"Layout overflow: text '{text[:30]}...' left edge ~{left_edge:.0f} "
            f"below safe area bound {left_bound:.0f}")
        return 1
    if y > bottom_bound:
        result['warnings'].append(
            f"Layout overflow: text '{text[:30]}...' y={y} "
            f"exceeds safe area bottom {bottom_bound:.0f}")
        return 1
    if y < top_bound:
        result['warnings'].append(
            f"Layout overflow: text '{text[:30]}...' y={y} "
            f"above safe area top {top_bound:.0f}")
        return 1
    return 0


def check_contrast(content: str, svg_path: Path, result: dict) -> None:
    """WCAG contrast check: text fill colors vs spec_lock background.

    Only checks text with font-size >= 14px — decorative micro-text
    (page numbers, footnotes) are exempt from the strict threshold.
    """
    bg_color = _spec_lock_bg_color(svg_path)
    if not bg_color:
        return

    text_blocks = re.findall(
        r'<text[^>]*\sfill\s*=\s*["\']([^"\']+)["\'][^>]*\sfont-size\s*=\s*["\']([^"\']+)["\'][^>]*>',
        content)

    for fill, fs in text_blocks:
        if not (fill.startswith('#') and len(fill) == 7):
            continue
        if fill.upper() == bg_color.upper():
            continue
        try:
            px = float(fs.replace('px', '').strip())
        except ValueError:
            continue
        if px < 14:
            continue
        try:
            contrast = _wcag_contrast(fill, bg_color)
        except Exception:
            continue
        if contrast < 3.0:
            result['warnings'].append(
                f"Text fill {fill} vs bg {bg_color}: "
                f"WCAG contrast {contrast:.1f}:1 (below 4.5:1; "
                f"verify text sits on darker local background like a card)")
        elif contrast < 4.5:
            result['warnings'].append(
                f"Text fill {fill} vs bg {bg_color}: "
                f"WCAG contrast {contrast:.1f}:1 (below 4.5:1 standard)")


def check_narrative_consistency(content: str, svg_path: Path, result: dict) -> None:
    """Check that SVG text content aligns with the page's core_argument
    from detailed_outline.json (narrative restatement mechanism)."""
    project_path = svg_path.parent.parent  # svg_output/ → project root
    outline_path = project_path / "detailed_outline.json"
    if not outline_path.exists():
        return

    try:
        with open(outline_path, 'r', encoding='utf-8') as f:
            outline = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    svg_name = svg_path.stem
    page_match = re.match(r'^(\d+)', svg_name)
    if not page_match:
        return
    page_num = int(page_match.group(1))

    pages = outline if isinstance(outline, list) else outline.get('pages', [])
    if page_num < 1 or page_num > len(pages):
        return
    page_entry = pages[page_num - 1]
    core_argument = page_entry.get('core_argument', '')
    if not core_argument or len(core_argument) < 10:
        return

    text_elements = re.findall(r'>([^<]+)<', content)
    svg_text = ' '.join(t.strip() for t in text_elements if t.strip())

    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'can', 'shall',
        'of', 'in', 'to', 'for', 'with', 'on', 'at', 'from', 'by',
        'and', 'or', 'but', 'not', 'this', 'that', 'these', 'those',
        '的', '是', '在', '了', '和', '与', '对', '为', '将', '把',
        '被', '从', '到', '也', '就', '都', '而', '及', '等',
    }
    arg_words = set(re.findall(r'[一-鿿]+|[a-zA-Z]{3,}', core_argument.lower()))
    arg_words -= stop_words
    if len(arg_words) < 2:
        return

    svg_lower = svg_text.lower()
    matched = sum(1 for w in arg_words if w in svg_lower)
    match_ratio = matched / len(arg_words) if arg_words else 0

    if match_ratio < 0.15:
        result['warnings'].append(
            f"Narrative consistency: SVG text has low overlap ({matched}/{len(arg_words)} "
            f"keywords) with detailed_outline core_argument for P{page_num:02d}. "
            f"Argument: '{core_argument[:80]}...'")


def check_element_spacing(content: str, result: dict) -> None:
    """Warn when text elements are too close together."""
    dims = _viewbox_dimensions(content)
    if dims is None:
        return
    vb_w = dims[0]

    positions = []
    for m in re.finditer(
        r'<(?:text|tspan)\b[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"', content
    ):
        try:
            positions.append((float(m.group(1)), float(m.group(2))))
        except ValueError:
            continue

    if len(positions) < 2:
        return

    global_fs = _extract_global_font_size(content) or 20
    overlap_count = 0

    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            x1, y1 = positions[i]
            x2, y2 = positions[j]
            dy = abs(y1 - y2)

            if dy < global_fs * 0.5:
                dx = abs(x1 - x2)
                if dx < MIN_H_GAP:
                    overlap_count += 1
                    if overlap_count <= 3:
                        result['warnings'].append(
                            f"Spacing: text elements at ({x1:.0f},{y1:.0f}) and "
                            f"({x2:.0f},{y2:.0f}) are only {dx:.0f}px apart "
                            f"(min {MIN_H_GAP}px)")
            elif dy < global_fs * 2:
                min_v_gap = global_fs * MIN_V_GAP_RATIO
                if dy < min_v_gap:
                    overlap_count += 1
                    if overlap_count <= 3:
                        result['warnings'].append(
                            f"Spacing: text elements vertically {dy:.0f}px apart "
                            f"(min {min_v_gap:.0f}px for {global_fs}px font)")

    if overlap_count > 3:
        result['warnings'].append(
            f"Spacing: {overlap_count - 3} more spacing violations (showing first 3)")
    if overlap_count > 0:
        result['info']['spacing_violations'] = overlap_count


def check_vertical_distribution(content: str, result: dict) -> None:
    """Report sparse vertical distribution for human composition review.

    Intentional sparse compositions are valid; this heuristic must never be
    satisfied by adding filler.
    """
    dims = _viewbox_dimensions(content)
    if dims is None:
        return
    vb_h = dims[1]

    y_positions = []
    for m in re.finditer(
        r'<(?:text|tspan|image|rect|circle|ellipse)\b[^>]*'
        r'\b(?:y|cy)="([^"]+)"', content
    ):
        try:
            y_positions.append(float(m.group(1)))
        except ValueError:
            continue

    if len(y_positions) < 2:
        return

    zone_h = vb_h / 3
    zone_counts = [0, 0, 0]
    for y in y_positions:
        zone_idx = min(int(y / zone_h), 2)
        zone_counts[zone_idx] += 1

    total = sum(zone_counts)
    if total == 0:
        return

    bottom_threshold = vb_h * 0.6
    has_bottom_content = any(y >= bottom_threshold for y in y_positions)
    if not has_bottom_content:
        result['warnings'].append(
            f"Review only: vertical distribution leaves the bottom 40% empty "
            f"(all {total} elements above y={bottom_threshold:.0f}). Verify the "
            "composition is intentional; do not add filler to occupy the canvas.")

    for idx, (label, count) in enumerate(
        zip(["top", "middle", "bottom"], zone_counts)
    ):
        ratio = count / total
        if ratio < 0.15 and count == 0:
            result['warnings'].append(
                f"Review only: vertical distribution leaves the {label} zone "
                f"(y={idx*zone_h:.0f}-{(idx+1)*zone_h:.0f}) empty. Verify the "
                "composition is intentional; do not add filler to occupy the zone.")


def check_emoji_usage(content: str, result: dict) -> None:
    """Check for emoji Unicode characters in SVG text content (§4.0 ban)."""
    for m in re.finditer(r'<text[^>]*>([^<]*(?:<tspan[^>]*>[^<]*</tspan>[^<]*)*)</text>',
                         content, re.DOTALL):
        text_block = m.group(0)
        emojis_found = _EMOJI_RE.findall(text_block)
        if emojis_found:
            sample = ''.join(emojis_found[:5])
            result['errors'].append(
                f"Emoji character(s) detected in SVG text: {sample}. "
                f"Use icons from the project icon library (data-icon placeholder) instead.")


def check_element_overlap(content: str, result: dict) -> None:
    """Check for overlapping content elements (>20px overlap in both axes)."""
    elements = []
    for m in re.finditer(
        r'<(rect|image|text|g)\b[^>]*'
        r'\bx="([^"]+)"[^>]*\by="([^"]+)"[^>]*'
        r'\bwidth="([^"]+)"[^>]*\bheight="([^"]+)"',
        content,
    ):
        try:
            x = float(m.group(2))
            y = float(m.group(3))
            w = float(m.group(4).rstrip('px'))
            h = float(m.group(5).rstrip('px'))
            elements.append((m.group(1), x, y, w, h))
        except ValueError:
            continue

    overlap_threshold = 20
    overlap_count = 0
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            _, x1, y1, w1, h1 = elements[i]
            _, x2, y2, w2, h2 = elements[j]
            ox = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
            oy = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
            if ox > overlap_threshold and oy > overlap_threshold:
                overlap_count += 1
    if overlap_count > 0:
        result['warnings'].append(
            f"Element overlap: {overlap_count} pair(s) of content elements "
            f"overlap by >{overlap_threshold}px in both axes")


def check_image_text_spacing(content: str, result: dict) -> None:
    """Check the minimum image-text gap and review unusually large gaps."""
    images = []
    for m in re.finditer(
        r'<image\b[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"[^>]*'
        r'\bwidth="([^"]+)"[^>]*\bheight="([^"]+)"', content
    ):
        try:
            images.append((
                float(m.group(1)), float(m.group(2)),
                float(m.group(3).rstrip('px')), float(m.group(4).rstrip('px'))
            ))
        except ValueError:
            continue

    texts = []
    for m in re.finditer(r'<text\b[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"', content):
        try:
            texts.append((float(m.group(1)), float(m.group(2))))
        except ValueError:
            continue

    if not images or not texts:
        return

    for ix, iy, iw, ih in images:
        min_dist = float('inf')
        for tx, ty in texts:
            dx = max(0, max(ix - tx, tx - (ix + iw)))
            dy = max(0, max(iy - ty, ty - (iy + ih)))
            dist = (dx ** 2 + dy ** 2) ** 0.5
            min_dist = min(min_dist, dist)
        if min_dist < 20:
            result['warnings'].append(
                f"Image-text spacing: image at ({ix:.0f},{iy:.0f}) has text "
                f"only {min_dist:.0f}px away (min 20px)")
        elif min_dist > 80 and len(texts) > 1:
            result['warnings'].append(
                f"Review only: image-text spacing places the image at "
                f"({ix:.0f},{iy:.0f}) {min_dist:.0f}px from nearest text. Verify "
                "the gap supports the composition; do not compress it solely to "
                "satisfy this heuristic.")


def check_whitespace_balance(content: str, result: dict) -> None:
    """Report strongly one-sided layouts for human composition review."""
    dims = _viewbox_dimensions(content)
    if dims is None:
        return
    vb_w = dims[0]

    midpoint = vb_w / 2
    left_count = 0
    right_count = 0
    for m in re.finditer(r'\bx="([^"]+)"', content):
        try:
            x = float(m.group(1))
            if x < midpoint:
                left_count += 1
            else:
                right_count += 1
        except ValueError:
            continue

    total = left_count + right_count
    if total < 4:
        return
    left_ratio = left_count / total
    if left_ratio > 0.80:
        result['warnings'].append(
            f"Review only: whitespace balance places {left_ratio:.0%} of elements "
            "on the left. Verify the one-sided composition is intentional; do not "
            "add filler merely to balance the canvas.")
    elif left_ratio < 0.20:
        result['warnings'].append(
            f"Review only: whitespace balance places {1-left_ratio:.0%} of "
            "elements on the right. Verify the one-sided composition is intentional; "
            "do not add filler merely to balance the canvas.")


def run_extensions(content: str, svg_path: Path, result: dict, *,
                    template_mode: bool = False) -> None:
    """Run all DeepPPT2-specific review checks into an existing result dict.

    Mirrors the pre-refactor invocation order. Template-mode projects skip the
    project-contract checks (spec_lock contrast, narrative outline) exactly as
    the legacy checker did.
    """
    check_dimensions(content, result)
    check_layout_bounds(content, result)
    if not template_mode:
        check_contrast(content, svg_path, result)
        check_narrative_consistency(content, svg_path, result)
    check_element_spacing(content, result)
    check_vertical_distribution(content, result)
    check_emoji_usage(content, result)
    check_element_overlap(content, result)
    check_image_text_spacing(content, result)
    check_whitespace_balance(content, result)


def classify_issue(msg: str) -> str:
    """Classify an error/warning message into must_fix/should_fix/accepted_risks."""
    msg_lower = msg.lower()
    if msg_lower.startswith('review only:'):
        return 'accepted_risks'
    for kw in _MUST_FIX_KEYWORDS:
        if kw.lower() in msg_lower:
            return 'must_fix'
    for kw in _SHOULD_FIX_KEYWORDS:
        if kw.lower() in msg_lower:
            return 'should_fix'
    return 'accepted_risks'


def export_integrated_review(checker, output_file: str) -> None:
    """Export structured three-tier review JSON (must_fix/should_fix/accepted_risks)."""
    from datetime import datetime, timezone

    pages = {}
    total_must = 0
    total_should = 0
    total_accepted = 0

    for result in checker.results:
        fname = result.get('file', 'unknown')
        must_fix = []
        should_fix = []
        accepted_risks = []

        for msg in list(result.get('errors', [])) + list(result.get('warnings', [])):
            tier = classify_issue(msg)
            if tier == 'must_fix':
                must_fix.append(msg)
            elif tier == 'should_fix':
                should_fix.append(msg)
            else:
                accepted_risks.append(msg)

        if must_fix:
            decision = 'needs_fix'
        elif should_fix:
            decision = 'acceptable_with_risks'
        else:
            decision = 'ready'

        pages[fname] = {
            'decision': decision,
            'must_fix': must_fix,
            'should_fix': should_fix,
            'accepted_risks': accepted_risks,
        }
        total_must += len(must_fix)
        total_should += len(should_fix)
        total_accepted += len(accepted_risks)

    if total_must > 0:
        gate = 'BLOCKED'
    elif total_should > 0:
        gate = 'PASS_WITH_WARNINGS'
    else:
        gate = 'CLEAN'

    report = {
        'reviewed_at': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        'method': 'svg_quality_checker --integrated-review',
        'pages': pages,
        'summary': {
            'total_must_fix': total_must,
            'total_should_fix': total_should,
            'total_accepted': total_accepted,
            'gate_status': gate,
        },
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n[INTEGRATED-REVIEW] Structured review exported: {output_file} (gate: {gate})")
