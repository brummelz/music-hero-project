# Functional Specifications: Horn Hero (working title)

Status: Draft v0.1. Requirement IDs (`FR-*`, `NFR-*`) are referenced by [TEST_CASES.md](TEST_CASES.md).

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
  - **Green (in tune):** |cents| ≤ tolerance. Default tolerance ±15 cents, configurable.
  - **Flat side:** cents < −tolerance (yellow near, red far).
  - **Sharp side:** cents > +tolerance (yellow near, red far).
- **FR-04** The needle position updates in real time (see NFR-01) and is clamped to the gauge range.
- **FR-05** When no pitched sound is detected (silence, noise, low confidence), the needle shows an idle state and the hold timer does not advance.

### 3.2 Hold timer and scoring

- **FR-06** While the pitch stays in the Green zone, a progress ring fills over **3.0 continuous seconds** (configurable constant).
- **FR-07** If the pitch leaves the Green zone before completion, the timer **resets to 0** (default). A configurable "pause" behavior is supported as an alternative.
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

- **FR-15** Levels have increasing difficulty. **Level 1:** Do, Ré, Mi (written C4, D4, E4). **Level 2+:** progressively adds Fa, Sol, La, and so on (full level table to be defined; see §8).
- **FR-16** The game prompts a note from the current level's note set; the child holds it for 3 s; the game awards points/stars and moves to the next note in the sequence.
- **FR-17** Completing a level unlocks the next one and records a star rating (rating rules: see §8).

## 5. Screens

### Screen 1: Mode and instrument selection

- **Header:** logo, current profile, total stars/score, active instrument indicator (Horn in F).
- **Mode cards:** Practice (pick Do, Ré, Mi, ...) and Adventure (level map with unlocked levels and star ratings).
- **Settings:** microphone sensitivity calibration, transposition profile toggle, audio volume.

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
- **NFR-01** End-to-end latency from sound to gauge update should be ≤ 100 ms (target; to be validated).
- **NFR-02** Detection should be accurate to within ±5 cents for clean sustained tones in the horn's range.

## 7. Reference pitch table (Horn in F)

| Written | Solfège | Written MIDI | Sounding | Sounding MIDI | Frequency (Hz) |
|---------|---------|--------------|----------|---------------|----------------|
| C4 | Do | 60 | F3 | 53 | 174.61 |
| D4 | Ré | 62 | G3 | 55 | 196.00 |
| E4 | Mi | 64 | A3 | 57 | 220.00 |
| C5 | Do | 72 | F4 | 65 | 349.23 |

## 8. Open questions

1. Level 2+ note sets and the star rating rules (e.g. by time or number of attempts) are not yet defined.
2. Default tolerance is ±15 cents; is this too strict or too loose for beginners (perhaps wider at Level 1)?
3. Reset vs. pause default on pitch loss (this spec defaults to reset, matching TC-04).
4. Written C4 is a very low note on horn and hard for beginners; confirm the starting range is intended.
5. Profiles: a single local profile or multiple children per install?
6. Octave errors: should a detected octave-off note count as wrong? (Assumed: wrong.)
