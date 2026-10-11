# Horn Hero

An offline desktop app that helps young children learn to play the French Horn in tune. It listens through the microphone, shows whether the note is flat, in tune or sharp, and rewards holding the note steady for 3 seconds.

- Requirements: [docs/SPECIFICATIONS.md](docs/SPECIFICATIONS.md)
- Test cases: [docs/TEST_CASES.md](docs/TEST_CASES.md)
- UI mockups: [docs/design/](docs/design/)

## Setup

Requires Python 3.12 (developed on 3.12.15). With [uv](https://docs.astral.sh/uv/):

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv -r requirements-dev.txt
```

Or with plain pip:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Running

```powershell
.\.venv\Scripts\python main.py              # uses the microphone
.\.venv\Scripts\python main.py --simulate   # no instrument needed
```

In simulation mode, on the gameplay screen hold **Space** to play the target note in tune, **↑** to play sharp and **↓** to play flat.

To test with the microphone but without a horn, sing, whistle or use a tone generator at the *sounding* pitch. On Horn in F, written C4 (Do) sounds F3, 174.6 Hz.

During play, the speaker button next to the note plays the target note. The microphone ignores it while it plays.

### Microphone troubleshooting

Open Settings by **holding** the gear button for a second. The **Microphone** section lets you pick the input and has a live test, which shows the input level and the note it hears (name, Hz and cents). "In use" shows which input is actually open.

- **Instrument mode vs voice mode:** most laptop microphone arrays run Windows noise suppression and echo cancellation. These remove a steady note within a fraction of a second while letting speech through. The list therefore offers:
  - *Instrument mode, unfiltered*: the driver's raw signal (Windows WDM-KS pins). These are **exclusive**, so if Windows or another app (Teams, a browser) is using a pin, it can't be opened. Only some drivers expose them.
  - *Instrument mode, Windows raw*: Windows' official "raw" capture, which asks the driver to switch processing off. It works on most Windows 10/11 machines.
  - *Voice mode, Windows filters*: the normal Windows path.
  - *Automatic* (the default) tries every unfiltered pin of your default microphone, then Windows raw. It falls back to the filtered default only if none works, and Settings then shows a warning.
- **Level bar stays at "Quiet" while you play:** raise *Sensitivity*, check the mic is not muted, and check that Windows lets desktop apps use the microphone (Settings > Privacy & security > Microphone).
- **The note shows but the game says "flat"/"sharp" by a lot:** compare the "Hearing" note with the target. On Horn in F the app expects the horn's *sounding* pitch, a fifth below written. A piano, harmonica or voice playing written C4 will read as G4 (SOL / G4), not C4.

Progress and settings are saved in `%APPDATA%\HornHero\profile.json`.

## Checks

Run before committing:

```powershell
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
.\.venv\Scripts\mypy
.\.venv\Scripts\python -m pytest
```

## Project layout

```
core/       pure game logic (notes, transposition, tuning, hold timer, levels, sessions, profile)
audio/      microphone capture, YIN pitch detector, keyboard simulator, sound effects
storage/    profile persistence (JSON) and resource paths
ui/         PySide6 screens and widgets
resources/  level table (levels.json) and cover image
tests/      pytest suites mirroring core/, audio/, storage/
main.py     entry point
```

## Building an .exe

```powershell
uv pip install --python .venv pyinstaller
.\.venv\Scripts\pyinstaller --noconfirm --windowed --name HornHero --add-data "resources;resources" main.py
```

The app is in `dist\HornHero\HornHero.exe`.
