// Shared test helpers: level data loading and approximate comparison.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { parseLevels } from "../js/core/levels.js";

export function readJson(relativePath) {
  return JSON.parse(readFileSync(new URL(relativePath, import.meta.url), "utf-8"));
}

export function loadLevels() {
  return parseLevels(readJson("../data/levels.json").levels);
}

export function approx(actual, expected, tolerance, message) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    message ?? `expected ${expected} ± ${tolerance}, got ${actual}`,
  );
}
