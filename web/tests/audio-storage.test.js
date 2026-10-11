// Pitch detection on synthetic horn-like tones (NFR-02) and profile storage (FR-20, FR-25).

import assert from "node:assert/strict";
import { describe, test } from "node:test";

import { WINDOW_SIZE } from "../js/audio/mic.js";
import { SimulatedMicrophone } from "../js/audio/simulator.js";
import { PitchTracker } from "../js/audio/tracker.js";
import { YinDetector, gateThreshold } from "../js/audio/yin.js";
import { HoldMode } from "../js/core/holdTimer.js";
import { seededRandom } from "../js/core/levels.js";
import { Note } from "../js/core/notes.js";
import { makeProfile, makeProgress, makeSettings, withProgressReset } from "../js/core/profile.js";
import { PracticeSession } from "../js/core/session.js";
import { HORN_IN_F } from "../js/core/transpose.js";
import { centsOffset } from "../js/core/tuning.js";
import { ProfileStore, STORAGE_KEY } from "../js/storage/store.js";
import { approx } from "./helpers.js";

const SR = 44_100;
const HOP = 512;
const HORN_HARMONICS = [0.6, 1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.1]; // 2nd harmonic stronger than the fundamental

function gaussian(random) {
  return Math.sqrt(-2 * Math.log(random() || 1e-12)) * Math.cos(2 * Math.PI * random());
}

function hornTone(f0, seconds, { noiseDb = -40, vibratoCents = 0, level = 0.02, sampleRate = SR } = {}) {
  const random = seededRandom(7);
  const n = Math.floor(sampleRate * seconds);
  const out = new Float32Array(n);
  const phases = HORN_HARMONICS.map(() => random() * 6);
  let phase = 0;
  let peak = 0;
  const tone = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / sampleRate;
    phase += (2 * Math.PI * f0 * 2 ** ((vibratoCents * Math.sin(2 * Math.PI * 5 * t)) / 1200)) / sampleRate;
    tone[i] = HORN_HARMONICS.reduce((sum, a, k) => sum + a * Math.sin((k + 1) * phase + phases[k]), 0);
    peak = Math.max(peak, Math.abs(tone[i]));
  }
  const noise = 10 ** (noiseDb / 20);
  for (let i = 0; i < n; i++) out[i] = level * (tone[i] / peak + noise * gaussian(random));
  return out;
}

function readings(tracker, signal) {
  const values = [];
  for (let s = 0; s + WINDOW_SIZE <= signal.length; s += HOP) values.push(tracker.update(signal.subarray(s, s + WINDOW_SIZE)));
  return values;
}

describe("pitch detection", () => {
  test("TC-01 and NFR-02: horn-range tones within 5 cents", () => {
    const detector = new YinDetector(SR);
    for (const hz of [174.61, 220.0, 349.23, 523.25]) {
      const result = detector.detect(hornTone(hz, 0.1).subarray(0, WINDOW_SIZE));
      approx(centsOffset(result.frequencyHz, hz), 0, 5, `${hz} Hz`);
    }
  });

  test("TC-16 an octave below is detected as such", () => {
    const result = new YinDetector(SR).detect(hornTone(87.31, 0.1).subarray(0, WINDOW_SIZE));
    approx(centsOffset(result.frequencyHz, 174.61), -1200, 10);
  });

  test("TC-10 noise is not pitched", () => {
    const random = seededRandom(1);
    const noise = Float32Array.from({ length: WINDOW_SIZE }, () => 0.2 * gaussian(random));
    assert.equal(new YinDetector(SR).detect(noise), null);
  });

  test("noisy room: tracker stays voiced without octave errors", () => {
    for (const f0 of [174.61, 349.23]) {
      const values = readings(new PitchTracker(SR), hornTone(f0, 1.5, { noiseDb: -12 })).slice(5);
      assert.ok(values.every((v) => v !== null && Math.abs(centsOffset(v, f0)) < 50), `${f0} Hz`);
    }
  });

  test("48 kHz input (typical in browsers) and a quiet microphone", () => {
    const values = readings(new PitchTracker(48_000), hornTone(220, 1, { level: 0.006, sampleRate: 48_000 })).slice(5);
    assert.ok(values.every((v) => v !== null && Math.abs(centsOffset(v, 220)) < 5));
  });

  test("wobbly noisy horn still completes holds", () => {
    const session = new PracticeSession(Note.parse("C4"), HORN_IN_F, 15);
    const tracker = new PitchTracker(SR);
    readings(tracker, hornTone(session.targetFrequency, 6.5, { noiseDb: -12, vibratoCents: 8 }))
      .forEach((hz, i) => session.process((i * HOP) / SR, hz));
    assert.equal(session.points, 2);
  });

  test("simulator round trip and gate ordering", () => {
    const mic = new SimulatedMicrophone();
    mic.frequencyHz = 196;
    approx(centsOffset(new YinDetector(SR).detect(mic.readWindow()).frequencyHz, 196), 0, 5);
    assert.ok(gateThreshold(0) > gateThreshold(0.5) && gateThreshold(0.5) > gateThreshold(1));
  });
});

class MemoryStorage {
  constructor() { this.items = new Map(); }
  getItem(key) { return this.items.has(key) ? this.items.get(key) : null; }
  setItem(key, value) { this.items.set(key, String(value)); }
}

describe("profile storage", () => {
  test("TC-37 fresh install gives the default profile", () => {
    assert.deepEqual(new ProfileStore(new MemoryStorage()).load(), makeProfile());
  });

  test("TC-21 and TC-28 round trip after restart", () => {
    const storage = new MemoryStorage();
    const profile = makeProfile(
      makeSettings({ toleranceCents: 10, volume: 0.3, micSensitivity: 0.9, holdMode: HoldMode.PAUSE, inputDevice: "abc" }),
      makeProgress({ 1: 3, 2: 1 }, 3),
    );
    new ProfileStore(storage).save(profile);
    assert.deepEqual(new ProfileStore(storage).load(), profile);
    assert.equal(JSON.parse(storage.getItem(STORAGE_KEY)).settings.tolerance_cents, 10); // desktop JSON shape
  });

  test("TC-38 reset persists; corrupt data falls back to defaults", () => {
    const storage = new MemoryStorage();
    const store = new ProfileStore(storage);
    store.save(makeProfile(makeSettings(), makeProgress({ 1: 3 }, 2)));
    store.save(withProgressReset(store.load()));
    assert.equal(store.load().progress.unlockedLevel, 1);
    storage.setItem(STORAGE_KEY, "{not json");
    assert.deepEqual(store.load(), makeProfile());
  });
});
