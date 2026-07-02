#!/usr/bin/env python3
"""
PPT Master - Icon Sync

Copy chosen library icons into a project's own `icons/` folder at the moment they
are selected. Run it with the icon names you are picking; each is copied from the
global library into `<project>/icons/<lib>/`. Any name the library does not have
is reported on the spot and the command exits non-zero — so you re-pick a valid
icon then, not at export time. Over-copying candidates is fine: finalize only
embeds the icons actually referenced by `<use data-icon>`, the rest sit unused.

Custom icons you place in `<project>/icons/<lib>/` yourself are honored too — a
name already present in the project is treated as satisfied, not missing.

Usage:
    python3 scripts/icon_sync.py <project_path> <lib/name> [<lib/name> ...]
    python3 scripts/icon_sync.py search <query> [--library lib] [--limit N]

Examples:
    python3 scripts/icon_sync.py projects/deck chunk-filled/home tabler-outline/chart
    python3 scripts/icon_sync.py projects/deck simple-icons/github
    python3 scripts/icon_sync.py search chart --library tabler-outline --limit 10

Dependencies:
    None (standard library only).

See references/executor-base.md §4 and templates/icons/README.md.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

_LIB_ALIASES = {"chunk": "chunk-filled"}
_GLOBAL_ICONS_DIR = Path(__file__).resolve().parent.parent / "templates" / "icons"
_SVG_SCAN_LINES = 12


def _split_name(icon_name: str) -> tuple[str, str]:
    """`lib/name` -> (lib, name), applying the chunk→chunk-filled alias."""
    if "/" not in icon_name:
        # legacy un-prefixed names live in chunk-filled/
        return "chunk-filled", icon_name
    lib, name = icon_name.split("/", 1)
    return _LIB_ALIASES.get(lib, lib), name


def sync_icons(
    project_path: Path,
    icon_names: list[str],
    global_dir: Path = _GLOBAL_ICONS_DIR,
) -> tuple[list[str], list[str]]:
    """Copy each `lib/name` from the global library into `<project>/icons/`.

    Returns (copied, missing). A name already present in the project (e.g. a
    custom icon) counts as satisfied, not missing.
    """
    project_icons = project_path / "icons"
    copied: list[str] = []
    missing: list[str] = []

    for raw in icon_names:
        lib, name = _split_name(raw)
        src = global_dir / lib / f"{name}.svg"
        dst = project_icons / lib / f"{name}.svg"
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(f"{lib}/{name}")
        elif dst.is_file():
            copied.append(f"{lib}/{name} (already in project)")
        else:
            missing.append(f"{lib}/{name}")

    return copied, missing


def _available_libraries(global_dir: Path = _GLOBAL_ICONS_DIR) -> list[str]:
    """Return available icon library directory names."""
    if not global_dir.is_dir():
        return []
    return sorted(path.name for path in global_dir.iterdir() if path.is_dir())


def _read_svg_head(path: Path, line_limit: int = _SVG_SCAN_LINES) -> str:
    """Read the first few lines of an SVG for tag/comment search."""
    lines: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for _ in range(line_limit):
                line = handle.readline()
                if not line:
                    break
                lines.append(line)
    except UnicodeDecodeError:
        return ""
    except OSError:
        return ""
    return "".join(lines).lower()


def search_icons(
    query: str,
    *,
    library: str | None = None,
    limit: int = 20,
    global_dir: Path = _GLOBAL_ICONS_DIR,
) -> list[str]:
    """Search icon filenames and SVG header tags, returning `lib/name` candidates."""
    query_words = [word for word in query.lower().replace("_", "-").split("-") if word]
    if not query_words:
        return []

    library_names = [_LIB_ALIASES.get(library, library)] if library else _available_libraries(global_dir)
    results: list[tuple[int, str]] = []

    for lib in library_names:
        if not lib:
            continue
        lib_dir = global_dir / lib
        if not lib_dir.is_dir():
            continue
        for svg_path in sorted(lib_dir.glob("*.svg")):
            name = svg_path.stem.lower()
            head = _read_svg_head(svg_path)
            score = 0
            for word in query_words:
                if word == name or word in name.split("-"):
                    score += 6
                elif word in name:
                    score += 4
                elif word in head:
                    score += 2
            if score:
                results.append((score, f"{lib}/{svg_path.stem}"))

    results.sort(key=lambda item: (-item[0], item[1]))
    return [name for _, name in results[:limit]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy chosen library icons into a project's icons/ folder, or search candidates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Legacy sync form remains supported:\n"
            "  python3 scripts/icon_sync.py <project_path> <lib/name> [<lib/name> ...]\n\n"
            "Search form:\n"
            "  python3 scripts/icon_sync.py search <query> [--library lib] [--limit N]"
        ),
    )
    return parser


def build_search_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search icon filenames and SVG header tags.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", choices=["search"], help=argparse.SUPPRESS)
    parser.add_argument("query", help="Search keyword, e.g. chart")
    parser.add_argument("--library", help="Limit search to one library, e.g. tabler-outline")
    parser.add_argument("--limit", type=int, default=20, help="Maximum candidates to print")
    return parser


def build_sync_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy chosen library icons into a project's icons/ folder; report missing ones.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("icons", nargs="+", help="Icon names to copy, e.g. chunk-filled/home")
    return parser


def _run_search(args: argparse.Namespace) -> int:
    if args.limit < 1:
        print("[ERROR] --limit must be >= 1", file=sys.stderr)
        return 2
    library = _LIB_ALIASES.get(args.library, args.library) if args.library else None
    if library and not (_GLOBAL_ICONS_DIR / library).is_dir():
        print(f"[ERROR] icon library not found: {library}", file=sys.stderr)
        return 2
    results = search_icons(args.query, library=library, limit=args.limit)
    for result in results:
        print(result)
    if not results:
        print(f"[WARN] no icons matched: {args.query}", file=sys.stderr)
        return 1
    return 0


def _run_sync(args: argparse.Namespace) -> int:
    project = Path(args.project_path)
    if not project.is_dir():
        print(f"[ERROR] project not found: {project}", file=sys.stderr)
        return 1

    copied, missing = sync_icons(project, args.icons)

    if copied:
        print(f"[OK] {len(copied)} icon(s) in {project / 'icons'}:", file=sys.stderr)
        for c in copied:
            print(f"     + {c}", file=sys.stderr)

    if missing:
        print(f"\n[MISSING] {len(missing)} icon(s) not in the library — re-pick before continuing:", file=sys.stderr)
        for m in missing:
            lib = m.split("/", 1)[0]
            print(f"     ✗ {m}   (search: ls {_GLOBAL_ICONS_DIR}/{lib}/ | grep <keyword>)", file=sys.stderr)
        return 1

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if not args_list or args_list[0] in {"-h", "--help"}:
        build_parser().parse_args(args_list)
        return 0
    if args_list[0] == "search":
        return _run_search(build_search_parser().parse_args(args_list))
    return _run_sync(build_sync_parser().parse_args(args_list))


if __name__ == "__main__":
    raise SystemExit(main())
