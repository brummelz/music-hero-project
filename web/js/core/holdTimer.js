// Hold-timer state machine (FR-06..FR-09, FR-22). Port of core/hold_timer.py.
// Time is passed in by the caller (seconds), so the timer is deterministic under test.

export const DEFAULT_HOLD_SECONDS = 3.0;
export const DEFAULT_GRACE_SECONDS = 0.15;

export const HoldMode = Object.freeze({
  RESET: "reset", // Leaving the Green zone resets progress to 0 (default, FR-07).
  PAUSE: "pause", // Leaving the Green zone keeps progress; it resumes on return.
});

export const HoldEvent = Object.freeze({
  NONE: "none",
  MISSED: "missed", // Progress was lost or paused after the hold had started (FR-22).
  COMPLETED: "completed", // The hold reached its full duration (FR-09).
});

/** @typedef {{holdSeconds: number, graceSeconds: number, mode: string}} HoldConfig */

/** @returns {HoldConfig} */
export function holdConfig(overrides = {}) {
  return Object.freeze({
    holdSeconds: DEFAULT_HOLD_SECONDS,
    graceSeconds: DEFAULT_GRACE_SECONDS,
    mode: HoldMode.RESET,
    ...overrides,
  });
}

/**
 * Tracks continuous time in the Green zone. Being out of the zone (wrong pitch or no
 * detection) for up to the grace period does not count as leaving it (FR-08).
 */
export class HoldTimer {
  /** @param {HoldConfig} [config] */
  constructor(config = holdConfig()) {
    this.config = config;
    this.reset();
  }

  /** Seconds of hold progress so far. */
  get elapsed() {
    if (this._runStart === null || this._lastInZone === null) return this._banked;
    return this._banked + this._lastInZone - this._runStart;
  }

  get fraction() {
    return Math.min(1, this.elapsed / this.config.holdSeconds);
  }

  reset() {
    this._banked = 0;
    this._runStart = null;
    this._lastInZone = null;
  }

  /** @param {number} now seconds @param {boolean} inZone @returns {string} a HoldEvent */
  update(now, inZone) {
    return inZone ? this._updateInZone(now) : this._updateOutOfZone(now);
  }

  _updateInZone(now) {
    if (this._runStart === null) this._runStart = now;
    this._lastInZone = now;
    if (this.elapsed < this.config.holdSeconds) return HoldEvent.NONE;
    // Start the next attempt immediately so a continuous note keeps scoring.
    this._banked = 0;
    this._runStart = now;
    return HoldEvent.COMPLETED;
  }

  _updateOutOfZone(now) {
    if (this._runStart === null || this._lastInZone === null) return HoldEvent.NONE;
    if (now - this._lastInZone <= this.config.graceSeconds) return HoldEvent.NONE;
    const progress = this.elapsed;
    this._banked = this.config.mode === HoldMode.PAUSE ? progress : 0;
    this._runStart = null;
    this._lastInZone = null;
    return progress > 0 ? HoldEvent.MISSED : HoldEvent.NONE;
  }
}
