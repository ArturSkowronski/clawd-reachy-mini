"""Bridge between OpenClaw and Reachy Mini SDK."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from clawd_reachy_mini.config import get_config, ReachyConfig

if TYPE_CHECKING:
    from reachy_mini import ReachyMini

logger = logging.getLogger(__name__)


class ReachyBridge:
    """Manages connection and communication with Reachy Mini robot."""

    def __init__(self, config: ReachyConfig | None = None):
        self.config = config or get_config()
        self._mini: ReachyMini | None = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if connected to the robot."""
        return self._connected and self._mini is not None

    def connect(self, connection_mode: str | None = None) -> dict:
        """Connect to the Reachy Mini robot."""
        if self.is_connected:
            return {"status": "already_connected"}

        try:
            from reachy_mini import ReachyMini

            mode = connection_mode or self.config.connection_mode
            kwargs = {}
            if mode != "auto":
                kwargs["connection_mode"] = mode

            self._mini = ReachyMini(**kwargs)
            self._mini.__enter__()
            self._connected = True

            logger.info("Connected to Reachy Mini")
            return {"status": "connected", "mode": mode}

        except ImportError:
            return {"status": "error", "message": "reachy-mini package not installed"}
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return {"status": "error", "message": str(e)}

    def disconnect(self) -> dict:
        """Disconnect from the Reachy Mini robot."""
        if not self.is_connected:
            return {"status": "not_connected"}

        try:
            self._mini.__exit__(None, None, None)
            self._mini = None
            self._connected = False

            logger.info("Disconnected from Reachy Mini")
            return {"status": "disconnected"}

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            return {"status": "error", "message": str(e)}

    def move_head(
        self,
        z: float = 0,
        roll: float = 0,
        pitch: float = 0,
        yaw: float = 0,
        duration: float | None = None,
    ) -> dict:
        """Move the robot's head to target position."""
        if not self.is_connected:
            return {"status": "error", "message": "Not connected to robot"}

        try:
            from reachy_mini.utils import create_head_pose

            # Apply safety limits
            roll = max(-self.config.max_roll, min(self.config.max_roll, roll))
            pitch = max(-self.config.max_pitch, min(self.config.max_pitch, pitch))
            yaw = max(-self.config.max_yaw, min(self.config.max_yaw, yaw))

            dur = duration or self.config.default_duration

            self._mini.goto_target(
                head=create_head_pose(z=z, roll=roll, pitch=pitch, yaw=yaw, degrees=True, mm=True),
                duration=dur,
            )

            return {
                "status": "success",
                "position": {"z": z, "roll": roll, "pitch": pitch, "yaw": yaw},
                "duration": dur,
            }

        except Exception as e:
            logger.error(f"Failed to move head: {e}")
            return {"status": "error", "message": str(e)}

    def move_antennas(
        self,
        left: float = 0,
        right: float = 0,
        duration: float | None = None,
    ) -> dict:
        """Move the robot's antennas."""
        if not self.is_connected:
            return {"status": "error", "message": "Not connected to robot"}

        try:
            dur = duration or self.config.antenna_duration

            self._mini.goto_target(
                left_antenna=left,
                right_antenna=right,
                duration=dur,
            )

            return {
                "status": "success",
                "antennas": {"left": left, "right": right},
                "duration": dur,
            }

        except Exception as e:
            logger.error(f"Failed to move antennas: {e}")
            return {"status": "error", "message": str(e)}

    def play_emotion(self, emotion: str) -> dict:
        """Play an emotion animation."""
        if not self.is_connected:
            return {"status": "error", "message": "Not connected to robot"}

        try:
            self._mini.play_emotion(emotion)
            return {"status": "success", "emotion": emotion}

        except Exception as e:
            logger.error(f"Failed to play emotion: {e}")
            return {"status": "error", "message": str(e)}

    def dance(self, dance_name: str) -> dict:
        """Trigger a dance routine."""
        if not self.is_connected:
            return {"status": "error", "message": "Not connected to robot"}

        try:
            self._mini.dance(dance_name)
            return {"status": "success", "dance": dance_name}

        except Exception as e:
            logger.error(f"Failed to dance: {e}")
            return {"status": "error", "message": str(e)}

    def capture_image(self) -> dict:
        """Capture an image from the robot's camera."""
        if not self.is_connected:
            return {"status": "error", "message": "Not connected to robot"}

        try:
            frame = self._mini.camera.get_frame()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.config.capture_dir / f"capture_{timestamp}.jpg"

            # Save using OpenCV if available
            try:
                import cv2
                cv2.imwrite(str(filepath), frame)
            except ImportError:
                # Fallback: assume frame has a save method or is PIL Image
                if hasattr(frame, "save"):
                    frame.save(filepath)
                else:
                    return {"status": "error", "message": "cv2 not available for saving images"}

            return {"status": "success", "filepath": str(filepath)}

        except Exception as e:
            logger.error(f"Failed to capture image: {e}")
            return {"status": "error", "message": str(e)}

    def say(self, text: str, voice: str | None = None) -> dict:
        """Make the robot speak using TTS."""
        if not self.is_connected:
            return {"status": "error", "message": "Not connected to robot"}

        try:
            kwargs = {"text": text}
            if voice:
                kwargs["voice"] = voice

            self._mini.say(**kwargs)
            return {"status": "success", "text": text}

        except Exception as e:
            logger.error(f"Failed to speak: {e}")
            return {"status": "error", "message": str(e)}

    def get_status(self) -> dict:
        """Get current robot status."""
        return {
            "connected": self.is_connected,
            "config": {
                "connection_mode": self.config.connection_mode,
                "media_backend": self.config.media_backend,
            },
        }


# Global bridge instance for skill tools
_bridge: ReachyBridge | None = None


def get_bridge() -> ReachyBridge:
    """Get or create the global bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = ReachyBridge()
    return _bridge
