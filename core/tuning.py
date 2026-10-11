"""Cents conversion, tuner zones and tolerance rules (FR-02..FR-05, FR-21)."""

from __future__ import annotations

import math
from enum import Enum

GAUGE_RANGE_CENTS = 50.0
"""The gauge spans ±50 cents; readings beyond are clamped to the ends (FR-04)."""

DEFAULT_TOLERANCE_CENTS = 15.0
MIN_TOLERANCE_CENTS = 5.0
MAX_TOLERANCE_CENTS = 50.0
TOLERANCE_PRESETS: dict[str, float] = {"Easy": 25.0, "Normal": 15.0, "Strict": 10.0}

NEAR_ZONE_FACTOR = 2.0
"""Yellow 'near' zones reach twice the tolerance; beyond that is red 'far'.

The spec names near/far zones without a boundary, so this is an assumption.
"""


class Zone(Enum):
    IDLE = "idle"
    FLAT_FAR = "flat_far"
    FLAT_NEAR = "flat_near"
    GREEN = "green"
    SHARP_NEAR = "sharp_near"
    SHARP_FAR = "sharp_far"


def cents_offset(frequency_hz: float, target_hz: float) -> float:
    """FR-02: cents = 1200 * log2(f / f_t)."""
    if frequency_hz <= 0 or target_hz <= 0:
        raise ValueError("Frequencies must be positive")
    return 1200.0 * math.log2(frequency_hz / target_hz)


def validate_tolerance(tolerance_cents: float) -> float:
    """FR-21: custom tolerance must be within ±5..±50 cents."""
    if not MIN_TOLERANCE_CENTS <= tolerance_cents <= MAX_TOLERANCE_CENTS:
        raise ValueError(
            f"Tolerance must be between {MIN_TOLERANCE_CENTS:g} and "
            f"{MAX_TOLERANCE_CENTS:g} cents, got {tolerance_cents:g}"
        )
    return tolerance_cents


def classify(cents: float | None, tolerance_cents: float) -> Zone:
    """FR-03 zones; ``None`` (no pitched sound) is IDLE (FR-05)."""
    if cents is None:
        return Zone.IDLE
    if abs(cents) <= tolerance_cents:
        return Zone.GREEN
    near = abs(cents) <= tolerance_cents * NEAR_ZONE_FACTOR
    if cents < 0:
        return Zone.FLAT_NEAR if near else Zone.FLAT_FAR
    return Zone.SHARP_NEAR if near else Zone.SHARP_FAR


def needle_position(cents: float) -> float:
    """Needle position in [-1, 1] across the gauge, clamped at the ends (FR-04)."""
    return max(-1.0, min(1.0, cents / GAUGE_RANGE_CENTS))
