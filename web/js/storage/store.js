// The single local profile in localStorage (FR-20, FR-25), in the same JSON shape as
// storage/store.py, so the two versions describe a profile the same way.

import { makeProfile, makeProgress, makeSettings } from "../core/profile.js";

export const SCHEMA_VERSION = 1;
export const STORAGE_KEY = "hornHero.profile";

export class ProfileStore {
  /** @param {Storage} storage e.g. window.localStorage */
  constructor(storage) {
    this.storage = storage;
  }

  /** Load the profile; a missing or unreadable entry gives a fresh one. */
  load() {
    try {
      const text = this.storage.getItem(STORAGE_KEY);
      return text ? profileFromJson(JSON.parse(text)) : makeProfile();
    } catch (error) {
      console.warn("Could not read the saved profile; starting fresh", error);
      return makeProfile();
    }
  }

  save(profile) {
    try {
      this.storage.setItem(STORAGE_KEY, JSON.stringify(profileToJson(profile)));
    } catch (error) {
      console.warn("Could not save progress", error); // e.g. private mode with storage disabled
    }
  }
}

export function profileToJson({ settings, progress }) {
  return {
    version: SCHEMA_VERSION,
    settings: {
      tolerance_cents: settings.toleranceCents,
      instrument: settings.instrument,
      volume: settings.volume,
      mic_sensitivity: settings.micSensitivity,
      hold_mode: settings.holdMode,
      input_device: settings.inputDevice,
    },
    progress: {
      unlocked_level: progress.unlockedLevel,
      best_stars: Object.fromEntries(Object.entries(progress.bestStars).map(([k, v]) => [String(k), v])),
    },
  };
}

export function profileFromJson(data) {
  const raw = data.settings ?? {};
  const defaults = makeSettings();
  const settings = makeSettings({
    toleranceCents: Number(raw.tolerance_cents ?? defaults.toleranceCents),
    instrument: String(raw.instrument ?? defaults.instrument),
    volume: Number(raw.volume ?? defaults.volume),
    micSensitivity: Number(raw.mic_sensitivity ?? defaults.micSensitivity),
    holdMode: String(raw.hold_mode ?? defaults.holdMode),
    inputDevice: String(raw.input_device ?? defaults.inputDevice),
  });
  const rawProgress = data.progress ?? {};
  const bestStars = Object.fromEntries(
    Object.entries(rawProgress.best_stars ?? {}).map(([level, stars]) => [Number(level), Number(stars)]),
  );
  return makeProfile(settings, makeProgress(bestStars, Number(rawProgress.unlocked_level ?? 1)));
}
