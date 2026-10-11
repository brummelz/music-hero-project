"""Encouragement messages (FR-18)."""

from __future__ import annotations

from enum import Enum

from core.hold_timer import HoldEvent
from core.notes import Note
from core.tuning import Zone


class Feedback(Enum):
    SILENCE = "silence"
    FLAT_FAR = "flat_far"
    FLAT_NEAR = "flat_near"
    IN_TUNE = "in_tune"
    SHARP_NEAR = "sharp_near"
    SHARP_FAR = "sharp_far"
    COMPLETED = "completed"
    TRY_AGAIN = "try_again"
    """Shown briefly after a well-started hold restarts, so the reset never feels silent."""


_FROM_ZONE = {
    Zone.IDLE: Feedback.SILENCE,
    Zone.FLAT_FAR: Feedback.FLAT_FAR,
    Zone.FLAT_NEAR: Feedback.FLAT_NEAR,
    Zone.GREEN: Feedback.IN_TUNE,
    Zone.SHARP_NEAR: Feedback.SHARP_NEAR,
    Zone.SHARP_FAR: Feedback.SHARP_FAR,
}

_MESSAGES = {
    Feedback.SILENCE: "Take a breath and play your {note}!",
    Feedback.FLAT_FAR: "A bit low! Lift the note up.",
    Feedback.FLAT_NEAR: "Almost there! Push a little higher!",
    Feedback.IN_TUNE: "Perfect! Keep it steady…",
    Feedback.SHARP_NEAR: "A touch too high, ease down a little!",
    Feedback.SHARP_FAR: "A bit high! Relax and come down.",
    Feedback.COMPLETED: "Great job! +1 point!",
    Feedback.TRY_AGAIN: "So close! Start the hold again.",
}


def feedback_for(zone: Zone, event: HoldEvent) -> Feedback:
    if event is HoldEvent.COMPLETED:
        return Feedback.COMPLETED
    return _FROM_ZONE[zone]


def message(feedback: Feedback, note: Note) -> str:
    return _MESSAGES[feedback].format(note=note.solfege)
