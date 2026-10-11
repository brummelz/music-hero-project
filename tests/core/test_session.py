import random

import pytest

from core.feedback import Feedback, message
from core.hold_timer import HoldConfig, HoldEvent, HoldMode
from core.levels import Level
from core.notes import Note
from core.profile import Profile, Progress, Settings
from core.session import FrameState, GameSession, LevelSession, PracticeSession
from core.transpose import HORN_IN_F
from core.tuning import Zone
from storage.store import load_levels

FRAME = 0.02


def play(session: GameSession, start: float, seconds: float, cents: float | None) -> list[FrameState]:
    """Feed frames at ``cents`` from the current target (``None`` = silence)."""
    states = []
    for i in range(round(seconds / FRAME)):
        hz = None if cents is None else session.target_frequency * 2 ** (cents / 1200)
        states.append(session.process(start + i * FRAME, hz))
    return states


def hold_once(session: GameSession, start: float) -> float:
    """Play the current target in tune until one point is scored; return the end time."""
    points = session.points
    t = start
    while session.points == points:
        session.process(t, session.target_frequency)
        t += FRAME
    return t


def practice(note: str = "C4") -> PracticeSession:
    return PracticeSession(Note.parse(note), HORN_IN_F, 15)


def test_tc01_style_in_tune_is_green() -> None:
    state = practice("C5").process(0.0, 349.23)
    assert state.zone is Zone.GREEN
    assert state.cents == pytest.approx(0, abs=1)


def test_tc10_silence_gives_idle_and_no_points() -> None:
    session = practice()
    states = play(session, 0.0, 5.0, None)
    assert all(s.zone is Zone.IDLE and s.hold_fraction == 0 for s in states)
    assert session.points == 0


def test_tc17_practice_ends_at_ten_points() -> None:
    session = practice()
    t = 0.0
    for _ in range(10):
        t = hold_once(session, t)
    assert session.finished
    play(session, t, 5.0, 0)
    assert session.points == 10


def test_tc18_practice_target_fixed() -> None:
    session = practice("D4")
    t = 0.0
    for _ in range(3):
        t = hold_once(session, t)
        assert session.target_frequency == pytest.approx(196.00, abs=0.01)


def test_tc40_wrong_note_never_starts() -> None:
    session = practice()
    for cents in (200, 1200, -1200):
        states = play(session, 0.0, 5.0, cents)
        assert all(s.hold_fraction == 0 for s in states)
    assert session.points == 0


def test_tc28_tolerance_change_applies_immediately() -> None:
    session = practice()
    assert play(session, 0.0, 0.1, 20)[-1].zone is Zone.SHARP_NEAR
    session.tolerance_cents = 25
    assert play(session, 0.1, 0.1, 20)[-1].zone is Zone.GREEN
    with pytest.raises(ValueError):
        session.tolerance_cents = 60


def test_tc19_level_completes_after_all_prompts() -> None:
    level1 = load_levels()[0]
    session = LevelSession(level1, HORN_IN_F, 15, rng=random.Random(3))
    t = 0.0
    seen = []
    while not session.finished:
        seen.append(session.target_note)
        t = hold_once(session, t)
    assert seen == session.prompts
    assert len(seen) == 6
    assert session.misses == 0 and session.stars == 3


def test_fr22_level_misses_counted_per_reset() -> None:
    session = LevelSession(load_levels()[0], HORN_IN_F, 15, rng=random.Random(0))
    t = 0.0
    for _ in range(3):
        play(session, t, 1.0, 0)
        play(session, t + 1.0, 0.5, 40)
        t += 1.5
    assert session.misses == 3


def test_tc34_level_silence_is_not_a_miss() -> None:
    session = LevelSession(load_levels()[0], HORN_IN_F, 15, rng=random.Random(0))
    play(session, 0.0, 10.0, None)
    hold_once(session, 10.0)
    assert session.misses == 0


def test_pause_mode_counts_first_pause_per_prompt_only() -> None:
    level = Level(1, "t", (Note.parse("C4"), Note.parse("D4")))
    session = LevelSession(level, HORN_IN_F, 15, HoldConfig(mode=HoldMode.PAUSE), random.Random(0))
    t = 0.0
    for _ in range(3):
        play(session, t, 0.5, 0)
        play(session, t + 0.5, 0.5, None)
        t += 1.0
    assert session.misses == 1


def test_tc23_encouragement_for_each_state() -> None:
    session = practice()
    note = session.target_note
    flat = play(session, 0.0, 0.1, -20)[-1].feedback
    sharp = play(session, 0.1, 0.1, 20)[-1].feedback
    silence = play(session, 0.2, 0.5, None)[-1].feedback
    in_tune = play(session, 0.7, 0.1, 0)[-1].feedback
    completed = next(s.feedback for s in play(session, 0.8, 3.5, 0) if s.event is HoldEvent.COMPLETED)
    assert (flat, sharp, silence, in_tune, completed) == (
        Feedback.FLAT_NEAR,
        Feedback.SHARP_NEAR,
        Feedback.SILENCE,
        Feedback.IN_TUNE,
        Feedback.COMPLETED,
    )
    assert "higher" in message(flat, note)
    assert "Do" in message(silence, note)


def test_tc20_completing_level1_unlocks_level2_only() -> None:
    progress = Progress().with_level_result(1, 3, level_count=5)
    assert progress.is_unlocked(2) and not progress.is_unlocked(3)
    assert progress.stars_for(1) == 3


def test_tc35_best_stars_kept() -> None:
    progress = Progress().with_level_result(1, 3, 5).with_level_result(1, 1, 5)
    assert progress.stars_for(1) == 3


def test_last_level_does_not_unlock_beyond_table() -> None:
    assert Progress(unlocked_level=5).with_level_result(5, 2, 5).unlocked_level == 5


def test_tc24_total_stars_is_sum_of_best() -> None:
    progress = Progress().with_level_result(1, 3, 5).with_level_result(2, 2, 5)
    assert progress.total_stars == 5


def test_tc38_reset_progress_keeps_settings() -> None:
    profile = Profile(Settings(tolerance_cents=25), Progress({1: 3}, 2))
    reset = profile.with_progress_reset()
    assert reset.progress == Progress()
    assert reset.settings.tolerance_cents == 25


def test_settings_validation() -> None:
    with pytest.raises(ValueError):
        Settings(tolerance_cents=4)
    with pytest.raises(ValueError):
        Settings(volume=1.5)


def test_restart_hold_drops_progress_without_a_miss() -> None:
    session = LevelSession(load_levels()[0], HORN_IN_F, 15, rng=random.Random(0))
    play(session, 0.0, 2.0, 0)
    session.restart_hold()
    assert play(session, 2.0, 0.04, 0)[-1].hold_fraction < 0.05
    assert session.misses == 0
