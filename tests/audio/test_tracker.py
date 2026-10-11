"""Pitch tracking on realistic horn-like input (NFR-02) and its effect on holds (FR-06)."""

import numpy as np
import pytest

from audio.sources import WINDOW_SIZE
from audio.tracker import PitchTracker
from core.notes import Note
from core.session import PracticeSession
from core.transpose import HORN_IN_F
from core.tuning import cents_offset

SAMPLE_RATE = 44_100
HOP = 512
# Horn spectra often have a 2nd harmonic stronger than the fundamental.
HORN_HARMONICS = (0.6, 1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.1)


def horn_tone(f0: float, seconds: float, noise_db: float, vibrato_cents: float, level: float = 0.02):
    rng = np.random.default_rng(7)
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    instantaneous = f0 * 2 ** (vibrato_cents * np.sin(2 * np.pi * 5 * t) / 1200)
    phase = 2 * np.pi * np.cumsum(instantaneous) / SAMPLE_RATE
    tone = sum(a * np.sin((k + 1) * phase + rng.uniform(0, 6)) for k, a in enumerate(HORN_HARMONICS))
    tone /= np.max(np.abs(tone))
    return level * (tone + rng.standard_normal(len(t)) * 10 ** (noise_db / 20))


def readings(tracker: PitchTracker, signal: np.ndarray) -> list[float | None]:
    return [tracker.update(signal[s : s + WINDOW_SIZE]) for s in range(0, len(signal) - WINDOW_SIZE, HOP)]


@pytest.mark.parametrize("f0", [174.61, 261.63, 349.23, 523.25])
def test_noisy_room_stays_voiced_without_octave_errors(f0: float) -> None:
    tracker = PitchTracker(SAMPLE_RATE)
    values = readings(tracker, horn_tone(f0, 2.0, noise_db=-12, vibrato_cents=0))[5:]
    assert all(v is not None for v in values)
    assert all(abs(cents_offset(v, f0)) < 50 for v in values if v is not None)


def test_quiet_microphone_is_not_gated_at_default_sensitivity() -> None:
    tracker = PitchTracker(SAMPLE_RATE)
    values = readings(tracker, horn_tone(220.0, 1.0, noise_db=-30, vibrato_cents=0, level=0.006))[5:]
    assert all(v is not None for v in values)


def test_silence_releases_quickly() -> None:
    tracker = PitchTracker(SAMPLE_RATE)
    readings(tracker, horn_tone(220.0, 0.5, noise_db=-30, vibrato_cents=0))
    silence = np.zeros(WINDOW_SIZE, dtype=np.float32)
    tracker.update(silence)
    assert tracker.update(silence) is None


@pytest.mark.parametrize("note", ["C4", "E4"])
def test_wobbly_noisy_horn_still_completes_holds(note: str) -> None:
    session = PracticeSession(Note.parse(note), HORN_IN_F, 15)
    tracker = PitchTracker(SAMPLE_RATE)
    signal = horn_tone(session.target_frequency, 6.5, noise_db=-12, vibrato_cents=8)
    for i, frequency in enumerate(readings(tracker, signal)):
        session.process(i * HOP / SAMPLE_RATE, frequency)
    assert session.points == 2


def test_follows_a_new_sample_rate() -> None:
    tracker = PitchTracker(16_000)
    tracker.set_sample_rate(48_000)
    t = np.arange(WINDOW_SIZE) / 48_000
    window = (0.1 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    values = [tracker.update(window) for _ in range(4)]
    assert values[-1] == pytest.approx(220, rel=0.003)
