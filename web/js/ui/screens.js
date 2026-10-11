// Home (spec Screen 1) and summary (FR-14, FR-17) screens. Ports of ui/home_screen.py and
// ui/summary_screen.py.

import { THREE_STAR_MAX_MISSES } from "../core/levels.js";
import { isUnlocked, starsFor, totalStars } from "../core/profile.js";
import { el, renderScore, starRow } from "./widgets.js";

const $ = (id) => document.getElementById(id);

export class HomeScreen {
  /** @param {{practiceNotes: any[], levels: any[], onPractice: (note: any) => void, onLevel: (n: number) => void}} options */
  constructor({ practiceNotes, levels, onPractice, onLevel }) {
    this.levels = levels;
    this.onLevel = onLevel;
    this.selected = practiceNotes[0];
    this.noteButtons = practiceNotes.map((note) => {
      const button = el("button", { class: "note-choice", type: "button", role: "radio", "aria-label": `${note.solfege} (${note.letter})` },
        el("span", { class: "solfege", text: note.solfege }), el("span", { class: "letter", text: note.letter }));
      button.addEventListener("click", () => {
        this.selected = note;
        this._markSelected();
      });
      return button;
    });
    $("practice-notes").replaceChildren(...this.noteButtons);
    this._practiceNotes = practiceNotes;
    this._markSelected();
    $("start-practice").addEventListener("click", () => onPractice(this.selected));
  }

  _markSelected() {
    this.noteButtons.forEach((button, i) => button.setAttribute("aria-checked", String(this._practiceNotes[i] === this.selected)));
  }

  refresh(progress, instrumentName) {
    const max = 3 * this.levels.length;
    $("total-stars").textContent = `★ ${totalStars(progress)} / ${max}`;
    $("total-stars").setAttribute("aria-label", `${totalStars(progress)} of ${max} stars earned`);
    $("instrument").textContent = instrumentName;
    $("level-list").replaceChildren(...this.levels.map((level) => el("li", {}, this._levelRow(level, progress))));
  }

  _levelRow(level, progress) {
    const unlocked = isUnlocked(progress, level.number);
    const stars = starsFor(progress, level.number);
    const button = el("button", { class: "level", type: "button" },
      el("span", { class: "badge", text: unlocked ? String(level.number) : "🔒︎" }),
      el("span", { class: "theme", text: level.theme }));
    if (!unlocked) {
      button.disabled = true;
      button.setAttribute("aria-label", `Level ${level.number}, ${level.theme}, locked`);
      button.append(el("span", { text: "Locked" }));
      return button;
    }
    button.addEventListener("click", () => this.onLevel(level.number));
    if (stars === 0) {
      button.classList.add("current");
      button.setAttribute("aria-label", `Level ${level.number}, ${level.theme}, play`);
      button.append(el("span", { class: "play", text: "Play" }));
    } else {
      button.setAttribute("aria-label", `Level ${level.number}, ${level.theme}, ${stars} of 3 stars`);
      const row = starRow(stars);
      row.setAttribute("width", "84");
      button.append(row);
    }
    return button;
  }
}

export class SummaryScreen {
  constructor({ onHome, onAgain, onNext }) {
    $("summary-home").addEventListener("click", onHome);
    $("summary-again").addEventListener("click", onAgain);
    $("summary-next").addEventListener("click", onNext);
  }

  showPractice(note, points) {
    $("summary-title").textContent = "You did it!";
    $("summary-stars").replaceChildren(); // FR-24: practice awards no stars, so show the points row.
    renderScore($("summary-points"), points, points);
    $("summary-points").hidden = false;
    $("summary-message").textContent = `You held ${points} steady ${note.solfege} notes. Super playing!`;
    $("summary-unlocked").hidden = true;
    $("summary-next").hidden = true;
    $("summary-again").className = "primary";
    $("summary-again").focus();
  }

  showLevel(level, stars, misses, newlyUnlocked, nextLevel) {
    $("summary-title").textContent = `Level ${level.number} complete!`;
    $("summary-stars").replaceChildren(starRow(stars));
    $("summary-points").hidden = true;
    $("summary-message").textContent = starReason(stars, misses);
    $("summary-unlocked").hidden = !newlyUnlocked;
    if (newlyUnlocked) $("summary-unlocked").textContent = `✓ Level ${newlyUnlocked.number} unlocked: ${newlyUnlocked.theme}`;
    $("summary-next").hidden = !nextLevel;
    $("summary-again").className = nextLevel ? "secondary" : "primary";
    (nextLevel ? $("summary-next") : $("summary-again")).focus();
  }
}

/** FR-22/FR-23: say why, so the stars feel earned rather than random. */
export function starReason(stars, misses) {
  if (misses === 0) return "Amazing! All 3 stars!";
  const restarts = misses === 1 ? "1 restart" : `${misses} restarts`;
  if (stars === 3) return `Amazing! All 3 stars (${restarts}).`;
  return `Great playing! You had ${restarts}. Keep it to ${THREE_STAR_MAX_MISSES} or fewer to win all 3 stars.`;
}
