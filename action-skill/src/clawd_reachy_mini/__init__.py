"""OpenClaw skill for Reachy Mini robot integration."""

from clawd_reachy_mini.bridge import ReachyBridge
from clawd_reachy_mini.tools import (
    reachy_connect,
    reachy_disconnect,
    reachy_move_head,
    reachy_move_antennas,
    reachy_play_emotion,
    reachy_dance,
    reachy_capture_image,
    reachy_say,
    reachy_status,
)

__version__ = "0.1.0"

__all__ = [
    "ReachyBridge",
    "reachy_connect",
    "reachy_disconnect",
    "reachy_move_head",
    "reachy_move_antennas",
    "reachy_play_emotion",
    "reachy_dance",
    "reachy_capture_image",
    "reachy_say",
    "reachy_status",
]
