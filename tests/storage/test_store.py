from pathlib import Path

from core.hold_timer import HoldMode
from core.profile import Profile, Progress, Settings
from storage.store import ProfileStore


def test_tc37_fresh_install_gives_default_profile(tmp_path: Path) -> None:
    assert ProfileStore(tmp_path / "profile.json").load() == Profile()


def test_tc21_tc28_round_trip_after_restart(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "profile.json"
    profile = Profile(
        Settings(
            tolerance_cents=10,
            volume=0.3,
            mic_sensitivity=0.9,
            hold_mode=HoldMode.PAUSE,
            input_device="USB Mic",
        ),
        Progress({1: 3, 2: 1}, unlocked_level=3),
    )
    ProfileStore(path).save(profile)
    assert ProfileStore(path).load() == profile


def test_tc38_reset_progress_persists(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profile.json")
    store.save(Profile(progress=Progress({1: 3}, 2)))
    store.save(store.load().with_progress_reset())
    loaded = store.load()
    assert loaded.progress.total_stars == 0
    assert loaded.progress.unlocked_level == 1


def test_corrupt_file_falls_back_to_defaults(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    path.write_text("{not json", encoding="utf-8")
    assert ProfileStore(path).load() == Profile()
