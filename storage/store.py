"""JSON persistence of the single local profile (FR-20, FR-25), and level data loading."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from core.hold_timer import HoldMode
from core.levels import Level, parse_levels
from core.profile import Profile, Progress, Settings
from storage.paths import resource_path, user_data_dir

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1
PROFILE_FILE_NAME = "profile.json"


def default_profile_path() -> Path:
    return user_data_dir() / PROFILE_FILE_NAME


def load_levels(path: Path | None = None) -> tuple[Level, ...]:
    with open(path or resource_path("levels.json"), encoding="utf-8") as file:
        return parse_levels(json.load(file)["levels"])


class ProfileStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Profile:
        """Load the profile; a missing or unreadable file gives a fresh one."""
        if not self.path.exists():
            return Profile()
        try:
            with open(self.path, encoding="utf-8") as file:
                return _profile_from_json(json.load(file))
        except (OSError, ValueError, KeyError, TypeError):
            log.warning("Could not read %s; starting with a fresh profile", self.path, exc_info=True)
            return Profile()

    def save(self, profile: Profile) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        with open(temporary, "w", encoding="utf-8") as file:
            json.dump(_profile_to_json(profile), file, indent=2, ensure_ascii=False)
        os.replace(temporary, self.path)  # Atomic, so a crash never leaves half a file.


def _profile_to_json(profile: Profile) -> dict[str, Any]:
    settings, progress = profile.settings, profile.progress
    return {
        "version": SCHEMA_VERSION,
        "settings": {
            "tolerance_cents": settings.tolerance_cents,
            "instrument": settings.instrument,
            "volume": settings.volume,
            "mic_sensitivity": settings.mic_sensitivity,
            "hold_mode": settings.hold_mode.value,
            "input_device": settings.input_device,
        },
        "progress": {
            "unlocked_level": progress.unlocked_level,
            "best_stars": {str(level): stars for level, stars in progress.best_stars.items()},
        },
    }


def _profile_from_json(data: dict[str, Any]) -> Profile:
    defaults = Settings()
    raw_settings = data.get("settings", {})
    settings = Settings(
        tolerance_cents=float(raw_settings.get("tolerance_cents", defaults.tolerance_cents)),
        instrument=str(raw_settings.get("instrument", defaults.instrument)),
        volume=float(raw_settings.get("volume", defaults.volume)),
        mic_sensitivity=float(raw_settings.get("mic_sensitivity", defaults.mic_sensitivity)),
        hold_mode=HoldMode(raw_settings.get("hold_mode", defaults.hold_mode.value)),
        input_device=str(raw_settings.get("input_device", defaults.input_device)),
    )
    raw_progress = data.get("progress", {})
    progress = Progress(
        best_stars={int(level): int(stars) for level, stars in raw_progress.get("best_stars", {}).items()},
        unlocked_level=int(raw_progress.get("unlocked_level", 1)),
    )
    return Profile(settings, progress)
