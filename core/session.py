"""Game sessions: Single Note Practice and Level Challenge (FR-12..FR-17, FR-22)."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.feedback import Feedback, feedback_for
from core.hold_timer import HoldConfig, HoldEvent, HoldMode, HoldTimer
from core.levels import Level, generate_prompts, stars_for_misses
from core.notes import Note
from core.transpose import InstrumentProfile, sounding_frequency
from core.tuning import Zone, cents_offset, classify, validate_tolerance

PRACTICE_GOAL_POINTS = 10
PRACTICE_NOTES: tuple[Note, ...] = tuple(Note.parse(name) for name in ("C4", "D4", "E4"))
"""FR-12: practice targets offered initially (Do, Ré, Mi)."""


@dataclass(frozen=True)
class FrameState:
    """What the gameplay screen shows after one detection frame."""

    cents: float | None
    zone: Zone
    hold_fraction: float
    event: HoldEvent
    feedback: Feedback


class GameSession(ABC):
    def __init__(
        self,
        profile: InstrumentProfile,
        tolerance_cents: float,
        hold_config: HoldConfig | None = None,
    ) -> None:
        self.profile = profile
        self._tolerance_cents = validate_tolerance(tolerance_cents)
        self._timer = HoldTimer(hold_config)
        self.points = 0

    @property
    @abstractmethod
    def target_note(self) -> Note: ...

    @property
    @abstractmethod
    def goal(self) -> int: ...

    @property
    def finished(self) -> bool:
        return self.points >= self.goal

    @property
    def target_frequency(self) -> float:
        return sounding_frequency(self.target_note.midi, self.profile)

    @property
    def hold_seconds(self) -> float:
        return self._timer.config.hold_seconds

    @property
    def tolerance_cents(self) -> float:
        return self._tolerance_cents

    @tolerance_cents.setter
    def tolerance_cents(self, value: float) -> None:
        """FR-21: a tolerance change applies immediately."""
        self._tolerance_cents = validate_tolerance(value)

    def restart_hold(self) -> None:
        """Drop hold progress without counting a miss, e.g. after the game was paused."""
        self._timer.reset()

    def process(self, now: float, frequency_hz: float | None) -> FrameState:
        """Feed one detection result (``None`` = no pitched sound) at time ``now``."""
        if self.finished:
            return FrameState(None, Zone.IDLE, 1.0, HoldEvent.NONE, Feedback.COMPLETED)
        cents = None if frequency_hz is None else cents_offset(frequency_hz, self.target_frequency)
        zone = classify(cents, self._tolerance_cents)
        event = self._timer.update(now, zone is Zone.GREEN)
        fraction = self._timer.fraction
        if event is HoldEvent.MISSED:
            self._on_miss()
        elif event is HoldEvent.COMPLETED:
            fraction = 1.0
            self.points += 1
            self._on_point()
        return FrameState(cents, zone, fraction, event, feedback_for(zone, event))

    def _on_miss(self) -> None:  # noqa: B027 - optional hook, not every mode counts misses
        """Hook for subclasses that count misses."""

    def _on_point(self) -> None:  # noqa: B027 - optional hook
        """Hook for subclasses that react to a completed hold."""


class PracticeSession(GameSession):
    """Mode 1: one fixed target note, 10 points to finish (FR-12..FR-14)."""

    def __init__(
        self,
        note: Note,
        profile: InstrumentProfile,
        tolerance_cents: float,
        hold_config: HoldConfig | None = None,
    ) -> None:
        super().__init__(profile, tolerance_cents, hold_config)
        self._note = note

    @property
    def target_note(self) -> Note:
        return self._note

    @property
    def goal(self) -> int:
        return PRACTICE_GOAL_POINTS


class LevelSession(GameSession):
    """Mode 2: a sequence of prompts from the level's note set (FR-15..FR-17)."""

    def __init__(
        self,
        level: Level,
        profile: InstrumentProfile,
        tolerance_cents: float,
        hold_config: HoldConfig | None = None,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(profile, tolerance_cents, hold_config)
        self.level = level
        self.prompts = generate_prompts(level, rng or random.Random())
        self.misses = 0
        self._missed_this_prompt = False

    @property
    def target_note(self) -> Note:
        return self.prompts[min(self.points, len(self.prompts) - 1)]

    @property
    def goal(self) -> int:
        return len(self.prompts)

    @property
    def stars(self) -> int:
        return stars_for_misses(self.misses)

    def _on_miss(self) -> None:
        # FR-23: in pause mode only the first pause within a prompt is a miss.
        if self._timer.config.mode is HoldMode.PAUSE and self._missed_this_prompt:
            return
        self.misses += 1
        self._missed_this_prompt = True

    def _on_point(self) -> None:
        # The next prompt is a new note, so start its hold from zero.
        self._timer.reset()
        self._missed_this_prompt = False
