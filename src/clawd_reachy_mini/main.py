"""Main entry point for Reachy Mini OpenClaw interface."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys

from clawd_reachy_mini.config import Config, load_config
from clawd_reachy_mini.interface import ReachyInterface


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Reachy Mini interface for OpenClaw",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    # Connection options
    parser.add_argument(
        "--gateway-host",
        default="127.0.0.1",
        help="OpenClaw Gateway host",
    )
    parser.add_argument(
        "--gateway-port",
        type=int,
        default=18789,
        help="OpenClaw Gateway port",
    )
    parser.add_argument(
        "--gateway-token",
        help="OpenClaw Gateway authentication token",
    )

    # Reachy options
    parser.add_argument(
        "--reachy-mode",
        choices=["auto", "localhost_only", "network"],
        default="auto",
        help="Reachy Mini connection mode",
    )

    # STT options
    parser.add_argument(
        "--stt",
        choices=["whisper", "faster-whisper", "openai"],
        default="whisper",
        help="Speech-to-text backend",
    )
    parser.add_argument(
        "--whisper-model",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size",
    )

    # Behavior options
    parser.add_argument(
        "--wake-word",
        help="Wake word to activate listening (e.g., 'hey reachy')",
    )
    parser.add_argument(
        "--no-emotions",
        action="store_true",
        help="Disable emotion animations",
    )
    parser.add_argument(
        "--no-idle",
        action="store_true",
        help="Disable idle animations",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Run in standalone mode without OpenClaw Gateway (for testing robot)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a quick demo of robot capabilities",
    )

    return parser.parse_args()


def create_config(args: argparse.Namespace) -> Config:
    """Create config from command line arguments."""
    config = load_config()

    # Override with CLI arguments
    config.gateway_host = args.gateway_host
    config.gateway_port = args.gateway_port
    if args.gateway_token:
        config.gateway_token = args.gateway_token

    config.reachy_connection_mode = args.reachy_mode
    config.stt_backend = args.stt
    config.whisper_model = args.whisper_model
    config.wake_word = args.wake_word
    config.play_emotions = not args.no_emotions
    config.idle_animations = not args.no_idle
    config.standalone_mode = args.standalone

    return config


async def run_demo() -> int:
    """Run a quick demo of robot capabilities."""
    logging.info("Starting Reachy Mini demo...")

    try:
        from reachy_mini import ReachyMini
        from reachy_mini.utils import create_head_pose
    except ImportError:
        logging.error("reachy-mini package not installed")
        return 1

    reachy = None
    try:
        reachy = ReachyMini()
        reachy.__enter__()
        logging.info("Connected to Reachy Mini!")

        # Wake up the robot
        logging.info("Waking up robot...")
        reachy.wake_up()
        await asyncio.sleep(1.0)

        # Move head - nod yes
        logging.info("Moving head - nodding yes...")
        for _ in range(2):
            head_pose = create_head_pose(roll=0, pitch=10, degrees=True)
            reachy.goto_target(head=head_pose, duration=0.3)
            await asyncio.sleep(0.4)
            head_pose = create_head_pose(roll=0, pitch=-10, degrees=True)
            reachy.goto_target(head=head_pose, duration=0.3)
            await asyncio.sleep(0.4)

        # Return to center
        head_pose = create_head_pose(roll=0, pitch=0, degrees=True)
        reachy.goto_target(head=head_pose, duration=0.5)
        await asyncio.sleep(0.6)

        # Move head - shake no
        logging.info("Moving head - shaking no...")
        for _ in range(2):
            head_pose = create_head_pose(roll=10, pitch=0, degrees=True)
            reachy.goto_target(head=head_pose, duration=0.3)
            await asyncio.sleep(0.4)
            head_pose = create_head_pose(roll=-10, pitch=0, degrees=True)
            reachy.goto_target(head=head_pose, duration=0.3)
            await asyncio.sleep(0.4)

        # Return to center
        head_pose = create_head_pose(roll=0, pitch=0, degrees=True)
        reachy.goto_target(head=head_pose, duration=0.5)
        await asyncio.sleep(0.6)

        # Move antennas (takes a list: [left, right])
        logging.info("Moving antennas...")
        reachy.set_target_antenna_joint_positions([30.0, -30.0])
        await asyncio.sleep(0.5)
        reachy.set_target_antenna_joint_positions([-30.0, 30.0])
        await asyncio.sleep(0.5)
        reachy.set_target_antenna_joint_positions([0.0, 0.0])
        await asyncio.sleep(0.5)

        logging.info("Demo completed successfully!")

    except Exception as e:
        logging.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if reachy:
            reachy.__exit__(None, None, None)

    return 0


async def async_main(config: Config) -> int:
    """Async main function."""
    interface = ReachyInterface(config)

    # Handle shutdown signals
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def signal_handler():
        logging.info("Shutdown signal received")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # Run interface until shutdown
        run_task = asyncio.create_task(interface.run())
        shutdown_task = asyncio.create_task(shutdown_event.wait())

        done, pending = await asyncio.wait(
            [run_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1
    finally:
        await interface.stop()

    return 0


def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)

    # Handle demo mode
    if args.demo:
        logging.info("Running Reachy Mini demo")
        exit_code = asyncio.run(run_demo())
        sys.exit(exit_code)

    config = create_config(args)

    if config.standalone_mode:
        logging.info("Starting Reachy Mini in standalone mode (no gateway)")
    else:
        logging.info("Starting Reachy Mini OpenClaw interface")
        logging.info(f"Gateway: {config.gateway_url}")

    logging.info(f"STT: {config.stt_backend} ({config.whisper_model})")
    if config.wake_word:
        logging.info(f"Wake word: {config.wake_word}")

    exit_code = asyncio.run(async_main(config))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
