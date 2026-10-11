// Written note names, labels and staff positions (FR-10, FR-11). Port of core/notes.py.

const LETTERS = ["C", "D", "E", "F", "G", "A", "B"];
const SOLFEGE = ["Do", "Ré", "Mi", "Fa", "Sol", "La", "Si"];
const PITCH_CLASSES = [0, 2, 4, 5, 7, 9, 11];
const CHROMATIC = [
  ["Do", "C"], ["Do♯", "C♯"], ["Ré", "D"], ["Ré♯", "D♯"], ["Mi", "E"], ["Fa", "F"],
  ["Fa♯", "F♯"], ["Sol", "G"], ["Sol♯", "G♯"], ["La", "A"], ["La♯", "A♯"], ["Si", "B"],
];

// Diatonic index of E4, the bottom line of the treble staff.
const TREBLE_BOTTOM_LINE = 4 * 7 + LETTERS.indexOf("E");

/** A natural written note such as C4 (MIDI 60). */
export class Note {
  /** @param {string} letter @param {number} octave */
  constructor(letter, octave) {
    if (!LETTERS.includes(letter)) throw new RangeError(`Unknown note letter: ${letter}`);
    this.letter = letter;
    this.octave = octave;
    Object.freeze(this);
  }

  /** Parse scientific pitch notation, e.g. "C4" or "G5". */
  static parse(name) {
    const match = /^([A-Ga-g])(-?\d+)$/.exec(name ?? "");
    if (!match) throw new RangeError(`Invalid note name: ${name}`);
    return new Note(match[1].toUpperCase(), Number(match[2]));
  }

  get name() {
    return `${this.letter}${this.octave}`;
  }

  get midi() {
    return 12 * (this.octave + 1) + PITCH_CLASSES[LETTERS.indexOf(this.letter)];
  }

  get solfege() {
    return SOLFEGE[LETTERS.indexOf(this.letter)];
  }

  /** Display label with solfège and letter name, e.g. "RÉ / D". */
  get label() {
    return `${this.solfege.toUpperCase()} / ${this.letter}`;
  }

  /** Diatonic steps above the treble staff's bottom line (E4 = 0, C4 = -2). */
  get staffStep() {
    return this.octave * 7 + LETTERS.indexOf(this.letter) - TREBLE_BOTTOM_LINE;
  }
}

/** Label for any written MIDI note, e.g. "SOL / G4" or "FA♯ / F♯4". */
export function midiLabel(midi) {
  const [solfege, letter] = CHROMATIC[((midi % 12) + 12) % 12];
  return `${solfege.toUpperCase()} / ${letter}${Math.floor(midi / 12) - 1}`;
}
