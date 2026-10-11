// Settings for a grown-up: playing, microphone with a live test, sound, progress (FR-21, FR-25).
// Port of ui/settings_dialog.py.

import { listMicrophones } from "../audio/mic.js";
import { PitchTracker } from "../audio/tracker.js";
import { HoldMode } from "../core/holdTimer.js";
import { midiLabel } from "../core/notes.js";
import { makeSettings } from "../core/profile.js";
import { PROFILES, nearestWrittenNote, profileByName } from "../core/transpose.js";
import { TOLERANCE_PRESETS } from "../core/tuning.js";

const CUSTOM = "Custom";
const METER_FLOOR_DB = -70;
const $ = (id) => document.getElementById(id);

function option(value, label) {
  const node = document.createElement("option");
  node.value = value;
  node.textContent = label;
  return node;
}

/** Map RMS to 0..100 on a dB scale so quiet sounds still move the bar. */
function meterPercent(level) {
  if (level <= 0) return 0;
  return Math.max(0, Math.min(1, (20 * Math.log10(level) - METER_FLOOR_DB) / -METER_FLOOR_DB)) * 100;
}

export class SettingsDialog {
  /**
   * @param {{audio: {mic: any}, simulate: boolean, onChange: (settings: any) => void,
   *   onReset: () => void, onClose: () => void}} options
   */
  constructor({ audio, simulate, onChange, onReset, onClose }) {
    this.audio = audio;
    this.simulate = simulate;
    this.onChange = onChange;
    this.dialog = $("settings");
    this.tracker = new PitchTracker(44_100);
    this._frame = 0;

    for (const [name, cents] of Object.entries(TOLERANCE_PRESETS)) $("set-preset").append(option(name, `${name} (±${cents} cents)`));
    $("set-preset").append(option(CUSTOM, CUSTOM));
    for (const profile of PROFILES) $("set-instrument").append(option(profile.name, profile.name));

    for (const id of ["set-preset", "set-custom", "set-instrument", "set-pause", "set-mic", "set-sensitivity", "set-volume"]) {
      $(id).addEventListener(id === "set-sensitivity" || id === "set-volume" ? "input" : "change", () => this._changed());
    }
    $("set-reset").addEventListener("click", () => {
      $("set-reset").hidden = true;
      $("set-reset-confirm").hidden = false;
    });
    $("set-reset-no").addEventListener("click", () => this._hideResetConfirm());
    $("set-reset-yes").addEventListener("click", () => {
      onReset();
      this._hideResetConfirm();
    });
    this.dialog.addEventListener("close", () => {
      cancelAnimationFrame(this._frame);
      this._hideResetConfirm();
      onClose();
    });
  }

  async open(settings) {
    this.settings = settings;
    const preset = Object.keys(TOLERANCE_PRESETS).find((name) => TOLERANCE_PRESETS[name] === settings.toleranceCents) ?? CUSTOM;
    $("set-preset").value = preset;
    $("set-custom").value = String(Math.round(settings.toleranceCents));
    $("set-custom").disabled = preset !== CUSTOM;
    $("set-instrument").value = settings.instrument;
    $("set-pause").checked = settings.holdMode === HoldMode.PAUSE;
    $("set-sensitivity").value = String(Math.round(settings.micSensitivity * 100));
    $("set-volume").value = String(Math.round(settings.volume * 100));
    await this._fillMicrophones(settings.inputDevice);
    this.tracker.setSensitivity(settings.micSensitivity);
    this.tracker.reset();
    this.dialog.showModal();
    this._runTest();
  }

  async _fillMicrophones(selected) {
    const select = $("set-mic");
    if (this.simulate) {
      select.replaceChildren(option("", "Keyboard simulation (no microphone)"));
      select.disabled = true;
      return;
    }
    const microphones = await listMicrophones();
    select.replaceChildren(option("", "Default microphone"), ...microphones.map((m) => option(m.deviceId, m.label)));
    select.value = microphones.some((m) => m.deviceId === selected) ? selected : "";
  }

  _changed() {
    const preset = $("set-preset").value;
    const custom = preset === CUSTOM;
    $("set-custom").disabled = !custom;
    let tolerance = custom ? Number($("set-custom").value) : TOLERANCE_PRESETS[preset];
    if (custom) {
      tolerance = Math.max(5, Math.min(50, Math.round(tolerance || 15))); // TC-27: clamp out-of-range input
      $("set-custom").value = String(tolerance);
    } else {
      $("set-custom").value = String(tolerance);
    }
    this.settings = makeSettings({
      ...this.settings,
      toleranceCents: tolerance,
      instrument: $("set-instrument").value,
      holdMode: $("set-pause").checked ? HoldMode.PAUSE : HoldMode.RESET,
      inputDevice: this.simulate ? "" : $("set-mic").value,
      micSensitivity: Number($("set-sensitivity").value) / 100,
      volume: Number($("set-volume").value) / 100,
    });
    this.tracker.setSensitivity(this.settings.micSensitivity);
    this.tracker.reset();
    this.onChange(this.settings);
  }

  _hideResetConfirm() {
    $("set-reset").hidden = false;
    $("set-reset-confirm").hidden = true;
  }

  _runTest() {
    const loop = () => {
      if (!this.dialog.open) return;
      this._updateTest();
      this._frame = requestAnimationFrame(loop);
    };
    this._frame = requestAnimationFrame(loop);
  }

  _updateTest() {
    const mic = this.audio.mic;
    $("set-in-use").textContent = `In use: ${mic.label}`;
    $("set-filtered").hidden = !mic.filtered;
    const window = mic.readWindow();
    if (!window) {
      $("set-heard").textContent = "Microphone not available";
      return;
    }
    this.tracker.setSampleRate(mic.sampleRate);
    const frequency = this.tracker.update(window);
    $("set-meter").style.width = `${meterPercent(this.tracker.lastLevel)}%`;
    $("set-gate").textContent = this.tracker.lastLevel >= this.tracker.gateRms ? "Sound ✓" : "Quiet";
    if (frequency === null) {
      $("set-heard").textContent = "—";
      return;
    }
    const { writtenMidi, cents } = nearestWrittenNote(frequency, profileByName(this.settings.instrument));
    const sign = cents >= 0 ? "+" : "−";
    $("set-heard").textContent = `${midiLabel(writtenMidi)}   ${frequency.toFixed(1)} Hz   ${sign}${Math.abs(cents).toFixed(0)} cents`;
  }
}
