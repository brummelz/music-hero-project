// Cents conversion, tuner zones and tolerance rules (FR-02..FR-05, FR-21). Port of core/tuning.py.

/** The gauge spans ±50 cents; readings beyond are clamped to the ends (FR-04). */
export const GAUGE_RANGE_CENTS = 50.0;

export const DEFAULT_TOLERANCE_CENTS = 15.0;
export const MIN_TOLERANCE_CENTS = 5.0;
export const MAX_TOLERANCE_CENTS = 50.0;
export const TOLERANCE_PRESETS = Object.freeze({ Easy: 25.0, Normal: 15.0, Strict: 10.0 });

/** Yellow "near" zones reach twice the tolerance; beyond is red "far". (Assumption: the spec
 * names near/far zones without a boundary.) */
export const NEAR_ZONE_FACTOR = 2.0;

export const Zone = Object.freeze({
  IDLE: "idle",
  FLAT_FAR: "flat_far",
  FLAT_NEAR: "flat_near",
  GREEN: "green",
  SHARP_NEAR: "sharp_near",
  SHARP_FAR: "sharp_far",
});

/** FR-02: cents = 1200 * log2(f / f_t). */
export function centsOffset(frequencyHz, targetHz) {
  if (!(frequencyHz > 0) || !(targetHz > 0)) throw new RangeError("Frequencies must be positive");
  return 1200 * Math.log2(frequencyHz / targetHz);
}

/** FR-21: custom tolerance must be within ±5..±50 cents. */
export function validateTolerance(toleranceCents) {
  if (!(toleranceCents >= MIN_TOLERANCE_CENTS && toleranceCents <= MAX_TOLERANCE_CENTS)) {
    throw new RangeError(
      `Tolerance must be between ${MIN_TOLERANCE_CENTS} and ${MAX_TOLERANCE_CENTS} cents, got ${toleranceCents}`,
    );
  }
  return toleranceCents;
}

/** FR-03 zones; null (no pitched sound) is IDLE (FR-05). */
export function classify(cents, toleranceCents) {
  if (cents === null || cents === undefined) return Zone.IDLE;
  if (Math.abs(cents) <= toleranceCents) return Zone.GREEN;
  const near = Math.abs(cents) <= toleranceCents * NEAR_ZONE_FACTOR;
  if (cents < 0) return near ? Zone.FLAT_NEAR : Zone.FLAT_FAR;
  return near ? Zone.SHARP_NEAR : Zone.SHARP_FAR;
}

/** Needle position in [-1, 1] across the gauge, clamped at the ends (FR-04). */
export function needlePosition(cents) {
  return Math.max(-1, Math.min(1, cents / GAUGE_RANGE_CENTS));
}
