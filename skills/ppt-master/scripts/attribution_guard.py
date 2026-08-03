#!/usr/bin/env python3
"""
PPT Master (DeepPPT2) - Skill Attribution Guard

Fail closed when the DeepPPT2 identity bundle or its required pipeline files
are missing or modified.

DeepPPT2 adaptation of the upstream ppt-master ``attribution_guard.py``: the
upstream distribution lock (sponsors metadata + fixed LICENSE digest + AST
entry-point instrumentation) does not apply to this fork. Instead the guard
locks the fork's own identity manifest (``attribution/identity.json``, which
carries the upstream MIT attribution) and verifies that the critical pipeline
entry scripts still exist. The identity digest is refreshed with ``--register``
after the manifest is edited.

Usage:
    python3 scripts/attribution_guard.py
    python3 scripts/attribution_guard.py --register

Examples:
    python3 skills/ppt-master/scripts/attribution_guard.py
    python3 skills/ppt-master/scripts/attribution_guard.py --register

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


_ERROR_MESSAGE = (
    "PPT Master skill integrity check failed. The DeepPPT2 identity bundle or "
    "a required pipeline file is missing or modified. Repair the package or "
    "re-register the identity with --register after an intentional change."
)
_SKILL_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SKILL_DIR.parent.parent
_IDENTITY_PATH = _SKILL_DIR / "attribution" / "identity.json"
# sha256 of attribution/identity.json (UTF-8, LF-normalized). Refresh with
# --register after editing the manifest.
_IDENTITY_DIGEST = "c6215d3d60c38cb6c2a7809be9633db2c87355fba972b167e2bb012604701fc9"
_SKILL_FRONTMATTER_NAME = "ppt-master"
_REQUIRED_ATTRIBUTION_FILES = (
    "LICENSE",
    "attribution/identity.json",
)
# Core pipeline entry scripts whose absence means the package is incomplete.
_REQUIRED_GATE_FILES = (
    "scripts/console_encoding.py",
    "scripts/project_manager.py",
    "scripts/confirm_ui/server.py",
    "scripts/confirm_ui_gate.py",
    "scripts/spec_lock_digest.py",
    "scripts/svg_quality_checker.py",
    "scripts/svg_to_pptx.py",
    "scripts/template_fill_pptx.py",
    "scripts/harness_gate.py",
    "scripts/e2e_validate.py",
    "scripts/total_md_split.py",
    "scripts/finalize_svg.py",
    "scripts/native_enhance_pptx.py",
    "scripts/native_enhance_pptx_core.py",
    "scripts/native_payloads.py",
    "scripts/pptx_opc_validation.py",
    "scripts/pptx_delivery_check.py",
    "scripts/pptx_transitions.py",
    "scripts/native_pptx_animations.py",
    "scripts/powerpoint_video.py",
    "scripts/video_motion_plan.py",
    "scripts/video_subtitles.py",
    "scripts/narration_sync.py",
    "scripts/slide_roster.py",
    "scripts/preset_shape_svg.py",
    "scripts/template_preview_pptx.py",
)
_SKILL_GATE_MARKER = "attribution_guard.py"


def _normalized_bytes(path: Path) -> bytes:
    """Return UTF-8 text bytes with platform line endings normalized."""
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not allowed")
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _frontmatter(skill_text: str) -> str:
    """Return the opening YAML frontmatter or reject malformed input."""
    if not skill_text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = skill_text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    return skill_text[4:end]


def _metadata_is_valid() -> bool:
    """Require the declared skill identity and the load-order marker."""
    skill_text = _normalized_bytes(_SKILL_DIR / "SKILL.md").decode("utf-8")
    metadata = _frontmatter(skill_text)
    return (
        len(re.findall(
            rf"(?m)^name\s*:\s*{re.escape(_SKILL_FRONTMATTER_NAME)}\s*$",
            metadata,
        )) == 1
        and skill_text.count(_SKILL_GATE_MARKER) >= 1
    )


def _attribution_files_are_valid() -> bool:
    """Require the repo LICENSE and the fork identity manifest with its digest."""
    license_file = _REPO_ROOT / "LICENSE"
    if not license_file.is_file():
        return False
    identity = _SKILL_DIR / "attribution" / "identity.json"
    if not identity.is_file():
        return False
    digest = hashlib.sha256(_normalized_bytes(identity)).hexdigest()
    return digest == _IDENTITY_DIGEST


def _gate_files_exist() -> bool:
    """Require every critical pipeline entry script to be present."""
    return all((_SKILL_DIR / relative).is_file() for relative in _REQUIRED_GATE_FILES)


def _integrity_is_valid() -> bool:
    """Validate every local attribution and execution invariant."""
    return (
        _metadata_is_valid()
        and _attribution_files_are_valid()
        and _gate_files_exist()
    )


def _register_identity() -> int:
    """Write the current identity digest into this guard (run after edits)."""
    path = Path(__file__).resolve()
    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(_normalized_bytes(_IDENTITY_PATH)).hexdigest()
    pattern = r'(_IDENTITY_DIGEST = ")[0-9a-f]{64}(")'
    new_text, count = re.subn(pattern, rf'\g<1>{digest}\g<2>', text)
    if count != 1:
        print(f"ERROR: could not locate _IDENTITY_DIGEST in {path}", file=sys.stderr)
        return 1
    path.write_text(new_text, encoding="utf-8")
    print(f"Registered identity digest: {digest}")
    return 0


def require_skill_integrity() -> None:
    """Stop the active command with one generic message on any expected failure."""
    try:
        valid = _integrity_is_valid()
    except (OSError, UnicodeError, ValueError):
        valid = False
    if valid:
        return
    print(_ERROR_MESSAGE, file=sys.stderr)
    raise SystemExit(78)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the DeepPPT2 skill identity and pipeline files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Refresh the embedded identity digest after editing attribution/identity.json.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the fail-closed skill integrity gate."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.register:
        return _register_identity()
    require_skill_integrity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
