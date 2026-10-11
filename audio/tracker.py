"""Turns raw analysis windows into a steady pitch reading for the game."""

from __future__ import annotations

import statistics
from collections import deque

import numpy as np
import numpy.typing as npt

from audio.pitch_yin import YinDetector, gate_threshold, rms

HISTORY_FRAMES = 5
"""Median over the last 5 frames (~60 ms): long enough to drop single-frame octave
errors, short enough to stay within the 100 ms latency budget (NFR-01)."""
MIN_VOICED_FRAMES = 3


class PitchTracker:
    """Noise gate, then pitch detection, then a short median filter."""

    def __init__(self, sample_rate: int, sensitivity: float = 0.5) -> None:
        self._detector = YinDetector(sample_rate)
        self._history: deque[float | None] = deque(maxlen=HISTORY_FRAMES)
        self.gate_rms = gate_threshold(sensitivity)
        self.last_level = 0.0

    def set_sensitivity(self, sensitivity: float) -> None:
        self.gate_rms = gate_threshold(sensitivity)

    def reset(self) -> None:
        self._history.clear()

    def set_sample_rate(self, sample_rate: int) -> None:
        """Follow the input device's native rate (it changes when the microphone does)."""
        if sample_rate != self._detector.sample_rate:
            self._detector = YinDetector(sample_rate)
            self.reset()

    def update(self, window: npt.NDArray[np.floating]) -> float | None:
        """Feed one window; return the steadied frequency, or ``None`` for no clear pitch."""
        self.last_level = rms(window)
        frequency = None
        if self.last_level >= self.gate_rms:
            result = self._detector.detect(window)
            frequency = result.frequency_hz if result else None
        self._history.append(frequency)

        voiced = [f for f in self._history if f is not None]
        if len(voiced) < MIN_VOICED_FRAMES or (frequency is None and self._history[-2] is None):
            return None
        return statistics.median_low(voiced)
