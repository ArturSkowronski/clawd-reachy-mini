"""Configuration for Reachy Mini OpenClaw interface."""

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class Config:
    """Configuration for the Reachy Mini interface."""

    # OpenClaw Gateway
    gateway_host: str = "127.0.0.1"
    gateway_port: int = 18789
    gateway_token: str | None = None

    # Reachy Mini connection
    reachy_connection_mode: str = "auto"  # "auto", "localhost_only", "network"
    reachy_media_backend: str = "default"  # "default" or "gstreamer"

    # Speech-to-text
    stt_backend: str = "whisper"  # "whisper", "faster-whisper", "openai"
    whisper_model: str = "base"  # "tiny", "base", "small", "medium", "large"
    openai_api_key: str | None = None

    # Text-to-speech (uses Reachy's built-in TTS)
    tts_voice: str | None = None

    # Audio settings
    sample_rate: int = 16000
    silence_threshold: float = 0.01
    silence_duration: float = 1.5  # seconds of silence before processing
    max_recording_duration: float = 30.0  # max seconds per utterance

    # Behavior
    wake_word: str | None = None  # None = always listening, or set e.g. "hey reachy"
    play_emotions: bool = True  # React with emotions during conversation
    idle_animations: bool = True  # Play idle animations when waiting

    # Paths
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".clawd-reachy-mini" / "cache")

    def __post_init__(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load from environment
        if not self.gateway_token:
            self.gateway_token = os.environ.get("OPENCLAW_TOKEN")
        if not self.openai_api_key:
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")

    @property
    def gateway_url(self) -> str:
        return f"ws://{self.gateway_host}:{self.gateway_port}"


def load_config() -> Config:
    """Load configuration from environment and defaults."""
    return Config(
        gateway_host=os.environ.get("OPENCLAW_HOST", "127.0.0.1"),
        gateway_port=int(os.environ.get("OPENCLAW_PORT", "18789")),
        stt_backend=os.environ.get("STT_BACKEND", "whisper"),
        whisper_model=os.environ.get("WHISPER_MODEL", "base"),
        wake_word=os.environ.get("WAKE_WORD"),
    )
