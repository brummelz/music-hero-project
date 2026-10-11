// Microphone capture in the browser (spec §6.1).
// Voice processing (echo cancellation, noise suppression, auto gain) removes sustained instrument
// tones, so it is switched off. Some systems still filter at the OS level; the Settings live test
// shows that, and `filtered` reports what the browser actually applied.

export const WINDOW_SIZE = 2048;

const RAW_AUDIO = { echoCancellation: false, noiseSuppression: false, autoGainControl: false };

export class Microphone {
  /** @param {AudioContext} context */
  constructor(context) {
    this.context = context;
    this._stream = null;
    this._source = null;
    this._analyser = null;
    this._window = new Float32Array(WINDOW_SIZE);
  }

  get sampleRate() {
    return this.context.sampleRate;
  }

  get running() {
    return this._stream !== null;
  }

  /** Ask for the microphone (needs a user gesture the first time). Throws if refused. */
  async start(deviceId = "") {
    this.stop();
    const audio = { ...RAW_AUDIO, channelCount: 1 };
    if (deviceId) audio.deviceId = { exact: deviceId };
    try {
      this._stream = await navigator.mediaDevices.getUserMedia({ audio });
    } catch (error) {
      if (!deviceId || error.name !== "OverconstrainedError") throw error;
      this._stream = await navigator.mediaDevices.getUserMedia({ audio: { ...RAW_AUDIO, channelCount: 1 } });
    }
    await this.context.resume();
    this._source = this.context.createMediaStreamSource(this._stream);
    this._analyser = this.context.createAnalyser();
    this._analyser.fftSize = WINDOW_SIZE;
    this._source.connect(this._analyser);
  }

  stop() {
    this._source?.disconnect();
    this._stream?.getTracks().forEach((track) => track.stop());
    this._stream = this._source = this._analyser = null;
  }

  /** The latest analysis window (shared buffer; copy it if you keep it). */
  readWindow() {
    if (!this._analyser) return null;
    this._analyser.getFloatTimeDomainData(this._window);
    return this._window;
  }

  get track() {
    return this._stream?.getAudioTracks()[0] ?? null;
  }

  get label() {
    return this.track?.label || "Microphone";
  }

  get deviceId() {
    return this.track?.getSettings().deviceId ?? "";
  }

  /** True if the browser left any voice processing on (it may not honour the request). */
  get filtered() {
    const settings = this.track?.getSettings() ?? {};
    return Boolean(settings.echoCancellation || settings.noiseSuppression || settings.autoGainControl);
  }
}

/** Microphones the browser offers (names appear only after permission was given). */
export async function listMicrophones() {
  if (!navigator.mediaDevices?.enumerateDevices) return [];
  const devices = await navigator.mediaDevices.enumerateDevices();
  return devices
    .filter((d) => d.kind === "audioinput" && d.deviceId && d.deviceId !== "default" && d.deviceId !== "communications")
    .map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Microphone ${i + 1}` }));
}
