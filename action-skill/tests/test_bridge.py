"""Tests for Reachy Mini bridge."""

import pytest
from unittest.mock import patch, MagicMock

from clawd_reachy_mini.bridge import ReachyBridge
from clawd_reachy_mini.config import ReachyConfig


@pytest.fixture
def config():
    return ReachyConfig()


@pytest.fixture
def bridge(config):
    return ReachyBridge(config=config)


class TestReachyBridge:
    def test_initial_state(self, bridge):
        assert not bridge.is_connected
        assert bridge._mini is None

    def test_disconnect_when_not_connected(self, bridge):
        result = bridge.disconnect()
        assert result["status"] == "not_connected"

    def test_move_head_when_not_connected(self, bridge):
        result = bridge.move_head(z=10, roll=5)
        assert result["status"] == "error"
        assert "Not connected" in result["message"]

    def test_get_status_when_not_connected(self, bridge):
        status = bridge.get_status()
        assert status["connected"] is False

    @patch("reachy_mini.ReachyMini")
    def test_connect_success(self, mock_reachy_class, bridge):
        mock_mini = MagicMock()
        mock_reachy_class.return_value = mock_mini

        result = bridge.connect()

        assert result["status"] == "connected"
        assert bridge.is_connected
        mock_mini.__enter__.assert_called_once()

    @patch("reachy_mini.ReachyMini")
    def test_connect_already_connected(self, mock_reachy_class, bridge):
        mock_mini = MagicMock()
        mock_reachy_class.return_value = mock_mini

        bridge.connect()
        result = bridge.connect()

        assert result["status"] == "already_connected"

    @patch("reachy_mini.ReachyMini")
    def test_disconnect_success(self, mock_reachy_class, bridge):
        mock_mini = MagicMock()
        mock_reachy_class.return_value = mock_mini

        bridge.connect()
        result = bridge.disconnect()

        assert result["status"] == "disconnected"
        assert not bridge.is_connected
        mock_mini.__exit__.assert_called_once()

    @patch("reachy_mini.ReachyMini")
    @patch("reachy_mini.utils.create_head_pose")
    def test_move_head_success(self, mock_create_pose, mock_reachy_class, bridge):
        mock_mini = MagicMock()
        mock_reachy_class.return_value = mock_mini
        mock_create_pose.return_value = {"pose": "data"}

        bridge.connect()
        result = bridge.move_head(z=10, roll=5, pitch=3, yaw=2, duration=0.5)

        assert result["status"] == "success"
        assert result["position"]["z"] == 10
        assert result["position"]["roll"] == 5
        mock_mini.goto_target.assert_called_once()

    @patch("reachy_mini.ReachyMini")
    def test_move_head_respects_safety_limits(self, mock_reachy_class, bridge):
        mock_mini = MagicMock()
        mock_reachy_class.return_value = mock_mini

        bridge.connect()

        with patch("reachy_mini.utils.create_head_pose") as mock_pose:
            mock_pose.return_value = {}
            result = bridge.move_head(roll=100)  # Exceeds max_roll of 30

        assert result["position"]["roll"] == 30  # Clamped to max

    @patch("reachy_mini.ReachyMini")
    def test_play_emotion_success(self, mock_reachy_class, bridge):
        mock_mini = MagicMock()
        mock_reachy_class.return_value = mock_mini

        bridge.connect()
        result = bridge.play_emotion("happy")

        assert result["status"] == "success"
        assert result["emotion"] == "happy"
        mock_mini.play_emotion.assert_called_with("happy")

    @patch("reachy_mini.ReachyMini")
    def test_say_success(self, mock_reachy_class, bridge):
        mock_mini = MagicMock()
        mock_reachy_class.return_value = mock_mini

        bridge.connect()
        result = bridge.say("Hello world")

        assert result["status"] == "success"
        assert result["text"] == "Hello world"
        mock_mini.say.assert_called_with(text="Hello world")


class TestConfig:
    def test_default_config(self):
        config = ReachyConfig()
        assert config.connection_mode == "auto"
        assert config.default_duration == 1.0
        assert config.max_roll == 30.0

    def test_custom_config(self):
        config = ReachyConfig(
            connection_mode="localhost_only",
            default_duration=2.0,
        )
        assert config.connection_mode == "localhost_only"
        assert config.default_duration == 2.0
