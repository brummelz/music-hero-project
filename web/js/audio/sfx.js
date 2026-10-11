// Sound effects with Web Audio, synthesized so no audio files are needed (FR-09).
// Port of audio/sfx.py.

export const REFERENCE_SECONDS = 1.6;
const REFERENCE_HARMONICS = [1.0, 0.7, 0.45, 0.3, 0.18, 0.1]; // Warm, horn-like timbre.
/** The child asked to hear the note, so play it audibly even if effects are turned down. */
const REFERENCE_MIN_VOLUME = 0.3;
const CHIME_NOTES_HZ = [523.25, 659.25, 783.99, 1046.5]; // Rising C major arpeggio.
const CHIME_SPACING_S = 0.07;
const CHIME_NOTE_S = 0.45;

function harmonicWave(context, amplitudes) {
  const real = new Float32Array(amplitudes.length + 1);
  const imag = Float32Array.from([0, ...amplitudes]);
  return context.createPeriodicWave(real, imag);
}

function tone(context, { frequency, start, duration, gain, wave, attack = 0.01, release = 0.25 }) {
  const oscillator = context.createOscillator();
  const envelope = context.createGain();
  if (wave) oscillator.setPeriodicWave(wave);
  oscillator.frequency.value = frequency;
  envelope.gain.setValueAtTime(0, start);
  envelope.gain.linearRampToValueAtTime(gain, start + attack);
  envelope.gain.setValueAtTime(gain, start + Math.max(attack, duration - release));
  envelope.gain.linearRampToValueAtTime(0, start + duration);
  oscillator.connect(envelope).connect(context.destination);
  oscillator.start(start);
  oscillator.stop(start + duration + 0.05);
}

/** @param {AudioContext} context */
export function playSuccess(context, volume) {
  if (!context || volume <= 0) return;
  const wave = harmonicWave(context, [1, 0, 0.3]);
  const now = context.currentTime;
  CHIME_NOTES_HZ.forEach((frequency, i) => {
    tone(context, {
      frequency, start: now + i * CHIME_SPACING_S, duration: CHIME_NOTE_S, gain: 0.12 * volume, wave,
      attack: 0.005, release: CHIME_NOTE_S - 0.01,
    });
  });
}

/** Play the target note so the child can hear it; returns its duration in seconds. */
export function playReference(context, frequencyHz, volume) {
  if (!context) return 0;
  tone(context, {
    frequency: frequencyHz, start: context.currentTime, duration: REFERENCE_SECONDS,
    gain: 0.25 * Math.max(volume, REFERENCE_MIN_VOLUME), wave: harmonicWave(context, REFERENCE_HARMONICS),
    attack: 0.08, release: 0.25,
  });
  return REFERENCE_SECONDS;
}
