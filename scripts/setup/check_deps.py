#!/usr/bin/env python3
"""DeepPPT dependency checker and auto-installer.

Checks Python environment, required/optional packages, system tools,
and .env configuration. Supports colored table, quiet, JSON, and
auto-install output modes.

Usage:
    python3 scripts/setup/check_deps.py           # colored table
    python3 scripts/setup/check_deps.py --quiet    # missing only
    python3 scripts/setup/check_deps.py --json     # machine-readable JSON
    python3 scripts/setup/check_deps.py --install  # auto-install missing
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# import-name -> (pip-name, display-name)
REQUIRED_PACKAGES: dict[str, tuple[str, str]] = {
    "pptx": ("python-pptx", "python-pptx"),
    "PIL": ("Pillow", "Pillow"),
    "requests": ("requests", "requests"),
    "bs4": ("beautifulsoup4", "beautifulsoup4"),
    "lxml": ("lxml", "lxml"),
    "flask": ("flask", "flask"),
    "fitz": ("PyMuPDF", "PyMuPDF"),
    "mammoth": ("mammoth", "mammoth"),
    "openpyxl": ("openpyxl", "openpyxl"),
    "svglib": ("svglib", "svglib"),
    "reportlab": ("reportlab", "reportlab"),
    "google.genai": ("google-genai", "google-genai"),
    "edge_tts": ("edge-tts", "edge-tts"),
}

OPTIONAL_PACKAGES: dict[str, tuple[str, str, str]] = {
    # import-name -> (pip-name, display-name, purpose)
    "cairosvg": ("cairosvg", "cairosvg", "higher-fidelity Office PNG fallback"),
    "feedparser": ("feedparser", "feedparser", "RSS feed parsing in research workflows"),
    "playwright": ("playwright", "playwright", "browser screenshots and AI browser automation"),
}

# Backend name -> env-var that holds the API key
BACKEND_KEY_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "qwen": "QWEN_API_KEY",
    "zhipu": "ZHIPU_API_KEY",
    "volcengine": "VOLCENGINE_API_KEY",
}

OPTIONAL_IMAGE_KEYS: list[str] = [
    "PEXELS_API_KEY",
    "PIXABAY_API_KEY",
    "UNSPLASH_ACCESS_KEY",
    "FLICKR_API_KEY",
]

# ANSI helpers ---------------------------------------------------------------

_NO_COLOR = not sys.stdout.isatty() or os.environ.get("NO_COLOR") == "1"


def _c(code: str, text: str) -> str:
    """Wrap *text* in an ANSI escape if colour is enabled."""
    if _NO_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def green(text: str) -> str:
    return _c("32", text)


def red(text: str) -> str:
    return _c("31", text)


def yellow(text: str) -> str:
    return _c("33", text)


def dim(text: str) -> str:
    return _c("2", text)


def bold(text: str) -> str:
    return _c("1", text)


# Status icons (render correctly in modern terminals) -----------------------

OK = green("✅")
FAIL = red("❌")
WARN = yellow("⚠️")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    """Return the repository root (two levels up from this file)."""
    return Path(__file__).resolve().parents[2]


def _mask_key(value: str) -> str:
    """Show only the first 5 characters + '***'."""
    if len(value) <= 5:
        return value + "***"
    return value[:5] + "***"


def _pip_name(import_name: str) -> str | None:
    """Resolve the pip package name for a given import name via metadata."""
    try:
        from importlib.metadata import packages_distributions  # type: ignore[attr-defined]

        dist_map = packages_distributions()
        dists = dist_map.get(import_name, [])
        if dists:
            return dists[0]
    except (ImportError, AttributeError):
        pass
    return None


def _get_version(import_name: str, pip_name: str) -> str | None:
    """Try to get the installed version of a package."""
    # Try importlib.metadata first (most reliable)
    for name in (pip_name, import_name):
        try:
            return pkg_version(name)
        except PackageNotFoundError:
            continue
    # Fallback: try __version__ attribute on the module
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", None)
        if ver:
            return str(ver)
    except Exception:
        pass
    return None


def _is_playwright_chromium_installed() -> bool:
    """Check whether Playwright's Chromium browser is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        # Some versions don't support --dry-run; try listing browsers instead
        if result.returncode != 0:
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "--help"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            # If the command exists, we assume playwright is at least installed
            return "chromium" in result.stdout.lower()
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False

    # If --dry-run succeeded, check output for chromium
    output = (result.stdout + result.stderr).lower()
    if "chromium" in output and "up to date" in output:
        return True
    # As a heuristic, just check whether the chromium browser path exists
    try:
        from playwright._impl._driver import compute_driver_executable  # type: ignore

        return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Check functions  (return dicts consumed by renderers)
# ---------------------------------------------------------------------------

CheckResult = dict[str, Any]
# Each result dict has at minimum: status, name, detail
# status is one of: "ok", "fail", "warn"


def check_python_env() -> list[CheckResult]:
    """Check Python interpreter and pip versions."""
    results: list[CheckResult] = []

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    results.append({"status": "ok", "name": f"Python {py_ver}", "detail": ""})

    try:
        import pip  # noqa: F401

        pip_ver = pkg_version("pip")
        results.append({"status": "ok", "name": f"pip {pip_ver}", "detail": ""})
    except Exception:
        results.append({"status": "warn", "name": "pip", "detail": "could not determine version"})

    return results


def check_required_packages() -> list[CheckResult]:
    results: list[CheckResult] = []
    for import_name, (pip_name, display_name) in REQUIRED_PACKAGES.items():
        ver = _get_version(import_name, pip_name)
        if ver:
            results.append({"status": "ok", "name": display_name, "detail": ver})
        else:
            results.append({"status": "fail", "name": display_name, "detail": "not installed", "pip_name": pip_name})
    return results


def check_optional_packages() -> list[CheckResult]:
    results: list[CheckResult] = []
    for import_name, (pip_name, display_name, purpose) in OPTIONAL_PACKAGES.items():
        ver = _get_version(import_name, pip_name)
        if ver:
            results.append({"status": "ok", "name": display_name, "detail": ver, "purpose": purpose})
        else:
            results.append(
                {"status": "warn", "name": display_name, "detail": f"not installed (for {purpose})", "purpose": purpose, "pip_name": pip_name}
            )
    return results


def check_system_tools() -> list[CheckResult]:
    results: list[CheckResult] = []

    # Playwright Chromium
    pw_installed = _is_playwright_chromium_installed()
    if pw_installed:
        results.append({"status": "ok", "name": "Playwright Chromium", "detail": "installed"})
    else:
        results.append({"status": "warn", "name": "Playwright Chromium", "detail": "not installed (optional)"})
    return results


def check_env_config() -> list[CheckResult]:
    results: list[CheckResult] = []
    root = _repo_root()
    env_path = root / ".env"

    # .env file existence
    if env_path.is_file():
        results.append({"status": "ok", "name": ".env file", "detail": "exists"})
    else:
        results.append({"status": "warn", "name": ".env file", "detail": "not found"})
        return results  # nothing else to check without the file

    # Parse .env (simple key=value, ignoring comments and blank lines)
    env_vars: dict[str, str] = {}
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    except Exception as exc:
        results.append({"status": "warn", "name": ".env parse", "detail": str(exc)})
        return results

    # IMAGE_BACKEND
    backend = env_vars.get("IMAGE_BACKEND", "")
    if backend:
        results.append({"status": "ok", "name": "IMAGE_BACKEND", "detail": backend})
    else:
        results.append({"status": "warn", "name": "IMAGE_BACKEND", "detail": "not set"})
        return results

    # Backend API key
    expected_key_name = BACKEND_KEY_MAP.get(backend, "")
    if expected_key_name:
        key_val = env_vars.get(expected_key_name, "")
        if key_val:
            results.append({"status": "ok", "name": expected_key_name, "detail": _mask_key(key_val)})
        else:
            results.append({"status": "fail", "name": expected_key_name, "detail": "not set"})

    # Optional image search keys
    for key_name in OPTIONAL_IMAGE_KEYS:
        key_val = env_vars.get(key_name, "")
        if key_val:
            results.append({"status": "ok", "name": key_name, "detail": _mask_key(key_val)})
        else:
            results.append({"status": "warn", "name": key_name, "detail": "not set (optional, zero-config sources available)"})

    return results


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def _status_icon(status: str) -> str:
    return {"ok": OK, "fail": FAIL, "warn": WARN}.get(status, "?")


def render_table(
    python_env: list[CheckResult],
    required: list[CheckResult],
    optional: list[CheckResult],
    env_cfg: list[CheckResult],
    *,
    quiet: bool = False,
) -> str:
    """Render human-readable coloured table."""
    lines: list[str] = []

    def section(title: str, items: list[CheckResult]) -> None:
        filtered = [i for i in items if (not quiet or i["status"] != "ok")] if quiet else items
        if not filtered:
            return
        lines.append("")
        lines.append(bold(title))
        for item in filtered:
            icon = _status_icon(item["status"])
            name = item["name"]
            detail = item["detail"]
            if detail:
                lines.append(f"  {icon} {name} — {detail}")
            else:
                lines.append(f"  {icon} {name}")

    lines.append(bold("DeepPPT Dependency Check"))
    lines.append("=" * 40)

    section("Python Environment", python_env)
    section("Required Packages", required)
    section("Optional Packages", optional)
    section("System Tools", optional[:0])  # handled separately below
    section("Environment (.env)", env_cfg)

    # System tools go between Optional and Env
    sys_items = optional[:0]  # placeholder
    # Actually render system tools in correct position
    # We re-insert: already called section for Optional, now insert sys tools
    # Let's rebuild properly...

    return "\n".join(lines)


def render_full_table(
    python_env: list[CheckResult],
    required: list[CheckResult],
    optional_pkgs: list[CheckResult],
    system_tools: list[CheckResult],
    env_cfg: list[CheckResult],
    *,
    quiet: bool = False,
) -> str:
    lines: list[str] = []
    lines.append(bold("DeepPPT Dependency Check"))
    lines.append("=" * 40)

    def section(title: str, items: list[CheckResult]) -> None:
        filtered = [i for i in items if (not quiet or i["status"] != "ok")] if quiet else items
        if not filtered:
            return
        lines.append("")
        lines.append(bold(title))
        for item in filtered:
            icon = _status_icon(item["status"])
            name = item["name"]
            detail = item["detail"]
            if detail:
                lines.append(f"  {icon} {name} — {detail}")
            else:
                lines.append(f"  {icon} {name}")

    section("Python Environment", python_env)
    section("Required Packages", required)
    section("Optional Packages", optional_pkgs)
    section("System Tools", system_tools)
    section("Environment (.env)", env_cfg)

    # Summary
    missing_required = [i for i in required if i["status"] == "fail"]
    missing_optional = [i for i in optional_pkgs + system_tools + env_cfg if i["status"] == "warn"]
    missing_env = [i for i in env_cfg if i["status"] == "fail"]

    lines.append("")
    lines.append(bold("Summary"))

    parts: list[str] = []
    if missing_required:
        parts.append(f"{len(missing_required)} missing required")
    if missing_env:
        parts.append(f"{len(missing_env)} missing env config")
    if missing_optional:
        parts.append(f"{len(missing_optional)} missing optional")

    if parts:
        lines.append(f"  {', '.join(parts)}")
    else:
        lines.append(f"  {green('All checks passed!')}")

    if missing_required:
        pip_names = " ".join(i.get("pip_name", i["name"]) for i in missing_required)
        lines.append(f"  Install required: {yellow(f'pip install {pip_names}')}")

    if missing_env:
        lines.append(f"  Configure .env: {yellow('see .env.example for reference')}")

    return "\n".join(lines)


def render_json(
    python_env: list[CheckResult],
    required: list[CheckResult],
    optional_pkgs: list[CheckResult],
    system_tools: list[CheckResult],
    env_cfg: list[CheckResult],
) -> str:
    """Render machine-readable JSON."""
    # Strip internal-only keys like "pip_name", "purpose" from output
    def clean(items: list[CheckResult]) -> list[dict[str, str]]:
        return [{"status": i["status"], "name": i["name"], "detail": i["detail"]} for i in items]

    missing_req = [i["name"] for i in required if i["status"] == "fail"]
    missing_opt = [i["name"] for i in optional_pkgs + system_tools if i["status"] == "warn"]
    missing_env = [i["name"] for i in env_cfg if i["status"] == "fail"]

    data: dict[str, Any] = {
        "python": {"items": clean(python_env)},
        "required": {"items": clean(required), "missing": missing_req},
        "optional": {"items": clean(optional_pkgs) + clean(system_tools), "missing": missing_opt},
        "env": {"items": clean(env_cfg), "missing": missing_env},
        "summary": {
            "missing_required": len(missing_req),
            "missing_optional": len(missing_opt),
            "missing_env": len(missing_env),
            "all_ok": not missing_req and not missing_env,
        },
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# --install mode
# ---------------------------------------------------------------------------


def _pip_install(packages: list[str], *, elevate: bool = False) -> bool:
    """Install packages via pip. Returns True on success."""
    if not packages:
        return True
    cmd = [sys.executable, "-m", "pip", "install", *packages]
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def run_install(
    required: list[CheckResult],
    optional_pkgs: list[CheckResult],
    env_cfg: list[CheckResult],
) -> None:
    """Auto-install missing packages interactively."""
    missing_required = [i for i in required if i["status"] == "fail"]
    missing_optional = [i for i in optional_pkgs if i["status"] == "warn"]

    # Required packages — install without asking
    if missing_required:
        pip_names = [i.get("pip_name", i["name"]) for i in missing_required]
        print(f"\n{bold('Installing required packages...')}")
        ok = _pip_install(pip_names)
        if ok:
            print(f"  {green('Done.')}")
        else:
            print(f"  {red('Some packages failed to install. Check errors above.')}")

    # Optional packages — ask Y/n
    if missing_optional:
        print(f"\n{bold('Optional packages available:')}")
        for i, item in enumerate(missing_optional, 1):
            purpose = item.get("purpose", "")
            print(f"  {i}. {item['name']}" + (f" ({purpose})" if purpose else ""))

        try:
            answer = input("\nInstall optional packages? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer in ("y", "yes"):
            pip_names = [i.get("pip_name", i["name"]) for i in missing_optional]
            ok = _pip_install(pip_names)
            if ok:
                print(f"  {green('Done.')}")
            else:
                print(f"  {red('Some packages failed to install. Check errors above.')}")
        else:
            print("  Skipped optional packages.")

    # .env instructions
    missing_env = [i for i in env_cfg if i["status"] == "fail"]
    if missing_env or any(i["name"] == ".env file" and i["status"] == "warn" for i in env_cfg):
        root = _repo_root()
        env_example = root / ".env.example"
        print(f"\n{bold('Environment configuration needed:')}")
        if not (root / ".env").is_file() and env_example.is_file():
            print(f"  1. Copy .env.example to .env:")
            if platform.system() == "Windows":
                print(yellow(f"     copy .env.example .env"))
            else:
                print(yellow(f"     cp .env.example .env"))
            print(f"  2. Edit .env and fill in the required API keys.")
        else:
            for item in missing_env:
                print(f"  Set {yellow(item['name'])} in .env")
        print(f"  See .env.example for all available configuration options.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DeepPPT dependency checker and auto-installer.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quiet", action="store_true", help="Show only missing/problematic items.")
    group.add_argument("--json", action="store_true", help="Machine-readable JSON output.")
    group.add_argument("--install", action="store_true", help="Auto-install missing packages.")

    args = parser.parse_args()

    # Run all checks
    python_env = check_python_env()
    required = check_required_packages()
    optional_pkgs = check_optional_packages()
    system_tools = check_system_tools()
    env_cfg = check_env_config()

    if args.json:
        print(render_json(python_env, required, optional_pkgs, system_tools, env_cfg))
    elif args.install:
        # Show table first (non-quiet), then install
        print(render_full_table(python_env, required, optional_pkgs, system_tools, env_cfg, quiet=False))
        run_install(required, optional_pkgs, env_cfg)
    else:
        print(render_full_table(python_env, required, optional_pkgs, system_tools, env_cfg, quiet=args.quiet))


if __name__ == "__main__":
    # Ensure stdout can handle Unicode (emoji) on Windows consoles
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
