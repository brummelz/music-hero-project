import pytest

from core.tuning import (
    TOLERANCE_PRESETS,
    Zone,
    cents_offset,
    classify,
    needle_position,
    validate_tolerance,
)

TARGET_HZ = 174.61


@pytest.mark.parametrize("k", [-50, -15, 0, 15, 50])
def test_tc05_cents_conversion(k: int) -> None:
    assert cents_offset(TARGET_HZ * 2 ** (k / 1200), TARGET_HZ) == pytest.approx(k, abs=0.01)


@pytest.mark.parametrize(
    ("cents", "zone"),
    [
        (-16, Zone.FLAT_NEAR),
        (-15, Zone.GREEN),
        (0, Zone.GREEN),
        (15, Zone.GREEN),
        (16, Zone.SHARP_NEAR),
    ],
)
def test_tc06_zone_boundaries(cents: float, zone: Zone) -> None:
    assert classify(cents, 15) is zone


def test_tc07_flat_and_sharp_sides() -> None:
    assert classify(-30, 15) is Zone.FLAT_NEAR
    assert classify(30, 15) is Zone.SHARP_NEAR
    assert needle_position(-30) < 0 < needle_position(30)


def test_far_zones_beyond_twice_tolerance() -> None:
    assert classify(-31, 15) is Zone.FLAT_FAR
    assert classify(31, 15) is Zone.SHARP_FAR


def test_tc16_octave_error_is_not_green() -> None:
    assert classify(1200, 15) is Zone.SHARP_FAR
    assert classify(-1200, 15) is Zone.FLAT_FAR


def test_fr05_no_detection_is_idle() -> None:
    assert classify(None, 15) is Zone.IDLE


def test_fr04_needle_clamped_to_gauge() -> None:
    assert needle_position(500) == 1.0
    assert needle_position(-500) == -1.0
    assert needle_position(25) == pytest.approx(0.5)


SHARP = {Zone.SHARP_NEAR, Zone.SHARP_FAR}


@pytest.mark.parametrize(("preset", "zones"), [("Easy", {Zone.GREEN}), ("Normal", SHARP), ("Strict", SHARP)])
def test_tc26_tolerance_presets(preset: str, zones: set[Zone]) -> None:
    assert classify(20, TOLERANCE_PRESETS[preset]) in zones


def test_tc27_custom_tolerance_range() -> None:
    assert validate_tolerance(5) == 5
    assert validate_tolerance(50) == 50
    for invalid in (4, 51):
        with pytest.raises(ValueError):
            validate_tolerance(invalid)


def test_cents_rejects_non_positive_frequency() -> None:
    with pytest.raises(ValueError):
        cents_offset(0, TARGET_HZ)
