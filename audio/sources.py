"""Audio sources that provide analysis windows: the microphone and a keyboard simulator."""

from __future__ import annotations

import logging
import math
import threading
import time
from typing import Any, Protocol

import numpy as np
import numpy.typing as npt

from audio import devices

log = logging.getLogger(__name__)

SAMPLE_RATE = 44_100
WINDOW_SIZE = 2048
"""~46 ms: two periods of the lowest detectable note, within the 100 ms latency budget."""
BLOCK_SIZE = 512


class AudioSource(Protocol):
    sample_rate: int
    """Sample rate of the windows returned by ``read_window``; may change on ``set_device``."""

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def set_device(self, key: str) -> None:
        """Switch input device (a key from ``audio.devices``), restarting if running."""
        ...

    def read_window(self) -> npt.NDArray[np.float32] | None:
        """The latest analysis window, or ``None`` if no new audio arrived since the last call."""
        ...

    @property
    def active_device(self) -> str:
        """Human-readable name of the input actually in use."""
        ...

    @property
    def active_is_filtered(self) -> bool:
        """True if Windows voice processing may be removing steady notes."""
        ...


PROBE_SECONDS = 0.25
"""How long a newly opened input must deliver real audio before it is trusted."""
_SILENT_PEAK = 1e-7
"""Some pins open but deliver exact digital zeros; real microphones never do."""
_FALLBACK_LABEL = "Windows default input (voice mode, Windows filters)"


def is_live(blocks_received: int, peak: float) -> bool:
    """An opened input counts only if audio arrives and it is not pure digital silence."""
    return blocks_received > 0 and peak > _SILENT_PEAK


class MicrophoneSource:
    """Captures mono audio from an input device on PortAudio's thread.

    Tries the inputs from ``audio.devices.candidates`` in order (unfiltered first), opening
    each at its native sample rate and keeping the first that delivers real audio.
    """

    def __init__(self, window_size: int = WINDOW_SIZE, device: str = devices.AUTOMATIC) -> None:
        self.sample_rate = SAMPLE_RATE
        self.device = device
        self._active = ""
        self._filtered = False
        self._buffer = np.zeros(window_size, dtype=np.float32)
        self._fresh = False
        self._blocks = 0
        self._peak = 0.0
        self._lock = threading.Lock()
        self._stream: Any = None

    def start(self) -> None:
        for candidate in devices.candidates(self.device):
            label = candidate.label if candidate else _FALLBACK_LABEL
            try:
                self._open(candidate)
            except Exception:
                log.info("Could not open %s; trying the next input", label, exc_info=True)
                continue
            if self._probe():
                self._active = label
                self._filtered = candidate is None or candidate.filtered
                log.info("Microphone in use: %s", label)
                return
            log.info("%s delivers no audio; trying the next input", label)
            self.stop()
        raise RuntimeError("No working microphone found")

    def _open(self, device: devices.InputDevice | None) -> None:
        import sounddevice as sd  # Imported lazily so tests never need PortAudio.

        extra = None
        if device is not None and device.capture is devices.Capture.RAW_MODE:
            extra = sd.WasapiSettings(auto_convert=True)
            # sounddevice doesn't expose WASAPI's raw option, but its C struct has the field.
            extra._streaminfo.streamOption = sd._lib.eStreamOptionRaw
        sample_rate = device.sample_rate if device else SAMPLE_RATE
        with self._lock:
            self._blocks = 0
            self._peak = 0.0
        stream = sd.InputStream(
            device=device.index if device else None,
            samplerate=sample_rate,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype="float32",
            latency="low",
            callback=self._on_audio,
            extra_settings=extra,
        )
        stream.start()
        self.sample_rate = sample_rate
        self._stream = stream

    def _probe(self) -> bool:
        time.sleep(PROBE_SECONDS)
        with self._lock:
            return is_live(self._blocks, self._peak)

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def set_device(self, key: str) -> None:
        running = self._stream is not None
        self.stop()
        self.device = key
        with self._lock:
            self._buffer[:] = 0
            self._fresh = False
        if running:
            self.start()

    def _on_audio(self, indata: npt.NDArray[np.float32], frames: int, _time: Any, status: Any) -> None:
        # Runs on the audio thread: copy and return, no heavy work here.
        if status:
            log.debug("Audio input status: %s", status)
        block = indata[:, 0]
        with self._lock:
            if frames >= len(self._buffer):
                self._buffer[:] = block[-len(self._buffer) :]
            else:
                self._buffer[:-frames] = self._buffer[frames:]
                self._buffer[-frames:] = block
            self._fresh = True
            self._blocks += 1
            self._peak = max(self._peak, float(np.max(np.abs(block))))

    def read_window(self) -> npt.NDArray[np.float32] | None:
        with self._lock:
            if not self._fresh:
                return None
            self._fresh = False
            return self._buffer.copy()

    @property
    def active_device(self) -> str:
        return self._active

    @property
    def active_is_filtered(self) -> bool:
        return self._filtered


class SimulatedSource:
    """Synthesizes a horn-like tone at a chosen frequency, for testing without an instrument."""

    AMPLITUDE = 0.2

    def __init__(self, sample_rate: int = SAMPLE_RATE, window_size: int = WINDOW_SIZE) -> None:
        self.sample_rate = sample_rate
        self._window_size = window_size
        self.frequency_hz: float | None = None
        self._phase = 0.0

    def start(self) -> None:
        """Nothing to open."""

    def stop(self) -> None:
        """Nothing to close."""

    def set_device(self, key: str) -> None:
        """The simulator has no devices."""

    def read_window(self) -> npt.NDArray[np.float32]:
        if self.frequency_hz is None:
            return np.zeros(self._window_size, dtype=np.float32)
        step = 2 * math.pi * self.frequency_hz / self.sample_rate
        phase = self._phase + step * np.arange(self._window_size)
        tone = np.sin(phase) + 0.5 * np.sin(2 * phase) + 0.25 * np.sin(3 * phase)
        self._phase = float(phase[-1] + step) % (2 * math.pi)
        return (self.AMPLITUDE * tone / 1.75).astype(np.float32)

    @property
    def active_device(self) -> str:
        return "Keyboard simulation"

    @property
    def active_is_filtered(self) -> bool:
        return False
