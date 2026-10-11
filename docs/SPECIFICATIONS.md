# Functional Specifications: Horn Hero (working title)

Status: Draft v0.2. Requirement IDs (`FR-*`, `NFR-*`) are referenced by [TEST_CASES.md](TEST_CASES.md).

## 1. Overview

Horn Hero is an offline, educational desktop app for young children learning a musical instrument, primarily the French Horn. It detects the pitch of the played note through the microphone, gives immediate visual feedback on intonation, and rewards steady note production.

## 2. Audience and instrument

- **Audience:** young children learning music / French Horn.
- **Primary instrument:** French Horn in F, a transposing instrument that sounds a perfect 5th (7 semitones) below written pitch.
- The app **displays written pitch** and **analyzes sounding (concert) pitch**.
- **FR-01** Transposition is a configurable profile (semitone offset), so other instruments (C, B♭, E♭, ...) can be added without changes to the detection or game logic. Horn in F = −7 semitones.

## 3. Core mechanics

### 3.1 Tuner and feedback

- **FR-02** The system converts detected fundamental frequency `f` to cents relative to the target frequency `f_t`: `cents = 1200 · log2(f / f_t)`.
- **FR-03** The tuner bar has three zones:
  - **Green (in tune):** |cents| ≤ tolerance. The tolerance is a user setting (FR-21); default ±15 cents.
  - **Flat side:** cents < −tolerance (yellow near, red far).
  - **Sharp side:** cents > +tolerance (yellow near, red far).
- **FR-04** The needle position updates in real time (see NFR-01) and is clamped to the gauge range.
- **FR-05** When no pitched sound is detected (silence, noise, low confidence), the needle shows an idle state and the hold timer does not advance.

### 3.2 Hold timer and scoring

- **FR-06** The player must hold the **correct note** (correct octave) inside the Green zone for **3.0 continuous seconds** (configurable constant). The counter **starts as soon as the pitch enters the Green zone**, with no extra delay or trigger, and the progress ring fills (with the elapsed time visible) for as long as the pitch stays in range.
- **FR-07** If the pitch leaves the Green zone before completion, the timer **resets to 0** (default, shown as **Hard**). The alternative **pause** behavior (shown as **Easy**) keeps the progress and resumes it when the pitch returns. The child or a grown-up chooses it with the Easy / Hard switch on Screen 1; the choice is a persisted setting (FR-20).
- **FR-08** Brief detection dropouts shorter than a grace period (default 150 ms) do not count as leaving the zone, so momentary detector glitches don't frustrate the child.
- **FR-09** Completing the hold awards **1 point**, plays a sound effect, and resets the timer for the next attempt.

### 3.3 Notation and naming

- **FR-10** Notes are shown on a treble staff (grand staff where needed) as **written** pitch.
- **FR-11** Each note is labelled with both the Italian solfège name (Do, Ré, Mi, Fa, Sol, La, Si) and the letter name (C, D, E, F, G, A, B).

## 4. Game modes

### Mode 1: Single Note Practice

- **FR-12** The user selects one target note (initially Do, Ré, Mi: written C4, D4, E4).
- **FR-13** The staff shows the target note for the whole session.
- **FR-14** Each completed hold awards 1 point; the session completes at **10 points**, followed by a celebration/summary.

### Mode 2: Level Challenge

- **FR-15** Levels have increasing difficulty and use the note sets in §4.1.
- **FR-16** A level consists of **6 prompts**. Prompts are drawn from the level's note set so that every note appears at least once, with no note repeated twice in a row. For each prompt the child holds the note for 3 s (1 point), then the game moves to the next prompt. A level is complete after 6 successful holds. There is no failure state: the child can keep trying a prompt indefinitely.
- **FR-17** Completing a level unlocks the next one and records a star rating (§4.2). Only the best rating per level is kept.

### 4.1 Level table (Horn in F)

Notes are written pitch; sounding frequency is given for Horn in F (FR-19).

| Level | Theme | Written notes (solfège) | Sounding frequencies (Hz) |
|-------|-------|-------------------------|---------------------------|
| 1 | First notes | C4 Do, D4 Ré, E4 Mi | 174.61, 196.00, 220.00 |
| 2 | Five-note scale | C4 Do, D4 Ré, E4 Mi, F4 Fa, G4 Sol | 174.61, 196.00, 220.00, 233.08, 261.63 |
| 3 | Full octave | C4 Do, D4 Ré, E4 Mi, F4 Fa, G4 Sol, A4 La, B4 Si, C5 Do | 174.61, 196.00, 220.00, 233.08, 261.63, 293.66, 329.63, 349.23 |
| 4 | Upper register | C5 Do, D5 Ré, E5 Mi, F5 Fa, G5 Sol | 349.23, 392.00, 440.00, 466.16, 523.25 |
| 5 | Leaps | C4 Do, G4 Sol, C5 Do, E5 Mi, G5 Sol | 174.61, 261.63, 349.23, 440.00, 523.25 |

Levels beyond 5 are out of scope for v1. The level table is data (configuration), not code, so it can be extended. Written notes stay the same across transposition profiles; sounding frequencies follow FR-19.

### 4.2 Star rating (assumptions)

- **FR-22** A *miss* is counted each time the hold timer is reset by leaving the Green zone after it has started (a reset per FR-07/FR-08). Silence before playing does not count.
- **FR-23** Stars for a completed level, based on total misses during the level: **3 stars** for 0–2 misses, **2 stars** for 3–6 misses, **1 star** for 7 or more. Completing a level always gives at least 1 star. In pause mode (FR-07), a miss is counted the first time the timer is paused within a prompt.
- **FR-24** Practice Mode awards no stars; it only counts points toward the 10-point goal. The header's total stars is the sum of each level's best stars (max 15 for 5 levels).

## 5. Screens

### Screen 1: Mode and instrument selection

- **Header:** logo, total stars/score, active instrument indicator (Horn in F).
- **Mode cards:** Practice (pick Do, Ré, Mi, ...) and Adventure (level map with unlocked levels and star ratings).
- **Easy / Hard switch (FR-07):** Easy keeps hold progress when the note slips, Hard restarts the hold. Default Hard.
- **Settings:** microphone sensitivity calibration, transposition profile toggle, audio volume, tuning tolerance (FR-21), reset progress (FR-25).

### Screen 2: Gameplay

- **Top bar:** back button, score (e.g. `7 / 10`), target note name (`DO / C`).
- **Center:** interactive staff showing the target note, dynamic tuner gauge (Flat / In Tune / Sharp), and a hold ring around the note head filling over 3 s.
- **Bottom bar:** real-time encouragement text/emoji (e.g. "Almost there! Push a little higher!", "Great job!").
- **FR-18** Encouragement messages reflect state: flat, sharp, in tune/holding, completed, silence. Flat/sharp hints derive from the cents offset.

## 6. Technical requirements

- **Platform:** offline desktop app, packaged as `.exe` via PyInstaller. No network access needed.
- **Audio input:** live microphone capture (e.g. PyAudio).
- **Pitch detection:** real-time F0 extraction (e.g. aubio).
- **Processing modules** (kept pure and testable without audio hardware):
  - pitch ↔ cents conversion (FR-02),
  - transposition mapping written note → sounding frequency (FR-01, FR-19),
  - hold-timer state machine (FR-06..FR-09).
- **FR-19** Sounding frequency: `f = 440 · 2^((m − 69 + offset) / 12)`, where `m` is the written MIDI note number and `offset` the profile semitone offset (Horn in F: −7).
- **FR-20 (Storage)** User progress, unlocked levels, stars, and calibration settings are stored locally and persist across restarts.
- **FR-21 (Tolerance setting)** The tuning tolerance is a persisted setting (FR-20). Presets: **Easy ±25 cents, Normal ±15 cents (default), Strict ±10 cents**, plus a custom value from ±5 to ±50 cents. A change applies immediately to the Green zone and hold-timer logic in both game modes.
- **FR-25 (Profile)** The app has a **single local profile** per install (no profile selection or login). Progress, stars, and settings belong to it. A "reset progress" action in Settings clears progress and stars after a confirmation.
- **NFR-01** End-to-end latency from sound to gauge update should be ≤ 100 ms (target; to be validated).
- **NFR-02** Detection should be accurate to within ±5 cents for clean sustained tones in the horn's range.

### 6.1 Web version (`web/`)

A browser version runs the same rules (FR-01 to FR-25) on computers, tablets and phones. The desktop `.exe` stays the primary target.

- **Platform:** static HTML + JavaScript in `web/`, published with GitHub Pages. It is installable as a Progressive Web App and works offline after the first visit.
- **Audio input:** `getUserMedia` with echo cancellation, noise suppression and automatic gain control turned off, because voice processing removes sustained instrument tones. The user can choose the microphone in Settings.
- **Storage (FR-20):** the single local profile (FR-25) is kept in the browser's `localStorage`, using the same JSON shape as the desktop app.
- **Start:** browsers allow audio only after a user action, so the cover's "Start Game!" button also asks for microphone permission. If permission is refused, the app explains how to allow it and offers a retry. It never shows a failure state (FR-16).

## 7. Reference pitch table (Horn in F)

| Written | Solfège | Written MIDI | Sounding | Sounding MIDI | Frequency (Hz) |
|---------|---------|--------------|----------|---------------|----------------|
| C4 | Do | 60 | F3 | 53 | 174.61 |
| D4 | Ré | 62 | G3 | 55 | 196.00 |
| E4 | Mi | 64 | A3 | 57 | 220.00 |
| C5 | Do | 72 | F4 | 65 | 349.23 |

## 8. Decisions and remaining open questions

Decided:

- Level 2+ note sets: §4.1.
- Star rating: miss-based, §4.2 (assumptions, tunable after playtesting).
- Tolerance is a user setting (FR-21), default ±15 cents.
- Written C4 stays as the lowest starting note for now.
- Octave-off notes count as wrong (not Green).
- Single profile per install (FR-25).
- Pause-on-loss (FR-07) is exposed on Screen 1 as an Easy / Hard switch, not hidden in Settings.

Open:

1. Star thresholds (0–2 / 3–6 / 7+ misses) and the 6-prompt level length are assumptions to validate with real children.
2. Levels 4 and 5 reach written G5, which is demanding for beginners; confirm or lower the range.
