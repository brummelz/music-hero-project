// Game sessions: Single Note Practice and Level Challenge (FR-12..FR-17, FR-22).
// Port of core/session.py.

import { Feedback, feedbackFor } from "./feedback.js";
import { HoldEvent, HoldMode, HoldTimer, holdConfig } from "./holdTimer.js";
import { generatePrompts, starsForMisses } from "./levels.js";
import { Note } from "./notes.js";
import { soundingFrequency } from "./transpose.js";
import { Zone, centsOffset, classify, validateTolerance } from "./tuning.js";

export const PRACTICE_GOAL_POINTS = 10;
/** FR-12: practice targets offered initially (Do, Ré, Mi). */
export const PRACTICE_NOTES = Object.freeze(["C4", "D4", "E4"].map((name) => Note.parse(name)));

/**
 * What the gameplay screen shows after one detection frame.
 * @typedef {{cents: number|null, zone: string, holdFraction: number, event: string, feedback: string}} FrameState
 */

class GameSession {
  constructor(profile, toleranceCents, config = holdConfig()) {
    this.profile = profile;
    this._toleranceCents = validateTolerance(toleranceCents);
    this._timer = new HoldTimer(config);
    this.points = 0;
  }

  get finished() {
    return this.points >= this.goal;
  }

  get targetFrequency() {
    return soundingFrequency(this.targetNote.midi, this.profile);
  }

  get holdSeconds() {
    return this._timer.config.holdSeconds;
  }

  get toleranceCents() {
    return this._toleranceCents;
  }

  /** FR-21: a tolerance change applies immediately. */
  set toleranceCents(value) {
    this._toleranceCents = validateTolerance(value);
  }

  /** Drop hold progress without counting a miss, e.g. after the game was paused. */
  restartHold() {
    this._timer.reset();
  }

  /**
   * Feed one detection result (null = no pitched sound) at time `now` (seconds).
   * @returns {FrameState}
   */
  process(now, frequencyHz) {
    if (this.finished) {
      return { cents: null, zone: Zone.IDLE, holdFraction: 1, event: HoldEvent.NONE, feedback: Feedback.COMPLETED };
    }
    const cents = frequencyHz === null ? null : centsOffset(frequencyHz, this.targetFrequency);
    const zone = classify(cents, this._toleranceCents);
    const event = this._timer.update(now, zone === Zone.GREEN);
    let holdFraction = this._timer.fraction;
    if (event === HoldEvent.MISSED) {
      this._onMiss();
    } else if (event === HoldEvent.COMPLETED) {
      holdFraction = 1;
      this.points += 1;
      this._onPoint();
    }
    return { cents, zone, holdFraction, event, feedback: feedbackFor(zone, event) };
  }

  _onMiss() {}

  _onPoint() {}
}

/** Mode 1: one fixed target note, 10 points to finish (FR-12..FR-14). */
export class PracticeSession extends GameSession {
  constructor(note, profile, toleranceCents, config) {
    super(profile, toleranceCents, config);
    this._note = note;
  }

  get targetNote() {
    return this._note;
  }

  get goal() {
    return PRACTICE_GOAL_POINTS;
  }
}

/** Mode 2: a sequence of prompts from the level's note set (FR-15..FR-17). */
export class LevelSession extends GameSession {
  constructor(level, profile, toleranceCents, config, random = Math.random) {
    super(profile, toleranceCents, config);
    this.level = level;
    this.prompts = generatePrompts(level, random);
    this.misses = 0;
    this._missedThisPrompt = false;
  }

  get targetNote() {
    return this.prompts[Math.min(this.points, this.prompts.length - 1)];
  }

  get goal() {
    return this.prompts.length;
  }

  get stars() {
    return starsForMisses(this.misses);
  }

  _onMiss() {
    // FR-23: in pause mode only the first pause within a prompt is a miss.
    if (this._timer.config.mode === HoldMode.PAUSE && this._missedThisPrompt) return;
    this.misses += 1;
    this._missedThisPrompt = true;
  }

  _onPoint() {
    // The next prompt is a new note, so start its hold from zero.
    this._timer.reset();
    this._missedThisPrompt = false;
  }
}
