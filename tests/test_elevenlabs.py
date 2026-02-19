"""Tests for ElevenLabs configuration loading."""

from __future__ import annotations

import pytest

from clawd_reachy_mini.elevenlabs import (
    DEFAULT_ELEVENLABS_VOICE_ID,
    load_elevenlabs_config,
)


def test_load_config_uses_default_voice_id_when_env_missing(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-api-key")
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)
    monkeypatch.delenv("REACHY_ELEVENLABS_VOICE_ID", raising=False)

    config = load_elevenlabs_config()

    assert config.voice_id == DEFAULT_ELEVENLABS_VOICE_ID


def test_load_config_uses_env_voice_id_when_present(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-api-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "env-voice-id")
    monkeypatch.delenv("REACHY_ELEVENLABS_VOICE_ID", raising=False)

    config = load_elevenlabs_config()

    assert config.voice_id == "env-voice-id"


def test_load_config_prefers_reachy_prefixed_env(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-api-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "env-voice-id")
    monkeypatch.setenv("REACHY_ELEVENLABS_VOICE_ID", "reachy-voice-id")

    config = load_elevenlabs_config()

    assert config.voice_id == "reachy-voice-id"


def test_load_config_rejects_invalid_voice_id(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-api-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "../evil")
    monkeypatch.delenv("REACHY_ELEVENLABS_VOICE_ID", raising=False)

    with pytest.raises(ValueError, match="Invalid ElevenLabs voice id"):
        load_elevenlabs_config()


def test_load_config_strips_voice_id(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-api-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "  env-voice-id  ")
    monkeypatch.delenv("REACHY_ELEVENLABS_VOICE_ID", raising=False)

    config = load_elevenlabs_config()

    assert config.voice_id == "env-voice-id"
