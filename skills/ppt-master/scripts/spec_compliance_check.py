#!/usr/bin/env python3
"""
PPT Master - spec_lock Compliance Checker

Semantic compliance validation between spec_lock.md and generated SVGs.
Complements svg_quality_checker.py (XML/structural/drift) and
e2e_validate.py (project-level structural consistency) by checking
the inverse direction: are all declared spec_lock entries properly
reflected in the project output?

Checks:
    1. Unused colors — declared in spec_lock colors but absent from all SVGs
    2. Layout template existence — page_layouts entries resolve to real files
    3. Chart template existence — page_charts entries resolve to real files
    4. Rhythm vocabulary — page_rhythm values are exactly anchor/dense/breathing
    5. Icon library validity — library is one of the four known values
    6. Inventory cross-check — SVG data-icon attrs use declared library + inventory
    7. Cross-section consistency — page_layouts/chart/rhythm keys exist in page_rhythm
    8. Image usage — images declared in spec_lock referenced by at least one SVG

Usage:
    python3 scripts/spec_compliance_check.py <project_path> [options]

Examples:
    python3 scripts/spec_compliance_check.py projects/my_deck_ppt169_20260626
    python3 scripts/spec_compliance_check.py projects/my_deck --json
    python3 scripts/spec_compliance_check.py projects/my_deck --strict

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# sys.path injection for sibling module
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from update_spec import parse_lock  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SUPPORTED_RHYTHMS = {"anchor", "dense", "breathing"}
SUPPORTED_ICON_LIBRARIES = {
    "chunk-filled",
    "tabler-filled",
    "tabler-outline",
    "phosphor-duotone",
}
COLOR_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_DATA_ICON_RE = re.compile(r'data-icon="([^"]+)"')


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class ComplianceIssue:
    severity: str  # "error" | "warn" | "info"
    check: str
    message: str
    detail: str = ""


@dataclass
class ComplianceReport:
    project: str
    issues: list[ComplianceIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warn_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warn")

    @property
    def passed(self) -> bool:
        return self.error_count == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _find_svg_dir(project: Path) -> Optional[Path]:
    """Return svg_output/ if it exists, else svg_final/, else None."""
    for name in ("svg_output", "svg_final"):
        d = project / name
        if d.is_dir() and any(d.glob("P*.svg")):
            return d
    return None


def _collect_svg_colors(svg_dir: Path) -> set[str]:
    """Return all lowercase HEX color values found in SVG fill/stroke/stop-color."""
    colors: set[str] = set()
    hex_re = re.compile(r'(?:fill|stroke|stop-color)\s*=\s*"(#[0-9A-Fa-f]{6})"')
    for svg in sorted(svg_dir.glob("P*.svg")):
        text = svg.read_text(encoding="utf-8", errors="replace")
        for m in hex_re.finditer(text):
            colors.add(m.group(1).lower())
    return colors


def _collect_svg_data_icons(svg_dir: Path) -> set[str]:
    """Return all data-icon attribute values across SVGs."""
    icons: set[str] = set()
    for svg in sorted(svg_dir.glob("P*.svg")):
        text = svg.read_text(encoding="utf-8", errors="replace")
        for m in _DATA_ICON_RE.finditer(text):
            icons.add(m.group(1))
    return icons


def _collect_svg_image_refs(svg_dir: Path) -> set[str]:
    """Return all image href paths referenced in SVGs."""
    refs: set[str] = set()
    href_re = re.compile(r'href="([^"]+)"')
    for svg in sorted(svg_dir.glob("P*.svg")):
        text = svg.read_text(encoding="utf-8", errors="replace")
        for m in href_re.finditer(text):
            val = m.group(1)
            # skip url() references (gradients, filters)
            if val.startswith("url("):
                continue
            refs.add(val)
    return refs


def _parse_page_ids(spec_lock: dict[str, dict[str, str]]) -> list[str]:
    """Extract page IDs (P01, P02, …) from page_rhythm keys."""
    rhythm = spec_lock.get("page_rhythm", {})
    ids = []
    for key in rhythm:
        # normalize: strip slug suffix (P01_cover → P01)
        pid = key.split("_")[0] if "_" in key else key
        ids.append(pid)
    return ids


_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def check_unused_colors(
    spec_lock: dict[str, dict[str, str]],
    svg_colors: set[str],
) -> list[ComplianceIssue]:
    """Check for declared colors not used in any SVG."""
    issues: list[ComplianceIssue] = []
    colors_section = spec_lock.get("colors", {})
    skip_keys = {"image_rendering", "image_palette", "image_rendering_behavior",
                 "image_palette_behavior"}
    for key, val in colors_section.items():
        if key in skip_keys:
            continue
        if not _HEX_RE.match(val):
            continue
        if val.lower() not in svg_colors:
            issues.append(ComplianceIssue(
                severity="warn",
                check="unused-color",
                message=f"Declared color {key}: {val} not found in any SVG",
                detail="This color is locked in spec_lock but unused. "
                       "Consider removing it to keep the lock tight.",
            ))
    return issues


def check_layout_templates(
    spec_lock: dict[str, dict[str, str]],
    project: Path,
) -> list[ComplianceIssue]:
    """Check that page_layouts entries resolve to real template SVGs."""
    issues: list[ComplianceIssue] = []
    layouts = spec_lock.get("page_layouts", {})
    templates_dir = _scripts_templates_dir()
    if not templates_dir:
        issues.append(ComplianceIssue(
            severity="info",
            check="layout-templates",
            message="Cannot locate templates/ directory — skipping layout existence check",
        ))
        return issues
    layouts_dir = templates_dir / "layouts"
    for page_id, tpl_name in layouts.items():
        svg_name = f"{tpl_name}.svg"
        # Search recursively in templates/layouts/ (organized by theme)
        matches = list(layouts_dir.rglob(svg_name)) if layouts_dir.is_dir() else []
        if not matches:
            issues.append(ComplianceIssue(
                severity="warn",
                check="layout-template-missing",
                message=f"{page_id}: template '{svg_name}' not found in templates/layouts/",
            ))
    return issues


def check_chart_templates(
    spec_lock: dict[str, dict[str, str]],
    project: Path,
) -> list[ComplianceIssue]:
    """Check that page_charts entries exist in charts_index.json."""
    issues: list[ComplianceIssue] = []
    charts = spec_lock.get("page_charts", {})
    if not charts:
        return issues
    templates_dir = _scripts_templates_dir()
    if not templates_dir:
        return issues
    index_path = templates_dir / "charts" / "charts_index.json"
    valid_names: set[str] = set()
    if index_path.exists():
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(index_data, dict):
                valid_names = set(index_data.keys())
            elif isinstance(index_data, list):
                valid_names = {
                    e.get("name", "") for e in index_data if isinstance(e, dict)
                }
        except (json.JSONDecodeError, OSError):
            issues.append(ComplianceIssue(
                severity="warn",
                check="chart-index-unreadable",
                message="charts_index.json exists but could not be parsed",
            ))
            return issues
    for page_id, chart_name in charts.items():
        if valid_names and chart_name not in valid_names:
            issues.append(ComplianceIssue(
                severity="error",
                check="chart-template-missing",
                message=f"{page_id}: chart template '{chart_name}' not in charts_index.json",
            ))
    return issues


def check_rhythm_vocabulary(
    spec_lock: dict[str, dict[str, str]],
) -> list[ComplianceIssue]:
    """Check that all page_rhythm values are valid."""
    issues: list[ComplianceIssue] = []
    rhythm = spec_lock.get("page_rhythm", {})
    for page_id, val in rhythm.items():
        if val not in SUPPORTED_RHYTHMS:
            issues.append(ComplianceIssue(
                severity="error",
                check="rhythm-invalid",
                message=f"{page_id}: rhythm '{val}' is not valid",
                detail=f"Must be one of: {', '.join(sorted(SUPPORTED_RHYTHMS))}",
            ))
    return issues


def check_icon_library(
    spec_lock: dict[str, dict[str, str]],
) -> list[ComplianceIssue]:
    """Check that icon library is a known value."""
    issues: list[ComplianceIssue] = []
    icons = spec_lock.get("icons", {})
    lib = icons.get("library", "")
    if lib and lib not in SUPPORTED_ICON_LIBRARIES:
        issues.append(ComplianceIssue(
            severity="error",
            check="icon-library-invalid",
            message=f"Icon library '{lib}' is not recognized",
            detail=f"Must be one of: {', '.join(sorted(SUPPORTED_ICON_LIBRARIES))}",
        ))
    return issues


def check_icon_inventory(
    spec_lock: dict[str, dict[str, str]],
    svg_icons: set[str],
) -> list[ComplianceIssue]:
    """Check that SVG data-icon values match declared library and inventory."""
    issues: list[ComplianceIssue] = []
    icons_section = spec_lock.get("icons", {})
    lib = icons_section.get("library", "")
    inv_raw = icons_section.get("inventory", "")
    inventory = {n.strip() for n in inv_raw.split(",") if n.strip()} if inv_raw else set()

    for icon_ref in sorted(svg_icons):
        # icon_ref format: "library/name" or just "name"
        if "/" in icon_ref:
            icon_lib, icon_name = icon_ref.split("/", 1)
            if lib and icon_lib != lib:
                issues.append(ComplianceIssue(
                    severity="error",
                    check="icon-library-mismatch",
                    message=f"SVG uses icon '{icon_ref}' from library '{icon_lib}', "
                            f"but spec_lock declares '{lib}'",
                ))
            if inventory and icon_name not in inventory:
                issues.append(ComplianceIssue(
                    severity="warn",
                    check="icon-not-in-inventory",
                    message=f"Icon '{icon_name}' used in SVG but not in spec_lock inventory",
                ))
        else:
            # bare name — can't check library
            if inventory and icon_ref not in inventory:
                issues.append(ComplianceIssue(
                    severity="warn",
                    check="icon-not-in-inventory",
                    message=f"Icon '{icon_ref}' used in SVG but not in spec_lock inventory",
                ))
    return issues


def check_cross_section_consistency(
    spec_lock: dict[str, dict[str, str]],
) -> list[ComplianceIssue]:
    """Check that page_layouts/chart keys exist in page_rhythm."""
    issues: list[ComplianceIssue] = []
    rhythm_ids = set(_parse_page_ids(spec_lock))

    for section_name in ("page_layouts", "page_charts"):
        section = spec_lock.get(section_name, {})
        for page_id in section:
            pid = page_id.split("_")[0] if "_" in page_id else page_id
            if pid not in rhythm_ids:
                issues.append(ComplianceIssue(
                    severity="warn",
                    check="cross-ref-missing",
                    message=f"{section_name} references {page_id}, "
                            f"but {pid} not in page_rhythm",
                ))
    return issues


def check_image_usage(
    spec_lock: dict[str, dict[str, str]],
    svg_image_refs: set[str],
) -> list[ComplianceIssue]:
    """Check that each declared image is referenced by at least one SVG."""
    issues: list[ComplianceIssue] = []
    images = spec_lock.get("images", {})
    if not images:
        return issues
    for label, raw_val in images.items():
        # value may be "images/foo.png" or "images/foo.png | no-crop"
        img_path = raw_val.split("|")[0].strip()
        # normalize for comparison — SVGs may use relative or absolute paths
        found = any(img_path in ref or ref.endswith(Path(img_path).name)
                    for ref in svg_image_refs)
        if not found:
            issues.append(ComplianceIssue(
                severity="warn",
                check="image-declared-unused",
                message=f"Image '{label}: {img_path}' declared in spec_lock "
                        f"but not referenced in any SVG",
            ))
    return issues


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
def _scripts_templates_dir() -> Optional[Path]:
    """Locate the templates/ directory relative to scripts/."""
    candidates = [
        _SCRIPTS_DIR.parent / "templates",
        _SCRIPTS_DIR.parent.parent / "templates",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return None


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def run_compliance(project_path: Path, *, strict: bool = False) -> ComplianceReport:
    """Run all compliance checks and return a report."""
    report = ComplianceReport(project=str(project_path))

    # Locate spec_lock.md
    lock_path = project_path / "spec_lock.md"
    if not lock_path.exists():
        report.issues.append(ComplianceIssue(
            severity="error",
            check="spec-lock-missing",
            message="spec_lock.md not found in project root",
        ))
        return report

    # Parse spec_lock
    try:
        spec_lock = parse_lock(lock_path)
    except Exception as exc:
        report.issues.append(ComplianceIssue(
            severity="error",
            check="spec-lock-parse-error",
            message=f"Failed to parse spec_lock.md: {exc}",
        ))
        return report

    # Locate SVGs
    svg_dir = _find_svg_dir(project_path)
    has_svgs = svg_dir is not None

    # Collect SVG data (empty sets if no SVGs yet)
    svg_colors = _collect_svg_colors(svg_dir) if has_svgs else set()
    svg_icons = _collect_svg_data_icons(svg_dir) if has_svgs else set()
    svg_image_refs = _collect_svg_image_refs(svg_dir) if has_svgs else set()

    # Run checks — spec-only (no SVGs needed)
    report.issues.extend(check_rhythm_vocabulary(spec_lock))
    report.issues.extend(check_icon_library(spec_lock))
    report.issues.extend(check_cross_section_consistency(spec_lock))
    report.issues.extend(check_layout_templates(spec_lock, project_path))
    report.issues.extend(check_chart_templates(spec_lock, project_path))

    # Run checks — require SVGs
    if has_svgs:
        report.issues.extend(check_unused_colors(spec_lock, svg_colors))
        report.issues.extend(check_icon_inventory(spec_lock, svg_icons))
        report.issues.extend(check_image_usage(spec_lock, svg_image_refs))
    else:
        report.issues.append(ComplianceIssue(
            severity="info",
            check="no-svgs",
            message="No SVG output found — SVG-dependent checks skipped",
        ))

    # In strict mode, promote warns to errors
    if strict:
        for issue in report.issues:
            if issue.severity == "warn":
                issue.severity = "error"

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate spec_lock.md semantic compliance against SVG output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path",
        help="Path to the project directory (e.g. projects/my_deck_ppt169_20260626)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote warnings to errors (exit 1 on any warning)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for programmatic use)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project = Path(args.project_path)
    if not project.is_dir():
        print(f"Error: project directory not found: {project}", file=sys.stderr)
        return 2

    report = run_compliance(project, strict=args.strict)

    # --json mode
    if args.json:
        out = {
            "project": report.project,
            "passed": report.passed,
            "errors": report.error_count,
            "warnings": report.warn_count,
            "issues": [
                {
                    "severity": i.severity,
                    "check": i.check,
                    "message": i.message,
                    "detail": i.detail,
                }
                for i in report.issues
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if report.passed else 1

    # Human-readable output
    print(f"=== spec_lock Compliance: {project.name} ===\n")

    if not report.issues:
        print("All checks passed — no issues found.")
        return 0

    for issue in report.issues:
        tag = {"error": "ERROR", "warn": "WARN", "info": "INFO"}[issue.severity]
        icon = {"error": "[X]", "warn": "[!]", "info": "[i]"}[issue.severity]
        print(f"  {icon} {tag} ({issue.check}) {issue.message}")
        if issue.detail:
            print(f"      {issue.detail}")

    # Summary
    print()
    print(f"  Errors: {report.error_count}  |  Warnings: {report.warn_count}  |  "
          f"Total issues: {len(report.issues)}")

    if report.passed:
        print("\n  Result: PASS")
    else:
        print("\n  Result: FAIL")

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
