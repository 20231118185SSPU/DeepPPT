"""Dashboard reader for OfficeCLI integration state.

Reads OfficeCLI runtime probe results, Office source inspection manifests,
and native revision plan/result state. All read-only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


def _read_json(path: Path) -> Optional[dict[str, Any]]:
    """Read a JSON file, returning None on any failure."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def officecli_runtime_state(project: Path) -> dict[str, Any]:
    """Return OfficeCLI runtime availability for the project.

    Checks whether the project has a project.json with OfficeCLI-related fields,
    and whether the pinned binary is available.
    """
    result: dict[str, Any] = {
        "available": False,
        "version": None,
        "platform": None,
        "error": None,
    }

    # Try to probe the runtime via the install script
    try:
        import subprocess
        import sys
        install_script = (
            Path(__file__).resolve().parent.parent / "install_officecli.py"
        )
        if install_script.exists():
            p = subprocess.run(
                [sys.executable, str(install_script), "--json", "check"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if p.returncode == 0:
                data = json.loads(p.stdout)
                if data.get("success"):
                    result["available"] = True
                    result["version"] = data.get("version")
                    result["platform"] = data.get("platform")
                    result["status"] = data.get("status", "ready")
    except Exception:
        pass

    return result


def office_sources_state(project: Path) -> Optional[dict[str, Any]]:
    """Read the Office source inspection manifest.

    Returns None if no manifest exists or the project has no Office sources.
    """
    manifest_path = project / "analysis" / "office_sources.json"
    manifest = _read_json(manifest_path)
    if manifest is None:
        return None

    # Summarize for dashboard (don't include full outline/issue details)
    sources: list[dict[str, Any]] = []
    for src in manifest.get("sources", []):
        summary = src.get("summary", {})
        issues = src.get("issues", [])
        sources.append({
            "path": src.get("path"),
            "format": src.get("format"),
            "status": src.get("status"),
            "slide_count": summary.get("slides"),
            "table_count": summary.get("tables", summary.get("totalShapes")),
            "chart_count": summary.get("charts"),
            "image_count": summary.get("pictures", summary.get("images")),
            "issue_count": len(issues) if isinstance(issues, list) else 0,
            "converter": src.get("converter", {}).get("authority"),
        })

    return {
        "schema": manifest.get("schema"),
        "officecli_version": manifest.get("officecli", {}).get("version"),
        "source_count": len(sources),
        "sources": sources,
    }


def native_revision_state(project: Path) -> Optional[dict[str, Any]]:
    """Read native PPTX revision state.

    Returns None if no revision project or plan exists.
    """
    plan_path = project / "analysis" / "native_revision_plan.json"
    result_path = project / "analysis" / "native_revision_result.json"
    validation_path = project / "quality" / "officecli_validation.json"

    plan = _read_json(plan_path)
    if plan is None:
        return None

    state: dict[str, Any] = {
        "plan_status": plan.get("status"),
        "operation_count": len(plan.get("operations", [])),
        "source_hash": (plan.get("source", {}).get("sha256", "")[:16] + "..."),
        "svg_divergence": None,
        "export_path": None,
        "validation": None,
    }

    # Result (if applied)
    result = _read_json(result_path)
    if result:
        state["result_success"] = result.get("success")
        state["svg_divergence"] = result.get("svg_divergence")
        state["export_path"] = result.get("export_path")

    # Validation
    validation = _read_json(validation_path)
    if validation:
        state["validation"] = {
            "status": validation.get("status"),
            "validate_passed": validation.get("validate_passed"),
            "source_unchanged": validation.get("source_unchanged"),
        }

    # Preview (watch)
    watch_path = project / "native_preview" / "officecli-watch.json"
    watch = _read_json(watch_path)
    if watch:
        state["preview"] = {
            "status": watch.get("status"),
            "url": watch.get("url"),
            "port": watch.get("port"),
        }

    return state
