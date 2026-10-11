// Gameplay screen: staff, tuner gauge, hold ring and encouragement (spec Screen 2).
// Port of ui/game_screen.py; timings match the desktop app.

import { playReference, playSuccess } from "../audio/sfx.js";
import { PitchTracker } from "../audio/tracker.js";
import { message } from "../core/feedback.js";
import { Feedback } from "../core/feedback.js";
import { HoldEvent, HoldMode } from "../core/holdTimer.js";
import { midiLabel } from "../core/notes.js";
import { nearestWrittenNote } from "../core/transpose.js";
import { Zone } from "../core/tuning.js";
import { Gauge, Staff, renderScore } from "./widgets.js";

const CELEBRATE_SECONDS = 1.2;
const FINISH_DELAY_MS = 1400;
/** A wobbling note should not make the message flicker; "in tune" still shows at once. */
const MIN_MESSAGE_SECONDS = 0.4;
/** Only a hold this far along gets the "So close!" cue when it restarts. */
const TRY_AGAIN_AFTER_SECONDS = 1.0;
const TRY_AGAIN_SECONDS = 1.5;
/** Keep ignoring the microphone briefly after the reference note, so its echo is not scored. */
const LISTEN_TAIL_SECONDS = 0.3;

const ICONS = {
  [Feedback.SILENCE]: "♪", [Feedback.FLAT_FAR]: "↑", [Feedback.FLAT_NEAR]: "↑", [Feedback.IN_TUNE]: "✓",
  [Feedback.SHARP_NEAR]: "↓", [Feedback.SHARP_FAR]: "↓", [Feedback.COMPLETED]: "★", [Feedback.TRY_AGAIN]: "↺",
};

// Simulation: keys and on-screen buttons play the target this many cents away.
const SIM_KEYS = { " ": 3, ArrowUp: 35, ArrowDown: -35 };

const $ = (id) => document.getElementById(id);

export class GameScreen {
  /**
   * @param {{audio: {context: AudioContext|null, mic: any}, simulate: boolean,
   *   onBack: () => void, onFinished: (session: any) => void}} options
   */
  constructor({ audio, simulate, onBack, onFinished }) {
    this.audio = audio;
    this.simulate = simulate;
    this.onBack = onBack;
    this.onFinished = onFinished;
    this.staff = new Staff($("staff"));
    this.gauge = new Gauge($("gauge"));
    this.tracker = new PitchTracker(44_100);
    this.session = null;
    this.settings = null;
    this._frame = 0;
    this._running = false;

    $("back").addEventListener("click", () => this.onBack());
    $("listen").addEventListener("click", () => this._playReference());
    $("sim-pad").hidden = !simulate;
    if (simulate) this._bindSimulation();
  }

  start(session, settings, caption) {
    this.session = session;
    $("caption").textContent = caption;
    $("staff-caption").textContent = `Written pitch · ${session.profile.name}`;
    $("hold-caption").textContent = `Hold for ${session.holdSeconds} seconds`;
    this.applySettings(settings);
    this._celebrateUntil = this._tryAgainUntil = this._listenUntil = 0;
    this._lastFraction = 0;
    this._feedback = null;
    this._feedbackSince = 0;
    this.tracker.reset();
    this._showTarget();
    this._showFeedback(Feedback.SILENCE, 0);
    this.staff.setState(0, false, true);
    this.gauge.setReading(null, Zone.IDLE);
    $("feedback-info").textContent = "";
    this._run();
  }

  stop() {
    this._running = false;
    cancelAnimationFrame(this._frame);
    if (this.simulate) this.audio.mic.frequencyHz = null;
  }

  pause() {
    this.stop();
  }

  /** Continue after a pause; the interrupted hold starts again from zero (no miss). */
  resume() {
    if (!this.session || this.session.finished || this._running) return;
    this.session.restartHold();
    this.tracker.reset();
    this._run();
  }

  get active() {
    return this._running;
  }

  /** FR-21: tolerance changes apply immediately to the running session. */
  applySettings(settings) {
    this.settings = settings;
    this.tracker.setSensitivity(settings.micSensitivity);
    this.gauge.setTolerance(settings.toleranceCents);
    if (this.session) this.session.toleranceCents = settings.toleranceCents;
  }

  _run() {
    this._running = true;
    const loop = () => {
      if (!this._running) return;
      this._tick(performance.now() / 1000);
      this._frame = requestAnimationFrame(loop);
    };
    this._frame = requestAnimationFrame(loop);
  }

  _showTarget() {
    const note = this.session.targetNote;
    $("note-label").textContent = note.label;
    this.staff.setNote(note);
    renderScore($("score"), this.session.points, this.session.goal);
  }

  _showFeedback(feedback, now) {
    if (feedback === this._feedback) return;
    const steadyFor = now - this._feedbackSince;
    if (this._feedback !== null && feedback !== Feedback.IN_TUNE && steadyFor < MIN_MESSAGE_SECONDS) return;
    this._feedback = feedback;
    this._feedbackSince = now;
    $("feedback").dataset.feedback = feedback;
    $("feedback-icon").textContent = ICONS[feedback];
    $("feedback-text").textContent = message(feedback, this.session.targetNote);
  }

  _playReference() {
    if (!this.session || this.session.finished) return;
    const duration = playReference(this.audio.context, this.session.targetFrequency, this.settings.volume);
    this._listenUntil = performance.now() / 1000 + duration + LISTEN_TAIL_SECONDS;
    this._feedback = null;
    $("feedback").dataset.feedback = Feedback.SILENCE;
    $("feedback-icon").textContent = "♪";
    $("feedback-text").textContent = "Listen… then play it back!";
    $("feedback-info").textContent = "";
  }

  _tick(now) {
    const session = this.session;
    const window = this.audio.mic.readWindow();
    if (!window) return;
    if (this._listenUntil) {
      if (now < this._listenUntil) return; // The reference note is playing; don't score what the mic hears.
      this._listenUntil = 0;
      session.restartHold();
      this.tracker.reset();
    }
    this.tracker.setSampleRate(this.audio.mic.sampleRate);
    const frequency = this.tracker.update(window);
    const state = session.process(now, frequency);

    if (state.event === HoldEvent.COMPLETED) {
      playSuccess(this.audio.context, this.settings.volume);
      this._celebrateUntil = now + CELEBRATE_SECONDS;
      this._feedback = null; // Show the celebration right away, naming the right note.
      if (session.finished) {
        renderScore($("score"), session.points, session.goal);
        this.stop();
        setTimeout(() => this.onFinished(session), FINISH_DELAY_MS);
      } else {
        this._showTarget();
      }
    } else if (state.event === HoldEvent.MISSED && this._shouldCueRestart(session)) {
      this._tryAgainUntil = now + TRY_AGAIN_SECONDS;
      this._feedback = null;
    }
    this._lastFraction = state.holdFraction;

    let feedback = state.feedback;
    if (now < this._celebrateUntil) feedback = Feedback.COMPLETED;
    else if (now < this._tryAgainUntil && state.zone !== Zone.GREEN) feedback = Feedback.TRY_AGAIN;
    this._showFeedback(feedback, now);

    // While celebrating, show the completed ring and "+1", not the next hold already counting.
    const celebrating = now < this._celebrateUntil;
    const idle = state.zone === Zone.IDLE && state.holdFraction === 0 && !celebrating;
    this.staff.setState(celebrating ? 1 : state.holdFraction, state.zone === Zone.GREEN || celebrating, idle);
    this.gauge.setReading(state.cents, state.zone);
    $("feedback-info").textContent = celebrating ? "+1 ★" : this._infoText(state.zone, frequency, state.holdFraction);
  }

  _shouldCueRestart(session) {
    const lostSeconds = this._lastFraction * session.holdSeconds;
    return this.settings.holdMode === HoldMode.RESET && lostSeconds >= TRY_AGAIN_AFTER_SECONDS;
  }

  /** Hold time while in tune; otherwise which note the app hears, to guide the player. */
  _infoText(zone, frequency, fraction) {
    const total = this.session.holdSeconds;
    if (zone === Zone.GREEN || (fraction > 0 && frequency === null)) return `${(fraction * total).toFixed(1)} / ${total.toFixed(1)} s`;
    if (frequency === null) return "Listening…";
    return `Hearing ${midiLabel(nearestWrittenNote(frequency, this.session.profile).writtenMidi)}`;
  }

  _bindSimulation() {
    const play = (cents) => {
      if (this.session) this.audio.mic.frequencyHz = this.session.targetFrequency * 2 ** (cents / 1200);
    };
    const release = () => { this.audio.mic.frequencyHz = null; };
    window.addEventListener("keydown", (event) => {
      if (!this._running || !(event.key in SIM_KEYS)) return;
      event.preventDefault();
      if (!event.repeat) play(SIM_KEYS[event.key]);
    });
    window.addEventListener("keyup", (event) => {
      if (event.key in SIM_KEYS) release();
    });
    for (const button of document.querySelectorAll("#sim-pad [data-sim]")) {
      button.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        play(Number(button.dataset.sim));
      });
      for (const type of ["pointerup", "pointerleave", "pointercancel"]) button.addEventListener(type, release);
    }
  }
}
