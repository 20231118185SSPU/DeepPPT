#!/usr/bin/env python3
"""PPT Master - PowerPoint Real Render Export

把导出后的 PPTX 用本机 PowerPoint（COM）逐页渲染为 PNG，
作为版式复核的"最终真相"——Chromium SVG 预览与 PowerPoint 的字体度量
存在差异（微软雅黑行高、字宽 headroom），文字遮挡/贴边问题往往只有
在 PowerPoint 真实渲染下才完全暴露。

Usage:
    python3 scripts/pptx_render_export.py --pptx <file.pptx> -o <out_dir>
    python3 scripts/pptx_render_export.py --pptx <file.pptx> -o <out_dir> --pages 1,5,7
    python3 scripts/pptx_render_export.py --pptx <file.pptx> -o <out_dir> --width 1920 --height 1080

Examples:
    python3 scripts/pptx_render_export.py \\
        --pptx projects/demo/exports/demo.pptx -o projects/demo/quality/pptx_render

Dependencies:
    Windows + Microsoft PowerPoint（Office 2016+）；PowerShell。
    非 Windows / 无 Office 时优雅退出（exit 2），不影响流水线。

输出:
    <out_dir>/p01_pptx.png … pNN_pptx.png；<out_dir>/render_summary.json
"""

import argparse
import base64
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

_EXPORT_SCRIPT = r"""
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ppt = $null
$pres = $null
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open(
        "{pptx}", $true, $false, $false
    )
    $outDir = "{out_dir}"
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $pages = @({pages})
    $width = {width}
    $height = {height}
    if ($pages.Count -eq 0) {
        for ($i = 1; $i -le $pres.Slides.Count; $i++) { $pages += $i }
    }
    foreach ($idx in $pages) {
        if ($idx -lt 1 -or $idx -gt $pres.Slides.Count) {
            throw "slide index $idx out of range 1..$($pres.Slides.Count)"
        }
        $name = "p{0:D2}_pptx.png" -f $idx
        $pres.Slides.Item($idx).Export(
            (Join-Path $outDir $name), "PNG", $width, $height
        )
    }
    [Console]::Out.WriteLine(
        "exported {0} slide(s) x {1}x{2}", $pages.Count, $width, $height
    )
} finally {
    if ($pres) { $pres.Close() }
    if ($ppt) { $ppt.Quit() }
}
"""


def _find_powershell() -> Optional[str]:
    return shutil.which("powershell.exe") or shutil.which("powershell")


def _run_powershell(script: str, timeout: int) -> int:
    executable = _find_powershell()
    if executable is None:
        print(
            "PowerPoint render export requires Windows PowerShell. "
            "Install or restore powershell.exe, then retry.",
            file=sys.stderr,
        )
        return 2
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        completed = subprocess.run(
            [
                executable,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-STA",
                "-OutputFormat",
                "Text",
                "-EncodedCommand",
                encoded,
            ],
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print(
            "PowerPoint automation exceeded the command timeout. "
            "Close any PowerPoint dialog and retry.",
            file=sys.stderr,
        )
        return 2
    return 0 if completed.returncode == 0 else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pptx_render_export.py",
        description=(
            "用本机 PowerPoint 渲染导出 PPTX 每页为 PNG（版式复核基准）。"
            "仅 Windows + Office 可用；不可用时退出码 2。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--pptx", required=True, help="目标 PPTX 文件路径")
    parser.add_argument("-o", "--out-dir", required=True, help="PNG 输出目录")
    parser.add_argument("--width", type=int, default=1280, help="导出宽度（默认 1280）")
    parser.add_argument("--height", type=int, default=720, help="导出高度（默认 720）")
    parser.add_argument(
        "--pages", help="逗号分隔的页号（默认全部，如 '1,5,7'）"
    )
    parser.add_argument("--timeout", type=int, default=300, help="PowerShell 超时秒数")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    pptx = Path(args.pptx)
    if not pptx.is_file():
        print(f"[ERROR] pptx not found: {pptx}", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages: list[int] = []
    if args.pages:
        for token in args.pages.split(","):
            token = token.strip()
            if not token.isdigit():
                print(f"[ERROR] invalid page token: {token!r}", file=sys.stderr)
                return 2
            pages.append(int(token))

    script = (
        _EXPORT_SCRIPT
        .replace("{pptx}", str(pptx.resolve()))
        .replace("{out_dir}", str(out_dir.resolve()))
        .replace("{pages}", ",".join(str(p) for p in pages))
        .replace("{width}", str(args.width))
        .replace("{height}", str(args.height))
    )
    rc = _run_powershell(script, timeout=args.timeout)
    if rc != 0:
        return rc

    exported = sorted(out_dir.glob("p*_pptx.png"))
    summary: dict[str, Any] = {
        "schema": "ppt_master.pptx_render_export.v1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "pptx": str(pptx),
        "out_dir": str(out_dir),
        "width": args.width,
        "height": args.height,
        "pages_exported": [int(p.stem.lstrip("p").split("_")[0]) for p in exported],
        "files": [
            {"name": p.name, "bytes": p.stat().st_size} for p in exported
        ],
    }
    (out_dir / "render_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[SUMMARY] {len(exported)} slide(s) rendered to {out_dir}")
    print(f"[REPORT] {out_dir / 'render_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
