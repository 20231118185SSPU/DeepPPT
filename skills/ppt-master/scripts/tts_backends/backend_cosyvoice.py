"""Alibaba CosyVoice backend for narration audio generation.

Purpose:
    Generate PPT narration audio through DashScope CosyVoice and download the
    returned audio asset.

Used by:
    ``notes_to_audio.py`` when the ``cosyvoice`` narration backend is selected.

Configuration:
    Reads the caller-provided key variable, ``COSYVOICE_API_KEY``, or
    ``DASHSCOPE_API_KEY``. ``COSYVOICE_TTS_BASE_URL`` or a direct ``base_url``
    argument may override the default endpoint.

Dependencies:
    Standard library plus shared helpers from ``tts_backends.backend_common``.

Public API:
    ``DEFAULT_ENDPOINT``, ``DEFAULT_MODEL``, ``output_extension``,
    ``read_cosyvoice_api_key``, ``resolve_url``, ``generate``, and
    ``print_voices``.
"""

from __future__ import annotations

import os
from pathlib import Path

from tts_backends.backend_common import download_audio, extension_from_format, post_json, read_api_key


DEFAULT_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
DEFAULT_MODEL = "cosyvoice-v3-flash"


def output_extension(audio_format: str) -> str:
    return extension_from_format(audio_format)


def read_cosyvoice_api_key(env_name: str) -> str:
    env_names = tuple(dict.fromkeys([env_name, "COSYVOICE_API_KEY", "DASHSCOPE_API_KEY"]))
    return read_api_key(*env_names, label="CosyVoice/DashScope")


def resolve_url(base_url: str | None = None) -> str:
    base = (base_url or os.environ.get("COSYVOICE_TTS_BASE_URL") or DEFAULT_ENDPOINT).rstrip("/")
    if base.endswith("/SpeechSynthesizer"):
        return base
    return base + "/api/v1/services/audio/tts/SpeechSynthesizer"


def generate(
    text: str,
    output_path: Path,
    *,
    api_key: str,
    voice_id: str,
    model: str,
    audio_format: str,
    sample_rate: int,
    volume: int | None,
    rate: float | None,
    pitch: float | None,
    instruction: str | None,
    language_hint: str | None,
    base_url: str | None,
) -> None:
    input_payload: dict[str, object] = {
        "text": text,
        "voice": voice_id,
        "format": audio_format,
        "sample_rate": sample_rate,
    }
    if volume is not None:
        input_payload["volume"] = volume
    if rate is not None:
        input_payload["rate"] = rate
    if pitch is not None:
        input_payload["pitch"] = pitch
    if instruction:
        input_payload["instruction"] = instruction
    if language_hint:
        input_payload["language_hints"] = [language_hint]

    data = post_json(
        resolve_url(base_url),
        headers={"Authorization": f"Bearer {api_key}"},
        payload={
            "model": model,
            "input": input_payload,
        },
        timeout=180,
    )
    audio = (data.get("output") or {}).get("audio") or {}
    audio_url = audio.get("url")
    if not audio_url:
        raise RuntimeError(f"CosyVoice response missing audio URL: {data}")
    download_audio(audio_url, output_path)


def print_voices() -> None:
    print("CosyVoice voices are selected by voice.")
    print("Use a system voice name or a cloned/designed voice_id from CosyVoice.")
    print("Example system voice from Alibaba Cloud docs: longanyang")
