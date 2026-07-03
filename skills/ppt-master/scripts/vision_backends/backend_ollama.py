#!/usr/bin/env python3
"""
Vision check backend for local Ollama models (LLaVA, Llama-3.2-Vision, etc.).

Purpose:
    Send rendered slide PNGs and review prompts to a local Ollama vision model,
    then parse structured findings.

Used by:
    vision_check.py when the selected vision backend is "ollama".

Configuration:
    VISION_OLLAMA_HOST   Optional Ollama API host; falls back to OLLAMA_HOST.
    VISION_OLLAMA_MODEL  Optional model override.

Dependencies:
    httpx; vision_backends.backend_common.

Public API:
    get_config(), is_available(), check().
"""

import sys

if __name__ == "__main__":
    print(__doc__)
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import os

from .backend_common import (
    encode_image_base64,
    parse_vision_response,
    retry_with_backoff,
)

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llava:13b"


def get_config(*, host=None, model=None):
    """Resolve configuration from params → env vars → defaults."""
    return {
        "host": (
            host
            or os.environ.get("VISION_OLLAMA_HOST")
            or os.environ.get("OLLAMA_HOST")
            or DEFAULT_HOST
        ).rstrip("/"),
        "model": (
            model
            or os.environ.get("VISION_OLLAMA_MODEL")
            or DEFAULT_MODEL
        ),
    }


def is_available(*, host=None, model=None) -> bool:
    """Check if Ollama is reachable."""
    cfg = get_config(host=host, model=model)
    try:
        import httpx
        resp = httpx.get(f"{cfg['host']}/api/tags", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


def check(png_path: str, prompt: str, *,
          host: str = None, model: str = None,
          api_key: str = None, base_url: str = None,
          max_tokens: int = 1500) -> dict:
    """
    Send a PNG image + prompt to local Ollama vision model.

    Returns parsed structured response dict.
    """
    import httpx

    cfg = get_config(host=host or base_url, model=model)
    img_b64 = encode_image_base64(png_path)

    payload = {
        "model": cfg["model"],
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "options": {"num_predict": max_tokens},
    }

    def _call():
        resp = httpx.post(
            f"{cfg['host']}/api/generate",
            json=payload,
            timeout=180.0,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data.get("response", "")
        return parse_vision_response(raw_text)

    return retry_with_backoff(_call)
