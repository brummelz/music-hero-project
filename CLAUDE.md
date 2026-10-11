# CLAUDE.md

Guidance for working on Horn Hero (repo: music-hero-project), an offline desktop app that teaches young children French Horn intonation via microphone pitch detection.

## Source of truth

- Requirements: [docs/SPECIFICATIONS.md](docs/SPECIFICATIONS.md). Requirement IDs (`FR-*`, `NFR-*`) are the contract.
- Tests: [docs/TEST_CASES.md](docs/TEST_CASES.md) maps test cases to requirement IDs.
- If code and spec disagree, stop and flag it. Do not silently change behavior. Spec changes go in the docs first, then code.
- Reference requirement IDs in docstrings and test names (e.g. `test_fr08_dropout_within_grace`).

## Stack

- Python 3.11+ (pin the exact version in the README once chosen).
- UI: PySide6 (Qt 6) unless the spec/README says otherwise.
- Audio capture: `sounddevice`. Pitch detection: aubio or an in-house NumPy YIN, behind the `PitchDetector` interface below.
- Tests: `pytest`. Lint/format: `ruff` (lint + format). Types: `mypy` (strict on `core/`).
- Packaging: PyInstaller (`.exe`). Everything must work offline, with no network calls.

## Architecture

Keep a strict layering. Dependencies point inward only.

```
core/      pure logic: cents, transposition, hold timer, levels, scoring
audio/     microphone capture + pitch detectors (hardware boundary)
storage/   local persistence (progress, settings)
ui/        screens and widgets (Qt)
main.py    composition root: wires the layers together
web/       browser version (spec §6.1), same layering in JavaScript:
           web/js/core (pure, like core/), web/js/audio, web/js/storage, web/js/ui, web/js/app.js
```

- `web/js/core` follows the same rules as `core/`: no DOM, no Web Audio, no storage, time passed in. Keep it a faithful port of `core/`; when a rule changes, change both and their tests.
- Web tests: `npm test` (runs `node --test "web/tests/*.test.js"`, no npm dependencies). `web/data/levels.json` must match `resources/levels.json` (a test checks this).

Rules:

- `core/` imports only the standard library. No Qt, no NumPy-audio, no file or device I/O. It must be fully testable without audio hardware (spec §6).
- `core/` takes time as an input (timestamps or `dt`) and never reads the clock itself, so the hold-timer state machine is deterministic in tests.
- `audio/` exposes a small interface (e.g. `PitchDetector.detect(frame) -> PitchResult | None` with frequency and confidence). The UI and core never touch the microphone API directly. Provide a fake/synthetic source for tests.
- Audio runs on its own thread/callback. Never block it, never touch Qt widgets from it. Hand results to the UI thread via Qt signals or a thread-safe queue.
- `ui/` renders state and forwards input. No game rules in widgets.
- Data over code: the level table, tolerance presets, and instrument profiles are configuration (spec §4.1), not hard-coded branches.

## Domain rules to never get wrong

- The app **displays written pitch** and **analyzes sounding pitch**. Keep the two distinct in names: `written_midi`, `sounding_midi`, `sounding_hz`.
- Horn in F offset is **−7 semitones**. Transposition is a profile value (FR-01), never a literal in game logic.
- `f = 440 · 2^((m − 69 + offset) / 12)` (FR-19). `cents = 1200 · log2(f / f_t)` (FR-02). Guard against `f <= 0`.
- Octave-off notes are wrong, not Green. No octave folding.
- Tolerance is a user setting (FR-21, default ±15 cents). Never hard-code 15.
- Hold: 3.0 s continuous, reset on leaving Green, 150 ms grace period (FR-06..FR-08). Constants live in one config module.

## Coding standards

- Type-annotate all public functions. Prefer `dataclass(frozen=True)` and `Enum` for state and value objects. Avoid mutable globals.
- Small, single-purpose functions and modules. Prefer composition over inheritance.
- Names describe intent and units: `tolerance_cents`, `grace_ms`, `hold_seconds`. No magic numbers; name them as constants.
- Raise specific exceptions on invalid input at boundaries (bad frequency, unknown level). Do not use bare `except:` or swallow errors. Log with the `logging` module, not `print`.
- Comments explain why, not what. Docstrings for public APIs, with the requirement ID where relevant.
- No dead code, no commented-out code, no speculative abstractions. Build what the spec asks for.
- Use `pathlib`, not string paths. Store user data under `%APPDATA%` (via a helper), never next to the executable. Be PyInstaller-safe: resolve bundled resources through a helper that handles `sys._MEIPASS`.

## Testing

- Write tests alongside the code, for `core/` first (TDD where practical). Aim for ~100% branch coverage of `core/`.
- Mirror the layout: `tests/core/`, `tests/audio/`, `tests/storage/`. Every test case in TEST_CASES.md should map to a real test.
- Pitch detection tests use synthetic sine/harmonic signals and check ±5 cents (NFR-02). Latency (NFR-01) is validated with a benchmark or manual protocol, not flaky unit tests.
- No tests depend on a real microphone, display, wall-clock time, or network.
- Persistence tests use `tmp_path`.

## Workflow

- Run before finishing any change: `ruff check .`, `ruff format --check .`, `mypy core`, `pytest`.
- Keep dependencies minimal and pinned in `requirements.txt` (dev tools in `requirements-dev.txt`). Justify any new dependency, and check that it installs on Windows without a compiler and bundles cleanly with PyInstaller.
- Small, focused commits with imperative messages (e.g. `Add hold-timer state machine`). One logical change per commit. Do not commit `venv/`, build output, or user data.
- Don't commit or push unless asked.
- When requirements are ambiguous, check the "Open" questions in spec §8 and ask rather than guess.

## Child UX review (required when testing the app)

- Whenever you test, run, or change anything the child sees (screens, widgets, theme, feedback, messages, sounds), use the `child-ux-reviewer` sub agent ([.claude/agents/child-ux-reviewer.md](.claude/agents/child-ux-reviewer.md)) before finishing.
- It reviews as a child of a given age band: 3-5, 6-8, 9-12, 12-15. Pass the bands explicitly; if the change is not age-specific, review all four (run them in parallel).
- Give it the thing to review: the running app or screenshots, the mockups in `docs/design/`, or the changed files in `ui/`.
- Reports are written to `docs/ux-reviews/`. Fix every Blocker. Triage Major and Minor findings with the user.
- If a finding conflicts with the spec, flag it and update the docs first. Do not change behavior silently.
- Automated tests do not replace this review, and this review does not replace the tests in "Workflow".

## Child-facing UX constraints

- No failure state: the child can retry indefinitely (FR-16). Never show punishing or negative messaging.
- Feedback must feel immediate (NFR-01, ≤100 ms). Avoid heavy work on the UI or audio threads.
- Use large, high-contrast visuals. Don't rely on color alone to convey flat/sharp/in tune; pair color with position or icons.
- Encouragement text is short and positive (FR-18).
