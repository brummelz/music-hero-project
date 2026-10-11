"""Written note names, labels and staff positions (FR-10, FR-11)."""

from __future__ import annotations

from dataclasses import dataclass

_LETTERS = ("C", "D", "E", "F", "G", "A", "B")
_SOLFEGE = ("Do", "Ré", "Mi", "Fa", "Sol", "La", "Si")
_PITCH_CLASSES = (0, 2, 4, 5, 7, 9, 11)

_CHROMATIC = (
    ("Do", "C"),
    ("Do♯", "C♯"),
    ("Ré", "D"),
    ("Ré♯", "D♯"),
    ("Mi", "E"),
    ("Fa", "F"),
    ("Fa♯", "F♯"),
    ("Sol", "G"),
    ("Sol♯", "G♯"),
    ("La", "A"),
    ("La♯", "A♯"),
    ("Si", "B"),
)

# Diatonic index of E4, the bottom line of the treble staff.
_TREBLE_BOTTOM_LINE = 4 * 7 + _LETTERS.index("E")


@dataclass(frozen=True)
class Note:
    """A natural written note such as C4 (MIDI 60)."""

    letter: str
    octave: int

    def __post_init__(self) -> None:
        if self.letter not in _LETTERS:
            raise ValueError(f"Unknown note letter: {self.letter!r}")

    @classmethod
    def parse(cls, name: str) -> Note:
        """Parse scientific pitch notation, e.g. ``"C4"`` or ``"G5"``."""
        if len(name) < 2:
            raise ValueError(f"Invalid note name: {name!r}")
        try:
            octave = int(name[1:])
        except ValueError:
            raise ValueError(f"Invalid note name: {name!r}") from None
        return cls(name[0].upper(), octave)

    @property
    def name(self) -> str:
        return f"{self.letter}{self.octave}"

    @property
    def midi(self) -> int:
        return 12 * (self.octave + 1) + _PITCH_CLASSES[_LETTERS.index(self.letter)]

    @property
    def solfege(self) -> str:
        return _SOLFEGE[_LETTERS.index(self.letter)]

    @property
    def label(self) -> str:
        """Display label with solfège and letter name, e.g. ``"RÉ / D"``."""
        return f"{self.solfege.upper()} / {self.letter}"

    @property
    def staff_step(self) -> int:
        """Diatonic steps above the treble staff's bottom line (E4 = 0, C4 = -2)."""
        return self.octave * 7 + _LETTERS.index(self.letter) - _TREBLE_BOTTOM_LINE


def midi_label(midi: int) -> str:
    """Label for any written MIDI note, e.g. ``"SOL / G4"`` or ``"FA♯ / F♯4"``."""
    solfege, letter = _CHROMATIC[midi % 12]
    return f"{solfege.upper()} / {letter}{midi // 12 - 1}"
