#!/usr/bin/env python3
"""
Vision check backend for Anthropic Messages API compatible endpoints.

Supports: Anthropic Claude (Sonnet/Haiku/Opus), AWS Bedrock Claude,
and any provider exposing the Anthropic Messages format.

Configuration (env vars):
  VISION_ANTHROPIC_API_KEY   — API key (falls back to ANTHROPIC_API_KEY)
  VISION_ANTHROPIC_BASE_URL  — Base URL (default: https://api.anthropic.com)
  VISION_ANTHROPIC_MODEL     — Model name (default: claude-sonnet-4-20250514)
"""

import sys

if __name__ == "__main__":
    print(__doc__)
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import os

from .backend_common import (
    detect_media_type,
    encode_image_base64,
    parse_vision_response,
    retry_with_backoff,
)

DEFAULT_BASE_URL = "https://api.anthropic.com"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 1500
API_VERSION = "2023-06-01"


def get_config(*, api_key=None, base_url=None, model=None):
    """Resolve configuration from params → env vars → defaults."""
    return {
        "api_key": (
            api_key
            or os.environ.get("VISION_ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
            or ""
        ),
        "base_url": (
            base_url
            or os.environ.get("VISION_ANTHROPIC_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/"),
        "model": (
            model
            or os.environ.get("VISION_ANTHROPIC_MODEL")
            or DEFAULT_MODEL
        ),
    }


def is_available(*, api_key=None, base_url=None, model=None) -> bool:
    """Check if this backend has valid configuration."""
    cfg = get_config(api_key=api_key, base_url=base_url, model=model)
    return bool(cfg["api_key"])


def check(png_path: str, prompt: str, *,
          api_key: str = None, base_url: str = None, model: str = None,
          max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
    """
    Send a PNG image + prompt to an Anthropic-format vision endpoint.

    Returns parsed structured response dict.
    """
    import httpx

    cfg = get_config(api_key=api_key, base_url=base_url, model=model)
    if not cfg["api_key"]:
        raise RuntimeError("No API key found for Anthropic-format vision backend. "
                           "Set VISION_ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.")

    img_b64 = encode_image_base64(png_path)
    media_type = detect_media_type(png_path)

    payload = {
        "model": cfg["model"],
        "max_tokens": max_tokens,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": img_b64,
                }}
            ]
        }]
    }

    headers = {
        "x-api-key": cfg["api_key"],
        "anthropic-version": API_VERSION,
        "Content-Type": "application/json",
    }

    def _call():
        resp = httpx.post(
            f"{cfg['base_url']}/v1/messages",
            headers=headers,
            json=payload,
            timeout=90.0,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["content"][0]["text"]
        return parse_vision_response(raw_text)

    return retry_with_backoff(_call)
