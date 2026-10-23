"""Colors, fonts and the shared stylesheet (see docs/design/README.md)."""

from __future__ import annotations

from PySide6.QtGui import QFont

from core.feedback import Feedback

GROUND = "#E9F3FF"
PANEL = "#FFFFFF"
INK = "#14213D"
MUTED = "#4A5A78"
ACCENT = "#4338CA"
ACCENT_SOFT = "#EEF0FF"
ACCENT_LINE = "#A5B4FC"
BORDER = "#B8C7E0"
TRACK = "#D7E3F5"
GREEN = "#3DD68C"
GREEN_SOFT = "#BDF0D3"
GREEN_DARK = "#0E7C3A"
RING_GREEN = "#16A34A"
YELLOW = "#FFC93C"
YELLOW_SOFT = "#FFE9A8"
RED = "#FF6B6B"
RED_SOFT = "#FFC9C9"
IDLE_SOFT = "#DCE6F7"
LOCKED = "#F3F6FB"
STAR_EMPTY = "#EEF3FB"
STAR_EMPTY_LINE = "#8A9AB8"

FEEDBACK_BACKGROUND = {
    Feedback.SILENCE: IDLE_SOFT,
    Feedback.FLAT_FAR: RED_SOFT,
    Feedback.FLAT_NEAR: YELLOW_SOFT,
    Feedback.IN_TUNE: GREEN_SOFT,
    Feedback.SHARP_NEAR: YELLOW_SOFT,
    Feedback.SHARP_FAR: RED_SOFT,
    Feedback.COMPLETED: GREEN_SOFT,
    Feedback.TRY_AGAIN: IDLE_SOFT,
}

FEEDBACK_ICON = {
    Feedback.SILENCE: "♪",
    Feedback.FLAT_FAR: "↑",
    Feedback.FLAT_NEAR: "↑",
    Feedback.IN_TUNE: "✓",
    Feedback.SHARP_NEAR: "↓",
    Feedback.SHARP_FAR: "↓",
    Feedback.COMPLETED: "★",
    Feedback.TRY_AGAIN: "↺",
}

DISPLAY_FAMILIES = ["Segoe UI Variable Display", "Segoe UI"]
BODY_FAMILIES = ["Segoe UI"]
MUSIC_FAMILY = "Segoe UI Symbol"
TREBLE_CLEF = "\U0001d11e"
TEXT_STYLE = "︎"  # Variation selector: draw symbols as monochrome text, not color emoji.
GEAR = "⚙" + TEXT_STYLE
LOCK = "\U0001f512" + TEXT_STYLE
SPEAKER = "🔊" + TEXT_STYLE


def display_font(pixel_size: int, weight: QFont.Weight = QFont.Weight.Bold) -> QFont:
    font = QFont()
    font.setFamilies(DISPLAY_FAMILIES)
    font.setPixelSize(pixel_size)
    font.setWeight(weight)
    return font


def body_font(pixel_size: int, weight: QFont.Weight = QFont.Weight.Bold) -> QFont:
    font = QFont()
    font.setFamilies(BODY_FAMILIES)
    font.setPixelSize(pixel_size)
    font.setWeight(weight)
    return font


STYLESHEET = f"""
QWidget {{ color: {INK}; }}
QMainWindow, QStackedWidget, #screen {{ background: {GROUND}; }}
QFrame#card {{ background: {PANEL}; border-radius: 28px; }}
QLabel#muted {{ color: {MUTED}; font-weight: 700; }}
QLabel#caption {{ color: {MUTED}; font-weight: 800; font-size: 15px; letter-spacing: 1px; }}

QPushButton {{ font-weight: 700; }}
QPushButton#primary {{
    background: {ACCENT}; color: white; border: 3px solid {ACCENT};
    border-radius: 34px; min-height: 62px; padding: 0 36px; font-size: 26px; font-weight: 700;
}}
QPushButton#primary:hover {{ background: #3730A3; border-color: #3730A3; }}
QPushButton#primary:focus {{ border-color: {YELLOW}; }}
QPushButton#secondary {{
    background: white; color: {INK}; border: 3px solid {INK};
    border-radius: 34px; min-height: 62px; padding: 0 32px; font-size: 26px; font-weight: 700;
}}
QPushButton#secondary:hover {{ background: {ACCENT_SOFT}; }}
QPushButton#round {{
    background: white; border: 3px solid {INK}; border-radius: 30px;
    min-width: 54px; max-width: 54px; min-height: 54px; max-height: 54px; font-size: 26px;
}}
QPushButton#round:hover {{ background: {ACCENT_SOFT}; }}

QPushButton#note {{
    background: white; border: 4px solid {BORDER}; border-radius: 24px;
    min-height: 100px; font-size: 40px; font-weight: 700;
}}
QPushButton#note:hover {{ border-color: {ACCENT_LINE}; }}
QPushButton#note:checked {{ background: {ACCENT_SOFT}; border-color: {ACCENT}; }}

QFrame#difficultySwitch {{ background: white; border: 3px solid {BORDER}; border-radius: 32px; }}
QPushButton#difficulty {{
    background: transparent; color: {MUTED}; border: none; border-radius: 24px;
    min-height: 48px; min-width: 120px; padding: 0 22px;
}}
QPushButton#difficulty:checked {{ background: {ACCENT}; color: white; }}

QPushButton#level {{
    background: white; border: 3px solid {BORDER}; border-radius: 26px;
    min-height: 52px; text-align: left;
}}
QPushButton#level:hover {{ border-color: {ACCENT_LINE}; }}
QPushButton#levelCurrent {{
    background: {ACCENT_SOFT}; border: 4px solid {ACCENT}; border-radius: 30px; min-height: 58px;
}}
QPushButton#levelLocked {{
    background: {LOCKED}; border: 3px dashed {BORDER}; border-radius: 26px; min-height: 52px;
}}

QDialog {{ background: {GROUND}; }}
QComboBox, QSpinBox {{
    background: white; border: 2px solid {BORDER}; border-radius: 10px; padding: 6px 10px; min-height: 28px;
}}
QSlider::groove:horizontal {{ height: 8px; background: {TRACK}; border-radius: 4px; }}
QSlider::handle:horizontal {{
    background: {ACCENT}; width: 22px; height: 22px; margin: -8px 0; border-radius: 11px;
}}
QProgressBar {{ background: {TRACK}; border: none; border-radius: 6px; max-height: 12px; }}
QProgressBar::chunk {{ background: {GREEN}; border-radius: 6px; }}
"""
