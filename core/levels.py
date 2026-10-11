"""Level Challenge rules: level data, prompt generation and stars (FR-15..FR-17, FR-23)."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from core.notes import Note

PROMPTS_PER_LEVEL = 6
THREE_STAR_MAX_MISSES = 2
TWO_STAR_MAX_MISSES = 6
_MAX_SHUFFLE_ATTEMPTS = 10_000


@dataclass(frozen=True)
class Level:
    number: int
    theme: str
    notes: tuple[Note, ...]

    @property
    def prompt_count(self) -> int:
        """FR-16 asks for 6 prompts with every note at least once.

        Level 3 has 8 notes, so both cannot hold; we extend that level to one
        prompt per note. (Spec conflict, flagged for review.)
        """
        return max(PROMPTS_PER_LEVEL, len(self.notes))


def parse_levels(data: Sequence[Mapping[str, Any]]) -> tuple[Level, ...]:
    """Build levels from configuration data (the level table is data, not code)."""
    levels = []
    for expected_number, entry in enumerate(data, start=1):
        number = int(entry["number"])
        if number != expected_number:
            raise ValueError(f"Levels must be numbered 1..n in order, got {number}")
        notes = tuple(Note.parse(name) for name in entry["notes"])
        if len(set(notes)) != len(notes) or len(notes) < 2:
            raise ValueError(f"Level {number} needs at least 2 distinct notes")
        levels.append(Level(number, str(entry["theme"]), notes))
    return tuple(levels)


def generate_prompts(level: Level, rng: random.Random) -> list[Note]:
    """FR-16: every note at least once, no note twice in a row."""
    count = level.prompt_count
    for _ in range(_MAX_SHUFFLE_ATTEMPTS):
        prompts = list(level.notes)
        prompts += [rng.choice(level.notes) for _ in range(count - len(prompts))]
        rng.shuffle(prompts)
        if all(a != b for a, b in pairwise(prompts)):
            return prompts
    raise RuntimeError(f"Could not generate prompts for level {level.number}")


def stars_for_misses(misses: int) -> int:
    """FR-23: 3 stars for 0-2 misses, 2 for 3-6, 1 for 7 or more."""
    if misses < 0:
        raise ValueError("Misses cannot be negative")
    if misses <= THREE_STAR_MAX_MISSES:
        return 3
    if misses <= TWO_STAR_MAX_MISSES:
        return 2
    return 1
