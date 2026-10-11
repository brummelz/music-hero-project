// Composition root: storage, audio and screens (like main.py + ui/main_window.py).

import { Microphone } from "./audio/mic.js";
import { SimulatedMicrophone } from "./audio/simulator.js";
import { holdConfig } from "./core/holdTimer.js";
import { parseLevels } from "./core/levels.js";
import { makeProfile, withLevelResult, withProgressReset } from "./core/profile.js";
import { LevelSession, PRACTICE_NOTES, PracticeSession } from "./core/session.js";
import { profileByName } from "./core/transpose.js";
import { ProfileStore } from "./storage/store.js";
import { GameScreen } from "./ui/game.js";
import { HomeScreen, SummaryScreen } from "./ui/screens.js";
import { SettingsDialog } from "./ui/settings.js";
import { makeHoldButton } from "./ui/widgets.js";

const SIMULATE = new URLSearchParams(location.search).has("sim");
const TOAST_MS = 1800;
const $ = (id) => document.getElementById(id);

const store = new ProfileStore(window.localStorage);
let profile = store.load();
const audio = { context: null, mic: null };
let replay = null;
let nextLevel = null;

function save(next) {
  profile = next;
  store.save(profile);
}

function show(screenId) {
  for (const screen of document.querySelectorAll(".screen")) screen.hidden = screen.id !== screenId;
  window.scrollTo(0, 0);
}

let toastTimer = 0;
function toast(text) {
  $("toast").textContent = text;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $("toast").hidden = true; }, TOAST_MS);
}

const levels = parseLevels((await (await fetch("data/levels.json")).json()).levels);

const game = new GameScreen({
  audio,
  simulate: SIMULATE,
  onBack: () => {
    game.stop();
    showHome();
  },
  onFinished: (session) => finishSession(session),
});

const home = new HomeScreen({
  practiceNotes: PRACTICE_NOTES,
  levels,
  onPractice: (note) => startPractice(note),
  onLevel: (number) => startLevel(number),
});

const summary = new SummaryScreen({
  onHome: () => showHome(),
  onAgain: () => replay?.(),
  onNext: () => nextLevel && startLevel(nextLevel.number),
});

const settingsDialog = new SettingsDialog({
  audio,
  simulate: SIMULATE,
  onChange: (settings) => applySettings(settings),
  onReset: () => {
    save(withProgressReset(profile));
    toast("Progress reset");
  },
  onClose: () => {
    if (!$("home").hidden) showHome();
    if (!$("game").hidden) game.resume();
  },
});

for (const button of document.querySelectorAll(".settings-button")) {
  makeHoldButton(button, openSettings, toast);
}

function openSettings() {
  game.pause();
  settingsDialog.open(profile.settings);
}

async function applySettings(settings) {
  const micChanged = settings.inputDevice !== profile.settings.inputDevice;
  save(makeProfile(settings, profile.progress));
  game.applySettings(settings);
  if (micChanged && !SIMULATE) {
    try {
      await audio.mic.start(settings.inputDevice);
    } catch (error) {
      console.warn("Could not switch microphone", error);
      toast("That microphone is not available");
    }
  }
}

function showHome() {
  home.refresh(profile.progress, profile.settings.instrument);
  show("home");
}

function startGame(session, caption, again) {
  replay = again;
  show("game");
  game.start(session, profile.settings, caption);
}

function startPractice(note) {
  const { settings } = profile;
  const session = new PracticeSession(note, profileByName(settings.instrument), settings.toleranceCents, holdConfig({ mode: settings.holdMode }));
  startGame(session, "Target note", () => startPractice(note));
}

function startLevel(number) {
  const level = levels[number - 1];
  const { settings } = profile;
  const session = new LevelSession(level, profileByName(settings.instrument), settings.toleranceCents, holdConfig({ mode: settings.holdMode }));
  startGame(session, `Level ${level.number} · ${level.theme}`, () => startLevel(number));
}

function finishSession(session) {
  if (session instanceof LevelSession) {
    const { level } = session;
    const before = profile.progress;
    const after = withLevelResult(before, level.number, session.stars, levels.length);
    save(makeProfile(profile.settings, after));
    nextLevel = level.number < levels.length ? levels[level.number] : null;
    const newlyUnlocked = after.unlockedLevel > before.unlockedLevel ? nextLevel : null;
    summary.showLevel(level, session.stars, session.misses, newlyUnlocked, nextLevel);
  } else {
    summary.showPractice(session.targetNote, session.points);
  }
  show("summary");
}

// Cover: "Start Game!" is the user gesture browsers need before audio and the microphone (spec §6.1).
async function begin() {
  $("start").hidden = true;
  $("cover-busy").hidden = false;
  $("mic-help").hidden = true;
  try {
    audio.context ??= new AudioContext();
    audio.mic ??= SIMULATE ? new SimulatedMicrophone() : new Microphone(audio.context);
    await audio.mic.start(profile.settings.inputDevice);
    await audio.context.resume();
    showHome();
  } catch (error) {
    console.warn("Microphone not available", error);
    $("mic-help-text").textContent = error?.name === "NotFoundError"
      ? "No microphone was found. Plug one in, then tap “Try again”."
      : "Horn Hero needs the microphone to hear your notes. Tap “Try again” and choose Allow.";
    $("mic-help").hidden = false;
  } finally {
    $("start").hidden = false;
    $("cover-busy").hidden = true;
  }
}

$("start").addEventListener("click", begin);
$("mic-retry").addEventListener("click", begin);

// Escape leaves the game; switching tabs pauses it so a hidden page never counts as a miss.
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("game").hidden && !$("settings").open) {
    game.stop();
    showHome();
  }
});
document.addEventListener("visibilitychange", () => {
  if ($("game").hidden || $("settings").open) return;
  if (document.hidden) game.pause();
  else game.resume();
});

if ("serviceWorker" in navigator && location.protocol !== "file:") {
  navigator.serviceWorker.register("sw.js").catch((error) => console.warn("Offline mode unavailable", error));
}
