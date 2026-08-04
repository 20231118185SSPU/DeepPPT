#!/usr/bin/env python3
"""PPT Master — Office Source Inspection

Read-only structural scan of Office source files (.docx, .xlsx, .pptx) in a
project's ``sources/`` directory. Produces ``analysis/office_sources.json``
with format-specific counts, outline, and issues. Never modifies source files.

Usage:
    python3 scripts/office_source_inspect.py <project_path> [--json]

Dependencies:
    ``officecli_bridge.py`` (same directory).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from officecli_bridge import (  # noqa: E402
    probe_officecli,
    run_officecli,
    validate_office_file,
    inspect_office_file,
    OFFICECLI_NOT_INSTALLED,
    OFFICECLI_COMMAND_FAILED,
)

# Best-effort trace import
try:
    from dashboard.trace_writer import trace_event as _trace_event
except ImportError:
    def _trace_event(*args: Any, **kwargs: Any) -> None:  # type: ignore[no-redef]
        pass

MANIFEST_SCHEMA = "ppt_master.office_sources.v1"

# Format-specific stat keys to extract
_PPTX_KEYS = {"slides", "totalShapes", "textBoxes", "pictures", "charts",
              "oleObjects", "tables", "words", "slidesWithoutTitle",
              "picturesWithoutAlt", "notesSlides"}
_DOCX_KEYS = {"sections", "paragraphs", "tables", "images", "comments",
              "revisions", "equations", "words", "pages"}
_XLSX_KEYS = {"sheets", "tables", "charts", "pivotTables", "formulas",
              "validations", "namedRanges", "rows", "columns"}


def _sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _inspect_one(source_path: Path, project_root: Path) -> dict[str, object]:
    """Inspect a single Office source file (read-only)."""
    source_hash = _sha256(source_path)
    fmt = source_path.suffix.lstrip(".").lower()

    result: dict[str, object] = {
        "path": str(source_path.relative_to(project_root)),
        "sha256": source_hash,
        "format": fmt,
        "status": "passed",
        "summary": {},
        "outline": [],
        "issues": [],
        "converter": {},
        "repair": None,
    }

    # Set converter authority based on format
    if fmt == "docx":
        result["converter"] = {"authority": "source_to_md/doc_to_md.py"}
    elif fmt == "xlsx":
        result["converter"] = {"authority": "source_to_md/excel_to_md.py"}
    elif fmt == "pptx":
        result["converter"] = {"authority": "source_to_md/ppt_to_md.py"}

    # Run stats
    stats_result = run_officecli(
        ["view", str(source_path), "stats", "--json"],
        timeout_s=30.0,
    )
    if stats_result.success:
        data = stats_result.data.get("data", stats_result.data)
        if isinstance(data, dict):
            # Filter format-specific keys
            if fmt == "pptx":
                keys = _PPTX_KEYS
            elif fmt == "docx":
                keys = _DOCX_KEYS
            elif fmt == "xlsx":
                keys = _XLSX_KEYS
            else:
                keys = set()
            result["summary"] = {k: v for k, v in data.items() if k in keys}
    else:
        result["status"] = "warning"
        result["summary"] = {"error": stats_result.message}

    # Run issues
    issues_result = run_officecli(
        ["view", str(source_path), "issues", "--json"],
        timeout_s=30.0,
    )
    if issues_result.success:
        issues_data = issues_result.data.get("data", issues_result.data)
        if isinstance(issues_data, list):
            result["issues"] = issues_data[:50]  # limit to 50 issues
        elif isinstance(issues_data, dict):
            result["issues"] = [issues_data]

    # Verify source unchanged
    assert _sha256(source_path) == source_hash, (
        f"Source file was modified during inspection: {source_path}"
    )

    return result


def _cmd_inspect(project_path: str, json_output: bool = False) -> int:
    """Main entry: scan project sources/ and write manifest."""
    project = Path(project_path).resolve()
    if not project.is_dir():
        print(f"Not a directory: {project}", file=sys.stderr)
        return 1

    # Check OfficeCLI ready
    runtime = probe_officecli()
    if runtime.status != "ready":
        msg = (
            f"OfficeCLI not ready (status={runtime.status}). "
            "Skipping Office source inspection."
        )
        if json_output:
            print(json.dumps({"success": False, "error_code": OFFICECLI_NOT_INSTALLED, "message": msg}))
        else:
            print(msg)
        return 0  # Not a hard error — just skip enrichment

    # Find Office source files
    sources_dir = project / "sources"
    if not sources_dir.is_dir():
        if json_output:
            print(json.dumps({"success": True, "message": "No sources/ directory"}))
        else:
            print("No sources/ directory — nothing to inspect.")
        return 0

    office_extensions = {".docx", ".xlsx", ".pptx"}
    office_files = [
        f for f in sources_dir.iterdir()
        if f.is_file() and f.suffix.lower() in office_extensions
    ]

    if not office_files:
        if json_output:
            print(json.dumps({"success": True, "message": "No Office source files found"}))
        else:
            print("No Office source files found.")
        return 0

    # Inspect each file
    sources_list: list[dict[str, object]] = []
    for src_file in sorted(office_files):
        print(f"Inspecting {src_file.name}...")
        entry = _inspect_one(src_file, project)
        sources_list.append(entry)

    # Build manifest
    manifest: dict[str, object] = {
        "schema": MANIFEST_SCHEMA,
        "officecli": {
            "version": runtime.expected_version,
            "status": runtime.status,
        },
        "sources": sources_list,
        "inspected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    # Write
    analysis_dir = project / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = analysis_dir / "office_sources.json"
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    if json_output:
        print(json.dumps({"success": True, "manifest": str(manifest_path), "count": len(sources_list)}))
    else:
        print(f"Manifest written to {manifest_path} ({len(sources_list)} source(s))")
        for s in sources_list:
            summary = s.get("summary", {})
            issues = s.get("issues", [])
            issue_count = len(issues) if isinstance(issues, list) else 0
            print(f"  {s['format']}: {s['path']} — {summary} — {issue_count} issues")

    # Trace event (no sensitive content)
    _trace_event(
        project,
        "office_source_inspect",
        f"Inspected {len(sources_list)} Office source(s)",
        status="PASS",
        source_count=len(sources_list),
        formats=[s.get("format") for s in sources_list],
    )

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Office source structure inspection",
    )
    parser.add_argument("project", help="Project directory path")
    parser.add_argument("--json", action="store_true", default=False,
                        help="Output machine-readable JSON")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return _cmd_inspect(args.project, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
