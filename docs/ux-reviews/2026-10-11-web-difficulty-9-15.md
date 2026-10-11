# Child UX review: ages 9-12 and 12-15 (Easy / Hard switch on Home, web)
Reviewed: four screenshots (desktop and phone, Hard and Easy), web/index.html (.difficulty), web/css/app.css (.difficulty-switch), web/js/ui/screens.js (DIFFICULTY_HINTS, HomeScreen), spec FR-07, FR-21, FR-23, Screen 1. 2026-10-11.
Evidence limits: app not launched (as instructed). Not seen: the switch under keyboard focus, the Settings dialog after the removal, Gameplay behaviour in Easy mode, the level-complete screen. Tolerance preset names were found only in web/js/core/tuning.js (Easy 25 / Normal 15 / Strict 10); the Settings dialog UI was not viewed, so how they are labelled there is unverified.

## Age 9-12
**Verdict:** "Easy or Hard? Cool, I pick Hard." It reads as a game choice, and the one-line hint is clear. The worry is whether Easy stars count the same.
**What works**
- Placed directly under the question and above the cards, so it is the first thing to decide. The selected state is obvious: filled purple pill plus white text, versus a plain label. Icon (smile or flame) plus word, so it does not rely on colour.
- Target is 48 px tall and 120 px wide, which is comfortable on desktop and phone. The font is large (1.25rem).
- Hints are short and literal: "Hard: if the note slips, the hold starts again." A 9-year-old can act on it. It is neutral, not shaming (FR-16, FR-18 respected). Hard is described as a rule, not a punishment.
- The hint changes with the selection, so the child sees cause and effect immediately.
**Problems**
1. [Major] Home, switch and hint - "If I choose Easy, do I get the same stars? Is it cheating?" Nothing says. Stars are earned with a different miss count (FR-23: only the first pause per prompt counts), and nothing shows the mode. A competitive 10-year-old who beats a friend's 3 stars on Easy may feel it is hollow, or the friend may call it out. Likely behaviour: picks Easy for stars, later learns it is "the baby setting", or avoids Easy and gets frustrated on Hard. Fix: (a) record the hold mode with each level's best stars (progress storage) and show a small Easy/Hard icon next to the stars on the level row and in the level-complete summary; (b) say in the Easy hint that stars are earned the same way, or not, once the spec decides. This changes FR-14/FR-23/FR-25 persistence, so it needs a spec decision first. I am flagging, not inventing the rule.
2. [Minor] Home, hint text - "the hold starts again" is slightly vague for a literal reader ("what hold?"). Fix: "Hard: if the note slips, the 3 seconds start over." and "Easy: if the note slips, the count waits for you."
3. [Minor] Home, hint text - it is small, muted, and bold at roughly 0.9 rem in a muted blue-grey on pale blue. Readable in the screenshots on desktop, but weak from arm's length with a horn. Fix: raise to about 1.1 rem and use the full text colour.
4. [Minor] Switch semantics - the label "Hard" has a flame, which promises a challenge but not a reward. Fix: none required; if the spec adds a star marker for Hard, use that.
**Would this child come back tomorrow?** Yes. Choice and control help. Fairness of stars is the only risk.

## Age 12-15
**Verdict:** "Fine, it is a difficulty toggle, not a kids' toggle." The visual is clean and not babyish. The smiley on Easy is slightly patronising.
**What works**
- A plain two-option segmented control, standard and quick to read. No cartoon, no lecture. The hint is one sentence and treats the player as capable.
- The Easy/Hard choice now lives on the Home screen, so a teen can change it without hunting through Settings (matches the spec decision on Screen 1).
- The control is not confusable with the Practice or Adventure cards: it sits above and apart, centred.
- On phone it fits one row with no wrapping, and the hint fits on one line in both states.
**Problems**
1. [Major] Fairness and visibility of mode - a teen will see Easy as an exploit: "Easy means one miss counts per prompt, so I can wobble all I want and still get 3 stars." They will compare screenshots. Nothing shows which mode earned a star, so a 3-star level is ambiguous in trust terms, and teachers cannot tell either. Fix: same as 9-12 item 1, store and display the mode with the best stars, for example a small icon on the star row; spec decision needed (FR-23 says nothing about mode when displaying). Option for the spec owner: keep Easy stars but mark them, rather than cap them, so no one is punished (FR-16).
2. [Minor] Easy icon - the smiley and the word "Easy" can read as "for little kids". It may discourage an older player who would still benefit from pause mode (it is a real learning aid for long notes). Fix: keep the word, but consider a neutral icon (for example a pause symbol), which also describes what the mode does, and avoid a face.
3. [Minor] Naming clash - the Settings tolerance presets are named Easy / Normal / Strict (FR-21; Easy = 25 cents, in web/js/core/tuning.js). A teen who explores Settings will find a second "Easy" and ask whether it means the same thing, or whether "Easy + Easy" stacks. Two Easys with different effects is a real confusion, and the one in Settings is not visible from Home. Likely behaviour: sets tolerance to Strict thinking it is the opposite of Easy mode, or assumes Home Easy changes tolerance. Fix: rename one side. Recommended: rename the Home switch or the tolerance presets. Tolerance is about pitch width, so name the presets by what they do (for example Wide / Medium / Narrow, or "Forgiving / Standard / Precise") and keep Easy/Hard on Home as the child-facing word, since Screen 1 and FR-07 already name it that way. This needs a spec edit to FR-21 first. Unverified: whether Settings shows these names to the user.
4. [Minor] Settings removal - the option no longer appears in the grown-up dialog, so a teacher who looks there will not find it. Fix: a one-line pointer in Settings ("Easy / Hard is on the Home screen") is enough. Unverified: not seen.
5. [Minor] Hint contrast and size - same as 9-12 item 3.
**Would this child come back tomorrow?** Yes if the stars feel earned; maybe not if Easy stars are visibly indistinguishable from Hard ones and the app feels like it can be gamed.

## Cross-age summary
- Shared, ranked:
  1. [Major] Stars do not show which mode earned them, and Easy changes how misses are counted (FR-23). Both older bands will notice the fairness question. Needs a spec decision (mode stored with best stars and shown on level rows and in the level-complete summary), not a silent code change.
  2. [Minor, but spec-relevant] Naming clash between Home Easy / Hard (FR-07) and tolerance presets Easy / Normal / Strict (FR-21). Rename the presets in the spec first.
  3. [Minor] Hint size and contrast; hint wording could be more literal.
- Conflicts: 9-12 likes the smiley and flame as friendly icons; 12-15 finds the smiley slightly young. Resolution: keep the icon plus word for 9-12 and younger bands, and consider a neutral icon (pause symbol) since it works for all ages and describes the effect.
- Spec flags: FR-07 and Screen 1 match the implementation (switch on Home, default Hard, persisted). FR-23 gives no rule for showing or storing the mode with the stars, and FR-24/FR-25 are silent on the same point. FR-21 preset names clash with FR-07's Easy / Hard naming. No Blocker findings.
