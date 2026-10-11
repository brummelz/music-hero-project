"""Gameplay screen: staff, tuner gauge, hold ring and encouragement (spec Screen 2)."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from audio import sfx
from audio.sources import AudioSource, SimulatedSource
from audio.tracker import PitchTracker
from core.feedback import Feedback, message
from core.hold_timer import HoldEvent, HoldMode
from core.notes import midi_label
from core.profile import Settings
from core.session import GameSession
from core.transpose import nearest_written_note
from core.tuning import Zone
from ui import theme
from ui.widgets import GaugeWidget, HoldButton, ScorePill, StaffWidget

TICK_MS = 15
CELEBRATE_SECONDS = 1.2
FINISH_DELAY_MS = 1400
MIN_MESSAGE_SECONDS = 0.4
"""A wobbling note should not make the message flicker; 'in tune' still shows at once."""
TRY_AGAIN_AFTER_SECONDS = 1.0
"""Only a hold this far along gets the 'So close!' cue when it restarts."""
TRY_AGAIN_SECONDS = 1.5
LISTEN_TAIL_SECONDS = 0.3
"""Keep ignoring the microphone briefly after the reference note, so its echo is not scored."""

# Simulation keys and the offset (cents) they play from the target.
_SIMULATED_KEYS = {Qt.Key.Key_Space: 3.0, Qt.Key.Key_Up: 35.0, Qt.Key.Key_Down: -35.0}


class GameScreen(QWidget):
    back_requested = Signal()
    settings_requested = Signal()
    session_finished = Signal(object)  # GameSession

    def __init__(self, source: AudioSource, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("screen")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._source = source
        self._tracker = PitchTracker(source.sample_rate)
        self._session: GameSession | None = None
        self._settings = Settings()
        self._feedback: Feedback | None = None
        self._feedback_since = 0.0
        self._celebrate_until = 0.0
        self._try_again_until = 0.0
        self._listen_until = 0.0
        self._last_fraction = 0.0
        self._audio_error: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(18)
        root.addLayout(self._build_top_bar())

        staff_card = QFrame()
        staff_card.setObjectName("card")
        staff_layout = QVBoxLayout(staff_card)
        staff_layout.setContentsMargins(0, 0, 0, 0)
        self._staff = StaffWidget()
        staff_layout.addWidget(self._staff)
        root.addWidget(staff_card, 1)

        gauge_card = QFrame()
        gauge_card.setObjectName("card")
        gauge_layout = QVBoxLayout(gauge_card)
        gauge_layout.setContentsMargins(0, 10, 0, 8)
        self._gauge = GaugeWidget()
        gauge_layout.addWidget(self._gauge)
        root.addWidget(gauge_card)

        root.addWidget(self._build_feedback_bar())

        self._simulation_hint = QLabel("Simulation: hold Space = in tune, ↑ = sharp, ↓ = flat")
        self._simulation_hint.setObjectName("muted")
        self._simulation_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._simulation_hint.setVisible(isinstance(source, SimulatedSource))
        root.addWidget(self._simulation_hint)

        self._timer = QTimer(self)
        self._timer.setInterval(TICK_MS)
        self._timer.timeout.connect(self._tick)

    def _build_top_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        back = QPushButton("←")
        back.setObjectName("round")
        back.setAccessibleName("Back")
        back.setToolTip("Back")
        back.clicked.connect(self.back_requested)
        bar.addWidget(back)
        bar.addStretch(1)

        center = QVBoxLayout()
        center.setSpacing(0)
        self._caption = QLabel()
        self._caption.setObjectName("caption")
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note_row = QHBoxLayout()
        note_row.setSpacing(14)
        self._note_label = QLabel()
        self._note_label.setFont(theme.display_font(44))
        listen = QPushButton(theme.SPEAKER)
        listen.setObjectName("round")
        listen.setFont(QFont(theme.MUSIC_FAMILY, 20))
        listen.setAccessibleName("Hear the note")
        listen.setToolTip("Hear the note")
        listen.setCursor(Qt.CursorShape.PointingHandCursor)
        listen.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # A click must not steal the game's keyboard focus.
        listen.clicked.connect(self._play_reference)
        note_row.addStretch(1)
        note_row.addWidget(self._note_label)
        note_row.addWidget(listen)
        note_row.addStretch(1)
        center.addWidget(self._caption)
        center.addLayout(note_row)
        bar.addLayout(center)
        bar.addStretch(1)

        settings = HoldButton(theme.GEAR, "Hold to open settings")
        settings.setObjectName("round")
        settings.setFont(QFont(theme.MUSIC_FAMILY, 20))
        settings.setAccessibleName("Settings (hold)")
        settings.held.connect(self.settings_requested)
        bar.addWidget(settings)
        bar.addSpacing(10)
        self._score = ScorePill()
        bar.addWidget(self._score)
        return bar

    def _build_feedback_bar(self) -> QFrame:
        self._feedback_bar = QFrame()
        self._feedback_bar.setObjectName("feedback")
        self._feedback_bar.setFixedHeight(84)
        row = QHBoxLayout(self._feedback_bar)
        row.setContentsMargins(22, 0, 28, 0)
        row.setSpacing(18)
        self._feedback_icon = QLabel()
        self._feedback_icon.setFixedSize(52, 52)
        self._feedback_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feedback_icon.setFont(theme.body_font(26, QFont.Weight.Black))
        self._feedback_icon.setStyleSheet("background: white; border-radius: 26px;")
        self._feedback_text = QLabel()
        self._feedback_text.setFont(theme.display_font(28, QFont.Weight.DemiBold))
        self._feedback_text.setStyleSheet("background: transparent;")
        self._info_label = QLabel()
        self._info_label.setFont(theme.body_font(22))
        self._info_label.setStyleSheet("background: transparent;")
        row.addWidget(self._feedback_icon)
        row.addWidget(self._feedback_text, 1)
        row.addWidget(self._info_label)
        return self._feedback_bar

    def set_audio_error(self, error: str | None) -> None:
        self._audio_error = error

    def start(self, session: GameSession, settings: Settings, caption: str) -> None:
        self._session = session
        self._caption.setText(caption.upper())
        self._staff.set_captions(
            f"Written pitch · {session.profile.name}", f"Hold for {session.hold_seconds:g} seconds"
        )
        self.apply_settings(settings)
        self._celebrate_until = self._try_again_until = self._listen_until = 0.0
        self._last_fraction = 0.0
        self._tracker.reset()
        self._feedback = None
        self._show_target()
        self._show_feedback(Feedback.SILENCE, 0.0)
        self._staff.set_state(0.0, False, True)
        self._gauge.set_reading(None, Zone.IDLE)
        self._info_label.setText("")
        self._timer.start()
        self.setFocus()

    def stop(self) -> None:
        self._timer.stop()
        if isinstance(self._source, SimulatedSource):
            self._source.frequency_hz = None

    def pause(self) -> None:
        self._timer.stop()

    def resume(self) -> None:
        """Continue after a pause; the interrupted hold starts again from zero."""
        if self._session is None or self._session.finished:
            return
        self._session.restart_hold()
        self._tracker.reset()
        self._timer.start()
        self.setFocus()

    def apply_settings(self, settings: Settings) -> None:
        """FR-21: tolerance changes apply immediately to the running session."""
        self._settings = settings
        self._tracker.set_sensitivity(settings.mic_sensitivity)
        self._gauge.set_tolerance(settings.tolerance_cents)
        if self._session is not None:
            self._session.tolerance_cents = settings.tolerance_cents

    def _play_reference(self) -> None:
        if self._session is None or self._session.finished:
            return
        duration = sfx.play_reference(self._session.target_frequency, self._settings.volume)
        self._listen_until = time.monotonic() + duration + LISTEN_TAIL_SECONDS
        self._feedback = None
        self._feedback_bar.setStyleSheet(
            f"QFrame#feedback {{ background: {theme.IDLE_SOFT}; border-radius: 28px; }}"
        )
        self._feedback_icon.setText("♪")
        self._feedback_text.setText("Listen… then play it back!")
        self._info_label.setText("")
        self.setFocus()

    def _show_target(self) -> None:
        assert self._session is not None
        note = self._session.target_note
        self._note_label.setText(note.label)
        self._staff.set_note(note)
        self._score.set_score(self._session.points, self._session.goal)

    def _show_feedback(self, feedback: Feedback, now: float) -> None:
        if feedback is self._feedback or self._session is None:
            return
        steady_since = now - self._feedback_since
        if (
            self._feedback is not None
            and feedback is not Feedback.IN_TUNE
            and steady_since < MIN_MESSAGE_SECONDS
        ):
            return
        self._feedback = feedback
        self._feedback_since = now
        self._feedback_bar.setStyleSheet(
            f"QFrame#feedback {{ background: {theme.FEEDBACK_BACKGROUND[feedback]}; border-radius: 28px; }}"
        )
        self._feedback_icon.setText(theme.FEEDBACK_ICON[feedback])
        self._feedback_text.setText(message(feedback, self._session.target_note))

    def _tick(self) -> None:
        session = self._session
        if session is None:
            return
        if self._audio_error:
            self._feedback_text.setText(self._audio_error)
            return
        window = self._source.read_window()
        if window is None:
            return
        now = time.monotonic()
        if self._listen_until:
            if now < self._listen_until:
                return  # The reference note is playing; don't score what the mic hears.
            self._listen_until = 0.0
            session.restart_hold()
            self._tracker.reset()
        self._tracker.set_sample_rate(self._source.sample_rate)
        frequency = self._tracker.update(window)
        state = session.process(now, frequency)

        if state.event is HoldEvent.COMPLETED:
            sfx.play_success(self._settings.volume)
            self._celebrate_until = now + CELEBRATE_SECONDS
            self._feedback = None  # Show the celebration right away, naming the right note.
            if session.finished:
                self._score.set_score(session.points, session.goal)
                self._timer.stop()
                QTimer.singleShot(FINISH_DELAY_MS, lambda: self.session_finished.emit(session))
            else:
                self._show_target()
        elif state.event is HoldEvent.MISSED and self._should_cue_restart(session):
            self._try_again_until = now + TRY_AGAIN_SECONDS
            self._feedback = None
        self._last_fraction = state.hold_fraction

        if now < self._celebrate_until:
            feedback = Feedback.COMPLETED
        elif now < self._try_again_until and state.zone is not Zone.GREEN:
            feedback = Feedback.TRY_AGAIN
        else:
            feedback = state.feedback
        self._show_feedback(feedback, now)

        idle = state.zone is Zone.IDLE and state.hold_fraction == 0
        in_tune = state.zone is Zone.GREEN or now < self._celebrate_until
        self._staff.set_state(state.hold_fraction, in_tune, idle)
        self._gauge.set_reading(state.cents, state.zone)
        self._info_label.setText(self._info_text(session, state.zone, frequency, state.hold_fraction))

    def _should_cue_restart(self, session: GameSession) -> bool:
        lost_seconds = self._last_fraction * session.hold_seconds
        return self._settings.hold_mode is HoldMode.RESET and lost_seconds >= TRY_AGAIN_AFTER_SECONDS

    @staticmethod
    def _info_text(session: GameSession, zone: Zone, frequency: float | None, fraction: float) -> str:
        """Hold time while in tune; otherwise which note the app hears, to guide the player."""
        if zone is Zone.GREEN or (fraction > 0 and frequency is None):
            total = session.hold_seconds
            return f"{fraction * total:.1f} / {total:.1f} s"
        if frequency is None:
            return "Listening…"
        written_midi, _ = nearest_written_note(frequency, session.profile)
        return f"Hearing {midi_label(written_midi)}"

    def keyPressEvent(self, event: QKeyEvent) -> None:
        offset = _SIMULATED_KEYS.get(Qt.Key(event.key()))
        if isinstance(self._source, SimulatedSource) and offset is not None and self._session:
            if not event.isAutoRepeat():
                self._source.frequency_hz = self._session.target_frequency * 2 ** (offset / 1200)
            return
        if event.key() == Qt.Key.Key_Escape:
            self.back_requested.emit()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        is_simulated_key = Qt.Key(event.key()) in _SIMULATED_KEYS
        if isinstance(self._source, SimulatedSource) and is_simulated_key and not event.isAutoRepeat():
            self._source.frequency_hz = None
            return
        super().keyReleaseEvent(event)
