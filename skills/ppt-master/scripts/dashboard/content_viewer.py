#!/usr/bin/env python3
"""
PPT Master - Dashboard Content Viewer

Read one project artifact safely for dashboard preview.

Usage:
    detail = artifact_detail(project, "design_spec.md")

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from artifact_registry import list_artifacts


_TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".html", ".css", ".js", ".svg",
    ".xml", ".log",
}
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
_AUDIO_SUFFIXES = {".mp3", ".m4a", ".wav", ".aac", ".ogg"}
_VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".mkv"}
_BINARY_SUFFIXES = {".pptx", ".pptm", ".pdf", ".emf", ".wmf"} | _AUDIO_SUFFIXES | _VIDEO_SUFFIXES
_MAX_TEXT_BYTES = 512 * 1024


def resolve_project_file(project: Path, rel_path: str) -> Path:
    """Resolve a project-relative path and reject traversal outside project."""
    rel = rel_path.replace("\\", "/").lstrip("/")
    candidate = (project / rel).resolve()
    root = project.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes project directory") from exc
    if not candidate.is_file():
        raise FileNotFoundError(rel_path)
    return candidate


def artifact_detail(project: Path, rel_path: str) -> dict:
    """Return a safe artifact preview payload."""
    path = resolve_project_file(project, rel_path)
    rel = path.relative_to(project.resolve()).as_posix()
    artifact = _find_artifact(project, rel)
    suffix = path.suffix.lower()
    size = path.stat().st_size

    payload = {
        "path": rel,
        "name": path.name,
        "artifact": artifact,
        "size_bytes": size,
        "preview_kind": _preview_kind(suffix),
        "content": None,
        "truncated": False,
        "open_url": f"/artifact-file/{rel}",
        "related": {},
    }

    if suffix in _TEXT_SUFFIXES:
        raw = path.read_bytes()
        payload["truncated"] = len(raw) > _MAX_TEXT_BYTES
        raw = raw[:_MAX_TEXT_BYTES]
        text = raw.decode("utf-8", errors="replace")
        if suffix == ".json":
            try:
                payload["content"] = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
                payload["preview_kind"] = "json"
            except json.JSONDecodeError:
                payload["content"] = text
        elif suffix == ".jsonl":
            payload["content"] = _format_jsonl(text)
            payload["preview_kind"] = "jsonl"
        else:
            payload["content"] = text
    elif suffix in {".pptx", ".pptm"}:
        payload["related"] = {"svg_pages": _svg_pages(project)}
    return payload


def _find_artifact(project: Path, rel_path: str) -> Optional[dict]:
    artifacts = list_artifacts(project)["artifacts"]
    for item in artifacts:
        if item["path"] == rel_path:
            return item
    return None


def _preview_kind(suffix: str) -> str:
    if suffix == ".svg":
        return "svg"
    if suffix == ".md":
        return "markdown"
    if suffix == ".json":
        return "json"
    if suffix == ".jsonl":
        return "jsonl"
    if suffix in _IMAGE_SUFFIXES:
        return "image"
    if suffix == ".pdf":
        return "pdf"
    if suffix in _AUDIO_SUFFIXES:
        return "audio"
    if suffix in _VIDEO_SUFFIXES:
        return "video"
    if suffix in {".pptx", ".pptm"}:
        return "pptx"
    if suffix in _TEXT_SUFFIXES:
        return "text"
    if suffix in _BINARY_SUFFIXES:
        return "binary"
    return "unknown"


def _format_jsonl(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            lines.append(json.dumps(json.loads(line), ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            lines.append(line)
    return "\n".join(lines)



def _svg_pages(project: Path) -> list[dict]:
    pages = []
    svg_dir = project / "svg_output"
    if not svg_dir.is_dir():
        svg_dir = project / "svg_final"
    if not svg_dir.is_dir():
        return pages
    for path in sorted(svg_dir.glob("*.svg")):
        rel = path.relative_to(project).as_posix()
        pages.append({"name": path.name, "path": rel, "url": f"/artifact-file/{rel}"})
    return pages
