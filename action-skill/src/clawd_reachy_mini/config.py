"""Configuration for Reachy Mini integration."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReachyConfig:
    """Configuration for connecting to Reachy Mini."""

    connection_mode: str = "auto"  # "auto", "localhost_only", "network"
    media_backend: str = "default"  # "default" or "gstreamer"
    capture_dir: Path = field(default_factory=lambda: Path.home() / ".clawd-reachy-mini" / "captures")

    # Movement defaults
    default_duration: float = 1.0
    antenna_duration: float = 0.5

    # Safety limits (degrees)
    max_roll: float = 30.0
    max_pitch: float = 30.0
    max_yaw: float = 45.0

    def __post_init__(self):
        self.capture_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
_config: ReachyConfig | None = None


def get_config() -> ReachyConfig:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = ReachyConfig()
    return _config


def set_config(config: ReachyConfig) -> None:
    """Set the global config instance."""
    global _config
    _config = config
