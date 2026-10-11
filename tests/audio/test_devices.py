"""Microphone selection: unfiltered inputs first, so steady instrument notes survive."""

from audio.devices import Capture, InputDevice, automatic_candidates
from audio.sources import is_live


def device(name: str, capture: Capture, index: int = 0) -> InputDevice:
    return InputDevice(f"{capture.value}|{name}", name, index, 48_000, capture)


ARRAY_DEFAULT = "Mic array (2- Intel Smart Sound"
DEVICES = [
    device("Mic array 1 ()", Capture.PIN, 18),
    device("Mic array 2 ()", Capture.PIN, 19),
    device("Microphone (Realtek HD Audio Mic input)", Capture.PIN, 13),
    device("Mic array (2- Intel Smart Sound for digital mics)", Capture.RAW_MODE, 9),
    device("Mic array (2- Intel Smart Sound", Capture.FILTERED, 1),
]


def test_automatic_tries_every_pin_then_raw_mode() -> None:
    names = [(d.name, d.capture) for d in automatic_candidates(DEVICES, ARRAY_DEFAULT)]
    assert names == [
        ("Mic array 1 ()", Capture.PIN),
        ("Mic array 2 ()", Capture.PIN),
        ("Mic array (2- Intel Smart Sound for digital mics)", Capture.RAW_MODE),
    ]


def test_automatic_never_picks_a_filtered_input_or_other_hardware() -> None:
    chosen = automatic_candidates(DEVICES, ARRAY_DEFAULT)
    assert all(not d.filtered for d in chosen)
    assert all("Realtek" not in d.name for d in chosen)


def test_automatic_with_raw_mode_only() -> None:
    usb = [device("USB Mic (Blue Yeti)", Capture.RAW_MODE), device("USB Mic (Blue Yeti)", Capture.FILTERED)]
    assert [d.capture for d in automatic_candidates(usb, "USB Mic (Blue Yeti)")] == [Capture.RAW_MODE]


def test_automatic_without_a_default_name() -> None:
    assert automatic_candidates(DEVICES, "") == []


def test_is_live_rejects_dead_inputs() -> None:
    assert not is_live(0, 0.0)  # Nothing arrived.
    assert not is_live(20, 0.0)  # Opened, but pure digital silence.
    assert is_live(20, 0.0003)  # A quiet room is still real audio.
