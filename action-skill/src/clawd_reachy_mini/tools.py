"""OpenClaw tool definitions for Reachy Mini control."""

from clawd_reachy_mini.bridge import get_bridge


def reachy_connect(connection_mode: str = "auto") -> dict:
    """
    Connect to the Reachy Mini robot.

    Args:
        connection_mode: Connection mode - "auto", "localhost_only", or "network"

    Returns:
        Status dict with connection result
    """
    bridge = get_bridge()
    return bridge.connect(connection_mode)


def reachy_disconnect() -> dict:
    """
    Disconnect from the Reachy Mini robot.

    Returns:
        Status dict with disconnection result
    """
    bridge = get_bridge()
    return bridge.disconnect()


def reachy_move_head(
    z: float = 0,
    roll: float = 0,
    pitch: float = 0,
    yaw: float = 0,
    duration: float = 1.0,
) -> dict:
    """
    Move the robot's head to a target position.

    Args:
        z: Vertical position in mm (default: 0)
        roll: Roll angle in degrees (default: 0)
        pitch: Pitch angle in degrees (default: 0)
        yaw: Yaw angle in degrees (default: 0)
        duration: Movement duration in seconds (default: 1.0)

    Returns:
        Status dict with movement result
    """
    bridge = get_bridge()
    return bridge.move_head(z=z, roll=roll, pitch=pitch, yaw=yaw, duration=duration)


def reachy_move_antennas(
    left: float = 0,
    right: float = 0,
    duration: float = 0.5,
) -> dict:
    """
    Move the robot's antennas.

    Args:
        left: Left antenna angle in degrees
        right: Right antenna angle in degrees
        duration: Movement duration in seconds (default: 0.5)

    Returns:
        Status dict with movement result
    """
    bridge = get_bridge()
    return bridge.move_antennas(left=left, right=right, duration=duration)


def reachy_play_emotion(emotion: str) -> dict:
    """
    Play a predefined emotion animation.

    Args:
        emotion: Name of emotion (e.g., "happy", "sad", "surprised", "angry", "thinking")

    Returns:
        Status dict with emotion result
    """
    bridge = get_bridge()
    return bridge.play_emotion(emotion)


def reachy_dance(dance_name: str) -> dict:
    """
    Trigger a dance routine.

    Args:
        dance_name: Name of the dance routine

    Returns:
        Status dict with dance result
    """
    bridge = get_bridge()
    return bridge.dance(dance_name)


def reachy_capture_image() -> dict:
    """
    Capture an image from the robot's camera.

    Returns:
        Status dict with filepath to captured image
    """
    bridge = get_bridge()
    return bridge.capture_image()


def reachy_say(text: str, voice: str | None = None) -> dict:
    """
    Make the robot speak using text-to-speech.

    Args:
        text: The text to speak
        voice: Voice to use (optional)

    Returns:
        Status dict with speech result
    """
    bridge = get_bridge()
    return bridge.say(text=text, voice=voice)


def reachy_status() -> dict:
    """
    Get the current status of the robot.

    Returns:
        Status dict with connection state and configuration
    """
    bridge = get_bridge()
    return bridge.get_status()
