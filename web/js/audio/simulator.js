// A stand-in for the microphone: synthesizes a horn-like tone at a chosen frequency, so the game
// can be tested without an instrument (open the app with ?sim). Port of SimulatedSource.

import { WINDOW_SIZE } from "./mic.js";

const AMPLITUDE = 0.2;

export class SimulatedMicrophone {
  constructor(sampleRate = 44_100) {
    this.sampleRate = sampleRate;
    this.frequencyHz = null;
    this.running = false;
    this.label = "Keyboard simulation";
    this.deviceId = "";
    this.filtered = false;
    this._phase = 0;
    this._window = new Float32Array(WINDOW_SIZE);
  }

  async start() {
    this.running = true;
  }

  stop() {
    this.running = false;
  }

  readWindow() {
    if (this.frequencyHz === null) return this._window.fill(0);
    const step = (2 * Math.PI * this.frequencyHz) / this.sampleRate;
    for (let i = 0; i < WINDOW_SIZE; i++) {
      const phase = this._phase + step * i;
      this._window[i] = (AMPLITUDE * (Math.sin(phase) + 0.5 * Math.sin(2 * phase) + 0.25 * Math.sin(3 * phase))) / 1.75;
    }
    this._phase = (this._phase + step * WINDOW_SIZE) % (2 * Math.PI);
    return this._window;
  }
}
