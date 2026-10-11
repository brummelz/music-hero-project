"""Celebration shown when a practice session or a level is complete (FR-14, FR-17)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.levels import THREE_STAR_MAX_MISSES, Level
from core.notes import Note
from ui import theme
from ui.widgets import ScorePill, StarRow


class SummaryScreen(QWidget):
    play_again_requested = Signal()
    next_level_requested = Signal()
    home_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("screen")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)

        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(22)
        layout.addStretch(1)

        self._title = QLabel()
        self._title.setFont(theme.display_font(58))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title)

        self._stars = StarRow(130)
        layout.addWidget(self._stars, 0, Qt.AlignmentFlag.AlignHCenter)

        self._points = ScorePill()
        layout.addWidget(self._points, 0, Qt.AlignmentFlag.AlignHCenter)

        self._message = QLabel()
        self._message.setFont(theme.body_font(24))
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setWordWrap(True)
        self._message.setObjectName("muted")
        layout.addWidget(self._message)

        self._unlocked = QLabel()
        self._unlocked.setFont(theme.body_font(20))
        self._unlocked.setStyleSheet(
            f"background: {theme.GREEN_SOFT}; border-radius: 22px; padding: 10px 22px;"
        )
        layout.addWidget(self._unlocked, 0, Qt.AlignmentFlag.AlignHCenter)

        buttons = QHBoxLayout()
        buttons.setSpacing(20)
        buttons.addStretch(1)
        self._home = QPushButton("Home")
        self._home.setObjectName("secondary")
        self._home.clicked.connect(self.home_requested)
        self._again = QPushButton("Play again")
        self._again.clicked.connect(self.play_again_requested)
        self._next = QPushButton("Next level")
        self._next.setObjectName("primary")
        self._next.clicked.connect(self.next_level_requested)
        for button in (self._home, self._again, self._next):
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addSpacing(8)
        layout.addLayout(buttons)
        layout.addStretch(1)
        root.addWidget(card)

    def show_practice(self, note: Note, points: int) -> None:
        self._title.setText("You did it!")
        self._stars.hide()  # FR-24: practice awards no stars, so show the points row instead.
        self._points.set_score(points, points)
        self._points.show()
        self._message.setText(f"You held {points} steady {note.solfege} notes. Super playing!")
        self._unlocked.hide()
        self._next.hide()
        self._again.setObjectName("primary")
        self._restyle(self._again)
        self._again.setFocus()

    def show_level(
        self,
        level: Level,
        stars: int,
        misses: int,
        newly_unlocked: Level | None,
        next_level: Level | None,
    ) -> None:
        self._title.setText(f"Level {level.number} complete!")
        self._stars.set_stars(stars)
        self._stars.show()
        self._points.hide()
        self._message.setText(self._star_reason(stars, misses))
        self._unlocked.setVisible(newly_unlocked is not None)
        if newly_unlocked is not None:
            self._unlocked.setText(f"✓  Level {newly_unlocked.number} unlocked: {newly_unlocked.theme}")
        self._next.setVisible(next_level is not None)
        self._again.setObjectName("secondary" if next_level else "primary")
        self._restyle(self._again)
        (self._next if next_level else self._again).setFocus()

    @staticmethod
    def _star_reason(stars: int, misses: int) -> str:
        """FR-22/FR-23: say why, so the stars feel earned rather than random."""
        if misses == 0:
            return "Amazing! All 3 stars!"
        restarts = "1 restart" if misses == 1 else f"{misses} restarts"
        if stars == 3:
            return f"Amazing! All 3 stars ({restarts})."
        return (
            f"Great playing! You had {restarts}. "
            f"Keep it to {THREE_STAR_MAX_MISSES} or fewer to win all 3 stars."
        )

    @staticmethod
    def _restyle(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
