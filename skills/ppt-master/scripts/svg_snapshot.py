#!/usr/bin/env python3
"""
PPT Master - SVG Snapshot & Diff Utilities

Provides content hashing, structural diffing, and element enumeration
for SVG files in the revision workflow.

Usage:
    python3 svg_snapshot.py snapshot <svg_path>
    python3 svg_snapshot.py snapshot-all <svg_dir>
    python3 svg_snapshot.py diff <before_path> <after_path>
    python3 svg_snapshot.py list <svg_path>
    python3 svg_snapshot.py save <svg_dir> [-o <snapshot_path>]
    python3 svg_snapshot.py load <snapshot_path>
    python3 svg_snapshot.py validate <svg_path> <expected_hash>

Examples:
    python3 svg_snapshot.py snapshot projects/my_project/svg_output/01_cover.svg
    python3 svg_snapshot.py snapshot-all projects/my_project/svg_output/
    python3 svg_snapshot.py diff old.svg new.svg
    python3 svg_snapshot.py list projects/my_project/svg_output/01_cover.svg
    python3 svg_snapshot.py save projects/my_project/svg_output/ -o snap.json
    python3 svg_snapshot.py load snap.json
    python3 svg_snapshot.py validate projects/my_project/svg_output/01_cover.svg abc123

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"

# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

_WHITESPACE_RE = re.compile(r">\s+<")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_TRAILING_SPACE_RE = re.compile(r"[ \t]+(?=\n)")


def _normalize_xml(text: str) -> str:
    """Collapse insignificant whitespace so formatting-only edits don't trip the hash."""
    # Normalise line endings to LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of whitespace between closing/opening tags
    text = _WHITESPACE_RE.sub("><", text)
    # Collapse runs of horizontal whitespace inside text content
    lines = []
    for line in text.split("\n"):
        line = _MULTI_SPACE_RE.sub(" ", line)
        line = _TRAILING_SPACE_RE.sub("", line)
        lines.append(line)
    text = "\n".join(lines)
    # Drop leading/trailing blank lines
    text = text.strip() + "\n"
    return text


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def snapshot(svg_path: Path | str) -> str:
    """Compute SHA-256 hash of *svg_path* after whitespace normalisation.

    Returns the hex digest string.
    """
    path = Path(svg_path)
    raw = path.read_text(encoding="utf-8")
    normalised = _normalize_xml(raw)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def snapshot_all(svg_dir: Path | str) -> Dict[str, str]:
    """Compute hashes for every ``*.svg`` file in *svg_dir*.

    Returns ``{filename: hash}`` sorted by filename.
    """
    directory = Path(svg_dir)
    result: OrderedDict[str, str] = OrderedDict()
    for svg_file in sorted(directory.glob("*.svg")):
        result[svg_file.name] = snapshot(svg_file)
    return dict(result)


def validate_hash(svg_path: Path | str, expected_hash: str) -> bool:
    """Return ``True`` if *svg_path* still matches *expected_hash*."""
    return snapshot(svg_path) == expected_hash


# ---------------------------------------------------------------------------
# Snapshot persistence
# ---------------------------------------------------------------------------


def save_snapshot(svg_dir: Path | str, snapshot_path: Path | str | None = None) -> Path:
    """Save ``snapshot_all(svg_dir)`` to a JSON file.

    Default *snapshot_path*: ``<project>/.revision/snapshots.json`` (where
    *project* is the parent of *svg_dir*).
    """
    svg_dir = Path(svg_dir)
    if snapshot_path is None:
        project_dir = svg_dir.parent
        revision_dir = project_dir / ".revision"
        revision_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = revision_dir / "snapshots.json"
    else:
        snapshot_path = Path(snapshot_path)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    data = snapshot_all(svg_dir)
    snapshot_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return snapshot_path


def load_snapshot(snapshot_path: Path | str) -> Dict[str, str]:
    """Load a snapshot JSON file previously written by :func:`save_snapshot`."""
    path = Path(snapshot_path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------


def _strip_ns(tag: str) -> str:
    """Remove the SVG namespace prefix from a tag name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _xpath_of(element: ET.Element, root: ET.Element) -> str:
    """Build a human-readable xpath for *element* relative to *root*."""
    parts: list[str] = []
    node = element
    while node is not root:
        parent_map = {child: parent for parent in root.iter() for child in parent}
        parent = parent_map.get(node)
        if parent is None:
            break
        tag = _strip_ns(node.tag)
        siblings_same_tag = [
            c for c in parent if _strip_ns(c.tag) == tag
        ]
        if len(siblings_same_tag) > 1:
            idx = siblings_same_tag.index(node) + 1
            parts.append(f"{tag}[{idx}]")
        else:
            parts.append(tag)
        node = parent
    parts.reverse()
    return "/" + "/".join(parts) if parts else "/"


def _element_key(elem: ET.Element, root: ET.Element) -> str:
    """Return a stable identity key: ``id`` attribute when present, else xpath."""
    elem_id = elem.get("id")
    if elem_id:
        return f"id:{elem_id}"
    return f"xpath:{_xpath_of(elem, root)}"


def _text_content(elem: ET.Element) -> str:
    """Recursively collect all text inside an element."""
    return "".join(elem.itertext()).strip()


def _flatten_attrs(elem: ET.Element) -> Dict[str, str]:
    """Return a plain dict of attributes (namespace-unaware keys kept as-is)."""
    return dict(elem.attrib)


# ---------------------------------------------------------------------------
# Structural diff
# ---------------------------------------------------------------------------


def diff(before_path: Path | str, after_path: Path | str) -> Dict:
    """Structural diff of two SVG files using ElementTree.

    Returns::

        {
          "added":   [{"id": ..., "tag": ..., "xpath": ...}, ...],
          "removed": [{"id": ..., "tag": ..., "xpath": ...}, ...],
          "modified":[{"id": ..., "tag": ..., "changes": {attr: (old, new)}}, ...],
          "summary": "N modified, N added, N removed"
        }

    Elements are keyed by ``id`` attribute when present, otherwise by xpath.
    """
    before_tree = ET.parse(str(before_path))
    after_tree = ET.parse(str(after_path))
    before_root = before_tree.getroot()
    after_root = after_tree.getroot()

    def _collect_index(root: ET.Element) -> Dict[str, ET.Element]:
        """Map element key -> element for every descendant of *root*."""
        index: Dict[str, ET.Element] = {}
        for elem in root.iter():
            if elem is root:
                continue
            key = _element_key(elem, root)
            # If a key collision occurs (e.g. two elements without id at the
            # same xpath), keep the first occurrence — the xpath itself is
            # already disambiguated by index in _xpath_of.
            if key not in index:
                index[key] = elem
        return index

    before_idx = _collect_index(before_root)
    after_idx = _collect_index(after_root)

    before_keys = set(before_idx)
    after_keys = set(after_idx)

    added_keys = after_keys - before_keys
    removed_keys = before_keys - after_keys
    common_keys = before_keys & after_keys

    added: list[Dict] = []
    removed: list[Dict] = []
    modified: list[Dict] = []

    for key in sorted(added_keys):
        elem = after_idx[key]
        entry: Dict = {"tag": _strip_ns(elem.tag)}
        if key.startswith("id:"):
            entry["id"] = key[3:]
        else:
            entry["xpath"] = key[6:]
        added.append(entry)

    for key in sorted(removed_keys):
        elem = before_idx[key]
        entry = {"tag": _strip_ns(elem.tag)}
        if key.startswith("id:"):
            entry["id"] = key[3:]
        else:
            entry["xpath"] = key[6:]
        removed.append(entry)

    for key in sorted(common_keys):
        old_elem = before_idx[key]
        new_elem = after_idx[key]

        # Compare tag
        if _strip_ns(old_elem.tag) != _strip_ns(new_elem.tag):
            changes: Dict[str, tuple] = {"_tag": (_strip_ns(old_elem.tag), _strip_ns(new_elem.tag))}
        else:
            changes = {}

        # Compare attributes
        old_attrs = _flatten_attrs(old_elem)
        new_attrs = _flatten_attrs(new_elem)
        all_attr_keys = sorted(set(old_attrs) | set(new_attrs))
        for attr in all_attr_keys:
            old_val = old_attrs.get(attr)
            new_val = new_attrs.get(attr)
            if old_val != new_val:
                changes[attr] = (old_val, new_val)

        # Compare text content for leaf-ish elements
        old_text = _text_content(old_elem)
        new_text = _text_content(new_elem)
        if old_text != new_text and (old_text or new_text):
            changes["_text"] = (old_text, new_text)

        if changes:
            entry = {"tag": _strip_ns(new_elem.tag), "changes": changes}
            if key.startswith("id:"):
                entry["id"] = key[3:]
            else:
                entry["xpath"] = key[6:]
            modified.append(entry)

    summary = f"{len(modified)} modified, {len(added)} added, {len(removed)} removed"
    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Element enumeration
# ---------------------------------------------------------------------------

_TAG_TO_TYPE = {
    "text": "text",
    "tspan": "text",
    "rect": "rect",
    "circle": "circle",
    "ellipse": "circle",
    "image": "image",
    "path": "path",
    "g": "group",
    "line": "path",
    "polyline": "path",
    "polygon": "path",
}


def list_editable_elements(svg_path: Path | str) -> List[Dict]:
    """Parse *svg_path* and list every element that has an ``id`` attribute.

    Returns a list of dicts::

        {"id": "...", "tag": "...", "text": "...", "fill": "...",
         "type": "text|rect|circle|image|path|group"}
    """
    tree = ET.parse(str(svg_path))
    root = tree.getroot()

    elements: List[Dict] = []
    for elem in root.iter():
        elem_id = elem.get("id")
        if not elem_id:
            continue

        tag = _strip_ns(elem.tag)
        entry: Dict = {
            "id": elem_id,
            "tag": tag,
            "type": _TAG_TO_TYPE.get(tag, tag),
        }

        # Fill (present on most shapes and text)
        fill = elem.get("fill")
        if fill:
            entry["fill"] = fill

        # Text content
        if tag in ("text", "tspan"):
            entry["text"] = _text_content(elem)

        elements.append(entry)

    return elements


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SVG snapshot, diff, and element utilities for the revision pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_snap = sub.add_parser("snapshot", help="Hash a single SVG file")
    p_snap.add_argument("svg_path", help="Path to SVG file")

    p_all = sub.add_parser("snapshot-all", help="Hash all SVGs in a directory")
    p_all.add_argument("svg_dir", help="Path to directory containing .svg files")

    p_diff = sub.add_parser("diff", help="Structural diff of two SVG files")
    p_diff.add_argument("before", help="Path to 'before' SVG")
    p_diff.add_argument("after", help="Path to 'after' SVG")

    p_list = sub.add_parser("list", help="List editable elements (those with id)")
    p_list.add_argument("svg_path", help="Path to SVG file")

    p_save = sub.add_parser("save", help="Save snapshot of a directory to JSON")
    p_save.add_argument("svg_dir", help="Path to directory containing .svg files")
    p_save.add_argument("-o", "--output", default=None, help="Output JSON path")

    p_load = sub.add_parser("load", help="Load a snapshot JSON file")
    p_load.add_argument("snapshot_path", help="Path to snapshot JSON file")

    p_val = sub.add_parser("validate", help="Validate an SVG against an expected hash")
    p_val.add_argument("svg_path", help="Path to SVG file")
    p_val.add_argument("expected_hash", help="Expected SHA-256 hex digest")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help(sys.stderr)
        return 1

    if args.command == "snapshot":
        h = snapshot(args.svg_path)
        print(h)

    elif args.command == "snapshot-all":
        data = snapshot_all(args.svg_dir)
        for filename, h in data.items():
            print(f"{filename}\t{h}")

    elif args.command == "diff":
        result = diff(args.before, args.after)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "list":
        elements = list_editable_elements(args.svg_path)
        print(json.dumps(elements, indent=2, ensure_ascii=False))

    elif args.command == "save":
        out = save_snapshot(args.svg_dir, args.output)
        print(f"Snapshot saved to {out}", file=sys.stderr)

    elif args.command == "load":
        data = load_snapshot(args.snapshot_path)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.command == "validate":
        ok = validate_hash(args.svg_path, args.expected_hash)
        status = "MATCH" if ok else "STALE"
        print(f"{status}  {args.svg_path}")
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
