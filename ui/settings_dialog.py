"""Settings for a grown-up: playing, microphone (with a live test), sound, progress (FR-21, FR-25)."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from audio.devices import AUTOMATIC, SYSTEM_DEFAULT, InputDevice
from audio.sources import AudioSource
from audio.tracker import PitchTracker
from core.hold_timer import HoldMode
from core.notes import midi_label
from core.profile import Settings
from core.transpose import PROFILES, nearest_written_note, profile_by_name
from core.tuning import MAX_TOLERANCE_CENTS, MIN_TOLERANCE_CENTS, TOLERANCE_PRESETS
from ui import theme

_CUSTOM = "Custom"
_TEST_INTERVAL_MS = 30
_METER_FLOOR_DB = -70.0


def _level_to_meter(level: float) -> int:
    """Map RMS to 0..100 on a dB scale so quiet sounds still move the bar."""
    if level <= 0:
        return 0
    decibels = 20 * math.log10(level)
    return round(max(0.0, min(1.0, (decibels - _METER_FLOOR_DB) / -_METER_FLOOR_DB)) * 100)


def _section(title: str) -> QLabel:
    label = QLabel(title)
    label.setFont(theme.display_font(20))
    label.setContentsMargins(0, 8, 0, 0)
    return label


class SettingsDialog(QDialog):
    settings_changed = Signal(object)  # Settings
    reset_requested = Signal()

    def __init__(
        self,
        settings: Settings,
        source: AudioSource,
        devices: list[InputDevice] | None,
        audio_error: Callable[[], str | None],
        parent: QWidget | None = None,
    ) -> None:
        """``devices`` is ``None`` when no real microphone is used (simulation)."""
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(640)
        self._settings = settings
        self._source = source
        self._audio_error = audio_error
        self._tracker = PitchTracker(source.sample_rate, settings.mic_sensitivity)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(10)
        title = QLabel("Settings")
        title.setFont(theme.display_font(32))
        root.addWidget(title)
        note = QLabel("For grown-ups. Changes are saved straight away.")
        note.setObjectName("muted")
        root.addWidget(note)

        root.addWidget(_section("Playing"))
        playing = self._form(root)
        self._preset = QComboBox()
        for name, cents in TOLERANCE_PRESETS.items():
            self._preset.addItem(f"{name} (±{cents:g} cents)", name)
        self._preset.addItem(_CUSTOM, _CUSTOM)
        self._custom = QSpinBox()
        self._custom.setRange(int(MIN_TOLERANCE_CENTS), int(MAX_TOLERANCE_CENTS))
        self._custom.setSuffix(" cents")
        self._custom.setPrefix("±")
        tolerance_row = QHBoxLayout()
        tolerance_row.addWidget(self._preset, 1)
        tolerance_row.addWidget(self._custom)
        playing.addRow("How exact the note must be", tolerance_row)
        self._instrument = QComboBox()
        for profile in PROFILES:
            self._instrument.addItem(profile.name)
        playing.addRow("Instrument", self._instrument)
        self._pause = QCheckBox("Keep progress when the note slips (pause, don't restart)")
        playing.addRow("Hold timer", self._pause)

        root.addWidget(_section("Microphone"))
        microphone = self._form(root)
        self._device = QComboBox()
        self._device.addItem("Automatic (best for instruments)", AUTOMATIC)
        for device in devices or []:
            self._device.addItem(device.label, device.key)
        self._device.addItem("Windows default input (voice mode, Windows filters)", SYSTEM_DEFAULT)
        if devices is None:
            self._device.clear()
            self._device.addItem("Keyboard simulation (no microphone)", AUTOMATIC)
            self._device.setEnabled(False)
        microphone.addRow("Microphone", self._device)
        self._in_use = QLabel()
        self._in_use.setObjectName("muted")
        self._in_use.setWordWrap(True)
        microphone.addRow("In use", self._in_use)
        self._filter_warning = QLabel(
            "⚠ Windows filters are on: steady notes may fade to Quiet. Close other apps that use "
            "the microphone, or choose an instrument-mode entry."
        )
        self._filter_warning.setWordWrap(True)
        self._filter_warning.setStyleSheet(
            f"background: {theme.YELLOW_SOFT}; border-radius: 10px; padding: 8px 12px; font-weight: 700;"
        )
        self._filter_warning.hide()
        microphone.addRow("", self._filter_warning)
        self._sensitivity = QSlider(Qt.Orientation.Horizontal)
        self._sensitivity.setRange(0, 100)
        microphone.addRow("Sensitivity", self._sensitivity)
        self._meter = QProgressBar()
        self._meter.setRange(0, 100)
        self._meter.setTextVisible(False)
        self._gate_status = QLabel()
        meter_row = QHBoxLayout()
        meter_row.addWidget(self._meter, 1)
        meter_row.addWidget(self._gate_status)
        microphone.addRow("Live test", meter_row)
        self._heard = QLabel()
        self._heard.setFont(theme.display_font(22))
        self._heard.setWordWrap(True)
        microphone.addRow("Hearing", self._heard)
        hint = QLabel(
            "Play a long note. The bar should move and the note should show here.\n"
            "Voice mode removes steady notes on many laptops; use instrument mode.\n"
            "If it says Quiet while playing, raise Sensitivity or pick another microphone."
        )
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        microphone.addRow("", hint)

        root.addWidget(_section("Sound"))
        sound = self._form(root)
        self._volume = QSlider(Qt.Orientation.Horizontal)
        self._volume.setRange(0, 100)
        sound.addRow("Volume", self._volume)

        buttons = QHBoxLayout()
        reset = QPushButton("Reset progress…")
        reset.setStyleSheet(f"color: {theme.MUTED}; padding: 8px 14px;")
        reset.clicked.connect(self._confirm_reset)
        buttons.addWidget(reset)
        buttons.addStretch(1)
        close = QPushButton("Done")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addSpacing(10)
        root.addLayout(buttons)

        self._load(settings)
        for signal in (
            self._preset.currentIndexChanged,
            self._custom.valueChanged,
            self._instrument.currentIndexChanged,
            self._device.currentIndexChanged,
            self._volume.valueChanged,
            self._sensitivity.valueChanged,
            self._pause.toggled,
        ):
            signal.connect(self._on_changed)

        self._test_timer = QTimer(self)
        self._test_timer.setInterval(_TEST_INTERVAL_MS)
        self._test_timer.timeout.connect(self._update_test)
        self._test_timer.start()

    @staticmethod
    def _form(root: QVBoxLayout) -> QFormLayout:
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(form)
        return form

    def _load(self, settings: Settings) -> None:
        preset = next((n for n, c in TOLERANCE_PRESETS.items() if c == settings.tolerance_cents), _CUSTOM)
        self._preset.setCurrentIndex(self._preset.findData(preset))
        self._custom.setValue(round(settings.tolerance_cents))
        self._custom.setEnabled(preset == _CUSTOM)
        self._instrument.setCurrentText(settings.instrument)
        device_index = self._device.findData(settings.input_device)
        if device_index < 0:  # The saved microphone is unplugged: show it so the choice is not lost.
            self._device.addItem(f"{settings.input_device} (not found)", settings.input_device)
            device_index = self._device.count() - 1
        self._device.setCurrentIndex(device_index)
        self._volume.setValue(round(settings.volume * 100))
        self._sensitivity.setValue(round(settings.mic_sensitivity * 100))
        self._pause.setChecked(settings.hold_mode is HoldMode.PAUSE)

    def _on_changed(self) -> None:
        preset = self._preset.currentData()
        custom = preset == _CUSTOM
        self._custom.setEnabled(custom)
        tolerance = float(self._custom.value()) if custom else TOLERANCE_PRESETS[preset]
        if not custom:
            self._custom.blockSignals(True)
            self._custom.setValue(round(tolerance))
            self._custom.blockSignals(False)
        self._settings = replace(
            self._settings,
            tolerance_cents=tolerance,
            instrument=self._instrument.currentText(),
            input_device=str(self._device.currentData() or ""),
            volume=self._volume.value() / 100,
            mic_sensitivity=self._sensitivity.value() / 100,
            hold_mode=HoldMode.PAUSE if self._pause.isChecked() else HoldMode.RESET,
        )
        self._tracker.set_sensitivity(self._settings.mic_sensitivity)
        self._tracker.reset()
        self.settings_changed.emit(self._settings)

    def _update_test(self) -> None:
        error = self._audio_error()
        if error:
            self._meter.setValue(0)
            self._gate_status.setText("")
            self._heard.setText(error)
            return
        self._in_use.setText(self._source.active_device)
        self._filter_warning.setVisible(self._source.active_is_filtered)
        window = self._source.read_window()
        if window is None:
            return
        self._tracker.set_sample_rate(self._source.sample_rate)
        frequency = self._tracker.update(window)
        self._meter.setValue(_level_to_meter(self._tracker.last_level))
        loud_enough = self._tracker.last_level >= self._tracker.gate_rms
        self._gate_status.setText("Sound ✓" if loud_enough else "Quiet")
        if frequency is None:
            self._heard.setText("—")
            return
        profile = profile_by_name(self._settings.instrument)
        written_midi, cents = nearest_written_note(frequency, profile)
        self._heard.setText(f"{midi_label(written_midi)}   {frequency:.1f} Hz   {cents:+.0f} cents")

    def _confirm_reset(self) -> None:
        answer = QMessageBox.question(
            self,
            "Reset progress?",
            "This clears all stars and locks levels 2 to 5 again.\nSettings are kept.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Reset,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Reset:
            self.reset_requested.emit()
