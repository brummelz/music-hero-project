import numpy as np
import pytest

from audio.pitch_yin import YinDetector, gate_threshold, rms
from audio.sources import WINDOW_SIZE, SimulatedSource
from core.tuning import cents_offset

SAMPLE_RATE = 44_100


def tone(hz: float, harmonics: bool = True, noise: float = 0.0, seed: int = 0) -> np.ndarray:
    t = np.arange(WINDOW_SIZE) / SAMPLE_RATE
    signal = np.sin(2 * np.pi * hz * t)
    if harmonics:  # Brass tones are rich in harmonics, which trip naive detectors.
        signal += 0.8 * np.sin(4 * np.pi * hz * t) + 0.6 * np.sin(6 * np.pi * hz * t)
    if noise:
        signal += noise * np.random.default_rng(seed).standard_normal(len(t))
    return (0.3 * signal / np.max(np.abs(signal))).astype(np.float32)


def test_tc01_pure_sine_within_five_cents() -> None:
    result = YinDetector(SAMPLE_RATE).detect(tone(349.23, harmonics=False))
    assert result is not None
    assert cents_offset(result.frequency_hz, 349.23) == pytest.approx(0, abs=5)


@pytest.mark.parametrize("hz", [174.61, 196.00, 220.00, 261.63, 349.23, 440.00, 523.25])
def test_nfr02_horn_range_with_harmonics(hz: float) -> None:
    result = YinDetector(SAMPLE_RATE).detect(tone(hz))
    assert result is not None
    assert cents_offset(result.frequency_hz, hz) == pytest.approx(0, abs=5)


def test_tc16_octave_below_is_detected_as_such() -> None:
    result = YinDetector(SAMPLE_RATE).detect(tone(87.31))
    assert result is not None
    assert cents_offset(result.frequency_hz, 174.61) == pytest.approx(-1200, abs=10)


def test_tc10_noise_is_not_pitched() -> None:
    noise = 0.2 * np.random.default_rng(1).standard_normal(WINDOW_SIZE).astype(np.float32)
    assert YinDetector(SAMPLE_RATE).detect(noise) is None


def test_tone_with_light_noise() -> None:
    result = YinDetector(SAMPLE_RATE).detect(tone(220.0, noise=0.1))
    assert result is not None
    assert cents_offset(result.frequency_hz, 220.0) == pytest.approx(0, abs=5)


def test_simulated_source_round_trip() -> None:
    source = SimulatedSource()
    source.frequency_hz = 196.0
    result = YinDetector(SAMPLE_RATE).detect(source.read_window())
    assert result is not None
    assert cents_offset(result.frequency_hz, 196.0) == pytest.approx(0, abs=5)
    source.frequency_hz = None
    assert rms(source.read_window()) == 0


def test_gate_threshold_decreases_with_sensitivity() -> None:
    assert gate_threshold(0.0) > gate_threshold(0.5) > gate_threshold(1.0) > 0
