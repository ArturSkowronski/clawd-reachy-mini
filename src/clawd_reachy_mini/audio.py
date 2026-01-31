"""Audio capture and processing for Reachy Mini."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass

import numpy as np

from clawd_reachy_mini.config import Config

logger = logging.getLogger(__name__)


@dataclass
class AudioChunk:
    """A chunk of captured audio."""

    data: np.ndarray
    sample_rate: int
    timestamp: float


class AudioCapture:
    """Captures audio from Reachy Mini's microphone."""

    def __init__(self, config: Config, reachy_mini=None):
        self.config = config
        self.reachy = reachy_mini
        self._running = False
        self._buffer: deque[np.ndarray] = deque(maxlen=1000)

    async def start(self) -> None:
        """Start audio capture."""
        self._running = True
        logger.info("Audio capture started")

    async def stop(self) -> None:
        """Stop audio capture."""
        self._running = False
        logger.info("Audio capture stopped")

    async def capture_utterance(self) -> np.ndarray | None:
        """
        Capture a complete utterance (speech followed by silence).

        Returns:
            Audio data as numpy array, or None if capture failed
        """
        if not self._running:
            return None

        frames: list[np.ndarray] = []
        silence_frames = 0
        max_silence_frames = int(self.config.silence_duration * self.config.sample_rate / 1024)
        max_frames = int(self.config.max_recording_duration * self.config.sample_rate / 1024)
        speech_detected = False
        energy_samples = []

        try:
            # Start recording on Reachy Mini if available
            if self.reachy and hasattr(self.reachy, "media"):
                self.reachy.media.start_recording()
                logger.debug("Started Reachy Mini audio recording")

            while self._running and len(frames) < max_frames:
                # Get audio from Reachy Mini's media manager
                if self.reachy and hasattr(self.reachy, "media"):
                    chunk = await asyncio.to_thread(
                        self.reachy.media.get_audio_sample
                    )
                else:
                    # Fallback: use sounddevice for local mic
                    chunk = await self._read_local_mic(1024)

                if chunk is None:
                    await asyncio.sleep(0.01)
                    continue

                # Convert to numpy if needed
                if not isinstance(chunk, np.ndarray):
                    chunk = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

                # Check for speech/silence
                energy = np.abs(chunk).mean()
                energy_samples.append(energy)

                # Log energy level periodically (every ~1 second)
                if len(energy_samples) % 16 == 0:
                    avg_energy = np.mean(energy_samples[-16:])
                    logger.debug(f"Audio energy: {avg_energy:.4f} (threshold: {self.config.silence_threshold})")

                if energy > self.config.silence_threshold:
                    if not speech_detected:
                        logger.info("🗣️ Speech detected!")
                    speech_detected = True
                    silence_frames = 0
                    frames.append(chunk)
                elif speech_detected:
                    silence_frames += 1
                    frames.append(chunk)

                    if silence_frames >= max_silence_frames:
                        # End of utterance
                        logger.info("⏹️ End of speech detected")
                        break

                await asyncio.sleep(0.001)  # Small yield

        except Exception as e:
            logger.error(f"Error capturing audio: {e}")
            return None
        finally:
            # Stop recording on Reachy Mini
            if self.reachy and hasattr(self.reachy, "media"):
                try:
                    self.reachy.media.stop_recording()
                except Exception:
                    pass

        if not frames or not speech_detected:
            return None

        # Concatenate all frames
        audio = np.concatenate(frames)
        logger.debug(f"Captured utterance: {len(audio) / self.config.sample_rate:.2f}s")
        return audio

    async def _read_local_mic(self, frames: int) -> np.ndarray | None:
        """Read from local microphone using sounddevice."""
        try:
            import sounddevice as sd

            recording = sd.rec(
                frames,
                samplerate=self.config.sample_rate,
                channels=1,
                dtype=np.float32,
            )
            sd.wait()
            return recording.flatten()

        except ImportError:
            logger.warning("sounddevice not available for local mic")
            return None
        except Exception as e:
            logger.error(f"Error reading local mic: {e}")
            return None


class WakeWordDetector:
    """Detects wake word in audio stream."""

    def __init__(self, wake_word: str, threshold: float = 0.8):
        self.wake_word = wake_word.lower()
        self.threshold = threshold

    def detect(self, text: str) -> bool:
        """Check if wake word is in transcribed text."""
        return self.wake_word in text.lower()
