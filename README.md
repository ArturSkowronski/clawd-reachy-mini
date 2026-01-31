# Clawd Reachy Mini

This project provides a voice-controlled interface for the [Reachy Mini](https://pollen-robotics.com/reachy-mini/) robot, acting as a client for the **OpenClaw** AI system.

It allows Reachy Mini to function as an embodied agent that can see, hear, speak, and move based on intelligence provided by OpenClaw.

## About OpenClaw & Clawd

**OpenClaw** (formerly known as *Clawdbot*) is an open-source autonomous AI personal assistant project designed to automate complex digital tasks and maintain persistent context.

*   **Clawd** refers to the specific persona or instance of the AI assistant (often powered by Anthropic's Claude models) that this robot interface is designed to embody.
*   **The Goal**: By connecting Reachy Mini to OpenClaw, we extend the assistant's capabilities from the digital realm (managing emails, calendars, code) into the physical world (gestures, vision, physical presence).

## Architecture

The system operates on a client-server architecture:

1.  **Robot Client (`src/clawd_reachy_mini`)**:
    *   Runs locally on the computer connected to the Reachy Mini.
    *   **Audio I/O**: Captures user speech via microphone and plays TTS responses.
    *   **STT (Speech-to-Text)**: Transcribes audio locally (using Whisper) or via cloud API before sending to the Gateway.
    *   **Robot Control**: Directly interfaces with the Reachy Mini hardware (USB/Network) to control motors, lights, and read sensors.
    *   **Gateway Client**: Maintains a WebSocket connection to the OpenClaw Gateway.

2.  **OpenClaw Gateway (Server)**:
    *   The central AI brain (LLM).
    *   Receives text input from the robot.
    *   Processes the input and determines the appropriate response (speech) or action (tool call).
    *   Sends commands back to the robot client.

3.  **Skill Definition (`action-skill/`)**:
    *   Defines the capabilities (Tools) available to the AI, such as "Move Head", "Dance", "Capture Image".
    *   These definitions tell OpenClaw what the robot can do.

## Folder Structure

*   `src/clawd_reachy_mini/`: Main application code.
    *   `main.py`: Entry point and configuration.
    *   `interface.py`: Manages the interaction loop (Listen -> Transcribe -> Send -> Speak).
    *   `gateway.py`: Handles WebSocket communication with OpenClaw.
    *   `bridge.py`: (In `action-skill` but used by tools) Low-level robot control logic.
    *   `audio.py` & `stt.py`: Audio capture and transcription.
*   `action-skill/`: The "Skill" package for OpenClaw.
    *   `SKILL.md`: Documentation of available tools for the LLM.
    *   `src/clawd_reachy_mini/tools.py`: Python implementation of the tools.

## Installation

1.  **Prerequisites**:
    *   Python 3.10+
    *   Reachy Mini SDK (`reachy-mini`)
    *   `ffmpeg` (for audio processing)

2.  **Install the package**:
    ```bash
    pip install .
    # OR for development
    pip install -e ".[dev]"
    ```

3.  **Install Optional Dependencies**:
    *   For local speech recognition: `pip install ".[local-stt]"`
    *   For vision support: `pip install ".[vision]"`

## Usage

Run the client to connect your Reachy Mini to OpenClaw:

```bash
clawd-reachy --gateway-host <YOUR_GATEWAY_IP>
```

### Configuration Options

*   `--gateway-host`: Hostname/IP of the OpenClaw Gateway (default: 127.0.0.1).
*   `--gateway-port`: Port of the Gateway (default: 18789).
*   `--reachy-mode`: Connection mode for the robot (`auto`, `localhost_only`, `network`).
*   `--stt`: Speech-to-text backend (`whisper`, `faster-whisper`, `openai`).
*   `--wake-word`: Optional wake word to trigger listening (e.g., "Hey Reachy").

### Example

```bash
clawd-reachy --gateway-host 192.168.1.100 --wake-word "Hey Reachy" --stt faster-whisper
```

## How It Works (Internal Flow)

1.  **Startup**: The `ReachyInterface` connects to the robot and the OpenClaw Gateway via WebSocket.
2.  **Listening**: The system listens for audio. If a wake word is configured, it waits for that phrase.
3.  **Transcription**: Speech is converted to text using the configured STT backend (e.g., Whisper).
4.  **Gateway Request**: The text is sent to OpenClaw as a `message.send` event.
5.  **AI Processing**: OpenClaw processes the text.
    *   If it's a conversational reply, it sends back text.
    *   If it requires an action (e.g., "raise your hand"), it sends a `tool.request`.
6.  **Action/Response**:
    *   **Text**: The robot speaks the response using its TTS engine.
    *   **Tool**: The client executes the requested robot command (e.g., `reachy_move_head`). *Note: Tool execution integration is currently in progress.*
7.  **Loop**: The system returns to the listening state.
