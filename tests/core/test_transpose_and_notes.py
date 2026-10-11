import json

import pytest

from core.notes import Note
from core.transpose import HORN_IN_F, InstrumentProfile, profile_by_name, sounding_frequency
from storage.paths import resource_path


def test_tc02_written_c4_on_horn_in_f() -> None:
    assert sounding_frequency(Note.parse("C4").midi, HORN_IN_F) == pytest.approx(174.61, abs=0.01)


@pytest.mark.parametrize(("name", "hz"), [("C4", 174.61), ("D4", 196.00), ("E4", 220.00), ("C5", 349.23)])
def test_tc08_reference_table(name: str, hz: float) -> None:
    assert sounding_frequency(Note.parse(name).midi, HORN_IN_F) == pytest.approx(hz, abs=0.01)


@pytest.mark.parametrize(("offset", "hz"), [(-2, 233.08), (0, 261.63)])
def test_tc09_alternate_profiles(offset: int, hz: float) -> None:
    profile = InstrumentProfile("test", offset)
    assert sounding_frequency(Note.parse("C4").midi, profile) == pytest.approx(hz, abs=0.01)


# §4.1 sounding frequencies, copied from the spec table.
_SPEC_LEVEL_FREQUENCIES = {
    1: [174.61, 196.00, 220.00],
    2: [174.61, 196.00, 220.00, 233.08, 261.63],
    3: [174.61, 196.00, 220.00, 233.08, 261.63, 293.66, 329.63, 349.23],
    4: [349.23, 392.00, 440.00, 466.16, 523.25],
    5: [174.61, 261.63, 349.23, 440.00, 523.25],
}


def test_tc29_level_note_frequencies() -> None:
    with open(resource_path("levels.json"), encoding="utf-8") as file:
        levels = json.load(file)["levels"]
    for level in levels:
        actual = [sounding_frequency(Note.parse(n).midi, HORN_IN_F) for n in level["notes"]]
        assert actual == pytest.approx(_SPEC_LEVEL_FREQUENCIES[level["number"]], abs=0.01)


@pytest.mark.parametrize(("name", "label"), [("C4", "DO / C"), ("D4", "RÉ / D"), ("E4", "MI / E")])
def test_tc22_note_labels(name: str, label: str) -> None:
    assert Note.parse(name).label == label


def test_tc22_staff_positions() -> None:
    assert Note.parse("E4").staff_step == 0  # bottom line
    assert Note.parse("C4").staff_step == -2  # first ledger line below
    assert Note.parse("D4").staff_step == -1
    assert Note.parse("F5").staff_step == 8  # top line


def test_midi_numbers() -> None:
    assert Note.parse("C4").midi == 60
    assert Note.parse("G5").midi == 79


def test_invalid_names_rejected() -> None:
    for bad in ("", "H4", "C", "Cx"):
        with pytest.raises(ValueError):
            Note.parse(bad)


def test_unknown_profile_rejected() -> None:
    with pytest.raises(ValueError):
        profile_by_name("Kazoo")


def test_midi_label_includes_sharps_and_octave() -> None:
    from core.notes import midi_label

    assert midi_label(60) == "DO / C4"
    assert midi_label(66) == "FA♯ / F♯4"
    assert midi_label(79) == "SOL / G5"


def test_nearest_written_note_on_horn_in_f() -> None:
    from core.transpose import nearest_written_note

    midi, cents = nearest_written_note(174.61, HORN_IN_F)
    assert midi == 60
    assert cents == pytest.approx(0, abs=0.5)
    midi, cents = nearest_written_note(174.61 * 2 ** (30 / 1200), HORN_IN_F)
    assert (midi, round(cents)) == (60, 30)
    with pytest.raises(ValueError):
        nearest_written_note(0, HORN_IN_F)
