"""Custom-painted widgets: staff with hold ring, tuner gauge, score pill and stars."""

from __future__ import annotations

import math

from PySide6.QtCore import QElapsedTimer, QPoint, QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPolygonF,
    QTransform,
)
from PySide6.QtWidgets import QPushButton, QSizePolicy, QToolTip, QWidget

from core.notes import Note
from core.tuning import GAUGE_RANGE_CENTS, NEAR_ZONE_FACTOR, Zone, needle_position
from ui import theme

_MIDDLE_LINE_STEP = 4  # B4: stems go up below it and down from it upward.


def _pen(color: str | QColor, width: float, style: Qt.PenStyle = Qt.PenStyle.SolidLine) -> QPen:
    return QPen(QColor(color), width, style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)


class StaffWidget(QWidget):
    """Treble staff showing the written target note with a hold ring around its head (FR-10)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._note: Note | None = None
        self._caption = ""
        self._hint = ""
        self._progress = 0.0
        self._in_tune = False
        self._idle = True
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName("Staff")

    def set_note(self, note: Note) -> None:
        self._note = note
        self.setAccessibleDescription(f"Target note {note.label}, written {note.name}")
        self.update()

    def set_captions(self, caption: str, hint: str) -> None:
        self._caption, self._hint = caption, hint
        self.update()

    def set_state(self, progress: float, in_tune: bool, idle: bool) -> None:
        if (progress, in_tune, idle) != (self._progress, self._in_tune, self._idle):
            self._progress, self._in_tune, self._idle = progress, in_tune, idle
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        space = min(height / 10.5, 30.0)
        bottom_line = height / 2 + 2.25 * space
        left, right = 40.0, width - 40.0

        painter.setFont(theme.body_font(15))
        painter.setPen(QColor(theme.MUTED))
        caption_rect = QRectF(32, 12, width - 64, 24)
        painter.drawText(
            caption_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._caption
        )
        painter.drawText(
            caption_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self._hint
        )

        painter.setPen(_pen(theme.INK, 3))
        for line in range(5):
            y = bottom_line - line * space
            painter.drawLine(QPointF(left, y), QPointF(right, y))
        self._draw_clef(painter, left + 0.6 * space, bottom_line - 5.5 * space, 7.0 * space)

        if self._note is not None:
            self._draw_note(painter, width / 2, bottom_line, space)

    @staticmethod
    def _draw_clef(painter: QPainter, x: float, top: float, height: float) -> None:
        path = QPainterPath()
        path.addText(0, 0, QFont(theme.MUSIC_FAMILY, 100), theme.TREBLE_CLEF)
        bounds = path.boundingRect()
        if bounds.height() <= 0:
            return
        scale = height / bounds.height()
        transform = (
            QTransform().translate(x, top).scale(scale, scale).translate(-bounds.left(), -bounds.top())
        )
        painter.fillPath(transform.map(path), QColor(theme.INK))

    def _draw_note(self, painter: QPainter, x: float, bottom_line: float, space: float) -> None:
        assert self._note is not None
        step = self._note.staff_step
        y = bottom_line - step * space / 2

        ring_radius, ring_width = 1.45 * space, 0.36 * space
        ring = QRectF(x - ring_radius, y - ring_radius, 2 * ring_radius, 2 * ring_radius)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self._idle:
            pen = _pen(theme.BORDER, 0.22 * space, Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawEllipse(ring)
        else:
            painter.setPen(QPen(QColor(theme.TRACK), ring_width))
            painter.drawEllipse(ring)
            if self._progress > 0:
                painter.setPen(_pen(theme.RING_GREEN, ring_width))
                painter.drawArc(ring, 90 * 16, -round(self._progress * 360 * 16))

        painter.setPen(_pen(theme.INK, 3))
        ledger_steps = list(range(-2, step - 1, -2)) + list(range(10, step + 1, 2))
        for ledger in ledger_steps:
            ledger_y = bottom_line - ledger * space / 2
            painter.drawLine(QPointF(x - 1.3 * space, ledger_y), QPointF(x + 1.3 * space, ledger_y))

        color = QColor(theme.GREEN_DARK if self._in_tune else theme.INK)
        head_rx, head_ry = 0.66 * space, 0.47 * space
        painter.setPen(_pen(color, 0.14 * space))
        if step < _MIDDLE_LINE_STEP:
            stem_x = x + 0.92 * head_rx
            painter.drawLine(QPointF(stem_x, y - 0.1 * space), QPointF(stem_x, y - 3.5 * space))
        else:
            stem_x = x - 0.92 * head_rx
            painter.drawLine(QPointF(stem_x, y + 0.1 * space), QPointF(stem_x, y + 3.5 * space))

        painter.save()
        painter.translate(x, y)
        painter.rotate(-20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QPointF(0, 0), head_rx, head_ry)
        painter.restore()


class GaugeWidget(QWidget):
    """Tuner bar: red / yellow / green zones and a needle (FR-03, FR-04, FR-05)."""

    SMOOTHING = 0.35

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tolerance = 15.0
        self._target = 0.0
        self._shown = 0.0
        self._zone = Zone.IDLE
        self.setMinimumHeight(132)
        self.setAccessibleName("Tuner")

    def set_tolerance(self, tolerance_cents: float) -> None:
        self._tolerance = tolerance_cents
        self.update()

    def set_reading(self, cents: float | None, zone: Zone) -> None:
        self._zone = zone
        self._target = 0.0 if cents is None else needle_position(cents)
        self._shown += (self._target - self._shown) * self.SMOOTHING
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        idle = self._zone is Zone.IDLE
        track = QRectF(36, 16, self.width() - 72, 52)

        def x_at(cents: float) -> float:
            fraction = max(-1.0, min(1.0, cents / GAUGE_RANGE_CENTS))
            return track.left() + (fraction + 1) / 2 * track.width()

        clip = QPainterPath()
        clip.addRoundedRect(track, track.height() / 2, track.height() / 2)
        painter.save()
        painter.setClipPath(clip)
        painter.setOpacity(0.35 if idle else 1.0)
        near = self._tolerance * NEAR_ZONE_FACTOR
        for color, limit in (
            (theme.RED, GAUGE_RANGE_CENTS),
            (theme.YELLOW, near),
            (theme.GREEN, self._tolerance),
        ):
            painter.fillRect(
                QRectF(x_at(-limit), track.top(), x_at(limit) - x_at(-limit), track.height()), QColor(color)
            )
        painter.setPen(QPen(QColor("white"), 2))
        painter.drawLine(QPointF(x_at(0), track.top() + 8), QPointF(x_at(0), track.bottom() - 8))
        painter.restore()

        needle_x = track.left() + (self._shown + 1) / 2 * track.width()
        if idle:
            painter.setPen(QPen(QColor(theme.MUTED), 3, Qt.PenStyle.DashLine))
            painter.setBrush(QColor("white"))
            painter.drawRoundedRect(QRectF(needle_x - 7, track.top(), 14, track.height()), 7, 7)
        else:
            painter.setPen(QPen(QColor("white"), 3))
            painter.setBrush(QColor(theme.INK))
            painter.drawRoundedRect(QRectF(needle_x - 8, track.top() - 10, 16, track.height() + 20), 8, 8)

        self._draw_labels(painter, track, track.bottom() + 16)

    def _draw_labels(self, painter: QPainter, track: QRectF, top: float) -> None:
        zone = self._zone
        chips = (
            (
                "♭  Flat",
                {Zone.FLAT_NEAR: theme.YELLOW, Zone.FLAT_FAR: theme.RED}.get(zone),
                Qt.AlignmentFlag.AlignLeft,
            ),
            ("✓  In tune", theme.GREEN if zone is Zone.GREEN else None, Qt.AlignmentFlag.AlignHCenter),
            (
                "♯  Sharp",
                {Zone.SHARP_NEAR: theme.YELLOW, Zone.SHARP_FAR: theme.RED}.get(zone),
                Qt.AlignmentFlag.AlignRight,
            ),
        )
        font = theme.body_font(17, QFont.Weight.ExtraBold)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        for text, active_color, alignment in chips:
            chip_width = metrics.horizontalAdvance(text) + 36
            if alignment is Qt.AlignmentFlag.AlignLeft:
                left = track.left()
            elif alignment is Qt.AlignmentFlag.AlignRight:
                left = track.right() - chip_width
            else:
                left = track.center().x() - chip_width / 2
            chip = QRectF(left, top, chip_width, 36)
            if active_color:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(active_color))
                painter.drawRoundedRect(chip, 18, 18)
            painter.setPen(QColor(theme.INK if active_color else theme.MUTED))
            painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, text)


class ScorePill(QWidget):
    """Indigo pill with ``points / goal`` and one dot per point."""

    MAX_DOTS = 12
    SLOT = 24  # Each point slot, px: big enough to see a new star appear.

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._points = 0
        self._goal = 10
        self.setFixedHeight(60)

    def set_score(self, points: int, goal: int) -> None:
        self._points, self._goal = points, goal
        self.setAccessibleName(f"Score {points} of {goal}")
        self.updateGeometry()
        self.update()

    def _text(self) -> str:
        return f"{self._points} / {self._goal}"

    def sizeHint(self) -> QSize:
        text_width = QFontMetrics(theme.display_font(30)).horizontalAdvance(self._text())
        dots = self.SLOT * self._goal if self._goal <= self.MAX_DOTS else 0
        return QSize(text_width + dots + 64, 60)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.ACCENT))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        painter.setFont(theme.display_font(30))
        painter.setPen(QColor("white"))
        text_width = QFontMetrics(painter.font()).horizontalAdvance(self._text())
        painter.drawText(
            QRectF(24, 0, text_width, rect.height()), Qt.AlignmentFlag.AlignVCenter, self._text()
        )
        if self._goal > self.MAX_DOTS:
            return
        x = 24 + text_width + 14
        for i in range(self._goal):
            center = QPointF(x + i * self.SLOT + self.SLOT / 2, rect.height() / 2)
            if i < self._points:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(theme.YELLOW))
                painter.drawPolygon(star_polygon(center, self.SLOT * 0.48))
            else:
                painter.setPen(QPen(QColor(theme.ACCENT_LINE), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, 6, 6)


def star_polygon(center: QPointF, radius: float) -> QPolygonF:
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else radius * 0.48
        angle = -math.pi / 2 + i * math.pi / 5
        points.append(QPointF(center.x() + r * math.cos(angle), center.y() + r * math.sin(angle)))
    return QPolygonF(points)


class StarRow(QWidget):
    """Earned stars filled gold, missing stars dashed outline (FR-23)."""

    def __init__(self, star_size: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._earned = 0
        self._total = 3
        self._star_size = star_size
        self.setFixedSize(QSize(round(star_size * 3.3), star_size))

    def set_stars(self, earned: int, total: int = 3) -> None:
        self._earned, self._total = earned, total
        self.setAccessibleName(f"{earned} of {total} stars")
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = self._star_size
        gap = (self.width() - self._total * size) / max(1, self._total - 1)
        for i in range(self._total):
            center = QPointF(i * (size + gap) + size / 2, size / 2 + size * 0.03)
            polygon = star_polygon(center, size * 0.48)
            if i < self._earned:
                painter.setPen(_pen(theme.INK, max(1.5, size / 22)))
                painter.setBrush(QColor(theme.YELLOW))
            else:
                painter.setPen(QPen(QColor(theme.STAR_EMPTY_LINE), max(1.5, size / 22), Qt.PenStyle.DashLine))
                painter.setBrush(QColor(theme.STAR_EMPTY))
            painter.drawPolygon(polygon)


class HoldButton(QPushButton):
    """Fires only after being held down, so a child cannot open it by accident.

    A ring fills around the button while it is held; a short tap shows a hint.
    """

    held = Signal()
    HOLD_MS = 1000
    _REPAINT_MS = 16

    def __init__(self, text: str, hint: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._hint = hint
        self._clock = QElapsedTimer()
        self._repaint = QTimer(self)
        self._repaint.setInterval(self._REPAINT_MS)
        self._repaint.timeout.connect(self._on_tick)
        self.pressed.connect(self._begin)
        self.released.connect(self._end)

    def _begin(self) -> None:
        self._clock.start()
        self._repaint.start()

    def _on_tick(self) -> None:
        if self._clock.elapsed() < self.HOLD_MS:
            self.update()
            return
        self._repaint.stop()
        self._clock.invalidate()
        self.setDown(False)
        self.update()
        self.held.emit()

    def _end(self) -> None:
        if self._repaint.isActive():
            self._repaint.stop()
            QToolTip.showText(self.mapToGlobal(QPoint(0, self.height())), self._hint, self)
        self._clock.invalidate()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        if not self._clock.isValid():
            return
        fraction = min(1.0, self._clock.elapsed() / self.HOLD_MS)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(_pen(theme.ACCENT, 5))
        ring = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        painter.drawArc(ring, 90 * 16, -round(fraction * 360 * 16))
