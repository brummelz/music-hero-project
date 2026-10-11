// Transposition profiles: written note to sounding frequency (FR-01, FR-19). Port of core/transpose.py.

export const A4_HZ = 440.0;
export const A4_MIDI = 69;

/** @typedef {{name: string, offsetSemitones: number}} InstrumentProfile */

/** @type {InstrumentProfile} */
export const HORN_IN_F = Object.freeze({ name: "Horn in F", offsetSemitones: -7 });

/** @type {readonly InstrumentProfile[]} */
export const PROFILES = Object.freeze([
  HORN_IN_F,
  Object.freeze({ name: "B♭ instrument", offsetSemitones: -2 }),
  Object.freeze({ name: "E♭ instrument", offsetSemitones: -9 }),
  Object.freeze({ name: "C instrument (concert pitch)", offsetSemitones: 0 }),
]);

export function profileByName(name) {
  const profile = PROFILES.find((p) => p.name === name);
  if (!profile) throw new RangeError(`Unknown instrument profile: ${name}`);
  return profile;
}

/** FR-19: f = 440 * 2^((m - 69 + offset) / 12). */
export function soundingFrequency(writtenMidi, profile) {
  return A4_HZ * 2 ** ((writtenMidi - A4_MIDI + profile.offsetSemitones) / 12);
}

/** The written MIDI note nearest to a sounding frequency, and the offset in cents. */
export function nearestWrittenNote(soundingHz, profile) {
  if (!(soundingHz > 0)) throw new RangeError("Frequency must be positive");
  const exact = A4_MIDI + 12 * Math.log2(soundingHz / A4_HZ) - profile.offsetSemitones;
  const writtenMidi = Math.round(exact);
  return { writtenMidi, cents: (exact - writtenMidi) * 100 };
}
