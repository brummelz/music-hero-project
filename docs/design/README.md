# Design mockups

UI mockups for Horn Hero, exported from the Claude Design canvas: https://claude.ai/artifact/SnV8qBB9Er1iigJRjt6B8v (private; the canvas is the editable source).

| File | Screen |
|------|--------|
| `Splash-Loading.dc.html` | Cover shown while the app loads |
| `Splash-Start.dc.html` | Cover / initial page with Start Game |
| `Home.dc.html` | Mode selection (Practice / Adventure), Screen 1 in the spec |
| `Main.dc.html` | Practice: in tune, holding (hold ring filling) |
| `Practice-Flat.dc.html` | Practice: flat |
| `Practice-Sharp.dc.html` | Practice: sharp |
| `Practice-Silence.dc.html` | Practice: waiting for sound (FR-05) |
| `Level-Challenge.dc.html` | Level Challenge, prompt 4 of 6 |
| `Level-Complete.dc.html` | Level complete with star rating (FR-17, FR-23) |

`canvas.json` holds the canvas layout. `assets/cover.jpg` is the cover illustration.

## Notes

- The `.dc.html` files are Design Component sources. They render in the Claude Design canvas (they need its `support.js` runtime), not directly in a browser. Treat them as a visual reference, not app code.
- The canvas mockups use a 1100×720 window, with fonts Fredoka (headings) and Nunito (body).
- Palette: ground `#E9F3FF`, ink `#14213D`, muted `#4A5A78`, accent indigo `#4338CA`, in tune green `#3DD68C`, near yellow `#FFC93C`, far red `#FF6B6B`.
- Tuner gauge spans ±50 cents with the green zone at the ±15 cent default; this range is an assumption, not in the spec.
- Not designed yet: Settings (FR-21, FR-25) and the Practice 10/10 summary.
