// Level Challenge rules: level data, prompt generation and stars (FR-15..FR-17, FR-23).
// Port of core/levels.py.

import { Note } from "./notes.js";

export const PROMPTS_PER_LEVEL = 6;
export const THREE_STAR_MAX_MISSES = 2;
export const TWO_STAR_MAX_MISSES = 6;
const MAX_SHUFFLE_ATTEMPTS = 10_000;

/** @typedef {{number: number, theme: string, notes: readonly Note[], promptCount: number}} Level */

/**
 * FR-16 asks for 6 prompts with every note at least once. Level 3 has 8 notes, so both
 * cannot hold; that level gets one prompt per note. (Spec conflict, flagged for review.)
 */
function promptCount(notes) {
  return Math.max(PROMPTS_PER_LEVEL, notes.length);
}

/** Build levels from configuration data (the level table is data, not code). */
export function parseLevels(data) {
  return Object.freeze(
    data.map((entry, i) => {
      const number = Number(entry.number);
      if (number !== i + 1) throw new RangeError(`Levels must be numbered 1..n in order, got ${number}`);
      const notes = Object.freeze(entry.notes.map((name) => Note.parse(name)));
      if (new Set(notes.map((n) => n.name)).size !== notes.length || notes.length < 2) {
        throw new RangeError(`Level ${number} needs at least 2 distinct notes`);
      }
      return Object.freeze({ number, theme: String(entry.theme), notes, promptCount: promptCount(notes) });
    }),
  );
}

/** A small seeded random generator (mulberry32), so prompt order is testable. */
export function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffle(items, random) {
  for (let i = items.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }
  return items;
}

/** FR-16: every note at least once, no note twice in a row. @param {() => number} random */
export function generatePrompts(level, random = Math.random) {
  for (let attempt = 0; attempt < MAX_SHUFFLE_ATTEMPTS; attempt++) {
    const prompts = [...level.notes];
    while (prompts.length < level.promptCount) {
      prompts.push(level.notes[Math.floor(random() * level.notes.length)]);
    }
    shuffle(prompts, random);
    if (prompts.every((note, i) => i === 0 || note.name !== prompts[i - 1].name)) return prompts;
  }
  throw new Error(`Could not generate prompts for level ${level.number}`);
}

/** FR-23: 3 stars for 0-2 misses, 2 for 3-6, 1 for 7 or more. */
export function starsForMisses(misses) {
  if (misses < 0) throw new RangeError("Misses cannot be negative");
  if (misses <= THREE_STAR_MAX_MISSES) return 3;
  if (misses <= TWO_STAR_MAX_MISSES) return 2;
  return 1;
}
