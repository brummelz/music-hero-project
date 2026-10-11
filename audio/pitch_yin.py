"""YIN fundamental-frequency detector (de Cheveigné & Kawahara, 2002).

A NumPy implementation, so there is no compiled pitch-detection dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
import numpy.typing as npt

DEFAULT_MIN_HZ = 60.0
DEFAULT_MAX_HZ = 1200.0
DEFAULT_THRESHOLD = 0.15
DEFAULT_FALLBACK_THRESHOLD = 0.4
"""Second, looser pass for noisy rooms and breathy tones; the tracker's median filter
removes the occasional octave error this lets through."""

DIP_SEARCH_RATIO = 1.15
"""After the first dip, take the deepest point within 15% of it: in noisy rooms false dips on
the way down read sharp. Octave errors (a factor of 2) stay far outside this range."""

# Mic sensitivity 0..1 maps to an RMS noise gate from 0.01 (-40 dBFS, loud input only)
# down to 0.0001 (-80 dBFS). The default 0.5 gates at 0.001 (-60 dBFS): low, because the
# detector already rejects unpitched room noise, and laptop mics are often quiet.
_LOUDEST_GATE_RMS = 0.01
_GATE_RANGE = 0.01


@dataclass(frozen=True)
class PitchResult:
    frequency_hz: float
    confidence: float


class PitchDetector(Protocol):
    def detect(self, frame: npt.NDArray[np.floating]) -> PitchResult | None: ...


def rms(frame: npt.NDArray[np.floating]) -> float:
    return float(np.sqrt(np.mean(np.square(frame, dtype=np.float64))))


def gate_threshold(sensitivity: float) -> float:
    """RMS level below which input counts as silence."""
    return float(_LOUDEST_GATE_RMS * _GATE_RANGE**sensitivity)


class YinDetector:
    def __init__(
        self,
        sample_rate: int,
        min_hz: float = DEFAULT_MIN_HZ,
        max_hz: float = DEFAULT_MAX_HZ,
        threshold: float = DEFAULT_THRESHOLD,
        fallback_threshold: float = DEFAULT_FALLBACK_THRESHOLD,
    ) -> None:
        self.sample_rate = sample_rate
        self.min_hz = min_hz
        self.max_hz = max_hz
        self.threshold = threshold
        self.fallback_threshold = fallback_threshold

    def detect(self, frame: npt.NDArray[np.floating]) -> PitchResult | None:
        """Return the fundamental of ``frame``, or ``None`` if it is not clearly pitched."""
        x = np.asarray(frame, dtype=np.float64)
        x = x - x.mean()
        n = len(x)
        tau_max = min(int(self.sample_rate / self.min_hz), n // 2)
        tau_min = max(2, int(self.sample_rate / self.max_hz))
        if tau_max <= tau_min + 1:
            raise ValueError("Frame too short for the configured frequency range")

        cmnd = self._cumulative_mean_normalized_difference(x, tau_max)
        tau = self._first_dip(cmnd, tau_min, tau_max, self.threshold)
        if tau is None:
            tau = self._first_dip(cmnd, tau_min, tau_max, self.fallback_threshold)
        if tau is None:
            return None
        refined = self._parabolic_peak(cmnd, tau)
        return PitchResult(self.sample_rate / refined, float(1.0 - cmnd[tau]))

    @staticmethod
    def _cumulative_mean_normalized_difference(
        x: npt.NDArray[np.float64], tau_max: int
    ) -> npt.NDArray[np.float64]:
        window = len(x) - tau_max
        size = 1 << int(np.ceil(np.log2(len(x) + window)))
        spectrum = np.fft.rfft(x, size) * np.conj(np.fft.rfft(x[:window], size))
        correlation = np.fft.irfft(spectrum, size)[: tau_max + 1]

        energy = np.concatenate(([0.0], np.cumsum(x * x)))
        taus = np.arange(tau_max + 1)
        shifted_energy = energy[taus + window] - energy[taus]
        difference = energy[window] + shifted_energy - 2.0 * correlation

        cmnd = np.ones(tau_max + 1)
        running = np.cumsum(difference[1:])
        with np.errstate(divide="ignore", invalid="ignore"):
            cmnd[1:] = np.where(running > 0, difference[1:] * taus[1:] / running, 1.0)
        return cmnd

    @staticmethod
    def _first_dip(cmnd: npt.NDArray[np.float64], tau_min: int, tau_max: int, threshold: float) -> int | None:
        below = np.nonzero(cmnd[tau_min:tau_max] < threshold)[0]
        if len(below) == 0:
            return None
        tau = tau_min + int(below[0])
        end = min(tau_max, int(tau * DIP_SEARCH_RATIO) + 1)
        return tau + int(np.argmin(cmnd[tau:end]))

    @staticmethod
    def _parabolic_peak(values: npt.NDArray[np.float64], index: int) -> float:
        if index <= 0 or index >= len(values) - 1:
            return float(index)
        left, center, right = values[index - 1], values[index], values[index + 1]
        denominator = left - 2 * center + right
        if denominator == 0:
            return float(index)
        return index + 0.5 * float(left - right) / float(denominator)
