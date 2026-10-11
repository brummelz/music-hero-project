// Turns raw analysis windows into a steady pitch reading for the game. Port of audio/tracker.py.

import { YinDetector, gateThreshold, rms } from "./yin.js";

/** Median over the last 5 frames: long enough to drop single-frame octave errors, short
 * enough to stay within the 100 ms latency budget (NFR-01). */
export const HISTORY_FRAMES = 5;
export const MIN_VOICED_FRAMES = 3;

/** Noise gate, then pitch detection, then a short median filter. */
export class PitchTracker {
  constructor(sampleRate, sensitivity = 0.5) {
    this._detector = new YinDetector(sampleRate);
    this._history = [];
    this.gateRms = gateThreshold(sensitivity);
    this.lastLevel = 0;
  }

  setSensitivity(sensitivity) {
    this.gateRms = gateThreshold(sensitivity);
  }

  /** Follow the input's sample rate (it differs between devices and browsers). */
  setSampleRate(sampleRate) {
    if (sampleRate !== this._detector.sampleRate) {
      this._detector = new YinDetector(sampleRate);
      this.reset();
    }
  }

  reset() {
    this._history = [];
  }

  /** Feed one window; return the steadied frequency, or null for no clear pitch. */
  update(window) {
    this.lastLevel = rms(window);
    let frequency = null;
    if (this.lastLevel >= this.gateRms) {
      const result = this._detector.detect(window);
      frequency = result ? result.frequencyHz : null;
    }
    this._history.push(frequency);
    if (this._history.length > HISTORY_FRAMES) this._history.shift();

    const voiced = this._history.filter((f) => f !== null).sort((a, b) => a - b);
    const releasing = frequency === null && this._history.at(-2) === null;
    if (voiced.length < MIN_VOICED_FRAMES || releasing) return null;
    return voiced[Math.floor((voiced.length - 1) / 2)]; // median_low, like the Python version
  }
}
