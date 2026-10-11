"""Cover shown while the app starts, then the initial page with Start Game."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPaintEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from ui import theme

# Where the illustration's own "Start Game!" button sits, as fractions of the image.
_BUTTON_AREA = (0.322, 0.794, 0.359, 0.099)
_BUTTON_COLOR = "#4636B9"  # Sampled from the illustration so the overlay blends in.
_LOADING_MS = 1600
_LOADING_STEP_MS = 30


class CoverScreen(QWidget):
    start_requested = Signal()

    def __init__(self, image_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("screen")
        self._image = QPixmap(str(image_path))
        self._ready = False

        self._loading = QFrame(self)
        self._loading_label = QLabel("Warming up the horn…")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_bar = QProgressBar()
        self._loading_bar.setTextVisible(False)
        self._loading_bar.setRange(0, _LOADING_MS)
        loading_layout = QVBoxLayout(self._loading)
        loading_layout.setContentsMargins(24, 6, 24, 10)
        loading_layout.setSpacing(6)
        loading_layout.addWidget(self._loading_label)
        loading_layout.addWidget(self._loading_bar)

        self._start = QPushButton("Start Game!", self)
        self._start.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start.clicked.connect(self.start_requested)
        self._start.hide()

        self._timer = QTimer(self)
        self._timer.setInterval(_LOADING_STEP_MS)
        self._timer.timeout.connect(self._advance_loading)

    def begin_loading(self) -> None:
        self._loading_bar.setValue(0)
        self._timer.start()

    def _advance_loading(self) -> None:
        value = self._loading_bar.value() + _LOADING_STEP_MS
        self._loading_bar.setValue(value)
        if value >= _LOADING_MS:
            self._timer.stop()
            self._ready = True
            self._loading.hide()
            self._start.show()
            self._start.setFocus()

    def _image_rect(self) -> QRectF:
        if self._image.isNull():
            return QRectF(self.rect())
        scale = min(self.width() / self._image.width(), self.height() / self._image.height())
        width, height = self._image.width() * scale, self._image.height() * scale
        return QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(theme.GROUND))
        if not self._image.isNull():
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(self._image_rect().toRect(), self._image)

    def resizeEvent(self, event: QResizeEvent) -> None:
        image = self._image_rect()
        x, y, w, h = _BUTTON_AREA
        area = QRect(
            round(image.left() + x * image.width()),
            round(image.top() + y * image.height()),
            round(w * image.width()),
            round(h * image.height()),
        )
        radius = area.height() // 2
        for widget in (self._loading, self._start):
            widget.setGeometry(area)
        self._start.setStyleSheet(
            f"QPushButton {{ background: {_BUTTON_COLOR}; color: white; border: none;"
            f" border-radius: {radius}px; font-size: {round(area.height() * 0.42)}px; font-weight: 800; }}"
            f"QPushButton:hover {{ background: #3B2DA3; }}"
            f"QPushButton:focus {{ border: 4px solid {theme.YELLOW}; }}"
        )
        self._loading.setStyleSheet(
            f"QFrame {{ background: {_BUTTON_COLOR}; border-radius: {radius}px; }}"
            f"QLabel {{ background: transparent; color: white;"
            f" font-size: {round(area.height() * 0.3)}px; font-weight: 700; }}"
            f"QProgressBar {{ background: rgba(255,255,255,0.3); max-height: 10px; border-radius: 5px; }}"
            f"QProgressBar::chunk {{ background: {theme.YELLOW}; border-radius: 5px; }}"
        )
        super().resizeEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._ready and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.start_requested.emit()
        else:
            super().keyPressEvent(event)
