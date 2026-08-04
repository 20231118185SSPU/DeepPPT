#!/usr/bin/env python3
"""PPT Master - SVG Geometry Audit Tool

确定性字形盒级排版审计（advisory，不参与现有 gate 的通过/阻塞判定）。

检查项：
  1. text-text 字形交叠（跨元素；字形盒 = baseline - 0.78*fs .. baseline + 0.22*fs）
  2. 同一 <text> 内 tspan 行距（dy 为累积语义，相对上一行而非 text 根）
  3. 底部页脚区贴边：页脚（baseline >= 680）与上方文字的字形间隙 < 6px
  4. 后绘制填充 <rect> 遮挡先绘制文字（按文档顺序的 z-order）
  5. 文字字形底超出其所在 <rect> 底
  6. 后绘制 <rect> 与先绘制 <rect> 部分相交（info）
  7. 内容型 <image> 短边过小（< 150px，info）

宽度度量复用 svg_to_pptx 的权威字符宽度估计（estimate_text_width），
避免与导出器口径不一致导致误报/漏报。

Usage:
    python3 scripts/svg_geometry_audit.py <project_path>
    python3 scripts/svg_geometry_audit.py <project_path> --strict
    python3 scripts/svg_geometry_audit.py <project_path> --json-out <file>

Examples:
    python3 scripts/svg_geometry_audit.py projects/gan_hemt_trap_test_ppt169_20260804
    python3 scripts/svg_geometry_audit.py projects/demo --strict

Dependencies:
    stdlib only (xml.etree)；复用 svg_to_pptx.drawingml.utils.estimate_text_width。

限制：
    translate() 已展开（嵌套累积）；rotate/scale/matrix 等其它 transform 未展开；
    text 内嵌套 tspan 仅解析一层；字体度量是估计值，以 PowerPoint/Chromium 真实渲染为最终裁决。
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

from svg_to_pptx.drawingml.utils import estimate_text_width  # noqa: E402

# ── 阈值常量 ──────────────────────────────────────────────────────────
ASCENT_RATIO = 0.78      # baseline 之上的字形高度比例
DESCENT_RATIO = 0.22     # baseline 之下的字形深度比例
OVERLAP_WARN_PX = 2.0    # 字形交叠 > 2px → warning
OVERLAP_ERROR_PX = 6.0   # 字形交叠 > 6px → error
LINE_SPACING_MIN_RATIO = 1.0   # 同一 text 内行距 < 1.0*fs → warning
FOOTER_Y = 680.0         # baseline >= 680 视为页脚行
FOOTER_GAP_WARN_PX = 6.0 # 页脚与上方文字字形间隙 < 6px → warning
FOOTER_GAP_ERROR_PX = 2.0  # 间隙 < 2px（含负值）→ error
TEXT_BEYOND_RECT_TOL = 1.0   # 字形底超出 rect 底 > 1px → warning
IMAGE_MIN_SHORT_SIDE = 150.0 # 内容型图片短边下限（info）
DEFAULT_FONT_SIZE = 15.0

SVG_NS = "http://www.w3.org/2000/svg"
SVG_NSMAP = {"svg": SVG_NS}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


@dataclass
class TextLine:
    x: float
    y: float
    size: float
    weight: str
    text: str
    anchor: str = "start"
    doc_order: int = 0
    text_id: int = 0   # 所属 <text> 元素的遍历序号，用于行距检查
    line_no: int = 0   # 该 text 内的行号（0 起）


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float
    fill: str
    doc_order: int = 0


@dataclass
class ImageInfo:
    x: float
    y: float
    w: float
    h: float
    doc_order: int = 0


@dataclass
class AuditIssue:
    severity: str   # error / warning / info
    check: str
    message: str
    page: str = ""


def _num(attrs: dict[str, str], key: str) -> Optional[float]:
    raw = attrs.get(key)
    if raw is None:
        return None
    try:
        return float(raw.rstrip("px"))
    except ValueError:
        return None


def _is_hidden(elem: ET.Element) -> bool:
    vis = elem.attrib.get("visibility", "")
    disp = elem.attrib.get("display", "")
    return vis == "hidden" or disp == "none"


_TRANSLATE_RE = re.compile(r"translate\(\s*([-+\d.]+)\s*[, ]\s*([-+\d.]+)\s*\)")


class _Collector:
    """按文档顺序收集 text 行 / rect / image，携带祖先后裔上下文。"""

    def __init__(self) -> None:
        self.lines: list[TextLine] = []
        self.rects: list[Rect] = []
        self.images: list[ImageInfo] = []
        self._order = 0
        self._text_seq = 0

    def _next(self) -> int:
        self._order += 1
        return self._order

    def walk(self, root: ET.Element) -> None:
        self._walk(root, size=None, weight="400", hidden=False, tx=0.0, ty=0.0)

    def _walk(
        self,
        elem: ET.Element,
        size: Optional[float],
        weight: str,
        hidden: bool,
        tx: float,
        ty: float,
    ) -> None:
        tag = _local(elem.tag)
        if hidden or _is_hidden(elem):
            return
        attrs = elem.attrib
        # Accumulate translate() offsets — real executor output groups schema
        # mockups under <g transform="translate(x,y)">, so local rect/text
        # coordinates must be lifted to page space before overlap checks.
        m = _TRANSLATE_RE.search(attrs.get("transform", ""))
        if m:
            tx += float(m.group(1))
            ty += float(m.group(2))
        if tag == "text":
            self._collect_text(elem, size, weight, tx, ty)
            return
        cur_size = _num(attrs, "font-size") or size
        cur_weight = attrs.get("font-weight", weight)
        if tag == "rect":
            x, y = _num(attrs, "x"), _num(attrs, "y")
            w, h = _num(attrs, "width"), _num(attrs, "height")
            fill = attrs.get("fill", "none")
            if x is not None and y is not None and w is not None and h is not None:
                self.rects.append(Rect(x + tx, y + ty, w, h, fill, self._next()))
        elif tag == "image":
            x, y = _num(attrs, "x") or 0.0, _num(attrs, "y") or 0.0
            w, h = _num(attrs, "width"), _num(attrs, "height")
            if w is not None and h is not None:
                self.images.append(ImageInfo(x + tx, y + ty, w, h, self._next()))
        for child in elem:
            self._walk(child, cur_size, cur_weight, hidden, tx, ty)

    def _collect_text(
        self,
        elem: ET.Element,
        size: Optional[float],
        weight: str,
        tx: float,
        ty: float,
    ) -> None:
        attrs = elem.attrib
        base_x = (_num(attrs, "x") or 0.0) + tx
        base_y = (_num(attrs, "y") or 0.0) + ty
        fs = _num(attrs, "font-size") or size or DEFAULT_FONT_SIZE
        wgt = attrs.get("font-weight", weight)
        anchor = attrs.get("text-anchor", "start")
        self._text_seq += 1
        tid = self._text_seq

        # text 元素自身文本（tspan 之外的首段）
        own = (elem.text or "").strip()
        if own:
            self.lines.append(
                TextLine(base_x, base_y, fs, wgt, own, anchor, self._next(), tid, 0)
            )
        # tspan 行：dy 为累积语义（相对上一行 baseline）
        cur_y = base_y
        cur_x = base_x
        line_no = 1 if own else 0
        for tspan in elem.findall(f"{{{SVG_NS}}}tspan"):
            tspan_x = _num(tspan.attrib, "x")
            dy = _num(tspan.attrib, "dy")
            txt = (tspan.text or "").strip()
            if not txt:
                continue
            if dy is not None:
                cur_y += dy
            if tspan_x is not None:
                cur_x = tspan_x + tx
            tsize = _num(tspan.attrib, "font-size") or fs
            twgt = tspan.attrib.get("font-weight", wgt)
            self.lines.append(
                TextLine(cur_x, cur_y, tsize, twgt, txt, anchor, self._next(), tid, line_no)
            )
            line_no += 1


def _line_box(line: TextLine) -> tuple[float, float, float, float]:
    """返回 (left, top, right, bottom) 字形盒（x 为估算宽度）。"""
    width = estimate_text_width(line.text, line.size, line.weight)
    if line.anchor == "middle":
        left = line.x - width / 2
    elif line.anchor == "end":
        left = line.x - width
    else:
        left = line.x
    top = line.y - ASCENT_RATIO * line.size
    bottom = line.y + DESCENT_RATIO * line.size
    return left, top, left + width, bottom


def _overlap_x(a: tuple[float, float], b: tuple[float, float]) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0]))


def _overlap_y(a: tuple[float, float], b: tuple[float, float]) -> float:
    return max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


# ── 检查项 ────────────────────────────────────────────────────────────

def check_text_overlap(lines: list[TextLine]) -> list[str]:
    """跨 <text> 元素的字形交叠；同一 text 的行间交叠跳过（行距检查另行处理）。"""
    msgs: list[str] = []
    boxes = [_line_box(l) for l in lines]
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            if lines[i].text_id == lines[j].text_id:
                continue
            ox = _overlap_x(boxes[i], boxes[j])
            oy = _overlap_y(boxes[i], boxes[j])
            if ox <= 0 or oy <= 0:
                continue
            if oy > OVERLAP_ERROR_PX:
                msgs.append(
                    f"ERROR text-text overlap {oy:.1f}px: '{lines[i].text[:16]}' "
                    f"× '{lines[j].text[:16]}'"
                )
            elif oy > OVERLAP_WARN_PX:
                msgs.append(
                    f"WARN text-text overlap {oy:.1f}px: '{lines[i].text[:16]}' "
                    f"× '{lines[j].text[:16]}'"
                )
    return msgs


def check_line_spacing(lines: list[TextLine]) -> list[str]:
    """同一 <text> 内相邻行 baseline 差 < 1.0*fs → warning（行距过窄）。"""
    msgs: list[str] = []
    by_text: dict[int, list[TextLine]] = {}
    for line in lines:
        by_text.setdefault(line.text_id, []).append(line)
    for tid, group in by_text.items():
        group.sort(key=lambda l: (l.line_no, l.y))
        for k in range(1, len(group)):
            prev, cur = group[k - 1], group[k]
            gap = cur.y - prev.y
            if gap <= 0:
                # Same baseline = inline <tspan> continuation (no dy), not a
                # line break — Golden Set showed 58/58 warnings were inline
                # runs like "$297<tspan>B</tspan>" flagged as 0.0px spacing.
                continue
            if gap < LINE_SPACING_MIN_RATIO * max(prev.size, cur.size):
                msgs.append(
                    f"WARN tight line spacing {gap:.1f}px "
                    f"(< {LINE_SPACING_MIN_RATIO:.1f}×{max(prev.size, cur.size):.0f}px): "
                    f"'{prev.text[:14]}' → '{cur.text[:14]}'"
                )
    return msgs


def check_footer_gap(lines: list[TextLine]) -> list[str]:
    """页脚行（baseline>=680）与上方水平重叠文字的字形间隙。"""
    msgs: list[str] = []
    footers = [l for l in lines if l.y >= FOOTER_Y]
    aboves = [l for l in lines if l.y < FOOTER_Y]
    if not footers or not aboves:
        return msgs
    for f in footers:
        fbox = _line_box(f)
        best_gap: Optional[float] = None
        best_above: Optional[TextLine] = None
        for a in aboves:
            abox = _line_box(a)
            if _overlap_x(fbox, abox) <= 0:
                continue
            gap = (f.y - ASCENT_RATIO * f.size) - (a.y + DESCENT_RATIO * a.size)
            if best_gap is None or gap < best_gap:
                best_gap, best_above = gap, a
        if best_above is None or best_gap is None:
            continue
        if best_gap < FOOTER_GAP_ERROR_PX:
            msgs.append(
                f"ERROR footer glyph gap {best_gap:.1f}px (< {FOOTER_GAP_ERROR_PX:.0f}): "
                f"footer '{f.text[:14]}' touches '{best_above.text[:14]}'"
            )
        elif best_gap < FOOTER_GAP_WARN_PX:
            msgs.append(
                f"WARN footer glyph gap {best_gap:.1f}px (< {FOOTER_GAP_WARN_PX:.0f}): "
                f"footer '{f.text[:14]}' tight vs '{best_above.text[:14]}'"
            )
    return msgs


def _rect_box(r: Rect) -> tuple[float, float, float, float]:
    return r.x, r.y, r.x + r.w, r.y + r.h


def _fill_opaque(fill: str) -> bool:
    f = fill.strip().lower()
    if f in ("none", "transparent"):
        return False
    if f.startswith("url("):  # 渐变/图案引用按不透明处理
        return True
    if f.startswith("#") and len(f) == 9:  # #RRGGBBAA
        return f[7:9].lower() != "00"
    return True


def check_rect_over_text(lines: list[TextLine], rects: list[Rect]) -> list[str]:
    """后绘制填充 rect 与先绘制文字字形盒相交 → 遮挡。"""
    msgs: list[str] = []
    for r in rects:
        if not _fill_opaque(r.fill):
            continue
        rbox = _rect_box(r)
        for line in lines:
            if line.doc_order > r.doc_order:
                continue  # 文字在 rect 之后绘制 → 文字在色块之上，正常
            lbox = _line_box(line)
            if _overlap_x(rbox, lbox) <= 0 or _overlap_y(rbox, lbox) <= 0:
                continue
            msgs.append(
                f"WARN rect drawn after text covers glyph: '{line.text[:16]}' "
                f"at y={line.y:.0f} vs rect y={r.y:.0f} h={r.h:.0f}"
            )
    return msgs


def check_text_beyond_rect(lines: list[TextLine], rects: list[Rect]) -> list[str]:
    """文字（字形底）超出其所属 rect 底。"""
    msgs: list[str] = []
    for r in rects:
        if not _fill_opaque(r.fill):
            continue
        rbox = _rect_box(r)
        for line in lines:
            lbox = _line_box(line)
            # 水平在内 + baseline 在 rect 垂直范围内
            if lbox[0] < rbox[0] - 1 or lbox[2] > rbox[2] + 1:
                continue
            if not (rbox[1] - 1 <= line.y <= rbox[3] + 1):
                continue
            overflow = lbox[3] - rbox[3]
            if overflow > TEXT_BEYOND_RECT_TOL:
                msgs.append(
                    f"WARN text glyph bottom {lbox[3]:.1f} exceeds rect bottom "
                    f"{rbox[3]:.1f} by {overflow:.1f}px: '{line.text[:16]}'"
                )
    return msgs


def check_rect_overlap(rects: list[Rect]) -> list[str]:
    """后绘制 rect 与先绘制 rect 部分相交（非完全包含）→ info。"""
    msgs: list[str] = []
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            if a.doc_order > b.doc_order:
                a, b = b, a
            abox, bbox = _rect_box(a), _rect_box(b)
            ox = _overlap_x(abox, bbox)
            oy = _overlap_y(abox, bbox)
            if ox <= 0 or oy <= 0:
                continue
            # 任一方向完全包含（嵌套容器/背景叠图）不算冲突
            a_in_b = (
                abox[0] >= bbox[0] and abox[1] >= bbox[1]
                and abox[2] <= bbox[2] and abox[3] <= bbox[3]
            )
            b_in_a = (
                bbox[0] >= abox[0] and bbox[1] >= abox[1]
                and bbox[2] <= abox[2] and bbox[3] <= abox[3]
            )
            if not (a_in_b or b_in_a):
                msgs.append(
                    f"INFO rect overlap: rect({a.x:.0f},{a.y:.0f},{a.w:.0f}×{a.h:.0f}) "
                    f"× rect({b.x:.0f},{b.y:.0f},{b.w:.0f}×{b.h:.0f}) "
                    f"intersect {ox:.0f}×{oy:.0f}"
                )
    return msgs


def check_image_size(images: list[ImageInfo]) -> list[str]:
    msgs: list[str] = []
    for img in images:
        short = min(img.w, img.h)
        if short < IMAGE_MIN_SHORT_SIDE:
            msgs.append(
                f"INFO image short side {short:.0f}px < {IMAGE_MIN_SHORT_SIDE:.0f}px "
                f"at ({img.x:.0f},{img.y:.0f}) — verify legibility at export scale"
            )
    return msgs


# ── 页面与报告 ────────────────────────────────────────────────────────

def audit_svg(path: Path) -> list[AuditIssue]:
    tree = ET.parse(str(path))
    root = tree.getroot()
    collector = _Collector()
    collector.walk(root)

    issues: list[AuditIssue] = []
    for check, msgs in (
        ("text-overlap", check_text_overlap(collector.lines)),
        ("line-spacing", check_line_spacing(collector.lines)),
        ("footer-gap", check_footer_gap(collector.lines)),
        ("rect-over-text", check_rect_over_text(collector.lines, collector.rects)),
        ("text-beyond-rect", check_text_beyond_rect(collector.lines, collector.rects)),
        ("rect-overlap", check_rect_overlap(collector.rects)),
        ("image-size", check_image_size(collector.images)),
    ):
        for msg in msgs:
            severity = msg.split(" ", 1)[0].lower()
            if severity not in ("error", "warn", "info"):
                severity = "warning"
            if severity == "warn":
                severity = "warning"
            issues.append(AuditIssue(severity, check, msg))
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="svg_geometry_audit.py",
        description=(
            "SVG 字形盒级排版审计（advisory）：文字交叠/行距/页脚贴边/"
            "rect 遮挡/越界/图片尺寸。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="PPT 项目目录（含 svg_output/）")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="存在 error 级问题时 exit 1（默认恒 exit 0，advisory）",
    )
    parser.add_argument(
        "--json-out",
        help="JSON 报告输出路径（默认 <project>/quality/geometry_audit.json）",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    project = Path(args.project_path)
    svg_dir = project / "svg_output"
    if not svg_dir.is_dir():
        print(f"[ERROR] no svg_output directory at {svg_dir}", file=sys.stderr)
        return 2

    pages: dict[str, list[dict[str, str]]] = {}
    counts = {"error": 0, "warning": 0, "info": 0}
    for svg_path in sorted(svg_dir.glob("*.svg")):
        issues = audit_svg(svg_path)
        page_issues: list[dict[str, str]] = []
        for issue in issues:
            counts[issue.severity] += 1
            page_issues.append(
                {"severity": issue.severity, "check": issue.check, "message": issue.message}
            )
            print(f"[{issue.severity.upper():7s}] {svg_path.name}: {issue.message}")
        pages[svg_path.name] = page_issues

    report: dict[str, Any] = {
        "schema": "ppt_master.svg_geometry_audit.v1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "project": str(project),
        "svg_dir": str(svg_dir),
        "strict": args.strict,
        "pages": pages,
        "summary": {
            "pages": len(pages),
            "errors": counts["error"],
            "warnings": counts["warning"],
            "infos": counts["info"],
        },
    }
    out = Path(args.json_out) if args.json_out else project / "quality" / "geometry_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"\n[SUMMARY] {len(pages)} pages, {counts['error']} errors, "
        f"{counts['warning']} warnings, {counts['info']} infos"
    )
    print(f"[REPORT] {out}")
    if args.strict and counts["error"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
