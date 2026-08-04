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


def _cli_main() -> int:
    """Run the export and emit one non-sensitive pptx_export trace event.

    The first positional argument is the project path (wrapper CLI contract).
    Best-effort trace write (never blocks/alters the export result).
    """
    import sys as _sys
    import time
    from pathlib import Path

    project_path = next(
        (token for token in _sys.argv[1:] if not token.startswith("-")),
        None,
    )
    started = time.perf_counter()
    rc = main()
    duration_ms = int((time.perf_counter() - started) * 1000)
    if project_path:
        try:
            from dashboard.trace_writer import trace_event
        except ImportError:
            return rc
        trace_event(
            project_path,
            "pptx_export",
            f"export rc={rc}",
            operation="pptx_export",
            status="PASS" if rc == 0 else "FAIL",
            duration_ms=duration_ms,
            step=7,
            error_code=None if rc == 0 else f"EXPORT_RC_{rc}",
        )
    return rc


if __name__ == '__main__':
    # Propagate the CLI exit code: pptx_cli.main returns 0/1 and prints errors
    # to stderr, so a bare call would silently mask every failure as rc=0.
    raise SystemExit(_cli_main())
