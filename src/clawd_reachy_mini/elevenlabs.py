"""ElevenLabs TTS support for Reachy Mini."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from typing import Any

import httpx


ELEVENLABS_API_BASE_URL = "https://api.elevenlabs.io/v1"
# Default to a premade voice so free-tier users can use TTS via API by default.
DEFAULT_ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George


@dataclass(frozen=True)
class ElevenLabsConfig:
    api_key: str
    voice_id: str
    model_id: str = "eleven_multilingual_v2"
    # NOTE: `wav_44100` requires Pro+ on ElevenLabs. `mp3_44100_128` works on Free.
    output_format: str = "mp3_44100_128"


def _accept_header_for_output_format(output_format: str) -> str:
    fmt = output_format.lower()
    if fmt.startswith("wav"):
        return "audio/wav"
    return "audio/mpeg"


def _suffix_for_output_format(output_format: str) -> str:
    fmt = output_format.lower()
    if fmt.startswith("wav"):
        return ".wav"
    return ".mp3"


_VOICE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _validate_voice_id(voice_id: str) -> str:
    # Voice id is interpolated into a URL path. Keep it strict to prevent
    # path traversal / URL manipulation if a user passes a crafted value.
    v = voice_id.strip()
    if not v:
        raise ValueError("ElevenLabs voice id must be non-empty.")
    if not _VOICE_ID_RE.fullmatch(v):
        raise ValueError(
            "Invalid ElevenLabs voice id. Allowed characters: A-Z a-z 0-9 _ -"
        )
    return v


def load_elevenlabs_config(
    *,
    api_key: str | None = None,
    voice_id: str | None = None,
    model_id: str | None = None,
    output_format: str | None = None,
) -> ElevenLabsConfig:
    # Support REACHY_* overrides for convenience in robot deployments.
    resolved_api_key = (
        api_key
        or os.getenv("REACHY_ELEVENLABS_API_KEY")
        or os.getenv("ELEVENLABS_API_KEY")
    )
    resolved_voice_id = (
        voice_id
        or os.getenv("REACHY_ELEVENLABS_VOICE_ID")
        or os.getenv("ELEVENLABS_VOICE_ID")
        or DEFAULT_ELEVENLABS_VOICE_ID
    )

    if not resolved_api_key:
        raise ValueError(
            "Missing ElevenLabs API key: set `REACHY_ELEVENLABS_API_KEY` or `ELEVENLABS_API_KEY`."
        )

    return ElevenLabsConfig(
        api_key=resolved_api_key,
        voice_id=_validate_voice_id(resolved_voice_id),
        model_id=model_id
        or os.getenv("REACHY_ELEVENLABS_MODEL_ID")
        or os.getenv("ELEVENLABS_MODEL_ID")
        or "eleven_multilingual_v2",
        output_format=output_format
        or os.getenv("REACHY_ELEVENLABS_OUTPUT_FORMAT")
        or os.getenv("ELEVENLABS_OUTPUT_FORMAT")
        or "mp3_44100_128",
    )


async def elevenlabs_tts_bytes(
    *,
    text: str,
    config: ElevenLabsConfig,
    voice_settings: dict[str, Any] | None = None,
    timeout_s: float = 30.0,
) -> bytes:
    if not text.strip():
        raise ValueError("Text must be non-empty.")

    payload: dict[str, Any] = {"text": text, "model_id": config.model_id}
    if voice_settings:
        payload["voice_settings"] = voice_settings

    url = f"{ELEVENLABS_API_BASE_URL}/text-to-speech/{config.voice_id}"

    headers = {
        "xi-api-key": config.api_key,
        "Content-Type": "application/json",
        "Accept": _accept_header_for_output_format(config.output_format),
    }

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.post(
            url,
            params={"output_format": config.output_format},
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.content


async def elevenlabs_tts_to_temp_audio_file(
    *,
    text: str,
    config: ElevenLabsConfig,
    voice_settings: dict[str, Any] | None = None,
    timeout_s: float = 30.0,
) -> str:
    audio_bytes = await elevenlabs_tts_bytes(
        text=text,
        config=config,
        voice_settings=voice_settings,
        timeout_s=timeout_s,
    )

    tmp = tempfile.NamedTemporaryFile(
        prefix="clawd_reachy_elevenlabs_",
        suffix=_suffix_for_output_format(config.output_format),
        delete=False,
    )
    try:
        tmp.write(audio_bytes)
        tmp.flush()
        return tmp.name
    finally:
        tmp.close()
