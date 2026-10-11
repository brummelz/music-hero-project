"""Sound effects, synthesized so no audio files need bundling (FR-09)."""

from __future__ import annotations

import logging

import numpy as np
import numpy.typing as npt

log = logging.getLogger(__name__)

_SAMPLE_RATE = 44_100
# A rising C major arpeggio: C5, E5, G5, C6.
_CHIME_NOTES_HZ = (523.25, 659.25, 783.99, 1046.50)
_NOTE_SPACING_S = 0.07
_NOTE_LENGTH_S = 0.45


def _chime() -> npt.NDArray[np.float32]:
    total = int(_SAMPLE_RATE * (_NOTE_SPACING_S * len(_CHIME_NOTES_HZ) + _NOTE_LENGTH_S))
    out = np.zeros(total, dtype=np.float64)
    t = np.arange(int(_SAMPLE_RATE * _NOTE_LENGTH_S)) / _SAMPLE_RATE
    envelope = np.exp(-t * 7.0) * np.minimum(1.0, t * 200.0)
    for i, frequency in enumerate(_CHIME_NOTES_HZ):
        start = int(i * _NOTE_SPACING_S * _SAMPLE_RATE)
        bell = np.sin(2 * np.pi * frequency * t) + 0.3 * np.sin(4 * np.pi * frequency * t)
        out[start : start + len(t)] += envelope * bell
    chime: npt.NDArray[np.float32] = (out / np.max(np.abs(out))).astype(np.float32)
    return chime


_CHIME = _chime()


REFERENCE_SECONDS = 1.6
_REFERENCE_HARMONICS = (1.0, 0.7, 0.45, 0.3, 0.18, 0.1)  # Warm, horn-like timbre.
_REFERENCE_MIN_VOLUME = 0.3
"""The child asked to hear the note, so play it audibly even if effects are turned down."""


def _reference_tone(frequency_hz: float) -> npt.NDArray[np.float32]:
    t = np.arange(int(_SAMPLE_RATE * REFERENCE_SECONDS)) / _SAMPLE_RATE
    tone = sum(a * np.sin(2 * np.pi * frequency_hz * (k + 1) * t) for k, a in enumerate(_REFERENCE_HARMONICS))
    envelope = np.minimum(1.0, t / 0.08) * np.minimum(1.0, (REFERENCE_SECONDS - t) / 0.25)
    out = tone * envelope
    result: npt.NDArray[np.float32] = (out / np.max(np.abs(out))).astype(np.float32)
    return result


def play_reference(frequency_hz: float, volume: float) -> float:
    """Play the target note so the child can hear it; returns its duration in seconds."""
    _play(_reference_tone(frequency_hz) * 0.5 * max(volume, _REFERENCE_MIN_VOLUME))
    return REFERENCE_SECONDS


def _play(samples: npt.NDArray[np.float32]) -> None:
    try:
        import sounddevice as sd

        sd.play(samples, _SAMPLE_RATE)
    except Exception:  # A missing output device must never break the game.
        log.warning("Could not play sound", exc_info=True)


def play_success(volume: float) -> None:
    if volume > 0:
        _play(_CHIME * 0.6 * volume)
