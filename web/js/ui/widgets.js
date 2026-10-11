// Widgets: staff with hold ring (FR-10), tuner gauge (FR-03..FR-05), score pill, stars and the
// hold-to-open button. Port of ui/widgets.py. They render state; no game rules here.

import { GAUGE_RANGE_CENTS, NEAR_ZONE_FACTOR, Zone, needlePosition } from "../core/tuning.js";
import { TREBLE_CLEF_HEIGHT, TREBLE_CLEF_PATH } from "./clef.js";

const SVG_NS = "http://www.w3.org/2000/svg";

export function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  node.append(...children);
  return node;
}

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, String(value));
  }
  node.append(...children);
  return node;
}

// ---------- Staff ----------

const SPACE = 26; // staff-line spacing in SVG units
const BOTTOM_LINE = 180; // y of E4
const STAFF_LEFT = 24;
const STAFF_HEIGHT = 260;
// Wide boxes get a long staff; narrow ones (phones in portrait) a shorter one, so the staff
// is drawn larger instead of leaving most of its card empty.
const LAYOUTS = { wide: { width: 700, noteX: 400 }, compact: { width: 420, noteX: 270 } };
const COMPACT_BELOW_RATIO = 2.0;
const RING_RADIUS = 1.45 * SPACE;
const RING_WIDTH = 0.36 * SPACE;
const RING_LENGTH = 2 * Math.PI * RING_RADIUS;
const MIDDLE_LINE_STEP = 4; // B4: stems go up below it, down from it upward
const INK = "#14213D";

export class Staff {
  constructor(container) {
    this.lines = [0, 1, 2, 3, 4].map((i) =>
      svg("line", { x1: STAFF_LEFT, y1: BOTTOM_LINE - i * SPACE, y2: BOTTOM_LINE - i * SPACE, stroke: INK, "stroke-width": 3, "stroke-linecap": "round" }));
    const clefScale = (7 * SPACE) / TREBLE_CLEF_HEIGHT;
    const clefTop = BOTTOM_LINE - 4 * SPACE - 1.5 * SPACE;
    const clef = svg("path", { d: TREBLE_CLEF_PATH, fill: INK, transform: `translate(${STAFF_LEFT + 14} ${clefTop}) scale(${clefScale})` });

    this.track = svg("circle", { r: RING_RADIUS, fill: "none", "stroke-width": RING_WIDTH });
    this.progress = svg("circle", { r: RING_RADIUS, fill: "none", stroke: "#16A34A", "stroke-width": RING_WIDTH, "stroke-linecap": "round" });
    this.ledgers = svg("g", { stroke: INK, "stroke-width": 3, "stroke-linecap": "round" });
    this.stem = svg("line", { "stroke-width": 0.14 * SPACE, "stroke-linecap": "round" });
    this.head = svg("ellipse", { rx: 0.66 * SPACE, ry: 0.47 * SPACE });
    this.root = svg("svg", { role: "img", "aria-label": "Staff", preserveAspectRatio: "xMidYMid meet" },
      ...this.lines, clef, this.track, this.progress, this.ledgers, this.stem, this.head);
    container.replaceChildren(this.root);
    this._state = "";
    this._note = null;
    this._applyLayout(LAYOUTS.wide);
    new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      const layout = height > 0 && width / height < COMPACT_BELOW_RATIO ? LAYOUTS.compact : LAYOUTS.wide;
      if (layout !== this._layout) this._applyLayout(layout);
    }).observe(container);
  }

  _applyLayout(layout) {
    this._layout = layout;
    this.root.setAttribute("viewBox", `0 0 ${layout.width} ${STAFF_HEIGHT}`);
    for (const line of this.lines) line.setAttribute("x2", layout.width - STAFF_LEFT);
    if (this._note) this.setNote(this._note);
  }

  setNote(note) {
    this._note = note;
    const noteX = this._layout.noteX;
    const step = note.staffStep;
    const y = BOTTOM_LINE - (step * SPACE) / 2;
    for (const circle of [this.track, this.progress]) {
      circle.setAttribute("cx", noteX);
      circle.setAttribute("cy", y);
    }
    this.progress.setAttribute("transform", `rotate(-90 ${noteX} ${y})`);
    this.ledgers.replaceChildren();
    const ledgerSteps = [];
    for (let s = -2; s >= step; s -= 2) ledgerSteps.push(s);
    for (let s = 10; s <= step; s += 2) ledgerSteps.push(s);
    for (const s of ledgerSteps) {
      const ly = BOTTOM_LINE - (s * SPACE) / 2;
      this.ledgers.append(svg("line", { x1: noteX - 1.3 * SPACE, x2: noteX + 1.3 * SPACE, y1: ly, y2: ly }));
    }
    const headRx = 0.66 * SPACE;
    const up = step < MIDDLE_LINE_STEP;
    const stemX = noteX + (up ? 0.92 : -0.92) * headRx;
    this.stem.setAttribute("x1", stemX);
    this.stem.setAttribute("x2", stemX);
    this.stem.setAttribute("y1", y + (up ? -0.1 : 0.1) * SPACE);
    this.stem.setAttribute("y2", y + (up ? -3.5 : 3.5) * SPACE);
    this.head.setAttribute("cx", noteX);
    this.head.setAttribute("cy", y);
    this.head.setAttribute("transform", `rotate(-20 ${noteX} ${y})`);
    this.root.setAttribute("aria-label", `Target note ${note.label}, written ${note.name}`);
    this._state = "";
  }

  setState(progress, inTune, idle) {
    const key = `${progress.toFixed(3)}|${inTune}|${idle}`;
    if (key === this._state) return;
    this._state = key;
    this.track.setAttribute("stroke", idle ? "#B8C7E0" : "#D7E3F5");
    this.track.setAttribute("stroke-dasharray", idle ? "2 14" : "none");
    this.track.setAttribute("stroke-width", idle ? 0.22 * SPACE : RING_WIDTH);
    this.progress.setAttribute("stroke-dasharray", `${progress * RING_LENGTH} ${RING_LENGTH}`);
    this.progress.style.opacity = idle || progress <= 0 ? "0" : "1";
    const color = inTune ? "#0E7C3A" : INK;
    this.head.setAttribute("fill", color);
    this.stem.setAttribute("stroke", color);
  }
}

// ---------- Gauge ----------

const CHIP_COLORS = {
  [Zone.FLAT_NEAR]: "var(--yellow)", [Zone.FLAT_FAR]: "var(--red)",
  [Zone.SHARP_NEAR]: "var(--yellow)", [Zone.SHARP_FAR]: "var(--red)", [Zone.GREEN]: "var(--green)",
};
const SMOOTHING = 0.35;

function percentAt(cents) {
  return ((Math.max(-1, Math.min(1, cents / GAUGE_RANGE_CENTS)) + 1) / 2) * 100;
}

export class Gauge {
  constructor(container) {
    this.zones = el("div", { class: "gauge-zones" });
    this.needle = el("div", { class: "gauge-needle" });
    this.track = el("div", { class: "gauge-track idle", role: "img", "aria-label": "Tuner" },
      this.zones, el("div", { class: "gauge-center" }), this.needle);
    this.chips = {
      flat: el("span", { class: "gauge-chip", text: "♭ Flat" }),
      green: el("span", { class: "gauge-chip", text: "✓ In tune" }),
      sharp: el("span", { class: "gauge-chip", text: "♯ Sharp" }),
    };
    container.replaceChildren(this.track, el("div", { class: "gauge-labels" }, this.chips.flat, this.chips.green, this.chips.sharp));
    this._shown = 0;
    this.setTolerance(15);
    this.setReading(null, Zone.IDLE);
  }

  setTolerance(toleranceCents) {
    const near = toleranceCents * NEAR_ZONE_FACTOR;
    const [a, b, c, d] = [-near, -toleranceCents, toleranceCents, near].map(percentAt);
    this.zones.style.background = `linear-gradient(to right, var(--red) 0 ${a}%, var(--yellow) ${a}% ${b}%,`
      + ` var(--green) ${b}% ${c}%, var(--yellow) ${c}% ${d}%, var(--red) ${d}% 100%)`;
  }

  setReading(cents, zone) {
    const target = cents === null ? 0 : needlePosition(cents);
    this._shown += (target - this._shown) * SMOOTHING;
    this.needle.style.left = `${((this._shown + 1) / 2) * 100}%`;
    this.track.classList.toggle("idle", zone === Zone.IDLE);
    const active = zone === Zone.GREEN ? "green" : zone.startsWith("flat") ? "flat" : zone.startsWith("sharp") ? "sharp" : null;
    for (const [name, chip] of Object.entries(this.chips)) {
      chip.classList.toggle("active", name === active);
      chip.style.setProperty("--chip", name === active ? CHIP_COLORS[zone] : "");
    }
  }
}

// ---------- Score pill and stars ----------

const MAX_SLOTS = 12;

export function starPoints(cx, cy, r) {
  const points = [];
  for (let i = 0; i < 10; i++) {
    const radius = i % 2 === 0 ? r : r * 0.48;
    const angle = -Math.PI / 2 + (i * Math.PI) / 5;
    points.push(`${(cx + radius * Math.cos(angle)).toFixed(2)},${(cy + radius * Math.sin(angle)).toFixed(2)}`);
  }
  return points.join(" ");
}

function slotIcon(earned) {
  return earned
    ? svg("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" }, svg("polygon", { points: starPoints(12, 12.5, 11.5), fill: "#FFC93C" }))
    : svg("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" }, svg("circle", { cx: 12, cy: 12, r: 6, fill: "none", stroke: "#A5B4FC", "stroke-width": 2 }));
}

export function renderScore(container, points, goal) {
  const slots = goal <= MAX_SLOTS
    ? el("span", { class: "slots" }, ...Array.from({ length: goal }, (_, i) => el("span", { class: "slot" }, slotIcon(i < points))))
    : "";
  container.replaceChildren(el("span", { class: "score-text", text: `${points} / ${goal}` }), slots);
  container.setAttribute("aria-label", `Score ${points} of ${goal}`);
}

/** Earned stars gold, missing stars dashed outline (FR-23). */
export function starRow(earned, total = 3) {
  const size = 100;
  const gap = 12;
  const width = total * size + (total - 1) * gap;
  const stars = Array.from({ length: total }, (_, i) => svg("polygon", {
    points: starPoints(i * (size + gap) + size / 2, size / 2 + 3, size * 0.48),
    fill: i < earned ? "#FFC93C" : "#EEF3FB",
    stroke: i < earned ? INK : "#8A9AB8",
    "stroke-width": 4.5,
    "stroke-linejoin": "round",
    "stroke-dasharray": i < earned ? "none" : "10 8",
  }));
  return svg("svg", { viewBox: `0 0 ${width} ${size + 6}`, role: "img", "aria-label": `${earned} of ${total} stars` }, ...stars);
}

// ---------- Hold-to-open button ----------

export const HOLD_MS = 1000;

/** Fires `onHeld` only after the button is held down, so a child cannot open it by accident.
 * A ring fills while held; a short tap shows a hint instead. */
export function makeHoldButton(button, onHeld, showHint) {
  let start = 0;
  let frame = 0;
  const reset = () => {
    cancelAnimationFrame(frame);
    start = 0;
    button.style.setProperty("--hold", "0");
  };
  const tick = () => {
    const fraction = Math.min(1, (performance.now() - start) / HOLD_MS);
    button.style.setProperty("--hold", String(fraction));
    if (fraction < 1) {
      frame = requestAnimationFrame(tick);
    } else {
      reset();
      onHeld();
    }
  };
  const begin = (event) => {
    event.preventDefault();
    if (start) return;
    start = performance.now();
    frame = requestAnimationFrame(tick);
  };
  const end = () => {
    if (!start) return;
    reset();
    showHint(button.dataset.hint ?? "Hold to open");
  };
  button.addEventListener("pointerdown", begin);
  button.addEventListener("pointerup", end);
  button.addEventListener("pointerleave", end);
  button.addEventListener("pointercancel", reset);
  button.addEventListener("contextmenu", (event) => event.preventDefault()); // long-press menu on phones
  button.addEventListener("keydown", (event) => {
    if ((event.key === "Enter" || event.key === " ") && !event.repeat) begin(event);
  });
  button.addEventListener("keyup", (event) => {
    if (event.key === "Enter" || event.key === " ") end();
  });
}
