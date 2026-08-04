#!/usr/bin/env python3
"""PPT Master - OfficeCLI Bridge Layer

Typed, zero-shell interface to the pinned OfficeCLI binary. Never uses
``shell=True``, PATH fallback, or raw command-string concatenation.

Usage:
    import officecli_bridge
    runtime = officecli_bridge.probe_officecli()
    result = officecli_bridge.validate_office_file(Path("deck.pptx"))

Dependencies:
    ``install_officecli.py`` (same directory) for binary resolution.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, Sequence

# ---------------------------------------------------------------------------
# Stable error codes
# ---------------------------------------------------------------------------
OFFICECLI_NOT_INSTALLED = "OFFICECLI_NOT_INSTALLED"
OFFICECLI_VERSION_MISMATCH = "OFFICECLI_VERSION_MISMATCH"
OFFICECLI_CHECKSUM_MISMATCH = "OFFICECLI_CHECKSUM_MISMATCH"
OFFICECLI_UNSUPPORTED_PLATFORM = "OFFICECLI_UNSUPPORTED_PLATFORM"
OFFICECLI_TIMEOUT = "OFFICECLI_TIMEOUT"
OFFICECLI_INVALID_JSON = "OFFICECLI_INVALID_JSON"
OFFICECLI_COMMAND_FAILED = "OFFICECLI_COMMAND_FAILED"
OFFICECLI_PLAN_INVALID = "OFFICECLI_PLAN_INVALID"
OFFICECLI_PLAN_STALE = "OFFICECLI_PLAN_STALE"
OFFICECLI_TARGET_MISSING = "OFFICECLI_TARGET_MISSING"
OFFICECLI_BATCH_ROLLED_BACK = "OFFICECLI_BATCH_ROLLED_BACK"
OFFICECLI_VALIDATION_FAILED = "OFFICECLI_VALIDATION_FAILED"
OFFICECLI_PREVIEW_UNAVAILABLE = "OFFICECLI_PREVIEW_UNAVAILABLE"
OFFICECLI_VISUAL_REVIEW_REQUIRED = "OFFICECLI_VISUAL_REVIEW_REQUIRED"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------
@dataclass
class OfficeCliRuntime:
    """Describes the resolved OfficeCLI runtime."""
    path: str
    expected_version: str
    actual_version: str
    platform: str
    sha256: str
    status: str  # "ready" | "not_installed" | "version_mismatch" | "checksum_mismatch"


@dataclass
class OfficeCliResult:
    """Result envelope for a single OfficeCLI command invocation."""
    success: bool
    returncode: int
    data: dict[str, object] = field(default_factory=dict)
    message: str = ""
    duration_ms: int = 0
    error_code: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent


def _load_lock() -> dict[str, Any]:
    """Load the lock manifest."""
    lock_path = _SCRIPT_DIR / "assets" / "officecli-lock.json"
    with open(lock_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _get_binary_path() -> Optional[Path]:
    """Return the pinned binary path if installed, else None."""
    lock = _load_lock()
    version = lock["version"]
    install_root = lock["install_root"]
    repo_root = _SCRIPT_DIR.parent.parent.parent
    version_dir = repo_root / install_root / version

    if not version_dir.exists():
        return None

    # Find the first platform subdirectory with the executable
    for plat_dir in sorted(version_dir.iterdir()):
        if not plat_dir.is_dir():
            continue
        plat = lock.get("platforms", {}).get(plat_dir.name)
        if plat is None:
            continue
        exe_path = plat_dir / plat["executable"]
        if exe_path.is_file():
            return exe_path

    return None


def _run(
    binary: Path,
    args: Sequence[str],
    *,
    timeout_s: float,
) -> OfficeCliResult:
    """Execute a single OfficeCLI command with JSON envelope parsing."""
    cmd = [str(binary)] + list(args)
    env = os.environ.copy()
    env.setdefault("OFFICECLI_NO_AUTO_RESIDENT", "1")

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        return OfficeCliResult(
            success=False,
            returncode=-1,
            message="Command timed out",
            duration_ms=duration_ms,
            error_code=OFFICECLI_TIMEOUT,
        )
    except FileNotFoundError:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        return OfficeCliResult(
            success=False,
            returncode=-1,
            message=f"Binary not found: {binary}",
            duration_ms=duration_ms,
            error_code=OFFICECLI_NOT_INSTALLED,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        return OfficeCliResult(
            success=False,
            returncode=-1,
            message=f"Subprocess error: {exc}",
            duration_ms=duration_ms,
            error_code=OFFICECLI_COMMAND_FAILED,
        )

    duration_ms = int((time.perf_counter() - t0) * 1000)

    # Parse JSON envelope from stdout
    data: dict[str, object] = {}
    parsed_ok = False
    if proc.stdout.strip():
        try:
            data = json.loads(proc.stdout)
            parsed_ok = True
        except json.JSONDecodeError:
            pass

    # Error classification
    if not parsed_ok and proc.stdout.strip():
        return OfficeCliResult(
            success=False,
            returncode=proc.returncode,
            message=f"Failed to parse JSON output. stdout preview: {proc.stdout[:200]}",
            duration_ms=duration_ms,
            error_code=OFFICECLI_INVALID_JSON,
        )

    # If JSON was parsed, check OfficeCLI envelope
    if parsed_ok:
        envelope_success = data.get("success")
        if envelope_success is False or proc.returncode != 0:
            return OfficeCliResult(
                success=False,
                returncode=proc.returncode,
                data=data,
                message=data.get("message", proc.stderr.strip() or "Command failed"),
                duration_ms=duration_ms,
                error_code=OFFICECLI_COMMAND_FAILED,
            )
        return OfficeCliResult(
            success=True,
            returncode=proc.returncode,
            data=data,
            message=data.get("message", ""),
            duration_ms=duration_ms,
            error_code=None,
        )

    # No JSON output — fall back to returncode
    if proc.returncode != 0:
        return OfficeCliResult(
            success=False,
            returncode=proc.returncode,
            message=proc.stderr.strip() or "Command failed with non-zero exit",
            duration_ms=duration_ms,
            error_code=OFFICECLI_COMMAND_FAILED,
        )

    return OfficeCliResult(
        success=True,
        returncode=proc.returncode,
        data={},
        message="",
        duration_ms=duration_ms,
        error_code=None,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def resolve_officecli() -> Path:
    """Return the absolute path to the pinned OfficeCLI binary.

    Raises ``FileNotFoundError`` if not installed.
    """
    binary = _get_binary_path()
    if binary is None:
        raise FileNotFoundError(
            "OfficeCLI is not installed. Run: "
            "python skills/ppt-master/scripts/install_officecli.py install"
        )
    return binary


def probe_officecli() -> OfficeCliRuntime:
    """Probe the installed runtime and return its metadata.

    Does not require network access.
    """
    lock = _load_lock()
    version = lock["version"]
    binary = _get_binary_path()

    if binary is None:
        # Try to detect platform for informational purposes
        import platform as _plat
        try:
            from install_officecli import _detect_platform
            plat_key = _detect_platform(lock)
        except Exception:
            plat_key = "unknown"
        plat_entry = lock.get("platforms", {}).get(plat_key, {})
        return OfficeCliRuntime(
            path="",
            expected_version=version,
            actual_version="",
            platform=plat_key,
            sha256=plat_entry.get("sha256", ""),
            status="not_installed",
        )

    # Compute checksum
    import hashlib
    sha = hashlib.sha256()
    with open(binary, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    actual_sha = sha.hexdigest()
    expected_sha = ""
    for plat in lock.get("platforms", {}).values():
        if plat["sha256"].lower() == actual_sha.lower():
            expected_sha = plat["sha256"]
            break
    if not expected_sha:
        # Find platform key by executable name match
        for plat in lock.get("platforms", {}).values():
            if binary.name == plat["executable"]:
                expected_sha = plat["sha256"]
                break

    # Platform key from binary parent dir
    plat_key = binary.parent.name

    # Get actual version
    actual_version = ""
    try:
        result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        actual_version = result.stdout.strip()
    except Exception:
        pass

    # Determine status
    if actual_version != version:
        status = "version_mismatch"
    elif actual_sha.lower() != expected_sha.lower():
        status = "checksum_mismatch"
    else:
        status = "ready"

    return OfficeCliRuntime(
        path=str(binary),
        expected_version=version,
        actual_version=actual_version,
        platform=plat_key,
        sha256=actual_sha,
        status=status,
    )


def run_officecli(
    args: Sequence[str],
    *,
    input_json: object = None,
    timeout_s: float = 60.0,
) -> OfficeCliResult:
    """Run an OfficeCLI command with the pinned binary.

    Args:
        args: Positional arguments (e.g. ``["view", "deck.pptx", "stats", "--json"]``).
        input_json: Optional data sent via stdin.
        timeout_s: Command timeout in seconds.

    Returns:
        ``OfficeCliResult`` with success, data, and error classification.
    """
    binary = resolve_officecli()
    cmd = [str(binary)] + list(args)

    env = os.environ.copy()
    env.setdefault("OFFICECLI_NO_AUTO_RESIDENT", "1")

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            input=json.dumps(input_json) if input_json is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        return OfficeCliResult(
            success=False,
            returncode=-1,
            message="Command timed out",
            duration_ms=duration_ms,
            error_code=OFFICECLI_TIMEOUT,
        )
    except FileNotFoundError:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        return OfficeCliResult(
            success=False,
            returncode=-1,
            message=f"Binary not found: {binary}",
            duration_ms=duration_ms,
            error_code=OFFICECLI_NOT_INSTALLED,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        return OfficeCliResult(
            success=False,
            returncode=-1,
            message=f"Subprocess error: {exc}",
            duration_ms=duration_ms,
            error_code=OFFICECLI_COMMAND_FAILED,
        )

    duration_ms = int((time.perf_counter() - t0) * 1000)

    # Parse JSON envelope
    data: dict[str, object] = {}
    parsed_ok = False
    if proc.stdout.strip():
        try:
            data = json.loads(proc.stdout)
            parsed_ok = True
        except json.JSONDecodeError:
            pass

    if not parsed_ok and proc.stdout.strip():
        return OfficeCliResult(
            success=False,
            returncode=proc.returncode,
            message=f"Invalid JSON: {proc.stdout[:200]}",
            duration_ms=duration_ms,
            error_code=OFFICECLI_INVALID_JSON,
        )

    if parsed_ok:
        if data.get("success") is False or proc.returncode != 0:
            return OfficeCliResult(
                success=False,
                returncode=proc.returncode,
                data=data,
                message=data.get("message", proc.stderr.strip() or "Command failed"),
                duration_ms=duration_ms,
                error_code=OFFICECLI_COMMAND_FAILED,
            )
        return OfficeCliResult(
            success=True,
            returncode=proc.returncode,
            data=data,
            message=data.get("message", ""),
            duration_ms=duration_ms,
            error_code=None,
        )

    if proc.returncode != 0:
        return OfficeCliResult(
            success=False,
            returncode=proc.returncode,
            message=proc.stderr.strip() or "Non-zero exit",
            duration_ms=duration_ms,
            error_code=OFFICECLI_COMMAND_FAILED,
        )

    return OfficeCliResult(
        success=True,
        returncode=0,
        data={},
        message="",
        duration_ms=duration_ms,
        error_code=None,
    )


def run_atomic_batch(
    file: Path,
    commands: Sequence[Mapping[str, object]],
    *,
    timeout_s: float = 120.0,
) -> OfficeCliResult:
    """Apply a sequence of mutations as a single atomic batch.

    Commands are sent via stdin JSON. If any item fails, OfficeCLI
    rolls back the entire batch. ``--best-effort`` is never used.

    Args:
        file: Path to the PPTX/DOCX/XLSX file to mutate.
        commands: List of command objects, each with at least ``command``,
            ``path``, and ``props`` keys.
        timeout_s: Command timeout in seconds.

    Returns:
        ``OfficeCliResult``.
    """
    binary = resolve_officecli()

    try:
        result = run_officecli(
            ["batch", str(file), "--json"],
            input_json=commands,  # raw array, not wrapped
            timeout_s=timeout_s,
        )
    except Exception as exc:
        return OfficeCliResult(
            success=False,
            returncode=-1,
            message=f"Batch execution error: {exc}",
            duration_ms=0,
            error_code=OFFICECLI_COMMAND_FAILED,
        )

    if not result.success:
        # Check if OfficeCLI reported atomic rollback
        rollback = result.data.get("atomicRolledBack")
        if rollback is True:
            result.error_code = OFFICECLI_BATCH_ROLLED_BACK
            result.message = result.data.get("message", "Batch rolled back")
    return result


def validate_office_file(file: Path) -> OfficeCliResult:
    """Run OfficeCLI validate on a file.

    Args:
        file: Path to the file to validate.

    Returns:
        ``OfficeCliResult``. On validation errors, ``error_code`` is
        ``OFFICECLI_VALIDATION_FAILED``.
    """
    result = run_officecli(
        ["validate", str(file), "--json"],
        timeout_s=60.0,
    )
    if not result.success:
        result.error_code = OFFICECLI_VALIDATION_FAILED
    return result


def inspect_office_file(
    file: Path,
    *,
    detail: str = "summary",
) -> dict[str, object]:
    """Return a read-only inspection summary of an Office file.

    Args:
        file: Path to the file to inspect.
        detail: ``"summary"`` for stats/outline/issues; ``"full"`` for
            per-element depth-limited inspection.

    Returns:
        Dict with keys determined by detail level.
    """
    result: dict[str, object] = {
        "path": str(file),
        "format": file.suffix.lstrip("."),
        "inspected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # Stats
    stats_result = run_officecli(
        ["view", str(file), "stats", "--json"],
        timeout_s=30.0,
    )
    if stats_result.success:
        result["stats"] = stats_result.data
    else:
        result["stats_error"] = stats_result.message

    # Outline
    outline_result = run_officecli(
        ["view", str(file), "outline", "--json"],
        timeout_s=30.0,
    )
    if outline_result.success:
        result["outline"] = outline_result.data
    else:
        result["outline_error"] = outline_result.message

    # Issues
    issues_result = run_officecli(
        ["view", str(file), "issues", "--json"],
        timeout_s=30.0,
    )
    if issues_result.success:
        result["issues"] = issues_result.data
    else:
        result["issues_error"] = issues_result.message

    if detail == "full":
        # Additional depth-limited per-slide/section inspection
        result["elements"] = []
        # For PPTX: get slide-level details
        outline = result.get("outline", {})
        if isinstance(outline, dict):
            slides = outline.get("slides", [])
            if isinstance(slides, list):
                for idx in range(1, min(len(slides) + 1, 50)):
                    slide_result = run_officecli(
                        ["get", str(file), f"/slide[{idx}]", "--depth", "2", "--json"],
                        timeout_s=15.0,
                    )
                    if slide_result.success:
                        result["elements"].append(slide_result.data)  # type: ignore[attr-defined]

    return result
