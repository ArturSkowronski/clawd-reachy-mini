# Reachy Mini

Control the Reachy Mini robot through natural language commands.

## Description

This skill enables OpenClaw to interact with a Reachy Mini robot, allowing you to:
- Move the robot's head and antennas
- Trigger emotions and dance animations
- Capture images from the robot's camera
- Make the robot speak using text-to-speech

## Setup

1. Connect your Reachy Mini via USB (Lite) or ensure it's on the same network (Wireless)
2. Install dependencies: `uv pip install clawd-reachy-mini-skill`
3. The skill auto-discovers the robot on first use

## Tools

### `reachy_connect`
Connect to the Reachy Mini robot.
- `connection_mode` (optional): "auto", "localhost_only", or "network"

### `reachy_disconnect`
Safely disconnect from the robot.

### `reachy_move_head`
Move the robot's head to a target position.
- `z`: Vertical position in mm (default: 0)
- `roll`: Roll angle in degrees (default: 0)
- `pitch`: Pitch angle in degrees (default: 0)
- `yaw`: Yaw angle in degrees (default: 0)
- `duration`: Movement duration in seconds (default: 1.0)

### `reachy_move_antennas`
Move the robot's antennas.
- `left`: Left antenna angle in degrees
- `right`: Right antenna angle in degrees
- `duration`: Movement duration in seconds (default: 0.5)

### `reachy_play_emotion`
Play a predefined emotion animation.
- `emotion`: Name of emotion (e.g., "happy", "sad", "surprised", "angry", "thinking")

### `reachy_dance`
Trigger a dance routine.
- `dance_name`: Name of the dance routine

### `reachy_capture_image`
Capture an image from the robot's camera.
- Returns: Path to the captured image file

### `reachy_say`
Make the robot speak using text-to-speech.
- `text`: The text to speak
- `voice` (optional): Voice to use

### `reachy_status`
Get the current status of the robot (connection state, position, etc.).

## Examples

"Move Reachy's head up and to the left"
"Make Reachy do a happy dance"
"Take a picture with Reachy's camera"
"Tell Reachy to say hello"
"Show me Reachy's current status"

## Notes

- The robot must be powered on and connected before using movement commands
- Camera features require the `vision` extra: `pip install clawd-reachy-mini-skill[vision]`
- Audio features require the `audio` extra: `pip install clawd-reachy-mini-skill[audio]`
- macOS is supported for USB connections; WebRTC streaming is Linux-only
