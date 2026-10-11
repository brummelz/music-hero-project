# Child UX review: ages 3-5 and 6-8 (web Home, Easy / Hard switch)
Reviewed: four screenshots (desktop and phone, Hard and Easy selected) plus web/index.html (.difficulty), web/css/app.css (.difficulty-switch) and web/js/ui/screens.js (DIFFICULTY_HINTS, HomeScreen), 2026-10-11. Scope is only the new switch and its effect on Home.
Evidence limits: app not launched. Tap feedback, persistence of the choice, and the behavior of the hold bar in Easy mode during play are unverified. The Settings dialog was not viewed; I only know from the brief that the option was removed from it.

## Age 3-5
**Verdict:** The child sees a big purple pill with a smiley and a flame and will likely tap it just because it is the shiniest thing under the title. They cannot read either the label or the hint, so the switch means nothing to them, and the default (Hard) is the less forgiving mode.

**What works**
- Selection is not color alone: the chosen half is filled with white text and a filled icon, and the other half is plain with a grey icon. Position plus fill plus icon.
- Smiley for Easy is a friendly, readable symbol.
- The control is centered and clearly separate from the cards.

**Problems**
1. [Major] Home, default state - "I can't read, so I never choose Easy; the grown-up isn't there." The youngest children get Hard by default, where a wobble restarts the 3-second hold. This is the exact repeated-miss frustration this age fears. Fix: do not change the spec default silently (FR-07 says reset is the default). Flag it: ask the product owner whether the default should be Easy for the 3-5 band, or whether a first-run grown-up prompt should pick it. Until then, record this as a spec question.
2. [Major] Home, switch placement - "A big shiny button right under the title; I tap it, then tap again, then I tap everything." The switch is the first interactive element and is bigger than the note cards, so it competes with the one real next action (pick a note / Start). Each tap flips the mode, so a masher ends in a random state and the hint text changes, which they cannot read. Fix: make the switch visually quieter (smaller, outlined, below the cards or next to Start), or put it where a grown-up sets it once. Keep the Start button the most prominent thing.
3. [Minor] Flame icon - "Fire is hot, that might hurt." A flame on one option can read as danger to a very small child. Fix: use a neutral icon for Hard (mountain, two steps, or a star outline), keeping the smiley for Easy.
4. [Minor] Targets - each half is 48 px tall, 120 px wide. Too small for imprecise fingers; two adjacent targets with a 4 px gap invite wrong taps. Fix: 64 px tall minimum and a visible gap, or one big toggle.
5. [Minor] Hint line - small muted text, unreadable and unheard. Harmless but pointless for this age. Fix: none needed if the hint stays a grown-up aid; optionally speak nothing, since spoken audio would add noise.

**Would this child come back tomorrow?** Maybe. The switch does not stop them playing. The risk is hitting Hard by default with no one to explain it.

## Age 6-8
**Verdict:** The child can read "Easy" and "Hard", picks one, and mostly understands it. The hint wording is abstract, and "Hard" next to "Easy" invites a pride choice they may regret.

**What works**
- Two words, each with an icon, as this age needs. The selected half is obvious (filled, white text).
- The hint changes immediately under the switch, so the cause and effect is visible.
- Easy/Hard is common vocabulary for this age; no jargon in the labels.
- On the phone, the switch is large and sits with the heading, no scrolling needed to reach Practice.

**Problems**
1. [Major] Hint text - "Easy: if the note slips, your progress stays." and "Hard: if the note slips, the hold starts again." A literal 6-year-old does not know that a note "slips" (slips where?), what "progress" is, or which "hold" starts again. The text is also small and muted grey. They read the words but cannot picture the consequence. Fix: concrete and positive, for example "Easy: wobble and we wait for you." and "Hard: wobble and the count starts again." Pair with a tiny picture (a bar that stays filled vs a bar that empties). Keep it short per FR-18; avoid any wording like "you lose".
2. [Major] Label "Hard" as the default - the child sees the default is Hard, and a child who picks Easy may feel babyish while one who stays on Hard gets frustrated after a few restarts. Easy/Hard also invites a ranking ("Hard is for good players"). Fix: use neutral names for the two behaviors, such as "Wait for me" / "Count again", or "Relaxed" / "Challenge", and let the hint explain. If Easy/Hard stays, flag the default question to the product owner (FR-07 default is reset).
3. [Minor] Switch above the note cards - the child must make a settings choice before the real choice (which note). The title "What do you want to play today?" is answered by the switch, not by the cards, which reads oddly. Fix: move the switch below the Start button area or into the Practice card, or add a short label like "How to hold:".
4. [Minor] Flame icon on Hard may read as "hot" or "danger"; see 3-5. Use a neutral icon.
5. [Minor] Persistence of the choice across levels and sessions is unverified. If it resets to Hard each visit, an Easy-choosing child will be surprised.

**Would this child come back tomorrow?** Yes, if Easy gives them a smoother first win. The switch itself is not a reason to leave.

## Naming clash with tolerance presets (FR-21: Easy / Normal / Strict)
- Children (both bands) never see the Settings dialog, so the child is not confused. Risk is with the grown-up: "Easy" now appears on Home meaning "keep progress when you slip" and in Settings meaning "wider in-tune zone". A parent who sets tolerance to Easy and then reads Home Easy may think they are the same control, or that Easy on Home also widens the green zone. A child who picks Easy on Home may also believe the target is easier to hit; it is not.
- [Minor] Fix: rename one set. The tolerance presets could become "Wide / Normal / Narrow" (or "Forgiving / Normal / Precise"), leaving Easy/Hard to the hold behavior, or rename the Home labels as in 6-8 problem 2. This is a spec wording change (FR-21 and Screen 1), so update the docs first.

## Cross-age summary
- No Blockers. No failure state is introduced: restart of the hold is not framed as failing, and the child can retry indefinitely (FR-16 respected).
- Shared Majors: (a) the default is Hard, the harsher mode, for the youngest children; flag against FR-07 (default reset) and ask the owner, do not change silently; (b) the hint text is abstract and small; (c) the switch is more prominent than the note choice (affects 3-5 most).
- Conflicts: 3-5 needs a bigger, icon-led control and no reading; 6-8 can use short words. Resolution: keep icon + one word, enlarge the targets, use friendlier neutral labels, and keep the hint as a small aid, not essential.
- Spec items to flag: FR-07 default (reset) versus the youngest age band's frustration; FR-21 preset names versus the new Home labels (naming clash).
