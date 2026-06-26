#!/usr/bin/env python3
"""
PPT Master - spec_lock Integrity Guard

Generates and verifies a SHA-256 digest for spec_lock.md to detect
unintended modifications between the Strategist phase (Step 4) and
the Executor phase (Step 6).

Usage:
    python3 scripts/spec_lock_digest.py generate <project_path>
    python3 scripts/spec_lock_digest.py verify <project_path>
    python3 scripts/spec_lock_digest.py show <project_path>

Examples:
    python3 scripts/spec_lock_digest.py generate projects/my_deck_ppt169_20260626
    python3 scripts/spec_lock_digest.py verify projects/my_deck_ppt169_20260626

Dependencies:
    None (only uses standard library)

Notes:
    - The digest file (.spec_lock.digest) is stored in the project root
    - generate: computes SHA-256 of spec_lock.md, writes .spec_lock.digest
    - verify: recomputes hash, compares with stored value, exits non-zero on mismatch
    - show: prints the stored digest metadata without verification
"""

import sys
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DIGEST_FILENAME = ".spec_lock.digest"
SPEC_LOCK_FILENAME = "spec_lock.md"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_path(project_path: Path) -> Path:
    """Return the path to the .spec_lock.digest file."""
    return project_path / DIGEST_FILENAME


def spec_lock_path(project_path: Path) -> Path:
    """Return the path to spec_lock.md."""
    return project_path / SPEC_LOCK_FILENAME


def generate_digest(project_path: Path) -> int:
    """Compute and store the spec_lock.md digest."""
    lock_file = spec_lock_path(project_path)
    if not lock_file.is_file():
        print(f"Error: {lock_file} not found.", file=sys.stderr)
        return 1

    sha256 = compute_sha256(lock_file)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    data = {
        "spec_lock_sha256": sha256,
        "generated_at": now,
        "source": str(lock_file.name),
    }

    out_path = digest_path(project_path)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Digest generated: {sha256}", file=sys.stderr)
    print(f"Stored in: {out_path}", file=sys.stderr)
    return 0


def verify_digest(project_path: Path) -> int:
    """Verify spec_lock.md matches the stored digest."""
    lock_file = spec_lock_path(project_path)
    if not lock_file.is_file():
        print(f"Error: {lock_file} not found.", file=sys.stderr)
        return 1

    dig_file = digest_path(project_path)
    if not dig_file.is_file():
        print(
            f"Error: {dig_file} not found. "
            "Run 'generate' first to create a baseline.",
            file=sys.stderr,
        )
        return 1

    with open(dig_file, "r", encoding="utf-8") as f:
        stored = json.load(f)

    expected = stored.get("spec_lock_sha256", "")
    if not expected:
        print("Error: digest file is missing 'spec_lock_sha256' field.", file=sys.stderr)
        return 1

    actual = compute_sha256(lock_file)

    if actual == expected:
        print(f"OK: spec_lock.md integrity verified (sha256: {actual[:16]}...)", file=sys.stderr)
        return 0
    else:
        print(
            f"MISMATCH: spec_lock.md has been modified since digest was generated.\n"
            f"  Expected: {expected}\n"
            f"  Actual:   {actual}\n"
            f"  Generated at: {stored.get('generated_at', 'unknown')}\n"
            f"\n"
            f"If the change was intentional, re-run 'generate' to update the digest.",
            file=sys.stderr,
        )
        return 2


def show_digest(project_path: Path) -> int:
    """Print the stored digest metadata."""
    dig_file = digest_path(project_path)
    if not dig_file.is_file():
        print(f"Error: {dig_file} not found. No digest has been generated.", file=sys.stderr)
        return 1

    with open(dig_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and verify spec_lock.md integrity digests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate", help="Compute and store spec_lock.md digest")
    gen.add_argument("project_path", help="Path to the project directory")

    ver = sub.add_parser("verify", help="Verify spec_lock.md against stored digest")
    ver.add_argument("project_path", help="Path to the project directory")

    sho = sub.add_parser("show", help="Print stored digest metadata")
    sho.add_argument("project_path", help="Path to the project directory")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    project = Path(args.project_path)
    if not project.is_dir():
        print(f"Error: project directory not found: {project}", file=sys.stderr)
        return 1

    if args.command == "generate":
        return generate_digest(project)
    elif args.command == "verify":
        return verify_digest(project)
    elif args.command == "show":
        return show_digest(project)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
