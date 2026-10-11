"""The single local profile: settings and progress (FR-17, FR-20, FR-21, FR-24, FR-25)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from core.hold_timer import HoldMode
from core.transpose import HORN_IN_F, profile_by_name
from core.tuning import DEFAULT_TOLERANCE_CENTS, validate_tolerance


@dataclass(frozen=True)
class Settings:
    tolerance_cents: float = DEFAULT_TOLERANCE_CENTS
    instrument: str = HORN_IN_F.name
    volume: float = 0.8
    mic_sensitivity: float = 0.5
    hold_mode: HoldMode = HoldMode.RESET
    input_device: str = ""
    """Microphone name; empty means the system default."""

    def __post_init__(self) -> None:
        validate_tolerance(self.tolerance_cents)
        profile_by_name(self.instrument)
        for name, value in (("volume", self.volume), ("mic_sensitivity", self.mic_sensitivity)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1, got {value}")


@dataclass(frozen=True)
class Progress:
    best_stars: dict[int, int] = field(default_factory=dict)
    unlocked_level: int = 1

    @property
    def total_stars(self) -> int:
        """FR-24: the sum of each level's best stars."""
        return sum(self.best_stars.values())

    def stars_for(self, level_number: int) -> int:
        return self.best_stars.get(level_number, 0)

    def is_unlocked(self, level_number: int) -> bool:
        return level_number <= self.unlocked_level

    def with_level_result(self, level_number: int, stars: int, level_count: int) -> Progress:
        """FR-17: keep only the best stars and unlock the next level."""
        best = dict(self.best_stars)
        best[level_number] = max(stars, best.get(level_number, 0))
        unlocked = max(self.unlocked_level, min(level_number + 1, level_count))
        return replace(self, best_stars=best, unlocked_level=unlocked)


@dataclass(frozen=True)
class Profile:
    settings: Settings = field(default_factory=Settings)
    progress: Progress = field(default_factory=Progress)

    def with_progress_reset(self) -> Profile:
        """FR-25: clear progress and stars, keep settings."""
        return replace(self, progress=Progress())
