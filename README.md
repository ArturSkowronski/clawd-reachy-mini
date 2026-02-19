# Clawd Reachy Mini

Voice interface that connects a Reachy Mini robot to OpenClaw over WebSocket.

[![CI](https://github.com/ArturSkowronski/clawd-reachy-mini/actions/workflows/ci.yml/badge.svg)](https://github.com/ArturSkowronski/clawd-reachy-mini/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Robot-Reachy Mini](https://img.shields.io/badge/robot-Reachy%20Mini-orange.svg)](https://www.pollen-robotics.com/reachy-mini/)

This project runs a conversation loop on a machine connected to Reachy Mini:

1. capture microphone audio
2. transcribe speech (Whisper, Faster-Whisper, or OpenAI)
3. send text to OpenClaw Gateway
4. receive AI response
5. speak response and animate the robot

## Quickstart

```bash
git clone https://github.com/ArturSkowronski/clawd-reachy-mini.git
cd clawd-reachy-mini
uv sync --extra dev --extra audio
uv run clawd-reachy --gateway-host 127.0.0.1
```

Standalone mode (no gateway, echoes what it heard):

```bash
uv run clawd-reachy --standalone
```

Robot demo mode:

```bash
uv run clawd-reachy --demo
```

## How It Works

```text
Mic/Reachy Media -> STT -> OpenClaw Gateway -> text response -> TTS + Reachy motion
```

Main modules:

- `src/clawd_reachy_mini/main.py`: CLI entrypoint and runtime wiring
- `src/clawd_reachy_mini/interface.py`: conversation loop and robot behavior
- `src/clawd_reachy_mini/gateway.py`: OpenClaw protocol + websocket client
- `src/clawd_reachy_mini/audio.py`: utterance capture and silence detection
- `src/clawd_reachy_mini/stt.py`: STT backend implementations
- `action-skill/`: OpenClaw skill package/tool wrappers

## Installation

### Prerequisites

- Python 3.10+
- Reachy Mini SDK (`reachy-mini`)
- `ffmpeg` (required for mp3->wav conversion before Reachy playback)
- macOS `afplay` is used as local playback fallback

### Install the main app

```bash
uv sync
```

Development install:

```bash
uv sync --extra dev
```

### Optional extras (main app)

- local faster transcription: `uv sync --extra local-stt`
- OpenAI cloud transcription: `uv sync --extra cloud-stt`
- local mic + TTS deps: `uv sync --extra audio`
- Reachy vision extras: `uv sync --extra vision`

### Install the action skill package

```bash
cd action-skill
uv sync --extra dev
```

Published package name for the skill is `clawd-reachy-mini-skill`.

## Usage

### Basic

```bash
uv run clawd-reachy --gateway-host <GATEWAY_IP>
```

Example:

```bash
uv run clawd-reachy \
  --gateway-host 192.168.1.100 \
  --gateway-port 18789 \
  --stt faster-whisper \
  --whisper-model base \
  --wake-word "hey reachy"
```

### CLI options

- `--gateway-host`: OpenClaw host (default: `127.0.0.1`)
- `--gateway-port`: OpenClaw port (default: `18789`)
- `--gateway-token`: bearer token for gateway auth
- `--reachy-mode`: `auto|localhost_only|network`
- `--stt`: `whisper|faster-whisper|openai`
- `--whisper-model`: `tiny|base|small|medium|large`
- `--audio-device`: input device name for local mic capture
- `--wake-word`: activate only after wake phrase is detected
- `--no-emotions`: disable emotion animations on errors/responses
- `--no-idle`: disable idle motion loop
- `--standalone`: run without gateway (local echo behavior)
- `--demo`: run a short direct robot movement demo and exit
- `-v, --verbose`: debug logs

## Environment Variables

- `OPENCLAW_HOST`: default gateway host override
- `OPENCLAW_PORT`: default gateway port override
- `OPENCLAW_TOKEN`: default gateway token
- `STT_BACKEND`: default STT backend (`whisper`, `faster-whisper`, `openai`)
- `WHISPER_MODEL`: default Whisper model
- `WAKE_WORD`: default wake word
- `OPENCLAW_OPENAI_TOKEN` or `OPENAI_API_KEY`: used for `--stt openai`

## OpenClaw Skill (`action-skill/`)

The action skill provides tool wrappers for robot control:

- connect/disconnect
- head movement
- antenna movement
- emotions and dance
- image capture
- robot speech
- status checks

Skill docs: `action-skill/SKILL.md`.

## Current Limitations

- Gateway-originated `tool.request` handling in the main app is currently a placeholder and returns an error from `src/clawd_reachy_mini/gateway.py`.
- Root CI currently runs lint for the main app and tests only for `action-skill/tests`.
- Local fallback playback uses `afplay` (macOS-specific).

## Development

From repo root:

```bash
uv sync --extra dev
uv tool run ruff check .
```

Action skill tests:

```bash
cd action-skill
uv sync --extra dev
uv run pytest
```

GitHub Actions CI runs on Python 3.10 and 3.11.
