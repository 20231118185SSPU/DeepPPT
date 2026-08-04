#!/usr/bin/env python3
"""
PPT Master - Canonical spec_lock.md Reader

Single parser owner for ``<project>/spec_lock.md`` (see
``plans/deepppt2-system-optimization-agent-brief.md`` T2.2). All consumers
(e2e_validate, layout_capacity_check, dashboard state_reader, svg_quality
checker, spec_compliance_check, ...) must read the lock through this module
instead of maintaining their own section regexes.

The Markdown file itself stays the human/agent authority artifact; this module
only provides the read model. The returned section dict keeps the historical
shape ``{section: {key: value}}`` (value always str) so ``update_spec.parse_lock``
and existing callers remain compatible; typed/derived accessors are separate
functions on top.

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SECTION_RE = re.compile(r"^##\s+(\S+)")
KEY_VALUE_RE = re.compile(r"^-\s+([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$")
PAGE_ID_RE = re.compile(r"^P?(\d{1,3})", re.IGNORECASE)


def parse_spec_lock(lock_path) -> Dict[str, Dict[str, str]]:
    """Parse ``spec_lock.md`` into ``{section_name: {key: value}}``.

    Value is always the raw string after the colon. Repeated keys inside one
    section overwrite (spec_lock rows use unique keys per section). Missing or
    unreadable file raises ``FileNotFoundError``/``OSError`` — callers that need
    tolerance wrap this themselves.
    """
    sections: Dict[str, Dict[str, str]] = {}
    current: Optional[str] = None
    for raw in Path(lock_path).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, {})
            continue
        if current is None:
            continue
        m = KEY_VALUE_RE.match(line)
        if m:
            sections[current][m.group(1)] = m.group(2)
    return sections


def get(spec: Dict[str, Dict[str, str]], section: str, key: str, default: str = "") -> str:
    """Read one ``- key: value`` row, returning ``default`` when absent."""
    return spec.get(section, {}).get(key, default)


def narrative_mode(spec: Dict[str, Dict[str, str]]) -> Optional[str]:
    """Locked narrative skeleton from ``## mode`` (pyramid/narrative/... or custom)."""
    value = get(spec, "mode", "mode").strip().lower()
    return value or None


def structure_mode(spec: Dict[str, Dict[str, str]]) -> Optional[str]:
    """``pptx_structure.mode`` — flat (default) or structured.

    The parser reads the ``mode:`` row, not ``pptx_structure.mode:`` (the
    section heading declares the namespace; see templates/spec_lock_reference.md).
    """
    value = get(spec, "pptx_structure", "mode").strip().lower()
    return value or None


def page_ids(spec: Dict[str, Dict[str, str]]) -> List[str]:
    """Sorted page IDs from ``## page_rhythm`` (``- page1: anchor`` rows).

    IDs keep their literal key (``P01`` / ``page1`` / ``01``), sorted
    numerically by their leading number when possible.
    """
    rhythm = spec.get("page_rhythm", {})
    ids = list(rhythm.keys())

    def _num_key(item: str) -> Tuple[int, str]:
        m = PAGE_ID_RE.match(item)
        return (int(m.group(1)) if m else 10**9, item)

    return sorted(ids, key=_num_key)


def images(lock_path) -> List[str]:
    """Image path values from ``## images``, option/comment suffixes stripped.

    The images section mixes labelled rows (``- label: images/foo.png``) with
    bare path rows (``- images/foo.png``), so it is parsed from the raw text
    rather than the key:value section dict. ``| no-crop`` options and
    ``# comment`` tails are dropped. Returns the declared paths in file order.
    """
    text = Path(lock_path).read_text(encoding="utf-8")
    result: List[str] = []
    in_images = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## images"):
            in_images = True
            continue
        if in_images and stripped.startswith("## "):
            break
        if not in_images or not stripped.startswith("- "):
            continue
        content = stripped[2:].split("|", 1)[0].split("#", 1)[0].strip()
        if not content:
            continue
        if ":" in content:
            _, _, path_part = content.partition(":")
            path_part = path_part.strip()
        else:
            path_part = content
        if path_part:
            result.append(path_part)
    return result


def canvas_dimensions(spec: Dict[str, Dict[str, str]]) -> Optional[Tuple[int, int]]:
    """``canvas.viewBox`` parsed as ``(width, height)``, or None when absent/bad."""
    viewbox = get(spec, "canvas", "viewBox")
    m = re.match(r"^\s*0\s+0\s+(\d+)\s+(\d+)\s*$", viewbox)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def body_size(spec: Dict[str, Dict[str, str]]) -> Optional[int]:
    """``typography.body`` as int, or None when absent/non-numeric.

    Accepts both ``- body: 18`` and the ``18px`` variant used by some legacy
    projects.
    """
    value = get(spec, "typography", "body").strip()
    m = re.match(r"^(\d+)(?:px)?$", value)
    return int(m.group(1)) if m else None


def lock_file_path(project_path) -> Path:
    """Canonical ``spec_lock.md`` path under a project (file may not exist)."""
    return Path(project_path) / "spec_lock.md"
