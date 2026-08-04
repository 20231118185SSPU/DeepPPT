#!/usr/bin/env python3
"""PPT Master - OfficeCLI Pinned Runtime Installer

Downloads, verifies, and installs the exact OfficeCLI version declared in
``assets/officecli-lock.json`` into the gitignored ``.tools/officecli/`` tree.
Never uses PATH fallback, upstream shell pipes, or automatic upgrades.

Usage:
    python3 scripts/install_officecli.py install [--json]
    python3 scripts/install_officecli.py check [--json]
    python3 scripts/install_officecli.py path [--json]

Dependencies:
    None (stdlib only). Requires network access for install.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform as _platform
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional
from urllib.request import urlopen


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_LOCK_PATH = _SCRIPT_DIR / "assets" / "officecli-lock.json"
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent  # DeepPPT2 repo root


def _load_lock() -> dict[str, Any]:
    """Load and minimally validate the lock manifest."""
    with open(_LOCK_PATH, "r", encoding="utf-8") as fh:
        lock = json.load(fh)
    if lock.get("schema") != "ppt_master.officecli_lock.v1":
        raise SystemExit(
            f"Unknown lock schema: {lock.get('schema', '<missing>')}"
        )
    if not lock.get("version"):
        raise SystemExit("Lock manifest missing version field")
    return lock


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------
def _detect_platform(lock: dict[str, Any]) -> str:
    """Return the platform key matching the current host (e.g. ``windows-x86_64``).

    Raises ``SystemExit`` with non-zero for unsupported platforms.
    """
    system = _platform.system().lower()
    machine = _platform.machine().lower()

    # Normalize machine names
    if machine in ("amd64", "x86_64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise SystemExit(
            f"Unsupported machine architecture: {machine}. "
            f"Supported: x86_64, arm64"
        )

    if system == "windows":
        key = f"windows-{arch}"
    elif system == "linux":
        # Detect Alpine / musl
        if _is_alpine():
            key = f"linux-alpine-{arch}"
        else:
            key = f"linux-{arch}"
    elif system == "darwin":
        key = f"darwin-{arch}"
    else:
        raise SystemExit(
            f"Unsupported OS: {system}. Supported: windows, linux, darwin"
        )

    platforms = lock.get("platforms", {})
    if key not in platforms:
        raise SystemExit(
            f"No platform entry for '{key}' in lock manifest. "
            f"Available: {', '.join(sorted(platforms.keys()))}"
        )
    return key


def _is_alpine() -> bool:
    """Return True when running on Alpine Linux (musl)."""
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as fh:
            content = fh.read().lower()
        return "alpine" in content
    except OSError:
        pass
    # Fallback: check for musl libc
    try:
        result = subprocess.run(
            ["ldd", "/bin/sh"], capture_output=True, text=True, timeout=5
        )
        return "musl" in result.stdout.lower()
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Install paths
# ---------------------------------------------------------------------------
def _install_dir(lock: dict[str, Any]) -> Path:
    """Return the versioned install directory."""
    return _REPO_ROOT / lock["install_root"] / lock["version"]


def _binary_path(lock: dict[str, Any], platform_key: str) -> Path:
    """Return the full path to the installed binary."""
    plat = lock["platforms"][platform_key]
    return _install_dir(lock) / platform_key / plat["executable"]


def _downloads_dir() -> Path:
    """Return the downloads staging directory."""
    return _REPO_ROOT / ".tools" / "officecli" / ".downloads"


# ---------------------------------------------------------------------------
# Install command
# ---------------------------------------------------------------------------
def _hash_file(path: Path) -> str:
    """Compute SHA-256 of a file."""
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _install(lock: dict[str, Any], platform_key: str, json_output: bool) -> int:
    """Download and install the pinned OfficeCLI binary."""
    plat = lock["platforms"][platform_key]
    version = lock["version"]
    expected_sha = plat["sha256"]
    url = plat["url"]
    exe_name = plat["executable"]

    version_dir = _install_dir(lock) / platform_key
    binary = version_dir / exe_name
    downloads = _downloads_dir()
    downloads.mkdir(parents=True, exist_ok=True)

    # Download to temporary file
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(downloads), prefix="officecli-", suffix=".download"
    )
    os.close(tmp_fd)
    tmp_file = Path(tmp_path)

    try:
        # Download with progress to stderr
        if not json_output:
            print(f"Downloading {url}", file=sys.stderr)
        with urlopen(url) as response:
            with open(tmp_file, "wb") as fh:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    fh.write(chunk)

        # Verify checksum
        actual_sha = _hash_file(tmp_file)
        if actual_sha.lower() != expected_sha.lower():
            tmp_file.unlink(missing_ok=True)
            msg = (
                f"Checksum mismatch for {plat['asset']}\n"
                f"  expected: {expected_sha}\n"
                f"  actual:   {actual_sha}"
            )
            if json_output:
                print(json.dumps({
                    "success": False,
                    "error_code": "OFFICECLI_CHECKSUM_MISMATCH",
                    "message": msg,
                    "expected_sha256": expected_sha,
                    "actual_sha256": actual_sha,
                }))
            else:
                print(msg, file=sys.stderr)
            return 1

        # Publish to version directory
        version_dir.mkdir(parents=True, exist_ok=True)

        # Set executable bit on Unix
        if _platform.system().lower() != "windows":
            os.chmod(tmp_file, tmp_file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        # Atomic rename (same volume)
        try:
            tmp_file.replace(binary)
        except OSError:
            # Cross-volume fallback
            shutil.move(str(tmp_file), str(binary))
            tmp_file = Path(str(binary))  # tmp_file no longer exists

        # Verify installed binary reports correct version
        result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_output = result.stdout.strip()
        if version_output != version:
            binary.unlink(missing_ok=True)
            msg = (
                f"Installed binary reports wrong version: "
                f"expected '{version}', got '{version_output}'"
            )
            if json_output:
                print(json.dumps({
                    "success": False,
                    "error_code": "OFFICECLI_VERSION_MISMATCH",
                    "message": msg,
                    "expected_version": version,
                    "actual_version": version_output,
                }))
            else:
                print(msg, file=sys.stderr)
            return 1

        # Success
        if json_output:
            print(json.dumps({
                "success": True,
                "version": version,
                "platform": platform_key,
                "path": str(binary),
                "sha256": expected_sha,
            }))
        else:
            print(f"OfficeCLI {version} installed to {binary}")
        return 0

    except Exception as exc:
        tmp_file.unlink(missing_ok=True)
        msg = f"Install failed: {exc}"
        if json_output:
            print(json.dumps({
                "success": False,
                "error_code": "OFFICECLI_COMMAND_FAILED",
                "message": msg,
            }))
        else:
            print(msg, file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# Check command (read-only, no network)
# ---------------------------------------------------------------------------
def _check(lock: dict[str, Any], platform_key: str, json_output: bool) -> int:
    """Check that the pinned binary is installed and correct."""
    plat = lock["platforms"][platform_key]
    version = lock["version"]
    expected_sha = plat["sha256"]
    binary = _binary_path(lock, platform_key)

    def _error(code: str, msg: str) -> int:
        if json_output:
            print(json.dumps({
                "success": False,
                "error_code": code,
                "message": msg,
                "expected_version": version,
                "expected_sha256": expected_sha,
                "platform": platform_key,
            }))
        else:
            print(msg, file=sys.stderr)
        return 1

    if not binary.is_file():
        return _error(
            "OFFICECLI_NOT_INSTALLED",
            f"OfficeCLI {version} is not installed.\n"
            f"Run: python skills/ppt-master/scripts/install_officecli.py install",
        )

    # Verify checksum
    actual_sha = _hash_file(binary)
    if actual_sha.lower() != expected_sha.lower():
        return _error(
            "OFFICECLI_CHECKSUM_MISMATCH",
            f"Installed binary checksum mismatch.\n"
            f"  expected: {expected_sha}\n"
            f"  actual:   {actual_sha}\n"
            f"Reinstall with: python skills/ppt-master/scripts/install_officecli.py install",
        )

    # Verify version
    try:
        result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        installed_version = result.stdout.strip()
    except Exception:
        return _error(
            "OFFICECLI_COMMAND_FAILED",
            f"Failed to run installed binary at {binary}",
        )

    if installed_version != version:
        return _error(
            "OFFICECLI_VERSION_MISMATCH",
            f"Installed binary version mismatch: "
            f"expected '{version}', got '{installed_version}'",
        )

    if json_output:
        print(json.dumps({
            "success": True,
            "version": version,
            "platform": platform_key,
            "path": str(binary),
            "sha256": actual_sha,
            "status": "ready",
        }))
    else:
        print(f"OfficeCLI {version} ready at {binary}")
    return 0


# ---------------------------------------------------------------------------
# Path command
# ---------------------------------------------------------------------------
def _path(lock: dict[str, Any], platform_key: str, json_output: bool) -> int:
    """Print install path for the pinned binary."""
    binary = _binary_path(lock, platform_key)
    plat = lock["platforms"][platform_key]

    if json_output:
        print(json.dumps({
            "path": str(binary),
            "exists": binary.is_file(),
            "version": lock["version"],
            "platform": platform_key,
        }))
    else:
        print(str(binary))
    return 0 if binary.is_file() else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install and verify the pinned OfficeCLI runtime",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        dest="json_output",
        help="Output machine-readable JSON",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("install", help="Download and install the pinned binary")
    sub.add_parser("check", help="Verify installed binary (no network)")
    sub.add_parser("path", help="Print the expected binary path")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        lock = _load_lock()
    except Exception as exc:
        if args.json_output:
            print(json.dumps({
                "success": False,
                "error_code": "OFFICECLI_COMMAND_FAILED",
                "message": f"Failed to load lock file: {exc}",
            }))
        else:
            print(f"Failed to load lock file: {exc}", file=sys.stderr)
        return 1

    try:
        platform_key = _detect_platform(lock)
    except SystemExit:
        if args.json_output:
            print(json.dumps({
                "success": False,
                "error_code": "OFFICECLI_UNSUPPORTED_PLATFORM",
                "message": "Current platform is not supported by the lock manifest",
            }))
        else:
            print(
                "Current platform is not supported by the lock manifest.",
                file=sys.stderr,
            )
        return 1

    if args.command == "install":
        return _install(lock, platform_key, args.json_output)
    elif args.command == "check":
        return _check(lock, platform_key, args.json_output)
    elif args.command == "path":
        return _path(lock, platform_key, args.json_output)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
