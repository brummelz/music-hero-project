"""Hold-timer state machine (FR-06..FR-09, FR-22).

Time is passed in by the caller, so the timer is deterministic under test.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DEFAULT_HOLD_SECONDS = 3.0
DEFAULT_GRACE_SECONDS = 0.150


class HoldMode(Enum):
    RESET = "reset"
    """Leaving the Green zone resets progress to 0 (default, FR-07)."""
    PAUSE = "pause"
    """Leaving the Green zone keeps progress; it resumes on return."""


class HoldEvent(Enum):
    NONE = "none"
    MISSED = "missed"
    """Progress was lost or paused after the hold had started (FR-22)."""
    COMPLETED = "completed"
    """The hold reached its full duration (FR-09)."""


@dataclass(frozen=True)
class HoldConfig:
    hold_seconds: float = DEFAULT_HOLD_SECONDS
    grace_seconds: float = DEFAULT_GRACE_SECONDS
    mode: HoldMode = HoldMode.RESET


class HoldTimer:
    """Tracks continuous time in the Green zone.

    Being out of the zone (wrong pitch or no detection) for up to the grace
    period does not count as leaving it (FR-08).
    """

    def __init__(self, config: HoldConfig | None = None) -> None:
        self.config = config or HoldConfig()
        self._banked = 0.0
        self._run_start: float | None = None
        self._last_in_zone: float | None = None

    @property
    def elapsed(self) -> float:
        """Seconds of hold progress so far."""
        if self._run_start is None or self._last_in_zone is None:
            return self._banked
        return self._banked + self._last_in_zone - self._run_start

    @property
    def fraction(self) -> float:
        return min(1.0, self.elapsed / self.config.hold_seconds)

    def reset(self) -> None:
        self._banked = 0.0
        self._run_start = None
        self._last_in_zone = None

    def update(self, now: float, in_zone: bool) -> HoldEvent:
        if in_zone:
            return self._update_in_zone(now)
        return self._update_out_of_zone(now)

    def _update_in_zone(self, now: float) -> HoldEvent:
        if self._run_start is None:
            self._run_start = now
        self._last_in_zone = now
        if self.elapsed < self.config.hold_seconds:
            return HoldEvent.NONE
        # Start the next attempt immediately so a continuous note keeps scoring.
        self._banked = 0.0
        self._run_start = now
        return HoldEvent.COMPLETED

    def _update_out_of_zone(self, now: float) -> HoldEvent:
        if self._run_start is None or self._last_in_zone is None:
            return HoldEvent.NONE
        if now - self._last_in_zone <= self.config.grace_seconds:
            return HoldEvent.NONE
        progress = self.elapsed
        self._banked = progress if self.config.mode is HoldMode.PAUSE else 0.0
        self._run_start = None
        self._last_in_zone = None
        return HoldEvent.MISSED if progress > 0 else HoldEvent.NONE
