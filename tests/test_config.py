"""Tests for runtime configuration loading."""

from __future__ import annotations

from clawd_reachy_mini.config import Config, load_config


def test_config_loads_tokens_from_environment(monkeypatch):
    monkeypatch.setenv("OPENCLAW_TOKEN", "gateway-token")
    monkeypatch.setenv("OPENCLAW_OPENAI_TOKEN", "openai-token")

    config = Config()

    assert config.gateway_token == "gateway-token"
    assert config.openai_api_key == "openai-token"
    assert config.cache_dir.exists()


def test_load_config_reads_environment_overrides(monkeypatch):
    monkeypatch.setenv("OPENCLAW_HOST", "10.0.0.9")
    monkeypatch.setenv("OPENCLAW_PORT", "19999")
    monkeypatch.setenv("STT_BACKEND", "faster-whisper")
    monkeypatch.setenv("WHISPER_MODEL", "small")
    monkeypatch.setenv("WAKE_WORD", "hey reachy")

    config = load_config()

    assert config.gateway_host == "10.0.0.9"
    assert config.gateway_port == 19999
    assert config.stt_backend == "faster-whisper"
    assert config.whisper_model == "small"
    assert config.wake_word == "hey reachy"
    assert config.gateway_url == "ws://10.0.0.9:19999"
