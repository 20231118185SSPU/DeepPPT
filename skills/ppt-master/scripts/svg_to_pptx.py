#!/usr/bin/env python3
"""
PPT Master - SVG to PPTX Tool

Exports PPT Master SVG pages to a native editable PPTX through the
svg_to_pptx package while keeping this wrapper for CLI backward compatibility.

Usage:
    python3 scripts/svg_to_pptx.py <project_path> [options]

Examples:
    python3 scripts/svg_to_pptx.py <project_path>

Dependencies:
    Internal svg_to_pptx package and its PPTX conversion dependencies.
"""

import sys
from pathlib import Path

# Ensure the scripts directory is on sys.path so the package can be found
sys.path.insert(0, str(Path(__file__).resolve().parent))

from svg_to_pptx import main

if __name__ == '__main__':
    main()
