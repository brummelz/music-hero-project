// Encouragement messages (FR-18). Port of core/feedback.py.

import { HoldEvent } from "./holdTimer.js";
import { Zone } from "./tuning.js";

export const Feedback = Object.freeze({
  SILENCE: "silence",
  FLAT_FAR: "flat_far",
  FLAT_NEAR: "flat_near",
  IN_TUNE: "in_tune",
  SHARP_NEAR: "sharp_near",
  SHARP_FAR: "sharp_far",
  COMPLETED: "completed",
  // Shown briefly after a well-started hold restarts, so the reset never feels silent.
  TRY_AGAIN: "try_again",
});

const FROM_ZONE = {
  [Zone.IDLE]: Feedback.SILENCE,
  [Zone.FLAT_FAR]: Feedback.FLAT_FAR,
  [Zone.FLAT_NEAR]: Feedback.FLAT_NEAR,
  [Zone.GREEN]: Feedback.IN_TUNE,
  [Zone.SHARP_NEAR]: Feedback.SHARP_NEAR,
  [Zone.SHARP_FAR]: Feedback.SHARP_FAR,
};

const MESSAGES = {
  [Feedback.SILENCE]: "Take a breath and play your {note}!",
  [Feedback.FLAT_FAR]: "A bit low! Lift the note up.",
  [Feedback.FLAT_NEAR]: "Almost there! Push a little higher!",
  [Feedback.IN_TUNE]: "Perfect! Keep it steady…",
  [Feedback.SHARP_NEAR]: "A touch too high, ease down a little!",
  [Feedback.SHARP_FAR]: "A bit high! Relax and come down.",
  [Feedback.COMPLETED]: "Great job! +1 point!",
  [Feedback.TRY_AGAIN]: "So close! Start the hold again.",
};

export function feedbackFor(zone, event) {
  return event === HoldEvent.COMPLETED ? Feedback.COMPLETED : FROM_ZONE[zone];
}

export function message(feedback, note) {
  return MESSAGES[feedback].replace("{note}", note.solfege);
}
