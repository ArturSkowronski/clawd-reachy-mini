"""Main Reachy Mini interface for OpenClaw."""

from __future__ import annotations

import asyncio
import logging
import random
from enum import Enum, auto

from clawd_reachy_mini.audio import AudioCapture, WakeWordDetector
from clawd_reachy_mini.config import Config
from clawd_reachy_mini.gateway import GatewayClient
from clawd_reachy_mini.stt import STTBackend, create_stt_backend

logger = logging.getLogger(__name__)


class InterfaceState(Enum):
    """Current state of the interface."""

    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    ERROR = auto()


class ReachyInterface:
    """
    Main interface connecting Reachy Mini to OpenClaw.

    Handles the voice conversation loop:
    1. Capture audio from Reachy Mini's microphone
    2. Transcribe speech to text
    3. Send to OpenClaw Gateway
    4. Receive response
    5. Speak response through Reachy Mini
    6. Animate robot during conversation
    """

    def __init__(self, config: Config):
        self.config = config
        self.state = InterfaceState.IDLE

        # Components
        self._reachy = None
        self._gateway: GatewayClient | None = None
        self._stt: STTBackend | None = None
        self._audio: AudioCapture | None = None
        self._wake_detector: WakeWordDetector | None = None

        # State
        self._running = False
        self._conversation_active = False

    async def start(self) -> None:
        """Start the interface."""
        logger.info("Starting Reachy Mini interface...")

        # Connect to Reachy Mini
        await self._connect_reachy()

        # Initialize components
        logger.info("🧠 Loading speech recognition model...")
        self._stt = create_stt_backend(self.config)
        await asyncio.to_thread(self._stt.preload)
        logger.info("✅ Speech recognition ready")

        self._audio = AudioCapture(self.config, self._reachy)

        if self.config.wake_word:
            self._wake_detector = WakeWordDetector(self.config.wake_word)

        # Connect to OpenClaw Gateway (unless in standalone mode)
        if not self.config.standalone_mode:
            self._gateway = GatewayClient(self.config)
            await self._gateway.connect()
        else:
            logger.info("Running in standalone mode - no gateway connection")

        # Start audio capture
        await self._audio.start()

        self._running = True
        self.state = InterfaceState.IDLE

        # Wake up the robot so it can move
        if self._reachy:
            logger.info("🦞 Waking up Reachy...")
            await asyncio.to_thread(self._reachy.wake_up)
            await asyncio.sleep(0.5)

        logger.info("✨ Reachy Mini interface started")
        logger.info("=" * 50)
        if self.config.wake_word:
            logger.info(f"Say \"{self.config.wake_word}\" to activate")
        else:
            logger.info("Speak anytime - I'm always listening!")
        logger.info("=" * 50)

        # Play startup animation - snap claws!
        # Note: antenna positions are in RADIANS (0.7 rad ≈ 40 degrees)
        if self._reachy:
            try:
                self._reachy.set_target_antenna_joint_positions([0.7, -0.7])
                await asyncio.sleep(0.2)
                self._reachy.set_target_antenna_joint_positions([-0.7, 0.7])
                await asyncio.sleep(0.2)
                self._reachy.set_target_antenna_joint_positions([0.0, 0.0])
            except Exception as e:
                logger.debug(f"Startup animation failed: {e}")

    async def stop(self) -> None:
        """Stop the interface."""
        logger.info("Stopping Reachy Mini interface...")

        self._running = False

        if self._audio:
            await self._audio.stop()

        if self._gateway:
            await self._gateway.disconnect()

        if self._reachy:
            self._reachy.__exit__(None, None, None)
            self._reachy = None

        self.state = InterfaceState.IDLE
        logger.info("Reachy Mini interface stopped")

    async def run(self) -> None:
        """Main conversation loop."""
        if not self._running:
            await self.start()

        logger.info("Entering conversation loop...")

        # Start idle animation task
        idle_task = None
        if self.config.idle_animations:
            idle_task = asyncio.create_task(self._idle_animation_loop())

        try:
            while self._running:
                await self._conversation_turn()

        except asyncio.CancelledError:
            logger.info("Conversation loop cancelled")
        except Exception as e:
            logger.error(f"Error in conversation loop: {e}")
            self.state = InterfaceState.ERROR
        finally:
            if idle_task:
                idle_task.cancel()
                try:
                    await idle_task
                except asyncio.CancelledError:
                    pass

    async def _conversation_turn(self) -> None:
        """Handle one turn of conversation."""
        # Listen for speech
        self.state = InterfaceState.LISTENING
        logger.info("🎤 Listening... (speak now)")
        audio = await self._audio.capture_utterance()

        if audio is None:
            await asyncio.sleep(0.1)
            return

        # Transcribe
        self.state = InterfaceState.PROCESSING
        logger.info("🔄 Processing speech...")
        try:
            text = await asyncio.to_thread(
                self._stt.transcribe, audio, self.config.sample_rate
            )
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return

        if not text or not text.strip():
            logger.info("(no speech detected)")
            return

        logger.info(f"📝 You said: \"{text}\"")

        # Check wake word if configured
        if self._wake_detector and not self._conversation_active:
            if not self._wake_detector.detect(text):
                logger.info(f"⏳ Waiting for wake word \"{self.config.wake_word}\"...")
                return
            logger.info(f"✅ Wake word detected!")

            # Quick lobster claw snap animation on activation (radians: 0.7 ≈ 40°)
            if self._reachy:
                logger.info("🦞 Playing wake-up claw snap!")
                try:
                    self._reachy.set_target_antenna_joint_positions([0.7, -0.7])
                    await asyncio.sleep(0.2)
                    self._reachy.set_target_antenna_joint_positions([-0.7, 0.7])
                    await asyncio.sleep(0.2)
                    self._reachy.set_target_antenna_joint_positions([0.0, 0.0])
                except Exception as e:
                    logger.error(f"Antenna animation failed: {e}")

            # Remove wake word from text
            text = text.lower().replace(self.config.wake_word.lower(), "").strip()
            self._conversation_active = True

        if not text:
            return

        # Get response - either from gateway or standalone echo
        if self.config.standalone_mode:
            # In standalone mode, just echo back what was heard
            response = f"I heard you say: {text}"
        else:
            # Send to OpenClaw and get response
            logger.info("🤖 Sending to AI...")

            # Start lobster claw animation while waiting
            animation_task = None
            if self._reachy:
                animation_task = asyncio.create_task(self._lobster_claw_animation())
                await asyncio.sleep(0.1)  # Let animation start

            try:
                response = await self._gateway.send_message(text)
            except Exception as e:
                logger.error(f"Gateway error: {e}")
                if self.config.play_emotions:
                    await self._play_emotion("sad")
                return
            finally:
                # Stop animation
                if animation_task:
                    animation_task.cancel()
                    try:
                        await animation_task
                    except asyncio.CancelledError:
                        pass
                    # Reset antennas to neutral (0 radians = center)
                    if self._reachy:
                        try:
                            self._reachy.set_target_antenna_joint_positions([0.0, 0.0])
                        except Exception:
                            pass

        logger.info(f"💬 Response: \"{response}\"")

        # Speak response
        self.state = InterfaceState.SPEAKING
        logger.info("🔊 Speaking response...")
        await self._speak(response)

        # Return to idle
        self.state = InterfaceState.IDLE
        logger.info("✅ Ready for next turn")

    async def _connect_reachy(self) -> None:
        """Connect to Reachy Mini robot."""
        try:
            from reachy_mini import ReachyMini

            kwargs = {}
            if self.config.reachy_connection_mode != "auto":
                kwargs["connection_mode"] = self.config.reachy_connection_mode
            if self.config.reachy_media_backend != "default":
                kwargs["media_backend"] = self.config.reachy_media_backend

            self._reachy = ReachyMini(**kwargs)
            self._reachy.__enter__()

            logger.info("Connected to Reachy Mini")

        except ImportError:
            logger.warning("reachy-mini not installed, running in simulation mode")
            self._reachy = None
        except Exception as e:
            logger.error(f"Failed to connect to Reachy Mini: {e}")
            self._reachy = None

    async def _speak(self, text: str) -> None:
        """Speak text through Reachy Mini using edge-tts."""
        import tempfile
        import edge_tts

        # Clean up markdown formatting for speech
        clean_text = text.replace("**", "").replace("*", "").replace("`", "")

        try:
            # Generate speech with edge-tts
            communicate = edge_tts.Communicate(clean_text, "en-US-GuyNeural")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name

            await communicate.save(temp_path)

            # Play through Reachy Mini if available
            if self._reachy and hasattr(self._reachy, "media"):
                try:
                    # Convert mp3 to wav for Reachy
                    import subprocess
                    wav_path = temp_path.replace(".mp3", ".wav")
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", temp_path, "-ar", "16000", "-ac", "1", wav_path],
                        capture_output=True,
                        check=True
                    )

                    # Play the audio
                    import wave
                    import numpy as np
                    with wave.open(wav_path, "rb") as wf:
                        audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                        audio_float = audio_data.astype(np.float32) / 32768.0

                    self._reachy.media.start_playing()
                    # Push audio in chunks with proper timing
                    sample_rate = 16000
                    chunk_size = 1600  # 100ms chunks
                    chunk_duration = chunk_size / sample_rate

                    # Start speaking animation in background
                    speak_animation_task = asyncio.create_task(
                        self._speak_animation(len(audio_float) / sample_rate)
                    )

                    # Push audio chunks
                    total_chunks = len(audio_float) // chunk_size
                    logger.info(f"🦞 Speaking with {total_chunks} chunks...")

                    for i in range(0, len(audio_float), chunk_size):
                        chunk = audio_float[i:i+chunk_size]
                        self._reachy.media.push_audio_sample(chunk)
                        await asyncio.sleep(chunk_duration * 0.9)

                    # Stop animation and reset
                    speak_animation_task.cancel()
                    try:
                        await speak_animation_task
                    except asyncio.CancelledError:
                        pass
                    logger.info("🦞 Speech done, resetting claws")
                    self._reachy.set_target_antenna_joint_positions([0.0, 0.0])
                    await asyncio.sleep(0.5)
                    self._reachy.media.stop_playing()

                    # Cleanup
                    import os
                    os.unlink(wav_path)
                except Exception as e:
                    logger.error(f"Reachy TTS playback failed: {e}")
                    # Fallback: play locally
                    import subprocess
                    subprocess.run(["afplay", temp_path], capture_output=True)
            else:
                # Fallback: play locally on Mac
                import subprocess
                subprocess.run(["afplay", temp_path], capture_output=True)

            # Cleanup
            import os
            os.unlink(temp_path)

        except Exception as e:
            logger.error(f"TTS failed: {e}")
            logger.info(f"[TTS] {text}")

    async def _play_emotion(self, emotion: str) -> None:
        """Play emotion animation on Reachy Mini."""
        if self._reachy and hasattr(self._reachy, "play_emotion"):
            try:
                await asyncio.to_thread(self._reachy.play_emotion, emotion)
            except Exception as e:
                logger.debug(f"Emotion playback failed: {e}")

    async def _speak_animation(self, duration: float) -> None:
        """Animate head bobbing while speaking to simulate talking."""
        if not self._reachy:
            return

        from reachy_mini.utils import create_head_pose

        logger.info(f"🗣️ Starting head bob animation for {duration:.1f}s")
        bob_state = 0
        try:
            while True:
                # Small head nods to simulate talking
                if bob_state == 0:
                    pose = create_head_pose(pitch=3, degrees=True)
                    bob_state = 1
                else:
                    pose = create_head_pose(pitch=-3, degrees=True)
                    bob_state = 0
                self._reachy.set_target_head_pose(pose)
                await asyncio.sleep(0.25)
        except asyncio.CancelledError:
            # Reset head to neutral
            try:
                self._reachy.set_target_head_pose(create_head_pose(pitch=0, degrees=True))
            except Exception:
                pass
            logger.info("🗣️ Head bob animation stopped")
            raise

    async def _lobster_claw_animation(self) -> None:
        """Animate antennas like lobster claws while thinking (positions in radians: 0.7 ≈ 40°)."""
        if not self._reachy:
            logger.warning("No Reachy for animation")
            return

        logger.info("🦞 Starting thinking claw animation...")
        try:
            while True:
                # Claws open
                self._reachy.set_target_antenna_joint_positions([0.7, -0.7])
                await asyncio.sleep(0.35)
                # Claws close
                self._reachy.set_target_antenna_joint_positions([-0.7, 0.7])
                await asyncio.sleep(0.35)
        except asyncio.CancelledError:
            logger.info("🦞 Claw animation stopped")
            raise

    async def _idle_animation_loop(self) -> None:
        """Play subtle idle animations when not in conversation."""
        idle_movements = [
            {"roll": 5, "pitch": 0},
            {"roll": -5, "pitch": 0},
            {"roll": 0, "pitch": 5},
            {"roll": 0, "pitch": -5},
        ]

        while self._running:
            try:
                if self.state == InterfaceState.IDLE:
                    # Small random head movement
                    if self._reachy and random.random() < 0.3:
                        movement = random.choice(idle_movements)
                        from reachy_mini.utils import create_head_pose

                        await asyncio.to_thread(
                            self._reachy.goto_target,
                            head=create_head_pose(**movement, degrees=True),
                            duration=2.0,
                        )

                await asyncio.sleep(5.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Idle animation error: {e}")
                await asyncio.sleep(5.0)
