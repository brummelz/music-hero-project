// YIN fundamental-frequency detector (de Cheveigné & Kawahara, 2002). Port of audio/pitch_yin.py.

export const DEFAULT_MIN_HZ = 60;
export const DEFAULT_MAX_HZ = 1200;
export const DEFAULT_THRESHOLD = 0.15;
/** Second, looser pass for noisy rooms and breathy tones; the tracker's median filter
 * removes the occasional octave error this lets through. */
export const DEFAULT_FALLBACK_THRESHOLD = 0.4;

/** After the first dip, take the deepest point within 15% of it: in noisy rooms false dips on
 * the way down read sharp. Octave errors (a factor of 2) stay far outside this range. */
export const DIP_SEARCH_RATIO = 1.15;

// Mic sensitivity 0..1 maps to an RMS noise gate from 0.01 (-40 dBFS, loud input only) down to
// 0.0001 (-80 dBFS). The default 0.5 gates at 0.001 (-60 dBFS): low, because the detector already
// rejects unpitched room noise, and laptop and phone mics are often quiet.
const LOUDEST_GATE_RMS = 0.01;
const GATE_RANGE = 0.01;

export function rms(frame) {
  let sum = 0;
  for (let i = 0; i < frame.length; i++) sum += frame[i] * frame[i];
  return Math.sqrt(sum / frame.length);
}

/** RMS level below which input counts as silence. */
export function gateThreshold(sensitivity) {
  return LOUDEST_GATE_RMS * GATE_RANGE ** sensitivity;
}

export class YinDetector {
  constructor(sampleRate, { minHz = DEFAULT_MIN_HZ, maxHz = DEFAULT_MAX_HZ, threshold = DEFAULT_THRESHOLD,
    fallbackThreshold = DEFAULT_FALLBACK_THRESHOLD } = {}) {
    this.sampleRate = sampleRate;
    this.minHz = minHz;
    this.maxHz = maxHz;
    this.threshold = threshold;
    this.fallbackThreshold = fallbackThreshold;
  }

  /** @param {Float32Array} frame @returns {{frequencyHz: number, confidence: number} | null} */
  detect(frame) {
    const n = frame.length;
    const tauMax = Math.min(Math.floor(this.sampleRate / this.minHz), Math.floor(n / 2));
    const tauMin = Math.max(2, Math.floor(this.sampleRate / this.maxHz));
    if (tauMax <= tauMin + 1) throw new RangeError("Frame too short for the configured frequency range");

    const cmnd = cumulativeMeanNormalizedDifference(frame, tauMax);
    let tau = firstDip(cmnd, tauMin, tauMax, this.threshold);
    if (tau === null) tau = firstDip(cmnd, tauMin, tauMax, this.fallbackThreshold);
    if (tau === null) return null;
    return { frequencyHz: this.sampleRate / parabolicPeak(cmnd, tau), confidence: 1 - cmnd[tau] };
  }
}

function cumulativeMeanNormalizedDifference(frame, tauMax) {
  const n = frame.length;
  let mean = 0;
  for (let i = 0; i < n; i++) mean += frame[i];
  mean /= n;
  const x = new Float64Array(n);
  for (let i = 0; i < n; i++) x[i] = frame[i] - mean;

  const window = n - tauMax;
  const cmnd = new Float64Array(tauMax + 1);
  cmnd[0] = 1;
  let running = 0;
  for (let tau = 1; tau <= tauMax; tau++) {
    let difference = 0;
    for (let j = 0; j < window; j++) {
      const delta = x[j] - x[j + tau];
      difference += delta * delta;
    }
    running += difference;
    cmnd[tau] = running > 0 ? (difference * tau) / running : 1;
  }
  return cmnd;
}

function firstDip(cmnd, tauMin, tauMax, threshold) {
  for (let tau = tauMin; tau < tauMax; tau++) {
    if (cmnd[tau] < threshold) {
      const end = Math.min(tauMax, Math.floor(tau * DIP_SEARCH_RATIO) + 1);
      let best = tau;
      for (let t = tau + 1; t < end; t++) if (cmnd[t] < cmnd[best]) best = t;
      return best;
    }
  }
  return null;
}

function parabolicPeak(values, index) {
  if (index <= 0 || index >= values.length - 1) return index;
  const left = values[index - 1];
  const center = values[index];
  const right = values[index + 1];
  const denominator = left - 2 * center + right;
  return denominator === 0 ? index : index + (0.5 * (left - right)) / denominator;
}
