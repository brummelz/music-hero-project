// The single local profile: settings and progress (FR-17, FR-20, FR-21, FR-24, FR-25).
// Port of core/profile.py. Values are frozen plain objects; "with…" functions return copies.

import { HoldMode } from "./holdTimer.js";
import { HORN_IN_F, profileByName } from "./transpose.js";
import { DEFAULT_TOLERANCE_CENTS, validateTolerance } from "./tuning.js";

/**
 * @typedef {{toleranceCents: number, instrument: string, volume: number,
 *   micSensitivity: number, holdMode: string, inputDevice: string}} Settings
 * @typedef {{bestStars: Readonly<Record<number, number>>, unlockedLevel: number}} Progress
 * @typedef {{settings: Settings, progress: Progress}} Profile
 */

/** @returns {Settings} validated settings, defaults filled in. */
export function makeSettings(values = {}) {
  const settings = {
    toleranceCents: DEFAULT_TOLERANCE_CENTS,
    instrument: HORN_IN_F.name,
    volume: 0.8,
    micSensitivity: 0.5,
    holdMode: HoldMode.RESET,
    inputDevice: "", // Microphone deviceId; empty means the browser default.
    ...values,
  };
  validateTolerance(settings.toleranceCents);
  profileByName(settings.instrument);
  for (const key of ["volume", "micSensitivity"]) {
    if (!(settings[key] >= 0 && settings[key] <= 1)) throw new RangeError(`${key} must be between 0 and 1`);
  }
  if (!Object.values(HoldMode).includes(settings.holdMode)) throw new RangeError("Unknown hold mode");
  return Object.freeze(settings);
}

/** @returns {Progress} */
export function makeProgress(bestStars = {}, unlockedLevel = 1) {
  return Object.freeze({ bestStars: Object.freeze({ ...bestStars }), unlockedLevel });
}

/** @returns {Profile} */
export function makeProfile(settings = makeSettings(), progress = makeProgress()) {
  return Object.freeze({ settings, progress });
}

/** FR-24: the sum of each level's best stars. */
export function totalStars(progress) {
  return Object.values(progress.bestStars).reduce((sum, stars) => sum + stars, 0);
}

export function starsFor(progress, levelNumber) {
  return progress.bestStars[levelNumber] ?? 0;
}

export function isUnlocked(progress, levelNumber) {
  return levelNumber <= progress.unlockedLevel;
}

/** FR-17: keep only the best stars and unlock the next level. */
export function withLevelResult(progress, levelNumber, stars, levelCount) {
  const best = { ...progress.bestStars, [levelNumber]: Math.max(stars, starsFor(progress, levelNumber)) };
  const unlocked = Math.max(progress.unlockedLevel, Math.min(levelNumber + 1, levelCount));
  return makeProgress(best, unlocked);
}

/** FR-25: clear progress and stars, keep settings. */
export function withProgressReset(profile) {
  return makeProfile(profile.settings, makeProgress());
}
