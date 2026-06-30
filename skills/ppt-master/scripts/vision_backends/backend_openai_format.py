#!/usr/bin/env python3
"""
Vision check backend for OpenAI Chat Completions compatible endpoints.

Supports: OpenAI GPT-4o, Azure OpenAI, DeepSeek-VL, Qwen-VL (DashScope compat),
SiliconFlow, OpenRouter, Gemini (via OpenAI compat), and any provider exposing
the standard /v1/chat/completions endpoint with vision support.

Configuration (env vars):
  VISION_OPENAI_API_KEY   — API key (falls back to OPENAI_API_KEY)
  VISION_OPENAI_BASE_URL  — Base URL (default: https://api.openai.com/v1)
  VISION_OPENAI_MODEL     — Model name (default: gpt-4o)
"""

import sys

if __name__ == "__main__":
    print(__doc__)
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import json
import os

from .backend_common import (
    detect_media_type,
    encode_image_base64,
    parse_vision_response,
    retry_with_backoff,
)

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_MAX_TOKENS = 1500


def get_config(*, api_key=None, base_url=None, model=None):
    """Resolve configuration from params → env vars → defaults."""
    return {
        "api_key": (
            api_key
            or os.environ.get("VISION_OPENAI_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        ),
        "base_url": (
            base_url
            or os.environ.get("VISION_OPENAI_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/"),
        "model": (
            model
            or os.environ.get("VISION_OPENAI_MODEL")
            or os.environ.get("OPENAI_MODEL")
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
    Send a PNG image + prompt to an OpenAI-format vision endpoint.

    Returns parsed structured response dict.
    """
    import httpx

    cfg = get_config(api_key=api_key, base_url=base_url, model=model)
    if not cfg["api_key"]:
        raise RuntimeError("No API key found for OpenAI-format vision backend. "
                           "Set VISION_OPENAI_API_KEY or OPENAI_API_KEY.")

    img_b64 = encode_image_base64(png_path)
    media_type = detect_media_type(png_path)

    payload = {
        "model": cfg["model"],
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:{media_type};base64,{img_b64}"
                }}
            ]
        }],
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }

    def _call():
        resp = httpx.post(
            f"{cfg['base_url']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=90.0,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        return parse_vision_response(raw_text)

    return retry_with_backoff(_call)
