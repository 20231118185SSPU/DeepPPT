#!/usr/bin/env python3
"""
PPT Master - Dashboard Artifact Registry

Scan a PPT Master project directory and classify notable files for dashboard
display.

Usage:
    from artifact_registry import list_artifacts

Examples:
    artifacts = list_artifacts(Path("projects/example"))

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


_SCAN_DIRS = {
    "sources",
    "templates",
    "analysis",
    "images",
    "icons",
    "svg_output",
    "svg_final",
    "notes",
    "exports",
    "backup",
    "audio",
    "confirm_ui",
    "live_preview",
}

_ROOT_FILES = {
    "README.md",
    "design_spec.md",
    "spec_lock.md",
    "animations.json",
    "trace.jsonl",
    "metadata.json",
}

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".emf", ".wmf"}
_AUDIO_SUFFIXES = {".mp3", ".m4a", ".wav", ".aac", ".ogg"}
_SVG_VIEWBOX_RE = re.compile(r'\bviewBox="([^"]+)"')


def _iso_mtime(path: Path) -> str | None:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


def _artifact_type(rel_path: str, path: Path) -> str:
    parts = rel_path.replace("\\", "/").split("/")
    top = parts[0] if parts else ""
    name = path.name
    suffix = path.suffix.lower()

    if top == "sources":
        return "source"
    if top == "templates":
        return "template"
    if top == "analysis":
        return "analysis"
    if top == "icons":
        return "icon"
    if top == "svg_output" and suffix == ".svg":
        return "svg"
    if top == "svg_final" and suffix == ".svg":
        return "svg_final"
    if top == "notes" or name == "total.md":
        return "notes"
    if top == "exports" and suffix == ".pptx":
        return "pptx"
    if top == "backup":
        return "backup"
    if top == "confirm_ui":
        return "confirm"
    if top == "audio" or suffix in _AUDIO_SUFFIXES:
        return "audio"
    if top == "images":
        if name == "image_prompts.json":
            return "image_ai"
        if name == "image_sources.json":
            return "image_web"
        if suffix in _IMAGE_SUFFIXES:
            return "image"
        return "config"
    if name == "design_spec.md":
        return "spec"
    if name == "spec_lock.md":
        return "lock"
    if name == "animations.json":
        return "animation"
    if name.endswith("_report.json") or "quality" in name:
        return "quality_report"
    return "config"


def _created_by_step(artifact_type: str) -> int | None:
    mapping = {
        "source": 1,
        "analysis": 2,
        "template": 3,
        "confirm": 4,
        "spec": 4,
        "lock": 4,
        "image": 5,
        "image_ai": 5,
        "image_web": 5,
        "image_user": 5,
        "image_formula": 5,
        "icon": 4,
        "svg": 6,
        "notes": 6,
        "svg_final": 7,
        "pptx": 7,
        "backup": 7,
        "audio": 7,
        "animation": 7,
        "quality_report": 6,
    }
    return mapping.get(artifact_type)


def _svg_metadata(path: Path) -> dict:
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return {}
    metadata: dict = {}
    match = _SVG_VIEWBOX_RE.search(head)
    if match:
        metadata["viewbox"] = match.group(1)
    try:
        root = ET.fromstring(head if "</svg>" in head else path.read_text(encoding="utf-8", errors="replace"))
        metadata["tag"] = root.tag.rsplit("}", 1)[-1]
    except (ET.ParseError, OSError):
        pass
    return metadata


def _artifact_dict(project: Path, path: Path) -> dict:
    rel = path.relative_to(project).as_posix()
    artifact_type = _artifact_type(rel, path)
    try:
        stat = path.stat()
        size = stat.st_size
        modified_at = stat.st_mtime
    except OSError:
        size = None
        modified_at = None
    metadata = _svg_metadata(path) if path.suffix.lower() == ".svg" else None
    return {
        "path": rel,
        "name": path.name,
        "type": artifact_type,
        "exists": path.exists(),
        "size_bytes": size,
        "modified_at": _timestamp_from_epoch(modified_at),
        "created_by_step": _created_by_step(artifact_type),
        "metadata": metadata,
    }


def _timestamp_from_epoch(value: float | None) -> str | None:
    if value is None:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def iter_artifact_files(project: Path) -> list[Path]:
    """Return notable project files, keeping scans bounded to known folders."""
    files: list[Path] = []
    if not project.is_dir():
        return files
    for name in sorted(_ROOT_FILES):
        path = project / name
        if path.is_file():
            files.append(path)
    for dirname in sorted(_SCAN_DIRS):
        root = project / dirname
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files.append(path)
    return files


def list_artifacts(
    project: Path,
    *,
    type_filter: Optional[str] = None,
    step_filter: Optional[int] = None,
) -> dict:
    """Return the dashboard ArtifactList payload."""
    artifacts = []
    by_type: dict[str, int] = {}
    for path in iter_artifact_files(project):
        item = _artifact_dict(project, path)
        if type_filter and item["type"] != type_filter:
            continue
        if step_filter is not None and item["created_by_step"] != step_filter:
            continue
        artifacts.append(item)
        by_type[item["type"]] = by_type.get(item["type"], 0) + 1
    return {
        "artifacts": artifacts,
        "total": len(artifacts),
        "by_type": by_type,
    }


def latest_pptx(project: Path) -> str | None:
    """Return the latest exported PPTX path relative to the project."""
    exports = project / "exports"
    if not exports.is_dir():
        return None
    pptx_files = sorted(exports.glob("*.pptx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not pptx_files:
        return None
    return pptx_files[0].relative_to(project).as_posix()

