"""Home: mode selection with Practice and Adventure (spec Screen 1)."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.levels import Level
from core.notes import Note
from core.profile import Progress
from ui import theme
from ui.widgets import HoldButton, StarRow


def _passive(widget: QWidget) -> QWidget:
    """Let clicks pass through a label placed inside a button."""
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    widget.setStyleSheet("background: transparent; border: none;")
    return widget


def _icon_circle(glyph: str, color: str, size: int = 58) -> QLabel:
    label = QLabel(glyph)
    label.setFixedSize(size, size)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFont(theme.body_font(round(size * 0.48)))
    label.setStyleSheet(f"background: {color}; border-radius: {size // 2}px;")
    return label


def _card_header(glyph: str, color: str, title: str, subtitle: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(16)
    row.addWidget(_icon_circle(glyph, color))
    text = QVBoxLayout()
    text.setSpacing(2)
    title_label = QLabel(title)
    title_label.setFont(theme.display_font(34))
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("muted")
    text.addWidget(title_label)
    text.addWidget(subtitle_label)
    row.addLayout(text, 1)
    return row


class HomeScreen(QWidget):
    practice_requested = Signal(object)  # Note
    level_requested = Signal(int)
    settings_requested = Signal()

    def __init__(
        self, practice_notes: Sequence[Note], levels: Sequence[Level], parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.setObjectName("screen")
        self._levels = levels
        self._practice_notes = list(practice_notes)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(18)
        root.addLayout(self._build_header())

        question = QLabel("What do you want to play today?")
        question.setFont(theme.display_font(38))
        question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(question)

        cards = QHBoxLayout()
        cards.setSpacing(24)
        cards.addWidget(self._build_practice_card(), 1)
        cards.addWidget(self._build_adventure_card(), 1)
        root.addLayout(cards, 1)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(14)
        logo = _icon_circle("♪", theme.ACCENT, 54)
        logo.setStyleSheet(logo.styleSheet() + " color: white;")
        header.addWidget(logo)
        title = QLabel("Horn Hero")
        title.setFont(theme.display_font(34))
        header.addWidget(title)
        header.addStretch(1)

        self._stars = QLabel()
        self._stars.setFont(theme.display_font(24))
        self._stars.setStyleSheet(
            f"background: {theme.YELLOW}; border-radius: 27px; padding: 0 20px; min-height: 54px;"
        )
        header.addWidget(self._stars)

        self._instrument = QLabel()
        self._instrument.setFont(theme.body_font(18))
        self._instrument.setStyleSheet(
            f"background: white; border: 3px solid {theme.INK}; border-radius: 27px;"
            " padding: 0 18px; min-height: 48px;"
        )
        header.addWidget(self._instrument)

        settings = HoldButton(theme.GEAR, "Hold to open settings")
        settings.setObjectName("round")
        settings.setFont(QFont(theme.MUSIC_FAMILY, 20))
        settings.setAccessibleName("Settings (hold)")
        settings.held.connect(self.settings_requested)
        header.addWidget(settings)
        return header

    def _build_practice_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(20)
        layout.addLayout(_card_header("♪", theme.YELLOW, "Practice", "Pick one note and play it 10 times."))

        notes_row = QHBoxLayout()
        notes_row.setSpacing(14)
        self._note_group = QButtonGroup(self)
        for index, note in enumerate(self._practice_notes):
            button = QPushButton()
            button.setObjectName("note")
            button.setCheckable(True)
            button.setAccessibleName(f"{note.solfege} ({note.letter})")
            inner = QVBoxLayout(button)
            inner.setSpacing(0)
            main = QLabel(note.solfege)
            main.setFont(theme.display_font(42))
            main.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub = QLabel(note.letter)
            sub.setFont(theme.body_font(20))
            sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub.setObjectName("muted")
            inner.addStretch(1)
            inner.addWidget(_passive(main))
            inner.addWidget(_passive(sub))
            inner.addStretch(1)
            self._note_group.addButton(button, index)
            notes_row.addWidget(button)
        buttons = self._note_group.buttons()
        if buttons:
            buttons[0].setChecked(True)
        layout.addLayout(notes_row)

        hint = QLabel("Hold the note steady for 3 seconds to score a point.")
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"background: {theme.GROUND}; border-radius: 16px; padding: 14px 16px; font-weight: 700;"
        )
        layout.addWidget(hint)
        layout.addStretch(1)

        start = QPushButton("Start practice")
        start.setObjectName("primary")
        start.clicked.connect(self._on_start_practice)
        layout.addWidget(start)
        return card

    def _build_adventure_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(18)
        layout.addLayout(_card_header("⚑", theme.GREEN, "Adventure", "Finish levels and collect stars."))
        self._level_list = QVBoxLayout()
        self._level_list.setSpacing(8)
        layout.addLayout(self._level_list)
        layout.addStretch(1)
        return card

    def _on_start_practice(self) -> None:
        index = self._note_group.checkedId()
        if index >= 0:
            self.practice_requested.emit(self._practice_notes[index])

    def refresh(self, progress: Progress, instrument_name: str) -> None:
        max_stars = 3 * len(self._levels)
        self._stars.setText(f"★  {progress.total_stars} / {max_stars}")
        self._stars.setAccessibleName(f"{progress.total_stars} of {max_stars} stars earned")
        self._instrument.setText(instrument_name)

        while self._level_list.count():
            item = self._level_list.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()
        for level in self._levels:
            self._level_list.addWidget(self._level_row(level, progress))

    def _level_row(self, level: Level, progress: Progress) -> QPushButton:
        unlocked = progress.is_unlocked(level.number)
        stars = progress.stars_for(level.number)
        current = unlocked and stars == 0

        button = QPushButton()
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row = QHBoxLayout(button)
        row.setContentsMargins(10, 4, 14, 4)
        row.setSpacing(12)

        badge = QLabel(str(level.number) if unlocked else theme.LOCK)
        badge.setFixedSize(38, 38)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFont(theme.display_font(20) if unlocked else QFont(theme.MUSIC_FAMILY, 13))
        theme_label = QLabel(level.theme)
        theme_label.setFont(theme.body_font(19))
        row.addWidget(_passive(badge))
        row.addWidget(_passive(theme_label), 1)

        if not unlocked:
            button.setObjectName("levelLocked")
            button.setEnabled(False)
            button.setAccessibleName(f"Level {level.number}, {level.theme}, locked")
            badge.setStyleSheet(f"background: {theme.IDLE_SOFT}; border-radius: 19px; color: {theme.MUTED};")
            theme_label.setStyleSheet(f"background: transparent; color: {theme.MUTED};")
            locked = QLabel("Locked")
            locked.setFont(theme.body_font(16))
            locked.setStyleSheet(f"background: transparent; color: {theme.MUTED};")
            row.addWidget(_passive(locked))
            return button

        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda: self.level_requested.emit(level.number))
        if current:
            button.setObjectName("levelCurrent")
            button.setAccessibleName(f"Level {level.number}, {level.theme}, play")
            badge.setStyleSheet(f"background: {theme.ACCENT}; color: white; border-radius: 19px;")
            play = QLabel("Play")
            play.setFont(theme.display_font(19))
            play.setStyleSheet(
                f"background: {theme.ACCENT}; color: white; border-radius: 18px; padding: 6px 20px;"
            )
            play.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row.addWidget(play)
        else:
            button.setObjectName("level")
            button.setAccessibleName(f"Level {level.number}, {level.theme}, {stars} of 3 stars")
            badge.setStyleSheet(f"background: {theme.GREEN_SOFT}; border-radius: 19px;")
            star_row = StarRow(24)
            star_row.set_stars(stars)
            row.addWidget(_passive(star_row))
        return button
