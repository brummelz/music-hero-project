"""Transposition profiles: written note to sounding frequency (FR-01, FR-19)."""

from __future__ import annotations

import math
from dataclasses import dataclass

A4_HZ = 440.0
A4_MIDI = 69


@dataclass(frozen=True)
class InstrumentProfile:
    """A transposing instrument: sounding pitch = written pitch + offset semitones."""

    name: str
    offset_semitones: int


HORN_IN_F = InstrumentProfile("Horn in F", -7)

PROFILES: tuple[InstrumentProfile, ...] = (
    HORN_IN_F,
    InstrumentProfile("B♭ instrument", -2),
    InstrumentProfile("E♭ instrument", -9),
    InstrumentProfile("C instrument (concert pitch)", 0),
)


def profile_by_name(name: str) -> InstrumentProfile:
    for profile in PROFILES:
        if profile.name == name:
            return profile
    raise ValueError(f"Unknown instrument profile: {name!r}")


def sounding_frequency(written_midi: int, profile: InstrumentProfile) -> float:
    """FR-19: f = 440 * 2^((m - 69 + offset) / 12)."""
    return A4_HZ * 2 ** ((written_midi - A4_MIDI + profile.offset_semitones) / 12)


def nearest_written_note(sounding_hz: float, profile: InstrumentProfile) -> tuple[int, float]:
    """The written MIDI note nearest to a sounding frequency, and the offset in cents."""
    if sounding_hz <= 0:
        raise ValueError("Frequency must be positive")
    exact = A4_MIDI + 12 * math.log2(sounding_hz / A4_HZ) - profile.offset_semitones
    written_midi = round(exact)
    return written_midi, (exact - written_midi) * 100
