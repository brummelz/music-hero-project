import pytest

from core.hold_timer import HoldConfig, HoldEvent, HoldMode, HoldTimer

FRAME = 0.02  # 20 ms detection frames


def run(timer: HoldTimer, start: float, end: float, in_zone: bool) -> list[HoldEvent]:
    """Feed frames in [start, end) and return the non-NONE events."""
    events = []
    steps = round((end - start) / FRAME)
    for i in range(steps):
        event = timer.update(start + i * FRAME, in_zone)
        if event is not HoldEvent.NONE:
            events.append(event)
    return events


def test_tc03_full_hold_completes_and_resets() -> None:
    timer = HoldTimer()
    events = run(timer, 0.0, 3.0 + FRAME, True)
    assert events == [HoldEvent.COMPLETED]
    assert timer.elapsed == pytest.approx(0.0)


def test_tc04_leaving_resets_without_point() -> None:
    timer = HoldTimer()
    assert run(timer, 0.0, 1.8, True) == []
    assert run(timer, 1.8, 2.5, False) == [HoldEvent.MISSED]
    assert timer.elapsed == 0.0


def test_tc10_silence_never_starts() -> None:
    timer = HoldTimer()
    assert run(timer, 0.0, 5.0, False) == []
    assert timer.elapsed == 0.0


def test_tc11_just_short_gives_no_point() -> None:
    timer = HoldTimer()
    assert run(timer, 0.0, 2.9, True) == []
    assert run(timer, 2.9, 3.5, False) == [HoldEvent.MISSED]


def test_tc12_dropout_within_grace_continues() -> None:
    timer = HoldTimer()
    run(timer, 0.0, 1.5, True)
    assert run(timer, 1.5, 1.6, False) == []
    assert run(timer, 1.6, 2.0, True) == []
    assert timer.elapsed == pytest.approx(2.0 - FRAME)


def test_tc13_dropout_beyond_grace_resets() -> None:
    timer = HoldTimer()
    run(timer, 0.0, 1.5, True)
    assert run(timer, 1.5, 1.8, False) == [HoldEvent.MISSED]
    assert timer.elapsed == 0.0


def test_tc14_pause_mode_resumes() -> None:
    timer = HoldTimer(HoldConfig(mode=HoldMode.PAUSE))
    run(timer, 0.0, 1.8 + FRAME, True)
    assert run(timer, 1.8 + FRAME, 2.8, False) == [HoldEvent.MISSED]
    assert timer.elapsed == pytest.approx(1.8)
    assert run(timer, 2.8, 2.8 + 1.2, True) == []
    assert timer.update(2.8 + 1.2, True) is HoldEvent.COMPLETED


def test_tc15_continuous_six_seconds_gives_two_points() -> None:
    timer = HoldTimer()
    assert run(timer, 0.0, 6.0 + FRAME, True) == [HoldEvent.COMPLETED, HoldEvent.COMPLETED]


def test_tc39_counter_starts_on_entering_range() -> None:
    timer = HoldTimer()
    assert run(timer, 0.0, 2.0, False) == []
    assert timer.elapsed == 0.0
    events_at = []
    t = 2.0
    while t < 5.5:
        if timer.update(t, True) is HoldEvent.COMPLETED:
            events_at.append(t)
        t += FRAME
    assert len(events_at) == 1
    assert events_at[0] == pytest.approx(5.0, abs=FRAME)


def test_tc34_silence_before_playing_is_not_a_miss() -> None:
    timer = HoldTimer()
    assert run(timer, 0.0, 10.0, False) == []
    assert run(timer, 10.0, 13.0 + FRAME, True) == [HoldEvent.COMPLETED]


def test_stopping_right_after_a_point_is_not_a_miss() -> None:
    timer = HoldTimer()
    run(timer, 0.0, 3.0 + FRAME, True)
    assert run(timer, 3.0 + FRAME, 4.0, False) == []
