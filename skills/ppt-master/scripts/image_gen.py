#!/usr/bin/env python3
"""
Unified Image Generation Tool

Dispatches to the appropriate backend based on explicit provider configuration.

Backend selection (`IMAGE_BACKEND` in `.env` or the current process environment):
  IMAGE_BACKEND=gemini      -> Gemini backend (google-genai SDK)
  IMAGE_BACKEND=openai      -> OpenAI-compatible backend (raw HTTP via requests)
  IMAGE_BACKEND=minimax     -> MiniMax image backend
  IMAGE_BACKEND=stability   -> Stability AI backend
  IMAGE_BACKEND=bfl         -> Black Forest Labs FLUX backend
  IMAGE_BACKEND=ideogram    -> Ideogram backend
  IMAGE_BACKEND=qwen        -> Alibaba Qwen image backend
  IMAGE_BACKEND=zhipu       -> Zhipu GLM-Image backend
  IMAGE_BACKEND=volcengine  -> Volcengine Seedream backend
  IMAGE_BACKEND=modelscope  -> ModelScope backend
  IMAGE_BACKEND=siliconflow -> SiliconFlow backend
  IMAGE_BACKEND=fal         -> fal.ai backend
  IMAGE_BACKEND=replicate   -> Replicate backend
  IMAGE_BACKEND=openrouter  -> OpenRouter backend

Configuration source (process env wins, `.env` is the fallback layer):
  1. Current process environment variables
  2. The first `.env` found among:
     - Current working directory
     - Skill directory (e.g. `~/.agents/skills/ppt-master/.env`)
     - Repo root (when running from a clone)
     - `~/.ppt-master/.env` (user-level config)

Supported keys:
  IMAGE_BACKEND    (required) backend name

  Provider-specific keys are used for credentials and overrides, for example:
    GEMINI_API_KEY / GEMINI_MODEL / GEMINI_BASE_URL
    OPENAI_API_KEY / OPENAI_MODEL / OPENAI_BASE_URL
    QWEN_API_KEY / QWEN_MODEL / QWEN_BASE_URL
    ZHIPU_API_KEY / ZHIPU_MODEL / ZHIPU_BASE_URL

Usage:
  python3 image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o images/
  python3 image_gen.py --manifest project/images/image_prompts.json -o project/images/
  python3 image_gen.py --list-backends
"""

import argparse
import concurrent.futures
import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from config import load_prefixed_env_file, resolve_env_path

ENV_PATH = resolve_env_path()
IMAGE_ENV_PREFIXES = (
    "IMAGE_",
    "GEMINI_",
    "OPENAI_",
    "MINIMAX_",
    "STABILITY_",
    "BFL_",
    "IDEOGRAM_",
    "QWEN_",
    "DASHSCOPE_",
    "ZHIPU_",
    "BIGMODEL_",
    "VOLCENGINE_",
    "ARK_",
    "MODELSCOPE_",
    "SILICONFLOW_",
    "FAL_",
    "REPLICATE_",
    "OPENROUTER_",
)
DEPRECATED_IMAGE_KEYS = {
    "IMAGE_API_KEY",
    "IMAGE_MODEL",
    "IMAGE_BASE_URL",
}

# All aspect ratios accepted by the unified CLI
# (each backend validates its own subset internally)
ALL_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8",
    "2:3", "3:2", "3:4", "4:1", "4:3",
    "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"
]

ALL_IMAGE_SIZES = ["512px", "1K", "2K", "4K"]

BACKEND_REGISTRY = {
    "gemini": {
        "module": "backend_gemini",
        "tier": "core",
        "label": "Google Gemini",
        "default_model": "gemini-3.1-flash-image-preview",
        "key_hint": "GEMINI_API_KEY",
        "aliases": ["google"],
    },
    "openai": {
        "module": "backend_openai",
        "tier": "core",
        "label": "OpenAI / OpenAI-compatible",
        "default_model": "gpt-image-2",
        "key_hint": "OPENAI_API_KEY",
        "aliases": ["openai-compatible", "openai_compatible"],
    },
    "minimax": {
        "module": "backend_minimax",
        "tier": "experimental",
        "label": "MiniMax Image",
        "default_model": "image-01",
        "key_hint": "MINIMAX_API_KEY",
        "aliases": ["minimaxi"],
    },
    "qwen": {
        "module": "backend_qwen",
        "tier": "core",
        "label": "Alibaba Qwen Image",
        "default_model": "qwen-image-2.0-pro",
        "key_hint": "QWEN_API_KEY / DASHSCOPE_API_KEY",
        "aliases": ["alibaba", "dashscope"],
    },
    "zhipu": {
        "module": "backend_zhipu",
        "tier": "core",
        "label": "Zhipu GLM-Image",
        "default_model": "glm-image",
        "key_hint": "ZHIPU_API_KEY / BIGMODEL_API_KEY",
        "aliases": ["bigmodel", "glm", "glm-image"],
    },
    "volcengine": {
        "module": "backend_volcengine",
        "tier": "core",
        "label": "Volcengine Seedream",
        "default_model": "doubao-seedream-4-5-251128",
        "key_hint": "VOLCENGINE_API_KEY / ARK_API_KEY",
        "aliases": ["ark", "doubao", "seedream"],
    },
    "modelscope": {
        "module": "backend_modelscope",
        "tier": "experimental",
        "label": "ModelScope",
        "default_model": "Tongyi-MAI/Z-Image-Turbo",
        "key_hint": "MODELSCOPE_API_KEY",
        "aliases": ["modelscope", "model-scope"]
    },
    "stability": {
        "module": "backend_stability",
        "tier": "extended",
        "label": "Stability AI",
        "default_model": "stable-image-core",
        "key_hint": "STABILITY_API_KEY",
        "aliases": ["stabilityai", "stability-ai"],
    },
    "bfl": {
        "module": "backend_bfl",
        "tier": "extended",
        "label": "Black Forest Labs FLUX",
        "default_model": "flux-pro-1.1-ultra",
        "key_hint": "BFL_API_KEY",
        "aliases": ["flux", "black-forest-labs", "black_forest_labs"],
    },
    "ideogram": {
        "module": "backend_ideogram",
        "tier": "extended",
        "label": "Ideogram",
        "default_model": "ideogram-v3",
        "key_hint": "IDEOGRAM_API_KEY",
    },
    "siliconflow": {
        "module": "backend_siliconflow",
        "tier": "experimental",
        "label": "SiliconFlow",
        "default_model": "Qwen/Qwen-Image",
        "key_hint": "SILICONFLOW_API_KEY",
        "aliases": ["silicon"],
    },
    "fal": {
        "module": "backend_fal",
        "tier": "experimental",
        "label": "fal.ai",
        "default_model": "fal-ai/imagen3/fast",
        "key_hint": "FAL_KEY / FAL_API_KEY",
        "aliases": ["fal-ai"],
    },
    "replicate": {
        "module": "backend_replicate",
        "tier": "experimental",
        "label": "Replicate",
        "default_model": "black-forest-labs/flux-1.1-pro",
        "key_hint": "REPLICATE_API_TOKEN / REPLICATE_API_KEY",
    },
    "openrouter": {
        "module": "backend_openrouter",
        "tier": "experimental",
        "label": "OpenRouter",
        "default_model": "google/gemini-3.1-flash-image-preview",
        "key_hint": "OPENROUTER_API_KEY",
    },
}

TIER_ORDER = {"core": 0, "extended": 1, "experimental": 2}
SUPPORTED_BACKENDS = tuple(sorted(BACKEND_REGISTRY))


def _load_image_env_file() -> None:
    """
    Load image generation config from the resolved `.env` as a fallback layer.

    Existing process environment variables win over `.env`.
    """
    replacements = {
        "IMAGE_API_KEY": "GEMINI_API_KEY / OPENAI_API_KEY / QWEN_API_KEY / ZHIPU_API_KEY / ...",
        "IMAGE_MODEL": "GEMINI_MODEL / OPENAI_MODEL / QWEN_MODEL / ZHIPU_MODEL / ...",
        "IMAGE_BASE_URL": "GEMINI_BASE_URL / OPENAI_BASE_URL / QWEN_BASE_URL / ZHIPU_BASE_URL / ...",
    }
    deprecated_messages = {
        key: (
            "Global image config keys have been removed.\n"
            f"Use IMAGE_BACKEND plus provider-specific keys instead, such as {replacement}."
        )
        for key, replacement in replacements.items()
    }
    load_prefixed_env_file(IMAGE_ENV_PREFIXES, deprecated_keys=deprecated_messages)


def _validate_runtime_config() -> None:
    """Reject deprecated global image variables from any configuration source."""
    for key in DEPRECATED_IMAGE_KEYS:
        if key not in os.environ:
            continue
        replacement = {
            "IMAGE_API_KEY": "GEMINI_API_KEY / OPENAI_API_KEY / QWEN_API_KEY / ZHIPU_API_KEY / ...",
            "IMAGE_MODEL": "GEMINI_MODEL / OPENAI_MODEL / QWEN_MODEL / ZHIPU_MODEL / ...",
            "IMAGE_BASE_URL": "GEMINI_BASE_URL / OPENAI_BASE_URL / QWEN_BASE_URL / ZHIPU_BASE_URL / ...",
        }[key]
        raise ValueError(
            f"Unsupported image config key: {key}\n"
            "Global image config keys have been removed.\n"
            f"Use IMAGE_BACKEND plus provider-specific keys instead, such as {replacement}."
        )


def _build_backend_aliases() -> dict[str, str]:
    """Build a lookup from aliases to canonical backend names."""
    aliases = {}
    for canonical_name, config in BACKEND_REGISTRY.items():
        aliases[canonical_name] = canonical_name
        for alias in config.get("aliases", []):
            aliases[alias] = canonical_name
    return aliases


BACKEND_ALIASES = _build_backend_aliases()


_BACKEND_PIP_HINTS = {
    "gemini": "google-genai",
    "openai": "openai",
}


def _load_backend(canonical_name: str) -> tuple[object, str]:
    """Import and return the configured backend module."""
    module_name = f"image_backends.{BACKEND_REGISTRY[canonical_name]['module']}"
    try:
        module = __import__(module_name, fromlist=["*"])
    except ImportError as exc:
        pip_name = _BACKEND_PIP_HINTS.get(canonical_name, exc.name or "<dependency>")
        print(
            f"Error: backend '{canonical_name}' needs a package that is not installed.\n"
            f"Missing: {exc.name}\n"
            f"Run: pip install {pip_name}",
            file=sys.stderr,
        )
        sys.exit(1)
    return module, canonical_name


def _print_backend_list() -> None:
    """Print supported backends grouped by support tier."""
    print("Supported image backends:\n")
    tiers = ("core", "extended", "experimental")
    for tier in tiers:
        print(f"{tier.upper()}:")
        for name, info in sorted(
            BACKEND_REGISTRY.items(),
            key=lambda item: (TIER_ORDER[item[1]["tier"]], item[0]),
        ):
            if info["tier"] != tier:
                continue
            print(
                f"  {name:<12} {info['label']} | default={info['default_model']} | keys={info['key_hint']}"
            )
        print()
    print("Recommendation: prefer CORE backends for everyday PPT generation.")
    print(f"Config fallback file: {ENV_PATH}")


def _resolve_backend() -> tuple[object, str]:
    """
    Determine which backend to use from explicit configuration.

    Returns:
        A backend module with a generate() function.
    """
    backend_name = os.environ.get("IMAGE_BACKEND", "").strip().lower()
    if backend_name:
        canonical = BACKEND_ALIASES.get(backend_name)
        if not canonical:
            supported = ", ".join(SUPPORTED_BACKENDS)
            print(f"Error: Unknown IMAGE_BACKEND='{backend_name}'. Supported: {supported}")
            sys.exit(1)
        return _load_backend(canonical)

    supported = ", ".join(SUPPORTED_BACKENDS)
    print(
        "Error: No image backend configured for Path A (image_gen.py).\n"
        "\n"
        "If your host (Codex / Antigravity / Claude Code / etc.) has a native image\n"
        "generation tool, do NOT run this script — switch to Path B: invoke the host's\n"
        "image tool directly with the prompts from images/image_prompts.json and save\n"
        "the outputs to images/<filename>. See references/image-generator.md §7 Path B.\n"
        "\n"
        "To use Path A instead, set IMAGE_BACKEND in one of these places:\n"
        f"  1. Current process environment\n"
        f"  2. {ENV_PATH}\n"
        "\n"
        f"Supported backends: {supported}\n"
        "\n"
        "Example:\n"
        "  IMAGE_BACKEND=openai\n"
        "  OPENAI_API_KEY=sk-xxx\n"
    )
    sys.exit(1)


def _validate_reference_image(value, item_label: str) -> str | None:
    """Validate that a reference_image is a real file path or URL.

    AI agents sometimes write plain-text descriptions into this field
    (e.g. "a classic portrait of a scholar") instead of an actual path.
    Detecting this early prevents a FileNotFoundError crash and lets the
    pipeline fall back to text-to-image mode gracefully.

    Returns the validated path/URL, or None (with a warning) when the
    value is not usable as a reference image.
    """
    if not value or not isinstance(value, str):
        return None

    trimmed = value.strip()
    if not trimmed:
        return None

    # Accept HTTP(S) URLs — the backend will download them.
    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        return trimmed

    # Accept local files that actually exist on disk.
    if os.path.isfile(trimmed):
        return trimmed

    # Anything else is almost certainly a text description, not a path.
    print(
        f"  [WARN] {item_label}: reference_image is not a valid file path or URL — "
        f"skipping img2img, falling back to text-to-image.\n"
        f"         value: {trimmed[:120]}{'...' if len(trimmed) > 120 else ''}",
        file=sys.stderr,
    )
    return None


REFERENCE_CONFIDENCE_THRESHOLD = 0.75
HIGH_RISK_REFERENCE_CONFIDENCE_THRESHOLD = 0.85
REFERENCE_STRONG_MATCH_VALUES = {
    "exact",
    "strong",
    "verified",
    "high",
    "same-subject",
    "same_subject",
}
REFERENCE_SOURCE_FIELDS = (
    "reference_source",
    "reference_source_url",
    "reference_url",
    "source_url",
    "source_page_url",
    "source_title",
    "source_path",
)
HIGH_AMBIGUITY_TERMS = (
    "person",
    "people",
    "portrait",
    "named person",
    "real person",
    "celebrity",
    "founder",
    "speaker",
    "character",
    "place",
    "landmark",
    "event",
    "人物",
    "真人",
    "名人",
    "创始人",
    "角色",
    "地点",
    "地标",
    "事件",
)


def _as_bool(value) -> bool:
    """Interpret common manifest truth values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "approved"}
    return False


def _as_float(value) -> float | None:
    """Convert a manifest confidence value to float when possible."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().rstrip("%")
        try:
            parsed = float(text)
        except ValueError:
            return None
        return parsed / 100 if parsed > 1 else parsed
    return None


def _reference_policy(item: dict) -> dict:
    """Normalize reference-image review fields from current and legacy manifests."""
    policy = item.get("reference_image_policy")
    if isinstance(policy, dict):
        normalized = dict(policy)
    else:
        normalized = {}

    provenance = item.get("reference_provenance")
    if isinstance(provenance, dict):
        normalized.setdefault("provenance", provenance)
        for key in REFERENCE_SOURCE_FIELDS:
            if provenance.get(key) and not normalized.get(key):
                normalized[key] = provenance.get(key)

    field_aliases = {
        "approved": ("reference_approved", "approved"),
        "confidence": ("reference_confidence", "reference_match_confidence"),
        "semantic_match": (
            "reference_semantic_match",
            "semantic_match",
            "subject_match",
        ),
        "fallback": ("reference_fallback", "fallback_plan"),
    }
    for target, aliases in field_aliases.items():
        for alias in aliases:
            if item.get(alias) is not None and normalized.get(target) is None:
                normalized[target] = item.get(alias)
                break
    for key in REFERENCE_SOURCE_FIELDS:
        if item.get(key) and not normalized.get(key):
            normalized[key] = item.get(key)
    return normalized


def _has_reference_source(policy: dict) -> bool:
    """Return true when the manifest records where the reference came from."""
    if _as_bool(policy.get("user_provided")):
        return True
    for key in REFERENCE_SOURCE_FIELDS:
        if str(policy.get(key) or "").strip():
            return True
    provenance = policy.get("provenance")
    if isinstance(provenance, dict):
        return any(str(provenance.get(key) or "").strip() for key in REFERENCE_SOURCE_FIELDS)
    return False


def _reference_match_is_strong(policy: dict) -> bool:
    """Return true when semantic match was explicitly reviewed as strong."""
    value = policy.get("semantic_match")
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in REFERENCE_STRONG_MATCH_VALUES


def _is_high_ambiguity_subject(item: dict, policy: dict) -> bool:
    """Identify rows where a wrong reference image can easily mislead img2img."""
    if _as_bool(item.get("high_ambiguity_subject")) or _as_bool(policy.get("high_ambiguity")):
        return True
    risk = str(item.get("subject_risk") or policy.get("subject_risk") or "").strip().lower()
    if risk in {"high", "ambiguous", "identity", "person", "place", "event"}:
        return True
    text = " ".join(
        str(item.get(key) or "")
        for key in ("prompt", "purpose", "subject", "description", "reference")
    ).lower()
    return any(term.lower() in text for term in HIGH_AMBIGUITY_TERMS)


def _reference_image_for_generation(item: dict, item_label: str) -> str | None:
    """Return a vetted reference image path/URL, or downgrade to text-to-image."""
    raw_value = item.get("reference_image")
    if not raw_value:
        return None

    policy = _reference_policy(item)
    validated = _validate_reference_image(raw_value, item_label)
    confidence = _as_float(policy.get("confidence"))
    high_risk = _is_high_ambiguity_subject(item, policy)
    threshold = (
        HIGH_RISK_REFERENCE_CONFIDENCE_THRESHOLD
        if high_risk
        else REFERENCE_CONFIDENCE_THRESHOLD
    )
    reasons: list[str] = []

    if not validated:
        reasons.append("reference_image is not a valid local file or HTTP(S) URL")
    if not _as_bool(policy.get("approved")):
        reasons.append("reference_image_policy.approved is not true")
    if not _has_reference_source(policy):
        reasons.append("reference source/provenance is missing")
    if not _reference_match_is_strong(policy):
        reasons.append("semantic match is not explicitly strong/exact/verified")
    if confidence is None:
        reasons.append("reference confidence is missing")
    elif confidence < threshold:
        reasons.append(f"reference confidence {confidence:.2f} is below {threshold:.2f}")

    review = {
        "used": not reasons,
        "checked_at": _utc_now(),
        "high_ambiguity_subject": high_risk,
        "required_confidence": threshold,
        "recorded_confidence": confidence,
        "semantic_match": policy.get("semantic_match", ""),
        "approved": _as_bool(policy.get("approved")),
        "source_recorded": _has_reference_source(policy),
    }
    if reasons:
        review["decision"] = "text-to-image"
        review["skip_reasons"] = reasons
        fallback = policy.get("fallback") or item.get("fallback_plan")
        review["fallback"] = fallback or (
            "Generate from the page-grounded prompt without img2img reference guidance."
        )
        item["reference_image_review"] = review
        print(
            f"  [REF]  {item_label}: skipping img2img reference; "
            + "; ".join(reasons),
            file=sys.stderr,
        )
        return None

    review["decision"] = "img2img"
    item["reference_image_review"] = review
    return validated


DEFAULT_MANIFEST_CONCURRENCY = 3
DEFAULT_FALLBACK_FAILURE_THRESHOLD = 2
DEFAULT_FALLBACK_CONSECUTIVE_THRESHOLD = 2
DEFAULT_ITEM_ATTEMPTS = 1

STATUS_PENDING = "Pending"
STATUS_GENERATED = "Generated"
STATUS_FAILED = "Failed"
STATUS_NEEDS_MANUAL = "Needs-Manual"
VALID_STATUSES = {STATUS_PENDING, STATUS_GENERATED, STATUS_FAILED, STATUS_NEEDS_MANUAL}
RETRYABLE_STATUSES = {STATUS_PENDING, STATUS_FAILED}
REQUIRED_ITEM_FIELDS = ("filename", "prompt", "aspect_ratio", "status")


def load_manifest(path: str) -> dict:
    """Load and validate an `image_prompts.json` manifest.

    Schema (top level): {"items": [ ... ]}, optionally with
    `deck_style_anchor`, `color_scheme`, `generated_at`.

    Each item requires: `filename`, `prompt`, `aspect_ratio`, `status`.
    Optional: `image_size`, `model`, `alt_text`, `purpose`, `type`,
    `last_error`.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path}: {exc.msg} "
            f"(line {exc.lineno}, col {exc.colno})"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: top level must be a JSON object, "
            f"got {type(data).__name__}"
        )

    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError(f"{path}: 'items' must be a non-empty array")

    seen_filenames: set[str] = set()
    for i, item in enumerate(items):
        prefix = f"{path}: items[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} must be an object")
        for field in REQUIRED_ITEM_FIELDS:
            if field not in item:
                raise ValueError(f"{prefix} missing required field '{field}'")
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(
                    f"{prefix} field '{field}' must be a non-empty string"
                )
        if item["status"] not in VALID_STATUSES:
            raise ValueError(
                f"{prefix} status '{item['status']}' is invalid. "
                f"Valid: {sorted(VALID_STATUSES)}"
            )
        fname = item["filename"]
        if fname in seen_filenames:
            raise ValueError(f"{prefix} duplicate filename '{fname}'")
        seen_filenames.add(fname)

    return data


def save_manifest(path: str, data: dict) -> None:
    """Atomically write manifest back to disk (tmp file + rename)."""
    from json_utils import atomic_write_json
    atomic_write_json(path, data)


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp for manifest audit events."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _append_manifest_event(manifest: dict, event: dict) -> None:
    """Append a bounded audit event to the manifest."""
    events = manifest.setdefault("events", [])
    if not isinstance(events, list):
        events = []
        manifest["events"] = events
    payload = {"at": _utc_now(), **event}
    events.append(payload)
    del events[:-200]


def _fallback_query_for_item(item: dict) -> str:
    """Build a keyword query for web image fallback from an AI prompt row."""
    explicit = (
        item.get("fallback_query")
        or item.get("web_search_query")
        or item.get("search_query")
    )
    if explicit:
        return str(explicit).strip()

    try:
        from image_sources.provider_common import simplify_query
        return simplify_query(str(item.get("prompt") or ""), max_words=4)
    except ImportError:
        words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", str(item.get("prompt") or ""))
        return " ".join(words[:4]) or str(item.get("prompt") or "").strip()


def _orientation_from_aspect_ratio(aspect_ratio: str) -> str:
    """Map a manifest aspect ratio to image_search.py's coarse orientation."""
    try:
        left, right = aspect_ratio.split(":", 1)
        width = float(left)
        height = float(right)
    except (ValueError, AttributeError):
        return "any"
    if width > height:
        return "landscape"
    if height > width:
        return "portrait"
    return "square"


def _copyright_risk_for_source(source_item: dict | None) -> str:
    """Summarize downstream license risk for a sourced fallback image."""
    if not source_item:
        return "unknown: no provider source record was written; manual review required"
    tier = str(source_item.get("license_tier") or "")
    if tier == "no-attribution":
        return (
            "low: provider metadata says no on-slide attribution is required; "
            "manual license review still recommended for external delivery"
        )
    if tier == "attribution-required":
        return "medium: license requires on-slide attribution using image_sources.json attribution_text"
    return "high: license tier is unknown; verify rights before external delivery"


def _fallback_search_one(
    item: dict,
    manifest_path: str,
    *,
    output_dir: str,
    trigger: str,
    backend_name: str,
    search_concurrency: int,
    save_candidates: bool,
    max_candidates: int,
) -> tuple[bool, str | None]:
    """Source one failed AI row through image_search.py and annotate provenance."""
    from image_search import (
        default_manifest_path,
        run_search_manifest,
    )
    from json_utils import load_json

    out_dir = Path(output_dir)
    query = _fallback_query_for_item(item)
    target_w = int(item.get("target_width") or 0)
    target_h = int(item.get("target_height") or 0)
    queries_path = Path(manifest_path).with_name("image_fallback_queries.json")
    sources_path = default_manifest_path(str(out_dir))
    fallback_manifest = load_json(queries_path, default={"items": []}) or {"items": []}
    rows = [row for row in fallback_manifest.get("items", []) if row.get("filename") != item["filename"]]
    rows.append({
        "filename": item["filename"],
        "query": query,
        "status": "Pending",
        "slide": item.get("slide") or item.get("page_id") or "",
        "purpose": item.get("purpose") or "ai-generation-fallback",
        "orientation": _orientation_from_aspect_ratio(item.get("aspect_ratio", "")),
        "min_width": target_w or 1200,
        "min_height": target_h or 800,
        "trigger": trigger,
        "source_ai_prompt": item.get("prompt", ""),
        "source_pack": item.get("source_pack") or "open_licensed_commons",
        "selection_reason": (
            "Fallback from failed AI image generation; choose the best downloadable "
            "candidate from routed web image search and keep provenance for review."
        ),
        "copyright_risk": "pending: fallback search has not completed",
        "manual_review_status": "pending",
        "needs_manual_review": bool(item.get("needs_manual_review")),
    })
    fallback_manifest["items"] = rows
    fallback_manifest["generated_from"] = str(Path(manifest_path).name)
    fallback_manifest["updated_at"] = _utc_now()
    save_manifest(str(queries_path), fallback_manifest)

    item["fallback"] = {
        "mode": "web-image-search",
        "trigger": trigger,
        "backend": backend_name,
        "query": query,
        "queries_manifest": str(queries_path),
        "sources_manifest": str(sources_path),
        "selection_reason": (
            "AI generation failed repeatedly; selected the highest-scoring downloadable "
            "open-license candidate from image_search.py's provider chain."
        ),
        "copyright_risk": "pending: fallback search has not completed",
        "started_at": _utc_now(),
    }

    sourced, needs_manual, _ = run_search_manifest(
        fallback_manifest,
        str(queries_path),
        output_dir=out_dir,
        sources_manifest_path=sources_path,
        concurrency=max(1, search_concurrency),
        save_candidates=save_candidates,
        max_candidates=max_candidates,
        default_provider=None,
        default_strict=False,
        default_min_width=target_w or 1200,
        default_min_height=target_h or 800,
    )

    latest_sources = load_json(sources_path, default={"items": []}) or {"items": []}
    source_item = next(
        (
            source
            for source in reversed(latest_sources.get("items", []))
            if source.get("filename") == item["filename"]
        ),
        None,
    )
    fallback = item.setdefault("fallback", {})
    fallback["finished_at"] = _utc_now()
    fallback["copyright_risk"] = _copyright_risk_for_source(source_item)

    if sourced and source_item:
        item["status"] = STATUS_GENERATED
        item["acquisition"] = "web-fallback"
        item["source_type"] = "web"
        item["fallback_status"] = "Sourced"
        item.pop("last_error", None)
        fallback.update({
            "provider": source_item.get("provider", ""),
            "stage": source_item.get("stage", ""),
            "title": source_item.get("title", ""),
            "author": source_item.get("author", ""),
            "source_page_url": source_item.get("source_page_url", ""),
            "download_url": source_item.get("download_url", ""),
            "source_pack": source_item.get("source_pack", ""),
            "selection_reason": source_item.get("selection_reason", ""),
            "discovery_source": source_item.get("discovery_source", ""),
            "manual_review_status": source_item.get("manual_review_status", ""),
            "license_name": source_item.get("license_name", ""),
            "license_url": source_item.get("license_url", ""),
            "license_tier": source_item.get("license_tier", ""),
            "attribution_required": bool(source_item.get("attribution_required")),
            "attribution_text": source_item.get("attribution_text", ""),
        })
        return True, None

    item["status"] = STATUS_NEEDS_MANUAL
    item["fallback_status"] = "Needs-Manual"
    error = "web image fallback found no acceptable candidate"
    if needs_manual:
        refreshed = load_json(queries_path, default={"items": []}) or {"items": []}
        row = next(
            (
                row for row in refreshed.get("items", [])
                if row.get("filename") == item["filename"]
            ),
            None,
        )
        error = str((row or {}).get("last_error") or error)
    item["last_error"] = error
    return False, error


def _should_trigger_fallback(
    *,
    fallback_enabled: bool,
    backend_failures: int,
    consecutive_failures: int,
    failure_threshold: int,
    consecutive_threshold: int,
) -> bool:
    """Decide whether AI generation should stop and web fallback should take over."""
    if not fallback_enabled:
        return False
    return (
        backend_failures >= max(1, failure_threshold)
        or consecutive_failures >= max(1, consecutive_threshold)
    )


def _run_manifest(manifest: dict, manifest_path: str, backend_module, *,
                  initial_concurrency: int,
                  image_size: str,
                  output_dir: str,
                  model: str | None,
                  backend_name: str = "",
                  fallback_enabled: bool = True,
                  fallback_failure_threshold: int = DEFAULT_FALLBACK_FAILURE_THRESHOLD,
                  fallback_consecutive_threshold: int = DEFAULT_FALLBACK_CONSECUTIVE_THRESHOLD,
                  item_attempts: int = DEFAULT_ITEM_ATTEMPTS,
                  fallback_search_concurrency: int = 1,
                  fallback_save_candidates: bool = True,
                  fallback_max_candidates: int = 8) -> tuple[int, int, int]:
    """Run Pending/Failed items through the backend with adaptive concurrency.

    Strategy:
      - Start at `initial_concurrency` workers per batch.
      - On any rate-limit error in a batch, halve concurrency (min 1) and
        requeue the rate-limited items.
      - Per-item failures are retried up to `item_attempts` manifest-level
        attempts. Backend modules may also have their own bounded retries.
      - When a backend crosses the failure threshold, unfinished rows switch
        to image_search.py web fallback and keep provenance in the manifest.
      - Status is written back to the manifest file after each completion;
        a Ctrl-C in the middle still preserves done items.
      - `Needs-Manual` items are skipped (user processes them externally).

    Returns (ok_count, failed_count, skipped_count).
    """
    from image_backends.backend_common import is_rate_limit_error

    items = manifest["items"]
    pending_idx = [
        i for i, it in enumerate(items) if it["status"] in RETRYABLE_STATUSES
    ]
    total = len(pending_idx)
    skipped = len(items) - total

    if total == 0:
        print(
            f"[Manifest] Nothing to do — all {len(items)} items already in "
            "a terminal state (Generated / Needs-Manual)."
        )
        return 0, 0, skipped

    print(
        f"\n[Manifest] {total} item(s) to generate, "
        f"{skipped} already done. concurrency={initial_concurrency}\n"
    )

    queue: list[int] = list(pending_idx)
    ok_count = 0
    fail_count = 0
    fallback_count = 0
    current = max(1, initial_concurrency)
    backend_failures = 0
    consecutive_failures = 0
    failed_for_fallback: list[int] = []
    state_lock = threading.Lock()

    manifest["fallback_policy"] = {
        "enabled": bool(fallback_enabled),
        "failure_threshold": max(1, fallback_failure_threshold),
        "consecutive_threshold": max(1, fallback_consecutive_threshold),
        "item_attempts": max(1, item_attempts),
        "backend": backend_name,
        "fallback": "image_search.py provider chain; no deprecated websearch API",
        "updated_at": _utc_now(),
    }

    def _one(idx: int):
        item = items[idx]
        max_attempts = max(1, int(item.get("max_attempts") or item_attempts))
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            item["attempt_count"] = int(item.get("attempt_count") or 0) + 1
            item["last_attempt_at"] = _utc_now()
            item["backend"] = backend_name
            try:
                ref_image = _reference_image_for_generation(
                    item, item.get("filename", f"items[{idx}]")
                )
                saved_path = backend_module.generate(
                    prompt=item["prompt"],
                    aspect_ratio=item["aspect_ratio"],
                    image_size=item.get("image_size", image_size),
                    output_dir=output_dir,
                    filename=Path(item["filename"]).stem,
                    model=item.get("model", model),
                    reference_image=ref_image,
                )
                # Layout-driven resize: crop to target dimensions if specified
                target_w = item.get("target_width")
                target_h = item.get("target_height")
                if target_w and target_h and saved_path:
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(saved_path)
                        cur_w, cur_h = img.size
                        if abs(cur_w - target_w) > target_w * 0.05 or abs(cur_h - target_h) > target_h * 0.05:
                            # Scale to cover target, then center-crop
                            scale = max(target_w / cur_w, target_h / cur_h)
                            new_w = int(cur_w * scale)
                            new_h = int(cur_h * scale)
                            img = img.resize((new_w, new_h), PILImage.LANCZOS)
                            left = (new_w - target_w) // 2
                            top = (new_h - target_h) // 2
                            img = img.crop((left, top, left + target_w, top + target_h))
                            img.save(saved_path)
                            print(f"  [CROP] {item['filename']}: {cur_w}x{cur_h} -> {target_w}x{target_h}")
                    except ImportError:
                        pass  # Pillow not available, skip resize
                    except (OSError, ValueError) as crop_exc:
                        print(f"  [WARN] {item['filename']}: crop failed: {crop_exc}")
                return idx, saved_path, None
            except Exception as exc:  # noqa: BLE001 — backend raises arbitrary types
                last_exc = exc
                if attempt < max_attempts:
                    delay = min(10, 2 * attempt)
                    print(
                        f"  [WARN] {item['filename']}: manifest attempt "
                        f"{attempt}/{max_attempts} failed: {exc}; retrying in {delay}s"
                    )
                    time.sleep(delay)
        return idx, None, last_exc

    while queue:
        if _should_trigger_fallback(
            fallback_enabled=fallback_enabled,
            backend_failures=backend_failures,
            consecutive_failures=consecutive_failures,
            failure_threshold=fallback_failure_threshold,
            consecutive_threshold=fallback_consecutive_threshold,
        ):
            trigger = (
                f"backend_failures={backend_failures}, "
                f"consecutive_failures={consecutive_failures}"
            )
            seen_remaining: set[int] = set()
            remaining: list[int] = []
            for candidate_idx in failed_for_fallback + queue:
                if candidate_idx in seen_remaining:
                    continue
                if items[candidate_idx]["status"] not in RETRYABLE_STATUSES:
                    continue
                seen_remaining.add(candidate_idx)
                remaining.append(candidate_idx)
            queue.clear()
            failed_for_fallback.clear()
            print(
                f"\n  [FALLBACK] AI backend '{backend_name}' crossed threshold "
                f"({trigger}). Switching {len(remaining)} item(s) to web search.\n"
            )
            _append_manifest_event(
                manifest,
                {
                    "type": "fallback-triggered",
                    "backend": backend_name,
                    "trigger": trigger,
                    "remaining": len(remaining),
                },
            )
            for idx in remaining:
                item = items[idx]
                ok, error = _fallback_search_one(
                    item,
                    manifest_path,
                    output_dir=output_dir,
                    trigger=trigger,
                    backend_name=backend_name,
                    search_concurrency=fallback_search_concurrency,
                    save_candidates=fallback_save_candidates,
                    max_candidates=fallback_max_candidates,
                )
                if ok:
                    fallback_count += 1
                    ok_count += 1
                    print(f"  [WEB]  {item['filename']} — sourced fallback")
                else:
                    print(f"  [MANUAL] {item['filename']} — {error}")
                save_manifest(manifest_path, manifest)
            break

        batch_size = min(current, len(queue))
        batch_idx = queue[:batch_size]
        queue = queue[batch_size:]

        print(
            f"--- Batch of {batch_size} (concurrency={current}, "
            f"remaining_after={len(queue)}) ---"
        )

        rate_limited = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as ex:
            futures = [ex.submit(_one, i) for i in batch_idx]
            for fut in concurrent.futures.as_completed(futures):
                idx, saved_path, exc = fut.result()
                item = items[idx]
                with state_lock:
                    if exc is None:
                        item["status"] = STATUS_GENERATED
                        item["acquisition"] = "ai-generated"
                        item.pop("last_error", None)
                        ok_count += 1
                        consecutive_failures = 0
                        print(f"  [OK]   {item['filename']}")
                    elif is_rate_limit_error(exc):
                        rate_limited = True
                        queue.append(idx)
                        backend_failures += 1
                        consecutive_failures += 1
                        item["last_error"] = str(exc)[:500]
                        item["failure_kind"] = "rate-limit"
                        print(f"  [RATE] {item['filename']} — requeued")
                    else:
                        item["status"] = STATUS_FAILED
                        item["last_error"] = str(exc)[:500]
                        item["failure_kind"] = exc.__class__.__name__
                        item["failed_at"] = _utc_now()
                        fail_count += 1
                        backend_failures += 1
                        consecutive_failures += 1
                        if fallback_enabled:
                            failed_for_fallback.append(idx)
                        print(f"  [FAIL] {item['filename']}: {exc}")
                    _append_manifest_event(
                        manifest,
                        {
                            "type": "image-result",
                            "filename": item["filename"],
                            "status": item["status"],
                            "backend": backend_name,
                            "failure_kind": item.get("failure_kind", ""),
                            "error": item.get("last_error", ""),
                            "backend_failures": backend_failures,
                            "consecutive_failures": consecutive_failures,
                        },
                    )
                    save_manifest(manifest_path, manifest)

        if _should_trigger_fallback(
            fallback_enabled=fallback_enabled,
            backend_failures=backend_failures,
            consecutive_failures=consecutive_failures,
            failure_threshold=fallback_failure_threshold,
            consecutive_threshold=fallback_consecutive_threshold,
        ) and failed_for_fallback:
            queue = failed_for_fallback + queue
            failed_for_fallback = []
            continue

        if rate_limited and current > 1:
            new_current = max(1, current // 2)
            print(
                f"\n  ⚠ Rate-limit hit — concurrency {current} → {new_current}, "
                "pausing 10s before next batch\n"
            )
            current = new_current
            time.sleep(10)
        elif queue:
            time.sleep(2)

    final_failed = sum(
        1
        for item in items
        if item.get("status") in {STATUS_FAILED, STATUS_NEEDS_MANUAL}
    )
    final_ok = sum(1 for item in items if item.get("status") == STATUS_GENERATED)

    print(
        f"\n[Manifest] Done: {final_ok} ok / {final_failed} failed "
        f"/ {fallback_count} web-fallback "
        f"({skipped} pre-skipped). Manifest written to {manifest_path}"
    )
    return final_ok, final_failed, skipped


def _resolve_concurrency(cli_value: int | None) -> int:
    """CLI value wins over IMAGE_CONCURRENCY env; default 3."""
    if cli_value is not None:
        return max(1, cli_value)
    env_val = os.environ.get("IMAGE_CONCURRENCY", "").strip()
    if env_val.isdigit():
        return max(1, int(env_val))
    return DEFAULT_MANIFEST_CONCURRENCY


def _resolve_positive_int_env(name: str, default: int) -> int:
    """Return a positive integer from env, or the provided default."""
    env_val = os.environ.get(name, "").strip()
    if env_val.isdigit():
        return max(1, int(env_val))
    return max(1, default)


def render_manifest_md(manifest: dict) -> str:
    """Render a manifest into the paste-ready Markdown view.

    The output is a read-only snapshot of the JSON manifest, intended as a
    fallback so a user can copy `Prompt` blocks into ChatGPT / Midjourney
    when `--manifest` cannot run (no key, no backend, network down).
    """
    lines: list[str] = []
    lines.append("# Image Generation Prompts")
    lines.append("")
    lines.append("> Auto-generated from `image_prompts.json` by `image_gen.py --render-md`.")
    lines.append("> Do not hand-edit — re-run the command to refresh.")
    lines.append("")

    project = manifest.get("project")
    generated_at = manifest.get("generated_at")
    color_scheme = manifest.get("color_scheme") or {}
    anchor = manifest.get("deck_style_anchor")

    if project:
        lines.append(f"> Project: {project}")
    if generated_at:
        lines.append(f"> Generated: {generated_at}")
    if color_scheme:
        cs = " | ".join(
            f"{k.capitalize()} {v}" for k, v in color_scheme.items()
        )
        lines.append(f"> Color scheme: {cs}")
    if anchor:
        lines.append(f"> Deck Style Anchor: {anchor}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, item in enumerate(manifest["items"], start=1):
        lines.append(f"### Image {i}: {item['filename']}")
        lines.append("")
        lines.append("| Attribute | Value |")
        lines.append("|---|---|")
        for label, key in (
            ("Purpose", "purpose"),
            ("Type", "type"),
            ("Aspect ratio", "aspect_ratio"),
            ("Image size", "image_size"),
            ("Status", "status"),
        ):
            value = item.get(key)
            if value:
                lines.append(f"| {label} | {value} |")
        if item.get("last_error"):
            lines.append(f"| Last error | {item['last_error']} |")
        if item.get("image_intent"):
            lines.append(f"| Image intent | {item['image_intent']} |")
        if item.get("page_evidence"):
            lines.append(f"| Page evidence | {item['page_evidence']} |")
        if item.get("fallback_plan"):
            lines.append(f"| Fallback plan | {item['fallback_plan']} |")
        policy = _reference_policy(item)
        if item.get("reference_image"):
            lines.append(f"| Reference image | {item['reference_image']} |")
            if policy:
                lines.append(f"| Reference approved | {_as_bool(policy.get('approved'))} |")
                confidence = _as_float(policy.get("confidence"))
                if confidence is not None:
                    lines.append(f"| Reference confidence | {confidence:.2f} |")
                if policy.get("semantic_match"):
                    lines.append(f"| Reference semantic match | {policy['semantic_match']} |")
                source = next(
                    (
                        str(policy.get(key))
                        for key in REFERENCE_SOURCE_FIELDS
                        if str(policy.get(key) or "").strip()
                    ),
                    "",
                )
                if source:
                    lines.append(f"| Reference source | {source} |")
            review = item.get("reference_image_review")
            if isinstance(review, dict):
                lines.append(f"| Reference decision | {review.get('decision', '')} |")
                reasons = review.get("skip_reasons")
                if isinstance(reasons, list) and reasons:
                    lines.append(f"| Reference skip reasons | {'; '.join(str(r) for r in reasons)} |")
        lines.append("")
        lines.append("**Prompt**:")
        lines.append("")
        lines.append(item["prompt"])
        lines.append("")
        if item.get("alt_text"):
            lines.append("**Alt Text**:")
            lines.append(f"> {item['alt_text']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_manifest_md_to_file(manifest_path: str, manifest: dict | None = None) -> str:
    """Render the manifest's Markdown sidecar next to the JSON file.

    Returns the written path. If `manifest` is omitted, it is loaded from
    `manifest_path` first.
    """
    if manifest is None:
        manifest = load_manifest(manifest_path)
    md_path = str(Path(manifest_path).with_suffix(".md"))
    Path(md_path).write_text(render_manifest_md(manifest), encoding="utf-8")
    return md_path


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate images using AI image model providers."
    )
    parser.add_argument(
        "prompt", nargs="?", default="a beautiful landscape",
        help="The text prompt for image generation."
    )
    parser.add_argument(
        "--aspect_ratio", default="1:1", choices=ALL_ASPECT_RATIOS,
        help=f"Aspect ratio. Default: 1:1."
    )
    parser.add_argument(
        "--image_size", default="1K",
        help=f"Image size. Choices: {ALL_IMAGE_SIZES}. Default: 1K. (case-insensitive)"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output directory. Default: current directory."
    )
    parser.add_argument(
        "--filename", "-f", default=None,
        help="Output filename (without extension). Overrides auto-naming."
    )
    parser.add_argument(
        "--model", "-m", default=None,
        help="Model name. Default depends on backend."
    )
    parser.add_argument(
        "--backend", "-b", default=None, choices=SUPPORTED_BACKENDS,
        help="Override IMAGE_BACKEND env var."
    )
    parser.add_argument(
        "--list-backends", action="store_true",
        help="List available backends grouped by support tier and exit."
    )
    parser.add_argument(
        "--manifest", default=None, metavar="IMAGE_PROMPTS_JSON",
        help=(
            "Path to image_prompts.json. Runs every Pending/Failed item in "
            "parallel; writes status back to the manifest as each completes."
        ),
    )
    parser.add_argument(
        "--concurrency", type=int, default=None,
        help=(
            "Max concurrent requests in --manifest mode. Defaults to "
            f"IMAGE_CONCURRENCY env or {DEFAULT_MANIFEST_CONCURRENCY}. "
            "Auto-halves on rate-limit; 1 is the serial fallback."
        ),
    )
    parser.add_argument(
        "--render-md", dest="render_md", default=None, metavar="IMAGE_PROMPTS_JSON",
        help=(
            "Render <json>'s read-only Markdown sidecar (image_prompts.md) "
            "next to the manifest, then exit. No backend / network needed."
        ),
    )
    parser.add_argument(
        "--reference-image", "-ri", default=None, metavar="PATH_OR_URL",
        help=(
            "Reference image for img2img mode. Accepts a local file path or "
            "an HTTP(S) URL. When provided, the backend uses its img2img endpoint."
        ),
    )
    parser.add_argument(
        "--disable-web-fallback",
        action="store_true",
        help=(
            "Disable automatic image_search.py fallback after repeated AI "
            "backend failures. By default fallback is enabled in --manifest mode."
        ),
    )
    parser.add_argument(
        "--fallback-failure-threshold",
        type=int,
        default=None,
        help=(
            "Switch remaining manifest rows to web image search after this many "
            "AI backend failures. Defaults to IMAGE_FALLBACK_FAILURE_THRESHOLD "
            f"or {DEFAULT_FALLBACK_FAILURE_THRESHOLD}."
        ),
    )
    parser.add_argument(
        "--fallback-consecutive-threshold",
        type=int,
        default=None,
        help=(
            "Switch to web image search after this many consecutive failed AI "
            "rows. Defaults to IMAGE_FALLBACK_CONSECUTIVE_THRESHOLD or "
            f"{DEFAULT_FALLBACK_CONSECUTIVE_THRESHOLD}."
        ),
    )
    parser.add_argument(
        "--item-attempts",
        type=int,
        default=None,
        help=(
            "Manifest-level attempts per item before counting it failed. "
            f"Defaults to IMAGE_ITEM_ATTEMPTS or {DEFAULT_ITEM_ATTEMPTS}."
        ),
    )
    parser.add_argument(
        "--fallback-search-concurrency",
        type=int,
        default=None,
        help=(
            "Max concurrent searches for fallback rows. Defaults to "
            "IMAGE_FALLBACK_SEARCH_CONCURRENCY or 1."
        ),
    )
    parser.add_argument(
        "--fallback-no-candidates",
        action="store_true",
        help="Do not save candidate pools when web fallback runs.",
    )
    parser.add_argument(
        "--fallback-max-candidates",
        type=int,
        default=8,
        help="Max web fallback candidates to save per image (default: 8).",
    )

    args = parser.parse_args()

    if args.list_backends:
        _print_backend_list()
        return

    if args.render_md:
        if not os.path.isfile(args.render_md):
            print(f"Error: manifest file not found: {args.render_md}")
            sys.exit(1)
        try:
            manifest = load_manifest(args.render_md)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        md_path = render_manifest_md_to_file(args.render_md, manifest)
        print(f"Rendered Markdown sidecar: {md_path}")
        return

    try:
        _load_image_env_file()
        _validate_runtime_config()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # CLI --backend overrides the value loaded from .env
    if args.backend:
        os.environ["IMAGE_BACKEND"] = args.backend

    backend, backend_name = _resolve_backend()
    print(f"Using backend: {backend_name}\n")

    if args.manifest:
        if not os.path.isfile(args.manifest):
            print(f"Error: manifest file not found: {args.manifest}")
            sys.exit(1)
        try:
            manifest = load_manifest(args.manifest)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        concurrency = _resolve_concurrency(args.concurrency)
        try:
            _, failed, _ = _run_manifest(
                manifest, args.manifest, backend,
                initial_concurrency=concurrency,
                image_size=args.image_size,
                output_dir=args.output or str(Path(args.manifest).parent),
                model=args.model,
                backend_name=backend_name,
                fallback_enabled=not args.disable_web_fallback,
                fallback_failure_threshold=(
                    max(1, args.fallback_failure_threshold)
                    if args.fallback_failure_threshold is not None
                    else _resolve_positive_int_env(
                        "IMAGE_FALLBACK_FAILURE_THRESHOLD",
                        DEFAULT_FALLBACK_FAILURE_THRESHOLD,
                    )
                ),
                fallback_consecutive_threshold=(
                    max(1, args.fallback_consecutive_threshold)
                    if args.fallback_consecutive_threshold is not None
                    else _resolve_positive_int_env(
                        "IMAGE_FALLBACK_CONSECUTIVE_THRESHOLD",
                        DEFAULT_FALLBACK_CONSECUTIVE_THRESHOLD,
                    )
                ),
                item_attempts=(
                    max(1, args.item_attempts)
                    if args.item_attempts is not None
                    else _resolve_positive_int_env(
                        "IMAGE_ITEM_ATTEMPTS",
                        DEFAULT_ITEM_ATTEMPTS,
                    )
                ),
                fallback_search_concurrency=(
                    max(1, args.fallback_search_concurrency)
                    if args.fallback_search_concurrency is not None
                    else _resolve_positive_int_env(
                        "IMAGE_FALLBACK_SEARCH_CONCURRENCY",
                        1,
                    )
                ),
                fallback_save_candidates=not args.fallback_no_candidates,
                fallback_max_candidates=max(1, args.fallback_max_candidates),
            )
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Partial progress preserved in manifest.")
            sys.exit(130)
        md_path = render_manifest_md_to_file(args.manifest, manifest)
        print(f"Rendered Markdown sidecar: {md_path}")
        sys.exit(1 if failed else 0)

    try:
        ref_image = _validate_reference_image(
            args.reference_image, "--reference-image"
        )
        backend.generate(
            prompt=args.prompt,
            aspect_ratio=args.aspect_ratio,
            image_size=args.image_size,
            output_dir=args.output,
            filename=args.filename,
            model=args.model,
            reference_image=ref_image,
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
