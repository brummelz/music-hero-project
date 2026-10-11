"""Microphone discovery, including capture that bypasses Windows voice processing.

Most laptop microphone arrays run noise suppression and echo cancellation on the normal
Windows path. Those filters treat a sustained instrument tone as noise and remove it within
a fraction of a second, while speech still gets through. Two ways around them:

- WDM-KS pins: the driver's unprocessed signal. Proven to keep steady tones, but exclusive
  (one user at a time) and only exposed by some drivers.
- WASAPI raw mode: Microsoft's official request to switch processing off. Works on any
  Windows 10/11 machine whose driver supports it.

Automatic tries the pins, then raw mode, then the filtered default as a last resort.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)

AUTOMATIC = ""
"""Setting value: try the unfiltered inputs of the default microphone, then the default."""
SYSTEM_DEFAULT = "system"
"""Setting value: the Windows default input, with its voice processing."""

_PIN_API = "Windows WDM-KS"
_RAW_MODE_API = "Windows WASAPI"
_FILTERED_API = "MME"
_MIN_PIN_SAMPLE_RATE = 44_100  # Low-rate pins (e.g. 16 kHz keyword spotting) are a poor fit.


class Capture(Enum):
    PIN = "pin"
    """Unprocessed WDM-KS pin."""
    RAW_MODE = "raw_mode"
    """WASAPI shared stream with the raw option (processing off where the driver allows)."""
    FILTERED = "filtered"
    """Normal Windows path with voice processing."""


_API_CAPTURE = {_PIN_API: Capture.PIN, _RAW_MODE_API: Capture.RAW_MODE, _FILTERED_API: Capture.FILTERED}
_LABELS = {
    Capture.PIN: "instrument mode, unfiltered",
    Capture.RAW_MODE: "instrument mode, Windows raw",
    Capture.FILTERED: "voice mode, Windows filters",
}


@dataclass(frozen=True)
class InputDevice:
    key: str
    """Stable identifier stored in settings: ``"<host API>|<device name>"``."""
    name: str
    index: int
    sample_rate: int
    capture: Capture

    @property
    def filtered(self) -> bool:
        return self.capture is Capture.FILTERED

    @property
    def label(self) -> str:
        return f"{self.name} ({_LABELS[self.capture]})"


def _sd() -> Any:
    import sounddevice as sd  # Imported lazily so tests never need PortAudio.

    return sd


def list_input_devices() -> list[InputDevice]:
    """Unfiltered (instrument) inputs first, then the normal Windows (voice) inputs."""
    sd = _sd()
    api_names = [api["name"] for api in sd.query_hostapis()]
    devices = list(sd.query_devices())
    output_names = {d["name"] for d in devices if d["max_output_channels"] > 0}
    found: list[InputDevice] = []
    for index, device in enumerate(devices):
        capture = _API_CAPTURE.get(api_names[device["hostapi"]])
        name = device["name"]
        if capture is None or device["max_input_channels"] <= 0 or "Sound Mapper" in name:
            continue  # The Sound Mapper is Windows' pseudo-device; "System default" covers it.
        too_slow = device["default_samplerate"] < _MIN_PIN_SAMPLE_RATE
        if capture is Capture.PIN and (_is_loopback(name, output_names) or too_slow):
            continue
        api = api_names[device["hostapi"]]
        found.append(InputDevice(f"{api}|{name}", name, index, int(device["default_samplerate"]), capture))
    order = list(Capture)
    return sorted(found, key=lambda d: order.index(d.capture))


def _suffix(name: str) -> str:
    """The bracketed hardware part of a device name, e.g. "(Realtek HD Audio output)"."""
    start = name.find(" (")
    return name[start + 1 :] if start >= 0 else ""


def _is_loopback(name: str, output_names: set[str]) -> bool:
    """WDM-KS also lists speaker-loopback and stereo-mix capture pins; hide them.

    A loopback pin carries the same hardware suffix as an output. Empty suffixes such as
    "()" are shared by unrelated devices (e.g. a mic array and headphones) and don't count.
    """
    suffix = _suffix(name)
    if "Stereo" in suffix:
        return True
    if len(suffix) <= len("()"):
        return False
    return any(_suffix(output) == suffix for output in output_names)


def automatic_candidates(devices: list[InputDevice], default_name: str) -> list[InputDevice]:
    """Unfiltered inputs of the default microphone: every pin (they are exclusive, so the
    first may be busy), then raw mode. Matched by the name before the bracket, e.g. the
    default "Mic array (Intel…)" matches the pins "Mic array 1 ()" and "Mic array 2 ()"."""
    prefix = default_name.split(" (")[0].strip()
    if not prefix:
        return []
    matching = [d for d in devices if not d.filtered and d.name.startswith(prefix)]
    order = list(Capture)
    return sorted(matching, key=lambda d: order.index(d.capture))


def candidates(key: str) -> list[InputDevice | None]:
    """Inputs to try in order for a setting value; ``None`` is the Windows default input."""
    if key == SYSTEM_DEFAULT:
        return [None]
    devices = list_input_devices()
    try:
        default_name: str = _sd().query_devices(kind="input")["name"]
    except Exception:
        default_name = ""
    automatic: list[InputDevice | None] = list(automatic_candidates(devices, default_name))
    if key != AUTOMATIC:
        chosen = [d for d in devices if d.key == key]
        if not chosen:
            log.warning("Microphone %r not found; choosing automatically", key)
        automatic = [*chosen, *(d for d in automatic if d not in chosen)]
    return [*automatic, None]
