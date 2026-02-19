"""Protocol-focused tests for GatewayClient."""

from __future__ import annotations

import asyncio

import pytest

from clawd_reachy_mini.config import Config
from clawd_reachy_mini.gateway import GatewayClient


@pytest.mark.asyncio
async def test_handle_connect_challenge_sends_connect_request():
    client = GatewayClient(Config(gateway_token="secret-token"))
    client._auth_event = asyncio.Event()
    sent: list[dict] = []

    async def fake_send_raw(data: dict) -> None:
        sent.append(data)

    client._send_raw = fake_send_raw  # type: ignore[method-assign]

    await client._handle_event("connect.challenge", {"payload": {"nonce": "n", "ts": "t"}})

    assert client._authenticated is True
    assert client._auth_event.is_set()
    assert sent
    assert sent[0]["type"] == "req"
    assert sent[0]["method"] == "connect"
    assert sent[0]["params"]["auth"]["token"] == "secret-token"


@pytest.mark.asyncio
async def test_handle_res_hello_ok_sets_register_event():
    client = GatewayClient(Config())
    client._register_event = asyncio.Event()

    await client._handle_message(
        {
            "type": "res",
            "ok": True,
            "payload": {"type": "hello-ok"},
        }
    )

    assert client._register_event.is_set()


@pytest.mark.asyncio
async def test_send_message_uses_chat_send_protocol_and_returns_text():
    client = GatewayClient(Config())
    client._connected = True
    client._ws = object()  # type: ignore[assignment]
    sent: list[dict] = []

    async def fake_send_raw(data: dict) -> None:
        sent.append(data)
        if data.get("method") == "chat.send":
            message_id = data["id"]
            future = client._response_handlers[message_id]
            future.set_result({"text": "pong"})

    client._send_raw = fake_send_raw  # type: ignore[method-assign]

    response = await client.send_message("ping")

    assert response == "pong"
    assert sent
    assert sent[0]["type"] == "req"
    assert sent[0]["method"] == "chat.send"
    params = sent[0]["params"]
    assert params["message"] == "ping"
    assert params["sessionKey"].startswith("reachy-mini:")
    assert params["idempotencyKey"] == sent[0]["id"]


@pytest.mark.asyncio
async def test_tool_request_placeholder_returns_error_response():
    client = GatewayClient(Config())
    sent: list[dict] = []

    async def fake_send_raw(data: dict) -> None:
        sent.append(data)

    client._send_raw = fake_send_raw  # type: ignore[method-assign]

    await client._handle_tool_request(
        {
            "id": "tool-1",
            "tool": "reachy_move_head",
            "arguments": {"pitch": 10},
        }
    )

    assert sent == [
        {
            "type": "tool.response",
            "id": "tool-1",
            "result": {"status": "error", "message": "Tool handler not registered"},
        }
    ]
