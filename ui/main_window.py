"""Main window: navigation between screens and the single profile (FR-20, FR-25)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import replace

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from audio.devices import InputDevice, list_input_devices
from audio.sources import AudioSource, MicrophoneSource
from core.hold_timer import HoldConfig
from core.levels import Level
from core.notes import Note
from core.profile import Profile, Settings
from core.session import PRACTICE_NOTES, GameSession, LevelSession, PracticeSession
from core.transpose import profile_by_name
from storage.paths import resource_path
from storage.store import ProfileStore
from ui.cover_screen import CoverScreen
from ui.game_screen import GameScreen
from ui.home_screen import HomeScreen
from ui.settings_dialog import SettingsDialog
from ui.summary_screen import SummaryScreen

log = logging.getLogger(__name__)

WINDOW_SIZE = (1100, 820)
MINIMUM_SIZE = (960, 720)


class MainWindow(QMainWindow):
    def __init__(self, store: ProfileStore, levels: Sequence[Level], source: AudioSource) -> None:
        super().__init__()
        self.setWindowTitle("Horn Hero")
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(*MINIMUM_SIZE)
        self._store = store
        self._levels = levels
        self._source = source
        self._profile = store.load()
        self._replay: Callable[[], None] | None = None
        self._next_level: Level | None = None
        self._audio_error: str | None = None

        self._cover = CoverScreen(resource_path("cover.jpg"))
        self._home = HomeScreen(PRACTICE_NOTES, levels)
        self._game = GameScreen(source)
        self._summary = SummaryScreen()
        self._stack = QStackedWidget()
        for screen in (self._cover, self._home, self._game, self._summary):
            self._stack.addWidget(screen)
        self.setCentralWidget(self._stack)

        self._cover.start_requested.connect(self._show_home)
        self._home.practice_requested.connect(self._start_practice)
        self._home.level_requested.connect(self._start_level)
        self._home.settings_requested.connect(self._open_settings)
        self._game.back_requested.connect(self._leave_game)
        self._game.settings_requested.connect(self._open_settings)
        self._game.session_finished.connect(self._on_session_finished)
        self._summary.home_requested.connect(self._show_home)
        self._summary.play_again_requested.connect(self._play_again)
        self._summary.next_level_requested.connect(self._play_next_level)

        QTimer.singleShot(0, self._start_up)

    def _start_up(self) -> None:
        self._cover.begin_loading()
        self._cover.setFocus()
        self._source.set_device(self._settings.input_device)
        self._open_audio(self._source.start)

    def _open_audio(self, action: Callable[[], None]) -> None:
        try:
            action()
            self._audio_error = None
        except Exception as error:  # Any PortAudio failure: keep the app usable and say why.
            log.exception("Could not open the microphone")
            self._audio_error = f"Microphone not available: {error}"
        self._game.set_audio_error(self._audio_error)

    def _devices(self) -> list[InputDevice] | None:
        if not isinstance(self._source, MicrophoneSource):
            return None
        try:
            return list_input_devices()
        except Exception:
            log.exception("Could not list microphones")
            return []

    @property
    def _settings(self) -> Settings:
        return self._profile.settings

    def _save(self, profile: Profile) -> None:
        self._profile = profile
        try:
            self._store.save(profile)
        except OSError:
            log.exception("Could not save progress to %s", self._store.path)

    def _hold_config(self) -> HoldConfig:
        return HoldConfig(mode=self._settings.hold_mode)

    def _show_home(self) -> None:
        self._home.refresh(self._profile.progress, self._settings.instrument)
        self._stack.setCurrentWidget(self._home)

    def _start_game(self, session: GameSession, caption: str, replay: Callable[[], None]) -> None:
        self._replay = replay
        self._stack.setCurrentWidget(self._game)
        self._game.start(session, self._settings, caption)

    def _start_practice(self, note: Note) -> None:
        profile = profile_by_name(self._settings.instrument)
        session = PracticeSession(note, profile, self._settings.tolerance_cents, self._hold_config())
        self._start_game(session, "Target note", lambda: self._start_practice(note))

    def _start_level(self, number: int) -> None:
        level = self._levels[number - 1]
        profile = profile_by_name(self._settings.instrument)
        session = LevelSession(level, profile, self._settings.tolerance_cents, self._hold_config())
        self._start_game(session, f"Level {level.number} · {level.theme}", lambda: self._start_level(number))

    def _leave_game(self) -> None:
        self._game.stop()
        self._show_home()

    def _on_session_finished(self, session: GameSession) -> None:
        self._game.stop()
        if isinstance(session, LevelSession):
            level = session.level
            before = self._profile.progress
            after = before.with_level_result(level.number, session.stars, len(self._levels))
            self._save(replace(self._profile, progress=after))
            has_next = level.number < len(self._levels)
            self._next_level = self._levels[level.number] if has_next else None
            newly_unlocked = self._next_level if after.unlocked_level > before.unlocked_level else None
            self._summary.show_level(level, session.stars, session.misses, newly_unlocked, self._next_level)
        elif isinstance(session, PracticeSession):
            self._summary.show_practice(session.target_note, session.points)
        self._stack.setCurrentWidget(self._summary)

    def _play_again(self) -> None:
        if self._replay:
            self._replay()

    def _play_next_level(self) -> None:
        if self._next_level:
            self._start_level(self._next_level.number)

    def _open_settings(self) -> None:
        in_game = self._stack.currentWidget() is self._game
        if in_game:
            self._game.pause()
        dialog = SettingsDialog(
            self._settings, self._source, self._devices(), lambda: self._audio_error, self
        )
        dialog.settings_changed.connect(self._apply_settings)
        dialog.reset_requested.connect(self._reset_progress)
        dialog.exec()
        if self._stack.currentWidget() is self._home:
            self._show_home()
        elif in_game:
            self._game.resume()

    def _apply_settings(self, settings: Settings) -> None:
        if settings.input_device != self._settings.input_device:
            self._open_audio(lambda: self._source.set_device(settings.input_device))
        self._save(replace(self._profile, settings=settings))
        self._game.apply_settings(settings)

    def _reset_progress(self) -> None:
        self._save(self._profile.with_progress_reset())

    def closeEvent(self, event: QCloseEvent) -> None:
        self._game.stop()
        self._source.stop()
        super().closeEvent(event)
