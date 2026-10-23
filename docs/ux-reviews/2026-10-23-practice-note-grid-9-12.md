# Child UX review: ages 9-12
Reviewed: Home screen Practice card, 7-note 4+3 grid (ui/home_screen.py `_build_practice_card`, ui/theme.py `QPushButton#note`, web/css/app.css `.note-choices` / `.note-choice` and phone block ~line 404, web/js/ui/screens.js HomeScreen), 2026-10-23
Evidence limits: App not run, no screenshots. Layout judgements come from code and CSS only, so sizes below are estimates (unverified). docs/design/Home.dc.html still shows the old 3-note card (it has no Sol/La/Si), so the mockup does not match the new layout.

## Age 9-12
**Verdict:** A confident reader gets what they wanted: all seven notes, in scale order, one tap each. The grid is easy to read. The risks are the last row looking unfinished, tight columns inside the narrow card, and a selected state that is only partly visible on desktop.

**What works**
- All 7 natural notes (FR-12) are choosable. The child can practise the exact note their teacher set, with no "Do/Ré/Mi only" limit.
- Each button shows the solfège name large and the letter small (FR-11), so a child who learned either system recognises it.
- Order Do to Si reads like a scale and matches what they know.
- Buttons are big: 100px min-height on desktop, 84-120px on web. Plenty for mouse or touch.
- Web: the selected note gets a check badge as well as a colour change, so selection is not colour alone. The 4-px border plus tinted fill is also strong.
- The hint "Hold the note steady for 3 seconds to score a point." is short and plain, and "Start practice" stays one obvious next action.

**Problems**
1. [Major] Home, Practice card (desktop Qt) - "Which one did I pick?" The `:checked` style is only a border colour and a pale fill (ACCENT vs BORDER, ACCENT_SOFT vs white). There is no check badge like the web has. With 7 similar white tiles, a child with a horn in their hands, or a colour-blind child, may not see the choice. Fix: add a check mark or thicker border on checked tiles in Qt, matching `.note-choice[aria-checked="true"]::after` on the web. Verify contrast of ACCENT_SOFT vs white (unverified).
2. [Major] Home, Practice card (web, narrow widths) - "The words are squashed or cut off." Four columns inside a card as narrow as 340px, minus padding and 3 gaps of 12px, gives about 65-70px per tile. The solfège font is clamp(1.8rem, 4vw, 2.7rem). "Sol" in the display font at 2.1-2.7rem may overflow or touch the border, and the 22px badge overlaps the text (unverified). Fix: check at 340px and 360px phone widths. Reduce the font or the gap, or let the grid drop to 3 or 4 columns per container width, so "Sol" and "Fa" never clip. Add no hard-coded sizes beyond the existing clamp pattern.
3. [Minor] Home, Practice card - "Why is the bottom row short? Is there a missing note?" 4+3 leaves an empty slot after Si, which can look like a hidden eighth note or a bug. Fix: let the three bottom tiles centre, or span evenly. Do not add an 8th (high Do) tile without a spec change (FR-12 stops at B4).
4. [Minor] Home, Practice card (desktop Qt) - "Does the keyboard work?" The tiles are checkable buttons in a QButtonGroup; Tab and arrow behaviour is unverified. In web, tiles have `role="radio"` but I found no roving tabindex or arrow-key handling in web/js, so keyboard users get 7 tab stops and the radio role promises arrow-key behaviour that does not exist. Fix: implement arrow-key movement per radiogroup, or drop the radio role for plain toggle buttons (aria-pressed).
5. [Minor] Home, Practice card (desktop) - The card is now taller (2 rows at 100px + hint + Start). Next to the Adventure card the "Start practice" button may be pushed down or the window may scroll at small sizes (unverified). Fix: check at the minimum window size so Start stays visible without scrolling.
6. [Minor] Home - Letter names are in the muted colour at 20px (desktop) / 1.2rem (web). Muted grey on white may be low contrast for the second label (unverified). Fix: confirm >= 4.5:1.
7. [Minor] Spec/doc drift - docs/design/Home.dc.html still shows the 3-note design. Flag only; update the mockup, not behaviour. FR-12 and the spec's mode-card text (7 notes) already match the new code.

**Would this child come back tomorrow?** Yes, for this screen. Choosing any note without a limit fits a 9-12 child's wish to master specific notes, and nothing here feels babyish. Fix the selected-state clarity and narrow-width fit so they do not fumble the first step.

## Cross-age summary
Only 9-12 was reviewed for this change.
- Shared issues likely for other bands: the weak selected state on desktop (#1) matters most for 3-8, who rely on non-colour cues; narrow-width fit (#2) affects all bands on phones.
- Conflicts: none found. Larger, check-marked tiles help younger children and do not look babyish to older ones.
- Spec conflicts: none. FR-11, FR-12 and the Practice card text in the spec agree with the 7-note grid. The design mockup (docs/design/Home.dc.html) disagrees with spec and code (3 notes). Flagged, not changed.
