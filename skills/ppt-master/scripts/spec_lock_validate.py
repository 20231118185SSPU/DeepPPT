#!/usr/bin/env python3
"""
PPT Master - Spec Lock Structural Validator

Validates that spec_lock.md has all required sections with populated data.
Complements spec_lock_digest.py (which checks integrity/hash) by checking
structural completeness before Executor starts.

Usage:
    python3 scripts/spec_lock_validate.py <project_path>
    python3 scripts/spec_lock_validate.py <project_path> --json

Exit codes:
    0 = valid structure
    1 = structural errors found
    2 = input error (file missing, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "canvas",
    "mode",
    "visual_style",
    "colors",
    "typography",
    "icons",
    "images",
    "decisions",
    "page_rhythm",
    "page_layouts",
    "page_charts",
    "forbidden",
]


def validate_spec_lock(project_path: str, *, as_json: bool = False) -> int:
    """Validate spec_lock.md structure. Returns exit code."""
    p = Path(project_path)
    spec_lock = p / "spec_lock.md"

    if not spec_lock.is_file():
        print(f"Error: spec_lock.md not found at {spec_lock}", file=sys.stderr)
        return 2

    text = spec_lock.read_text(encoding="utf-8")

    # Extract H2 sections
    section_pattern = re.compile(r"^## (\S+)", re.MULTILINE)
    found_sections = set(section_pattern.findall(text))

    errors: list[str] = []
    warnings: list[str] = []

    if re.search(r"(?mi)^##\s+page_expression\s*$", text):
        errors.append(
            "spec_lock.md must not contain ## page_expression; use page_expression.json"
        )

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in found_sections:
            errors.append(f"Missing required section: ## {section}")

    # Check for empty sections (## heading followed immediately by another ## or EOF)
    section_content_pattern = re.compile(
        r"^## (\S+)\s*\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
    )
    for match in section_content_pattern.finditer(text):
        name = match.group(1)
        content = match.group(2).strip()
        # Filter out guidance lines (starting with >)
        data_lines = [
            line for line in content.splitlines()
            if line.strip() and not line.strip().startswith(">")
        ]
        if not data_lines:
            warnings.append(f"Section ## {name} has no data lines (only guidance/empty)")

    # Check canvas has viewBox
    if "canvas" in found_sections:
        if "viewBox" not in text:
            errors.append("## canvas missing viewBox value")

    # Check mode has a value — read only from the ## mode section. The
    # ## pptx_structure section also declares a `- mode:` row (flat/structured);
    # a bare global search would misread that row as the narrative mode.
    mode_section = next(
        (
            m.group(2)
            for m in section_content_pattern.finditer(text)
            if m.group(1) == "mode"
        ),
        None,
    )
    if mode_section is not None:
        mode_match = re.search(r"^- mode:\s*(\S+)", mode_section, re.MULTILINE)
        if mode_match:
            mode_val = mode_match.group(1)
            if mode_val == "pyramid" or mode_val in (
                "narrative", "instructional", "showcase", "briefing", "custom"
            ):
                pass  # valid
            else:
                warnings.append(f"Unusual mode value: {mode_val}")

    # Check colors have hex values
    hex_pattern = re.compile(r"#[0-9a-fA-F]{6}")
    if "colors" in found_sections:
        for m in section_content_pattern.finditer(text):
            if m.group(1) == "colors":
                if not hex_pattern.search(m.group(2)):
                    warnings.append("## colors section has no hex color values")
                break

    # Output
    if as_json:
        result = {
            "file": str(spec_lock),
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sections_found": sorted(found_sections),
            "sections_missing": [s for s in REQUIRED_SECTIONS if s not in found_sections],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if errors:
            print("Spec Lock Validation: FAIL")
            print("-" * 40)
            for e in errors:
                print(f"  [ERROR] {e}")
        else:
            print("Spec Lock Validation: PASS")

        if warnings:
            for w in warnings:
                print(f"  [WARN]  {w}")

        if not errors and not warnings:
            print(f"  All {len(REQUIRED_SECTIONS)} required sections present with data")

    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate spec_lock.md structure")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    return validate_spec_lock(args.project_path, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
