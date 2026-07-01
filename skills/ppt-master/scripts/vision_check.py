#!/usr/bin/env python3
"""
External vision check for PPT slides when the main model lacks multimodal capability.

Sends rendered PNG slides to an external vision-capable model (via OpenAI-compatible
or Anthropic-compatible API) and returns structured visual quality feedback.

Supports any provider that exposes OpenAI Chat Completions format or Anthropic Messages
format — covers GPT-4o, Gemini, Claude, DeepSeek-VL, Qwen-VL, SiliconFlow, OpenRouter,
Azure OpenAI, AWS Bedrock, and local Ollama models.

Usage:
  python vision_check.py <project_path>                        # Auto-detect backend
  python vision_check.py <project_path> --format openai        # Force OpenAI format
  python vision_check.py <project_path> --format anthropic     # Force Anthropic format
  python vision_check.py <png_file>                            # Single file check
  python vision_check.py <project_path> --rubric quick         # Quick scan only
  python vision_check.py <project_path> --format openai \\
    --base-url https://api.siliconflow.cn/v1 \\
    --model Qwen/Qwen2.5-VL-72B-Instruct                      # Custom endpoint

Environment variables:
  VISION_OPENAI_API_KEY / OPENAI_API_KEY       — For OpenAI-format endpoints
  VISION_OPENAI_BASE_URL / OPENAI_BASE_URL     — Custom base URL
  VISION_OPENAI_MODEL / OPENAI_MODEL           — Model override
  VISION_ANTHROPIC_API_KEY / ANTHROPIC_API_KEY  — For Anthropic-format endpoints
  VISION_ANTHROPIC_BASE_URL                    — Custom base URL
  VISION_ANTHROPIC_MODEL                       — Model override
  VISION_OLLAMA_HOST / OLLAMA_HOST             — Local Ollama host
  VISION_OLLAMA_MODEL                          — Local model name
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Auto-load .env from repo root so VISION_* vars are available without manual export
try:
    from dotenv import load_dotenv
    _repo_root = Path(__file__).resolve().parent.parent.parent.parent
    load_dotenv(_repo_root / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from vision_backends import backend_common  # noqa: E402

BACKEND_PRIORITY = [
    ("openai_format", "VISION_OPENAI_API_KEY", "OPENAI_API_KEY"),
    ("anthropic_format", "VISION_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    ("ollama", None, None),
]


def load_backend(name: str):
    """Dynamically load a vision backend module."""
    import importlib
    module_name = f"vision_backends.backend_{name}"
    return importlib.import_module(module_name)


def auto_detect_backend(api_key=None, base_url=None):
    """Find the first available backend based on env vars."""
    import os

    if api_key and base_url:
        if "anthropic" in base_url.lower():
            return "anthropic_format"
        return "openai_format"

    for backend_name, primary_key, fallback_key in BACKEND_PRIORITY:
        if backend_name == "ollama":
            mod = load_backend(backend_name)
            if mod.is_available():
                return backend_name
        else:
            if primary_key and os.environ.get(primary_key):
                return backend_name
            if fallback_key and os.environ.get(fallback_key):
                return backend_name

    return None


def find_pngs(target: str) -> list:
    """Find PNG files to check — either a single file or project directory."""
    target_path = Path(target)

    if target_path.is_file() and target_path.suffix.lower() == ".png":
        return [target_path]

    search_dirs = [
        target_path / ".preview",
        target_path / "svg_output",
        target_path,
    ]

    for d in search_dirs:
        if d.is_dir():
            pngs = sorted(d.glob("*.png"))
            if pngs:
                return pngs

    return []


def check_single_page(backend_mod, png_path: str, rubric_prompt: str, **kwargs) -> dict:
    """Run vision check on a single PNG."""
    try:
        result = backend_mod.check(str(png_path), rubric_prompt, **kwargs)
        result["vision_available"] = True
        return result
    except Exception as e:
        return {
            "vision_available": False,
            "error": str(e),
            "issues": [],
            "overall": "check_failed",
            "suggestions": [],
        }


def main():
    parser = argparse.ArgumentParser(
        description="External vision check for PPT slides (multi-backend).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("target", help="Project path or single PNG file")
    parser.add_argument("--format", choices=["openai", "anthropic", "ollama", "auto"],
                        default="auto", help="API format to use (default: auto-detect)")
    parser.add_argument("--base-url", default=None, help="Override API base URL")
    parser.add_argument("--model", default=None, help="Override model name")
    parser.add_argument("--api-key", default=None, help="Override API key")
    parser.add_argument("--rubric", default="quality",
                        choices=["quality", "quick", "brand"],
                        help="Rubric type (default: quality)")
    parser.add_argument("--rubric-file", default=None,
                        help="Path to custom rubric file (overrides --rubric)")
    parser.add_argument("--output", default=None,
                        help="Output JSON path (default: <project>/vision_check_report.json)")
    parser.add_argument("--max-pages", type=int, default=50,
                        help="Maximum pages to check (default: 50)")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    # Resolve backend
    fmt = args.format
    if fmt == "auto":
        detected = auto_detect_backend(api_key=args.api_key, base_url=args.base_url)
        if not detected:
            print("[ERROR] No vision backend available. Set one of:")
            print("  VISION_OPENAI_API_KEY / OPENAI_API_KEY (for GPT-4o, Qwen-VL, etc.)")
            print("  VISION_ANTHROPIC_API_KEY / ANTHROPIC_API_KEY (for Claude)")
            print("  Or start Ollama locally with a vision model")
            sys.exit(1)
        fmt = detected
    elif fmt == "openai":
        fmt = "openai_format"
    elif fmt == "anthropic":
        fmt = "anthropic_format"

    backend_mod = load_backend(fmt)

    if not args.quiet:
        print(f"Vision Check — backend: {fmt}")

    # Find PNGs
    pngs = find_pngs(args.target)
    if not pngs:
        print(f"[ERROR] No PNG files found in: {args.target}")
        print("  Run visual_review.py first to render SVGs to PNG, or point to a .png file.")
        sys.exit(1)

    pngs = pngs[:args.max_pages]
    if not args.quiet:
        print(f"  Found {len(pngs)} PNG(s) to check")

    # Build rubric prompt
    rubric = args.rubric_file if args.rubric_file else args.rubric
    project_path = str(Path(args.target)) if Path(args.target).is_dir() else str(Path(args.target).parent)
    spec_excerpt = backend_common.extract_spec_lock_excerpt(project_path)
    rubric_prompt = backend_common.build_rubric_prompt(rubric, spec_lock_excerpt=spec_excerpt)

    # Prepare backend kwargs
    call_kwargs = {}
    if args.api_key:
        call_kwargs["api_key"] = args.api_key
    if args.base_url:
        call_kwargs["base_url"] = args.base_url
    if args.model:
        call_kwargs["model"] = args.model

    # Run checks
    pages = {}
    total_issues = {"must_fix": 0, "should_fix": 0, "accepted": 0}

    for i, png in enumerate(pngs, 1):
        if not args.quiet:
            print(f"  [{i}/{len(pngs)}] Checking {png.name}...", end=" ", flush=True)

        result = check_single_page(backend_mod, str(png), rubric_prompt, **call_kwargs)
        pages[png.name] = result

        if result.get("vision_available"):
            for issue in result.get("issues", []):
                sev = issue.get("severity", "accepted")
                if sev in total_issues:
                    total_issues[sev] += 1
            if not args.quiet:
                n_issues = len(result.get("issues", []))
                print(f"{result.get('overall', '?')} ({n_issues} issues)")
        else:
            if not args.quiet:
                print(f"FAILED: {result.get('error', 'unknown')[:60]}")

    # Determine gate status
    if total_issues["must_fix"] > 0:
        gate = "BLOCKED"
    elif total_issues["should_fix"] > 0:
        gate = "PASS_WITH_WARNINGS"
    else:
        gate = "CLEAN"

    # Build report
    cfg = backend_mod.get_config(**call_kwargs) if hasattr(backend_mod, "get_config") else {}
    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "backend": fmt,
        "model": cfg.get("model", args.model or "unknown"),
        "rubric": args.rubric,
        "pages_checked": len(pngs),
        "summary": {
            "total_must_fix": total_issues["must_fix"],
            "total_should_fix": total_issues["should_fix"],
            "total_accepted": total_issues["accepted"],
            "gate_status": gate,
        },
        "pages": pages,
    }

    # Write output
    output_path = Path(args.output) if args.output else Path(project_path) / "vision_check_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.quiet:
        print(f"\n  Gate: {gate}")
        print(f"  must_fix: {total_issues['must_fix']}  "
              f"should_fix: {total_issues['should_fix']}  "
              f"accepted: {total_issues['accepted']}")
        print(f"  Report: {output_path}")

    sys.exit(1 if gate == "BLOCKED" else 0)


if __name__ == "__main__":
    main()
