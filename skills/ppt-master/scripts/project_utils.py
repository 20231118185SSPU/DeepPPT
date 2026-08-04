#!/usr/bin/env python3
"""
PPT Master - Project Utilities Module

Provides common functions for project information parsing and validation,
reusable by other tools.
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Canvas format definitions (unified source)
try:
    from config import CANVAS_FORMATS
except ImportError:
    # Fallback: maintain minimal usable configuration to avoid runtime crashes
    CANVAS_FORMATS = {
        'ppt169': {
            'name': 'PPT 16:9',
            'dimensions': '1280×720',
            'viewbox': '0 0 1280 720',
            'aspect_ratio': '16:9'
        },
        'ppt43': {
            'name': 'PPT 4:3',
            'dimensions': '1024×768',
            'viewbox': '0 0 1024 768',
            'aspect_ratio': '4:3'
        },
        'wechat': {
            'name': 'WeChat Article Header',
            'dimensions': '900×383',
            'viewbox': '0 0 900 383',
            'aspect_ratio': '2.35:1'
        },
        'xiaohongshu': {
            'name': '小红书',
            'dimensions': '1242×1660',
            'viewbox': '0 0 1242 1660',
            'aspect_ratio': '3:4'
        },
        'moments': {
            'name': 'Moments/Instagram',
            'dimensions': '1080×1080',
            'viewbox': '0 0 1080 1080',
            'aspect_ratio': '1:1'
        },
        'story': {
            'name': 'Story/Vertical',
            'dimensions': '1080×1920',
            'viewbox': '0 0 1080 1920',
            'aspect_ratio': '9:16'
        },
        'banner': {
            'name': 'Horizontal Banner',
            'dimensions': '1920×1080',
            'viewbox': '0 0 1920 1080',
            'aspect_ratio': '16:9'
        },
        'a4': {
            'name': 'A4 Print',
            'dimensions': '1240×1754',
            'viewbox': '0 0 1240 1754',
            'aspect_ratio': '√2:1'
        }
    }

CANVAS_FORMAT_ALIASES = {
    'xhs': 'xiaohongshu',
    'wechat_moment': 'moments',
    'wechat-moment': 'moments',
    '朋友圈': 'moments',
    '小红书': 'xiaohongshu',
}


def normalize_canvas_format(format_key: str) -> str:
    """Normalize canvas format key name (supports common aliases)."""
    if not format_key:
        return ''
    key = format_key.strip().lower()
    return CANVAS_FORMAT_ALIASES.get(key, key)


def parse_project_name(dir_name: str) -> Dict[str, str]:
    """
    Parse project information from the project directory name.

    Args:
        dir_name: Project directory name

    Returns:
        Dictionary containing name, format, date
    """
    result = {
        'name': dir_name,
        'format': 'unknown',
        'format_name': 'Unknown format',
        'date': 'unknown',
        'date_formatted': 'Unknown date'
    }

    dir_name_lower = dir_name.lower()

    # Extract date (format: _YYYYMMDD)
    date_match = re.search(r'_(\d{8})$', dir_name)
    if date_match:
        date_str = date_match.group(1)
        result['date'] = date_str
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            result['date_formatted'] = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Prefer parsing standard format: name_format_YYYYMMDD
    full_match = re.match(r'^(?P<name>.+)_(?P<format>[a-z0-9_-]+)_(?P<date>\d{8})$', dir_name_lower)
    if full_match:
        raw_format = full_match.group('format')
        normalized_format = normalize_canvas_format(raw_format)
        if normalized_format in CANVAS_FORMATS:
            result['format'] = normalized_format
            result['format_name'] = CANVAS_FORMATS[normalized_format]['name']
            result['name'] = dir_name[:len(full_match.group('name'))]
            return result

    # Fallback: only match trailing `_format` to avoid deleting parts of the project name
    sorted_formats = sorted(CANVAS_FORMATS.keys(), key=len, reverse=True)
    for fmt_key in sorted_formats:
        if re.search(rf'_{re.escape(fmt_key)}(?:_\d{{8}})?$', dir_name_lower):
            result['format'] = fmt_key
            result['format_name'] = CANVAS_FORMATS[fmt_key]['name']
            break

    # Extract project name (only remove trailing date and format suffix)
    name = re.sub(r'_\d{8}$', '', dir_name)
    if result['format'] != 'unknown':
        name = re.sub(rf'_{re.escape(result["format"])}$', '', name, flags=re.IGNORECASE)
    result['name'] = name

    return result


def get_project_info(project_path: str) -> Dict:
    """
    Get detailed project information.

    Args:
        project_path: Project directory path

    Returns:
        Project information dictionary
    """
    project_path = Path(project_path)

    # Parse directory name
    parsed = parse_project_name(project_path.name)

    info = {
        'path': str(project_path),
        'dir_name': project_path.name,
        'name': parsed['name'],
        'format': parsed['format'],
        'format_name': parsed['format_name'],
        'date': parsed['date'],
        'date_formatted': parsed['date_formatted'],
        'exists': project_path.exists(),
        'svg_count': 0,
        'has_spec': False,
        'has_readme': False,
        'has_source': False,
        'source_count': 0,
        'spec_file': None,
        'svg_files': []
    }

    if not project_path.exists():
        return info

    # Check README.md
    info['has_readme'] = (project_path / 'README.md').exists()

    # Check design specification files (current standard + legacy names)
    spec_files = ['design_spec.md', '设计规范与内容大纲.md', 'design_specification.md', '设计规范.md']
    for spec_file in spec_files:
        if (project_path / spec_file).exists():
            info['has_spec'] = True
            info['spec_file'] = spec_file
            break

    # Check source documents
    legacy_source_file = project_path / '来源文档.md'
    sources_dir = project_path / 'sources'
    info['has_source'] = legacy_source_file.exists() or sources_dir.exists()

    if sources_dir.exists():
        info['source_count'] = len([p for p in sources_dir.iterdir() if p.is_file()])

    # Count SVG files
    svg_output = project_path / 'svg_output'
    if svg_output.exists():
        svg_files = sorted(svg_output.glob('*.svg'))
        info['svg_count'] = len(svg_files)
        info['svg_files'] = [f.name for f in svg_files]

    # Get canvas format details
    if info['format'] in CANVAS_FORMATS:
        info['canvas_info'] = CANVAS_FORMATS[info['format']]

    return info


def validate_project_structure(project_path: str, verbose: bool = False) -> Tuple[bool, List[str], List[str]]:
    """
    Validate project structure completeness.

    Args:
        project_path: Project directory path
        verbose: Whether to show detailed fix suggestions

    Returns:
        (is_valid, error_list, warning_list)
    """
    project_path = Path(project_path)
    errors = []
    warnings = []

    # Try to import error helper
    try:
        from error_helper import ErrorHelper
        use_helper = True
    except ImportError:
        use_helper = False

    # Check if directory exists
    if not project_path.exists():
        msg = f"Project directory does not exist: {project_path}"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_directory',
                                                           {'project_path': str(project_path)})
        errors.append(msg)
        return False, errors, warnings

    if not project_path.is_dir():
        errors.append(f"Not a valid directory: {project_path}")
        return False, errors, warnings

    # Check required files
    if not (project_path / 'README.md').exists():
        msg = "Missing required file: README.md"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_readme',
                                                           {'project_path': str(project_path)})
        errors.append(msg)

    # Check design specification file
    spec_files = ['design_spec.md', '设计规范与内容大纲.md', 'design_specification.md', '设计规范.md']
    has_spec = any((project_path / f).exists() for f in spec_files)
    if not has_spec:
        msg = "Missing design specification file (suggested filename: design_spec.md)"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_spec')
        warnings.append(msg)

    # Check svg_output directory
    svg_output = project_path / 'svg_output'
    if not svg_output.exists():
        msg = "Missing svg_output directory"
        if use_helper and verbose:
            msg += "\n" + \
                ErrorHelper.format_error_message('missing_svg_output')
        errors.append(msg)
    elif not svg_output.is_dir():
        errors.append("svg_output is not a directory")
    else:
        # Check for SVG files
        svg_files = list(svg_output.glob('*.svg'))
        if not svg_files:
            msg = "svg_output directory is empty, no SVG files found"
            if use_helper and verbose:
                msg += "\n" + \
                    ErrorHelper.format_error_message('empty_svg_output')
            warnings.append(msg)
        else:
            # Validate SVG file naming (consistent with project_manager.py)
            for svg_file in svg_files:
                if not re.match(r'^(slide_\d+_\w+|P?\d+_.+)\.svg$', svg_file.name):
                    msg = f"Non-standard SVG file naming: {svg_file.name}"
                    if use_helper and verbose:
                        msg += "\n" + ErrorHelper.format_error_message('invalid_svg_naming',
                                                                       {'file_name': svg_file.name})
                    warnings.append(msg)

    # Check directory naming format
    dir_name = project_path.name
    if not re.search(r'_\d{8}$', dir_name):
        msg = f"Directory name missing date suffix (_YYYYMMDD): {dir_name}"
        if use_helper and verbose:
            msg += "\n" + \
                ErrorHelper.format_error_message('missing_date_suffix')
        warnings.append(msg)

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_svg_viewbox(svg_files: List[Path], expected_format: Optional[str] = None) -> List[str]:
    """
    Validate the viewBox settings of SVG files.

    Args:
        svg_files: List of SVG files
        expected_format: Expected canvas format (e.g. 'ppt169')

    Returns:
        List of warnings
    """
    warnings = []
    viewbox_pattern = re.compile(r'viewBox="([^"]+)"')
    viewboxes = set()

    # Determine expected viewBox
    expected_viewbox = None
    if expected_format and expected_format in CANVAS_FORMATS:
        expected_viewbox = CANVAS_FORMATS[expected_format]['viewbox']

    for svg_file in svg_files[:10]:  # Check first 10 files
        try:
            with open(svg_file, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # Only read first 2000 characters
                match = viewbox_pattern.search(content)
                if match:
                    viewbox = match.group(1)
                    viewboxes.add(viewbox)

                    # If expected format is specified, check for match
                    if expected_viewbox and viewbox != expected_viewbox:
                        warnings.append(
                            f"{svg_file.name}: viewBox '{viewbox}' does not match expected format "
                            f"'{expected_format}' (expected: '{expected_viewbox}')"
                        )
                else:
                    warnings.append(f"{svg_file.name}: viewBox attribute not found")
        except Exception as e:
            warnings.append(f"{svg_file.name}: Failed to read - {e}")

    # Check for multiple different viewBoxes
    if len(viewboxes) > 1:
        warnings.append(f"Multiple different viewBox settings detected: {viewboxes}")

    return warnings


def find_all_projects(base_dir: str) -> List[Path]:
    """
    Find all projects under the specified directory.

    Args:
        base_dir: Base directory path

    Returns:
        List of project directories
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        return []

    projects = []
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it's a valid project directory (contains svg_output or design spec)
            has_svg_output = (item / 'svg_output').exists()
            has_spec = any((item / f).exists() for f in
                           ['design_spec.md', '设计规范与内容大纲.md', 'design_specification.md', '设计规范.md'])

            if has_svg_output or has_spec:
                projects.append(item)

    return sorted(projects)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted file size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_project_stats(project_path: str) -> Dict:
    """
    Get project statistics.

    Args:
        project_path: Project directory path

    Returns:
        Statistics dictionary
    """
    project_path = Path(project_path)
    stats = {
        'total_files': 0,
        'svg_files': 0,
        'md_files': 0,
        'html_files': 0,
        'total_size': 0,
        'svg_size': 0
    }

    if not project_path.exists():
        return stats

    # Walk with depth limit to avoid runaway traversal on large/deep trees
    max_depth = 5
    stack = [(project_path, 0)]
    while stack:
        current, depth = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_file():
                stats['total_files'] += 1
                file_size = entry.stat().st_size
                stats['total_size'] += file_size

                if entry.suffix == '.svg':
                    stats['svg_files'] += 1
                    stats['svg_size'] += file_size
                elif entry.suffix == '.md':
                    stats['md_files'] += 1
                elif entry.suffix == '.html':
                    stats['html_files'] += 1
            elif entry.is_dir() and depth < max_depth:
                stack.append((entry, depth + 1))

    return stats


# ---------------------------------------------------------------------------
# Canonical artifact accessors (single source of truth for project paths)
#
# Consumers: project_manager checkpoint, dashboard artifact_registry/state_reader,
# and any script that must read a project's produced artifacts. Pure stdlib only
# (no Flask / Provider SDK / PPTX SDK) so every layer can call these.
# ---------------------------------------------------------------------------

# Directories the pipeline may populate. init/README.md documents lazily-created
# ones; this tuple is the canonical registry both writers and readers agree on.
PROJECT_ARTIFACT_DIRS = (
    "sources",
    "analysis",
    "images",
    "icons",
    "svg_output",
    "svg_final",
    "notes",
    "exports",
    "backup",
    "quality",
    "validation",
    "confirm_ui",
    "dashboard",
    "live_preview",
    "audio",
    "templates",
    "_research",
)

# Where quality reports may have been written across versions. New writes target
# ``validation/`` (structural gates) and ``quality/`` (visual/pptx QA); older
# runs also wrote into ``analysis/``. Readers use find_quality_report() below
# instead of maintaining their own fallback lists.
_QUALITY_REPORT_CANDIDATE_DIRS = ("quality", "validation", "analysis")


def latest_export(project_path) -> Optional[Path]:
    """Return the newest ``exports/*.pptx`` for a project, or None.

    ``exports/`` is the canonical export location (svg_to_pptx.py writes here);
    project-root ``*.pptx`` is never the export source of truth.
    """
    exports = Path(project_path) / "exports"
    if not exports.is_dir():
        return None
    pptx_files = sorted(exports.glob("*.pptx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return pptx_files[0] if pptx_files else None


def has_export(project_path) -> bool:
    """True when the project has at least one canonical exported PPTX."""
    return latest_export(project_path) is not None


def svg_pages(project_path) -> List[Path]:
    """Sorted raw SVG pages in ``svg_output/`` (Executor's hand-written pages)."""
    svg_dir = Path(project_path) / "svg_output"
    if not svg_dir.is_dir():
        return []
    return sorted(svg_dir.glob("*.svg"))


def final_svg_pages(project_path) -> List[Path]:
    """Sorted finalized SVG pages in ``svg_final/``."""
    svg_dir = Path(project_path) / "svg_final"
    if not svg_dir.is_dir():
        return []
    return sorted(svg_dir.glob("*.svg"))


def notes_total(project_path) -> Optional[Path]:
    """Path to ``notes/total.md`` (Executor's speaker-notes source), or None."""
    path = Path(project_path) / "notes" / "total.md"
    return path if path.is_file() else None


def has_notes_total(project_path) -> bool:
    return notes_total(project_path) is not None


def spec_lock_path(project_path) -> Path:
    """Canonical ``spec_lock.md`` path (file may not exist yet)."""
    return Path(project_path) / "spec_lock.md"


def has_spec_lock(project_path) -> bool:
    return spec_lock_path(project_path).is_file()


def design_spec_path(project_path) -> Path:
    """Canonical ``design_spec.md`` path (file may not exist yet)."""
    return Path(project_path) / "design_spec.md"


def has_design_spec(project_path) -> bool:
    return design_spec_path(project_path).is_file()


def confirmation_result(project_path) -> Optional[Dict]:
    """Read ``confirm_ui/result.json`` as dict, or None when absent/invalid.

    The Confirm UI schema is owned by ``scripts/docs/confirm_ui.md``; this is
    only the canonical read accessor, not a schema definition.
    """
    result_path = Path(project_path) / "confirm_ui" / "result.json"
    if not result_path.is_file():
        return None
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def find_quality_report(project_path, basename: str) -> Optional[Path]:
    """Locate a quality report by basename across the historical candidate dirs.

    Order: ``quality/``, ``validation/``, ``analysis/``. New gates write to the
    first two; the ``analysis/`` fallback keeps legacy runs readable.
    """
    project = Path(project_path)
    for sub in _QUALITY_REPORT_CANDIDATE_DIRS:
        candidate = project / sub / basename
        if candidate.is_file():
            return candidate
    return None


def derive_pipeline_state(project_path) -> Dict:
    """Deterministically derive the pipeline step from produced artifacts.

    Single source of truth for pipeline-state derivation; project_manager's
    ``checkpoint_save`` and dashboard state readers both consume this instead of
    maintaining their own inference. Returned dict: ``{step, artifacts,
    next_step}`` (stable across repeated calls on the same fixture; no time
    fields). ``exports/*.pptx`` is the export fact (project-root ``*.pptx`` is
    never authoritative).
    """
    p = Path(project_path)

    has_sources = any((p / "sources").iterdir()) if (p / "sources").is_dir() else False
    has_spec_lock = spec_lock_path(project_path).is_file()
    has_design_spec = design_spec_path(project_path).is_file()
    has_notes = any((p / "notes").glob("*.md")) if (p / "notes").is_dir() else False
    has_total_md = notes_total(project_path) is not None
    has_images = any(
        f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}
        for f in (p / "images").iterdir()
    ) if (p / "images").is_dir() else False
    has_svgs = bool(svg_pages(project_path))
    has_final_svgs = bool(final_svg_pages(project_path))
    has_export = latest_export(project_path) is not None
    has_content_sel = (p / "content_selection.json").is_file()
    has_detailed_outline = (p / "detailed_outline.json").is_file()
    has_research = (p / "research_report.md").is_file()

    # Build artifact list (mirrors the historical checkpoint inventory)
    artifacts: List[str] = []
    if has_sources:
        artifacts.append("sources/")
    if has_research:
        artifacts.append("research_report.md")
    if has_content_sel:
        artifacts.append("content_selection.json")
    if has_detailed_outline:
        artifacts.append("detailed_outline.json")
    if has_design_spec:
        artifacts.append("design_spec.md")
    if has_spec_lock:
        artifacts.append("spec_lock.md")
    if has_images:
        artifacts.append("images/")
    if has_svgs:
        artifacts.append("svg_output/")
    if has_notes:
        artifacts.append("notes/")
    if has_total_md:
        artifacts.append("notes/total.md")
    if has_final_svgs:
        artifacts.append("svg_final/")
    if has_export:
        artifacts.append("exports/*.pptx")

    # Step inference (order matters — first match wins, mirrors the pipeline)
    if has_export:
        step = "8-export"
        next_step = "Done. Validate with e2e_validate.py or present."
    elif has_final_svgs:
        step = "7c-export"
        next_step = "Run svg_to_pptx.py to export PPTX."
    elif has_svgs and has_total_md:
        step = "7b-postprocess"
        next_step = "Run total_md_split.py, then finalize_svg.py, then svg_to_pptx.py."
    elif has_svgs:
        step = "7a-svg-gen"
        next_step = "Complete SVG generation, run quality check, generate speaker notes."
    elif has_images:
        step = "6-images"
        next_step = "Generate SVG pages (Step 6 in SKILL.md)."
    elif has_spec_lock:
        step = "5-spec-lock"
        next_step = "Run Image_Generator for images, then begin Executor SVG generation."
    elif has_design_spec:
        step = "4-design-spec"
        next_step = "Complete Eight Confirmations, seal spec_lock.md."
    elif has_detailed_outline:
        step = "3-outline"
        next_step = "Run Strategist Eight Confirmations."
    elif has_content_sel:
        step = "3-content-selection"
        next_step = "Generate detailed outline."
    elif has_sources or has_research:
        step = "2-sources"
        next_step = "Read SKILL.md Step 1-2. Select template, run Content Selection if research exists."
    else:
        step = "1-init"
        next_step = "Import source materials or run research workflow."

    return {"step": step, "artifacts": artifacts, "next_step": next_step}


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the diagnostic entry point."""
    parser = argparse.ArgumentParser(description="Inspect and validate a PPT Master project.")
    parser.add_argument("project_path", help="Project directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the diagnostic CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    project_path = args.project_path
    info = get_project_info(project_path)

    print(f"\nProject Info: {info['dir_name']}")
    print("=" * 60)
    print(f"Project Name: {info['name']}")
    print(f"Canvas Format: {info['format_name']} ({info['format']})")
    print(f"Created: {info['date_formatted']}")
    print(f"SVG Files: {info['svg_count']}")
    print(f"README: {'Yes' if info['has_readme'] else 'No'}")
    print(f"Design Spec: {'Yes' if info['has_spec'] else 'No'}")

    print("\nValidation Results:")
    print("-" * 60)
    is_valid, errors, warnings = validate_project_structure(project_path)

    if errors:
        print("[ERROR]")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("[WARN]")
        for warning in warnings:
            print(f"  - {warning}")

    if is_valid and not warnings:
        print("[OK] Project structure is complete, no issues found")
    return 0 if is_valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
