// Core rules, ported from tests/core (same TC IDs as docs/TEST_CASES.md).

import assert from "node:assert/strict";
import { describe, test } from "node:test";

import { Feedback, message } from "../js/core/feedback.js";
import { HoldEvent, HoldMode, HoldTimer, holdConfig } from "../js/core/holdTimer.js";
import { generatePrompts, parseLevels, seededRandom, starsForMisses } from "../js/core/levels.js";
import { Note, midiLabel } from "../js/core/notes.js";
import {
  isUnlocked, makeProfile, makeProgress, makeSettings, starsFor, totalStars, withLevelResult,
  withProgressReset,
} from "../js/core/profile.js";
import { LevelSession, PRACTICE_NOTES, PracticeSession } from "../js/core/session.js";
import { HORN_IN_F, nearestWrittenNote, profileByName, soundingFrequency } from "../js/core/transpose.js";
import {
  TOLERANCE_PRESETS, Zone, centsOffset, classify, needlePosition, validateTolerance,
} from "../js/core/tuning.js";
import { approx, loadLevels, readJson } from "./helpers.js";

const FRAME = 0.02;

describe("tuning", () => {
  test("TC-05 cents conversion", () => {
    for (const k of [-50, -15, 0, 15, 50]) approx(centsOffset(174.61 * 2 ** (k / 1200), 174.61), k, 0.01);
  });

  test("TC-06 zone boundaries", () => {
    assert.deepEqual([-16, -15, 0, 15, 16].map((c) => classify(c, 15)), [
      Zone.FLAT_NEAR, Zone.GREEN, Zone.GREEN, Zone.GREEN, Zone.SHARP_NEAR,
    ]);
  });

  test("TC-07 flat and sharp sides, far zones", () => {
    assert.equal(classify(-30, 15), Zone.FLAT_NEAR);
    assert.equal(classify(31, 15), Zone.SHARP_FAR);
    assert.ok(needlePosition(-30) < 0 && needlePosition(30) > 0);
  });

  test("TC-16 octave errors are not green; FR-05 silence is idle", () => {
    assert.equal(classify(1200, 15), Zone.SHARP_FAR);
    assert.equal(classify(-1200, 15), Zone.FLAT_FAR);
    assert.equal(classify(null, 15), Zone.IDLE);
  });

  test("FR-04 needle clamped", () => {
    assert.equal(needlePosition(500), 1);
    assert.equal(needlePosition(-500), -1);
  });

  test("TC-26 presets and TC-27 custom range", () => {
    assert.equal(classify(20, TOLERANCE_PRESETS.Easy), Zone.GREEN);
    assert.ok([Zone.SHARP_NEAR, Zone.SHARP_FAR].includes(classify(20, TOLERANCE_PRESETS.Normal)));
    assert.ok([Zone.SHARP_NEAR, Zone.SHARP_FAR].includes(classify(20, TOLERANCE_PRESETS.Strict)));
    assert.equal(validateTolerance(5), 5);
    assert.equal(validateTolerance(50), 50);
    assert.throws(() => validateTolerance(4));
    assert.throws(() => validateTolerance(51));
    assert.throws(() => centsOffset(0, 440));
  });
});

describe("notes and transposition", () => {
  test("TC-02 and TC-08 reference table", () => {
    const expected = { C4: 174.61, D4: 196.0, E4: 220.0, C5: 349.23 };
    for (const [name, hz] of Object.entries(expected)) approx(soundingFrequency(Note.parse(name).midi, HORN_IN_F), hz, 0.01);
  });

  test("TC-09 alternate profiles", () => {
    approx(soundingFrequency(60, { name: "Bb", offsetSemitones: -2 }), 233.08, 0.01);
    approx(soundingFrequency(60, { name: "C", offsetSemitones: 0 }), 261.63, 0.01);
    assert.throws(() => profileByName("Kazoo"));
  });

  test("TC-29 level note frequencies match the §4.1 table", () => {
    const table = {
      1: [174.61, 196.0, 220.0],
      2: [174.61, 196.0, 220.0, 233.08, 261.63],
      3: [174.61, 196.0, 220.0, 233.08, 261.63, 293.66, 329.63, 349.23],
      4: [349.23, 392.0, 440.0, 466.16, 523.25],
      5: [174.61, 261.63, 349.23, 440.0, 523.25],
    };
    for (const level of loadLevels()) {
      level.notes.forEach((note, i) => approx(soundingFrequency(note.midi, HORN_IN_F), table[level.number][i], 0.01));
    }
  });

  test("web level data matches the desktop level data", () => {
    assert.deepEqual(readJson("../data/levels.json"), readJson("../../resources/levels.json"));
  });

  test("TC-41 practice notes are natural C4 to B4", () => {
    assert.deepEqual(PRACTICE_NOTES.map((n) => `${n.letter}${n.octave}`), ["C4", "D4", "E4", "F4", "G4", "A4", "B4"]);
  });

  test("TC-22 labels and staff positions", () => {
    assert.deepEqual(
      ["C4", "D4", "E4", "F4", "G4", "A4", "B4"].map((n) => Note.parse(n).label),
      ["DO / C", "RÉ / D", "MI / E", "FA / F", "SOL / G", "LA / A", "SI / B"],
    );
    assert.equal(Note.parse("E4").staffStep, 0);
    assert.equal(Note.parse("C4").staffStep, -2);
    assert.equal(Note.parse("F5").staffStep, 8);
    assert.equal(Note.parse("G5").midi, 79);
    for (const bad of ["", "H4", "C", "Cx"]) assert.throws(() => Note.parse(bad));
  });

  test("midi labels and nearest written note", () => {
    assert.equal(midiLabel(66), "FA♯ / F♯4");
    const { writtenMidi, cents } = nearestWrittenNote(174.61 * 2 ** (30 / 1200), HORN_IN_F);
    assert.equal(writtenMidi, 60);
    approx(cents, 30, 0.5);
  });
});

function runTimer(timer, start, end, inZone) {
  const events = [];
  const steps = Math.round((end - start) / FRAME);
  for (let i = 0; i < steps; i++) {
    const event = timer.update(start + i * FRAME, inZone);
    if (event !== HoldEvent.NONE) events.push(event);
  }
  return events;
}

describe("hold timer", () => {
  test("TC-03 full hold completes and resets", () => {
    const timer = new HoldTimer();
    assert.deepEqual(runTimer(timer, 0, 3 + FRAME, true), [HoldEvent.COMPLETED]);
    approx(timer.elapsed, 0, 1e-9);
  });

  test("TC-04 and TC-11 leaving resets without a point", () => {
    const timer = new HoldTimer();
    assert.deepEqual(runTimer(timer, 0, 2.9, true), []);
    assert.deepEqual(runTimer(timer, 2.9, 3.5, false), [HoldEvent.MISSED]);
    assert.equal(timer.elapsed, 0);
  });

  test("TC-10 silence never starts", () => {
    const timer = new HoldTimer();
    assert.deepEqual(runTimer(timer, 0, 5, false), []);
  });

  test("TC-12 dropout within grace continues; TC-13 beyond grace resets", () => {
    const timer = new HoldTimer();
    runTimer(timer, 0, 1.5, true);
    assert.deepEqual(runTimer(timer, 1.5, 1.6, false), []);
    runTimer(timer, 1.6, 2.0, true);
    approx(timer.elapsed, 2.0 - FRAME, 1e-6);
    const other = new HoldTimer();
    runTimer(other, 0, 1.5, true);
    assert.deepEqual(runTimer(other, 1.5, 1.8, false), [HoldEvent.MISSED]);
  });

  test("TC-14 pause mode resumes", () => {
    const timer = new HoldTimer(holdConfig({ mode: HoldMode.PAUSE }));
    runTimer(timer, 0, 1.8 + FRAME, true);
    assert.deepEqual(runTimer(timer, 1.8 + FRAME, 2.8, false), [HoldEvent.MISSED]);
    approx(timer.elapsed, 1.8, 1e-6);
    runTimer(timer, 2.8, 4.0, true);
    assert.equal(timer.update(4.0, true), HoldEvent.COMPLETED);
  });

  test("TC-15 six seconds gives two points", () => {
    assert.deepEqual(runTimer(new HoldTimer(), 0, 6 + FRAME, true), [HoldEvent.COMPLETED, HoldEvent.COMPLETED]);
  });

  test("TC-39 counter starts on entering range", () => {
    const timer = new HoldTimer();
    runTimer(timer, 0, 2, false);
    const completions = [];
    for (let t = 2; t < 5.5; t += FRAME) if (timer.update(t, true) === HoldEvent.COMPLETED) completions.push(t);
    assert.equal(completions.length, 1);
    approx(completions[0], 5, FRAME);
  });
});

describe("levels and stars", () => {
  test("TC-30 prompt generation over many seeds", () => {
    for (const level of loadLevels()) {
      for (let seed = 0; seed < 300; seed++) {
        const prompts = generatePrompts(level, seededRandom(seed));
        assert.equal(prompts.length, level.promptCount);
        assert.deepEqual(new Set(prompts.map((n) => n.name)), new Set(level.notes.map((n) => n.name)));
        prompts.forEach((note, i) => i > 0 && assert.notEqual(note.name, prompts[i - 1].name));
      }
    }
  });

  test("Level 3 extends prompts to cover all 8 notes (FR-16 conflict)", () => {
    assert.equal(loadLevels()[2].promptCount, 8);
  });

  test("TC-31..33 stars", () => {
    assert.deepEqual([0, 2, 3, 6, 7, 20].map(starsForMisses), [3, 3, 2, 2, 1, 1]);
  });

  test("bad level data is rejected", () => {
    assert.throws(() => parseLevels([{ number: 2, theme: "x", notes: ["C4", "D4"] }]));
    assert.throws(() => parseLevels([{ number: 1, theme: "x", notes: ["C4"] }]));
  });
});

function play(session, start, seconds, cents) {
  const states = [];
  for (let i = 0; i < Math.round(seconds / FRAME); i++) {
    const hz = cents === null ? null : session.targetFrequency * 2 ** (cents / 1200);
    states.push(session.process(start + i * FRAME, hz));
  }
  return states;
}

function holdOnce(session, start) {
  const points = session.points;
  let t = start;
  while (session.points === points) {
    session.process(t, session.targetFrequency);
    t += FRAME;
  }
  return t;
}

describe("sessions", () => {
  const practice = (name = "C4") => new PracticeSession(Note.parse(name), HORN_IN_F, 15);

  test("TC-17 practice ends at ten points; TC-18 target fixed", () => {
    const session = practice("D4");
    let t = 0;
    for (let i = 0; i < 10; i++) {
      t = holdOnce(session, t);
      approx(session.targetFrequency, 196.0, 0.01);
    }
    assert.ok(session.finished);
    play(session, t, 5, 0);
    assert.equal(session.points, 10);
  });

  test("TC-40 wrong notes never start the counter", () => {
    const session = practice();
    for (const cents of [200, 1200, -1200]) assert.ok(play(session, 0, 5, cents).every((s) => s.holdFraction === 0));
  });

  test("TC-28 tolerance change applies immediately", () => {
    const session = practice();
    assert.equal(play(session, 0, 0.1, 20).at(-1).zone, Zone.SHARP_NEAR);
    session.toleranceCents = 25;
    assert.equal(play(session, 0.1, 0.1, 20).at(-1).zone, Zone.GREEN);
    assert.throws(() => { session.toleranceCents = 60; });
  });

  test("TC-19 level completes after all prompts; TC-34 silence is not a miss", () => {
    const session = new LevelSession(loadLevels()[0], HORN_IN_F, 15, undefined, seededRandom(3));
    play(session, 0, 10, null);
    let t = 10;
    const seen = [];
    while (!session.finished) {
      seen.push(session.targetNote);
      t = holdOnce(session, t);
    }
    assert.deepEqual(seen, session.prompts);
    assert.equal(session.misses, 0);
    assert.equal(session.stars, 3);
  });

  test("FR-22 misses counted per reset; pause mode counts once per prompt", () => {
    const session = new LevelSession(loadLevels()[0], HORN_IN_F, 15, undefined, seededRandom(0));
    let t = 0;
    for (let i = 0; i < 3; i++, t += 1.5) {
      play(session, t, 1.0, 0);
      play(session, t + 1.0, 0.5, 40);
    }
    assert.equal(session.misses, 3);

    const paused = new LevelSession(loadLevels()[0], HORN_IN_F, 15, holdConfig({ mode: HoldMode.PAUSE }), seededRandom(0));
    t = 0;
    for (let i = 0; i < 3; i++, t += 1.0) {
      play(paused, t, 0.5, 0);
      play(paused, t + 0.5, 0.5, null);
    }
    assert.equal(paused.misses, 1);
  });

  test("restartHold drops progress without a miss", () => {
    const session = new LevelSession(loadLevels()[0], HORN_IN_F, 15, undefined, seededRandom(0));
    play(session, 0, 2, 0);
    session.restartHold();
    assert.ok(play(session, 2, 0.04, 0).at(-1).holdFraction < 0.05);
    assert.equal(session.misses, 0);
  });

  test("TC-23 encouragement for each state", () => {
    const session = practice();
    const note = session.targetNote;
    const flat = play(session, 0, 0.1, -20).at(-1).feedback;
    const sharp = play(session, 0.1, 0.1, 20).at(-1).feedback;
    const silence = play(session, 0.2, 0.5, null).at(-1).feedback;
    const inTune = play(session, 0.7, 0.1, 0).at(-1).feedback;
    const completed = play(session, 0.8, 3.5, 0).find((s) => s.event === HoldEvent.COMPLETED).feedback;
    assert.deepEqual([flat, sharp, silence, inTune, completed], [
      Feedback.FLAT_NEAR, Feedback.SHARP_NEAR, Feedback.SILENCE, Feedback.IN_TUNE, Feedback.COMPLETED,
    ]);
    assert.match(message(flat, note), /higher/);
    assert.match(message(silence, note), /Do/);
  });
});

describe("profile", () => {
  test("TC-20 unlock, TC-35 best stars kept, TC-24 total", () => {
    let progress = withLevelResult(makeProgress(), 1, 3, 5);
    assert.ok(isUnlocked(progress, 2) && !isUnlocked(progress, 3));
    progress = withLevelResult(progress, 1, 1, 5);
    assert.equal(starsFor(progress, 1), 3);
    progress = withLevelResult(progress, 2, 2, 5);
    assert.equal(totalStars(progress), 5);
    assert.equal(withLevelResult(makeProgress({}, 5), 5, 2, 5).unlockedLevel, 5);
  });

  test("TC-38 reset keeps settings; settings are validated", () => {
    const profile = makeProfile(makeSettings({ toleranceCents: 25 }), makeProgress({ 1: 3 }, 2));
    const reset = withProgressReset(profile);
    assert.equal(totalStars(reset.progress), 0);
    assert.equal(reset.settings.toleranceCents, 25);
    assert.throws(() => makeSettings({ toleranceCents: 4 }));
    assert.throws(() => makeSettings({ volume: 1.5 }));
  });
});
