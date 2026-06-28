#!/usr/bin/env python3
"""
PPT Master - Research Output Sync Tool

Syncs deep-research artifacts from <project>/_research/ into the main PPT
pipeline directories.

Usage:
    python3 scripts/research/sync_research_outputs.py <project_path>
    python3 scripts/research/sync_research_outputs.py <project_path> --strict

Examples:
    python3 skills/ppt-master/scripts/research/sync_research_outputs.py projects/my_deck_ppt169_20260628

Dependencies:
    None (only uses standard library)
"""

import argparse
import shutil
import sys
from pathlib import Path


FILE_MAPPINGS = [
    ("_research/step6_narrative/research_report.md", "sources/research_report.md"),
    ("_research/step5_analysis/research_analysis.json", "analysis/research_analysis.json"),
    ("_research/step7_visual/visual_strategy.json", "analysis/visual_strategy.json"),
]

DIR_MAPPINGS = [
    ("_research/step7_visual/ref", "images/ref"),
    ("_research/step3_search/images", "images/web_assets"),
]

REQUIRED_DIRS = [
    "sources",
    "analysis",
    "images/ref",
    "images/web_assets",
]


def _copy_file(src: Path, dst: Path) -> str:
    """Copy one file, creating the destination parent."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst)


def _copy_dir_contents(src: Path, dst: Path) -> int:
    """Copy all files under src into dst, preserving relative paths."""
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        count += 1
    return count


def sync_research_outputs(project_path: Path, *, strict: bool = False) -> tuple[int, list[str]]:
    """Sync research outputs and return copied count plus warnings."""
    project = project_path.resolve()
    warnings: list[str] = []
    copied = 0

    if not project.exists() or not project.is_dir():
        raise FileNotFoundError(f"project directory not found: {project}")

    for rel in REQUIRED_DIRS:
        (project / rel).mkdir(parents=True, exist_ok=True)

    for src_rel, dst_rel in FILE_MAPPINGS:
        src = project / src_rel
        dst = project / dst_rel
        if not src.exists():
            warnings.append(f"missing file: {src_rel}")
            continue
        _copy_file(src, dst)
        copied += 1
        print(f"[file] {src_rel} -> {dst_rel}")

    for src_rel, dst_rel in DIR_MAPPINGS:
        src = project / src_rel
        dst = project / dst_rel
        if not src.exists():
            warnings.append(f"missing directory: {src_rel}")
            continue
        count = _copy_dir_contents(src, dst)
        copied += count
        print(f"[dir]  {src_rel} -> {dst_rel} ({count} files)")

    if strict and warnings:
        return copied, warnings
    return copied, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync deep-research outputs into main PPT pipeline directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory containing _research/")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any expected research artifact is missing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        copied, warnings = sync_research_outputs(Path(args.project_path), strict=args.strict)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    print(f"Research sync complete: {copied} files copied")
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
