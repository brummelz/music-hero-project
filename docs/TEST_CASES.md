# Test Cases: Horn Hero

Traces to [SPECIFICATIONS.md](SPECIFICATIONS.md). All cases are automatable with synthetic signals or injected frequency streams (no microphone needed) and a simulated clock. Defaults: tolerance ±15 cents, hold time 3.0 s, reset-on-loss.

## Core acceptance tests

| ID | Title | Req | Input | Expected result |
|----|-------|-----|-------|-----------------|
| TC-01 | Pitch detection and gauge | FR-02, FR-03, FR-04 | Sine at 349.23 Hz (concert F4 = written C5 on Horn in F); target written C5 | Detected F0 within ±5 cents; gauge at center (≈0 cents), Green zone |
| TC-02 | Transposition | FR-01, FR-19 | Target written C4 (Do), Horn in F profile | Target frequency = concert F3 ≈ 174.61 Hz (±0.01 Hz) |
| TC-03 | Hold timer and point | FR-06, FR-09 | Signal within ±10 cents of target for 3.0 s continuous | Ring completes, score +1, sound effect triggered, timer reset to 0 |
| TC-04 | Off-pitch reset | FR-07 | Signal in Green for 1.8 s, then shifted outside tolerance | Timer resets to 0, no point awarded |

## Additional tests

| ID | Title | Req | Input | Expected result |
|----|-------|-----|-------|-----------------|
| TC-05 | Cents conversion | FR-02 | f = f_t·2^(k/1200) for k = −50, −15, 0, +15, +50 | Returns k (±0.01 cents) |
| TC-06 | Zone boundaries | FR-03 | Offsets −16, −15, 0, +15, +16 cents | Flat, Green, Green, Green, Sharp |
| TC-07 | Flat/sharp side | FR-03, FR-04 | Offsets −30 and +30 cents | Needle left / right of center; flat-side / sharp-side zone |
| TC-08 | Reference table | FR-19 | Written C4, D4, E4, C5 on Horn in F | 174.61, 196.00, 220.00, 349.23 Hz (±0.01) |
| TC-09 | Alternate profiles | FR-01 | Written C4 with B♭ profile (−2 semitones) and C profile (0) | 233.08 Hz and 261.63 Hz (±0.01) |
| TC-10 | Silence | FR-05 | Silence/noise for 5 s | Idle gauge state, timer stays 0, no points |
| TC-11 | Timer just short | FR-06 | In Green 2.9 s, then out | No point |
| TC-12 | Grace period | FR-08 | In Green 1.5 s, 100 ms dropout, back in Green | Timer continues, not reset |
| TC-13 | Dropout beyond grace | FR-07, FR-08 | In Green 1.5 s, 300 ms dropout | Timer reset to 0 |
| TC-14 | Pause setting | FR-07 | Pause mode on; Green 1.8 s, out 1 s, Green again | Timer resumes from 1.8 s; point after a further 1.2 s |
| TC-15 | Consecutive points | FR-09 | 6.0 s continuous in Green | Exactly 2 points |
| TC-16 | Octave error | FR-03 (Open Q6) | Sine one octave above/below target | Not Green; no point |
| TC-17 | Practice session end | FR-14 | Complete 10 holds | Session completes at 10/10; summary shown; no 11th point |
| TC-18 | Practice target fixed | FR-13 | Start session on Ré | Target stays written D4 (≈196.00 Hz) throughout |
| TC-19 | Level 1 sequence | FR-15, FR-16 | Play Level 1 | Prompts only Do, Ré, Mi; advances after each completed hold |
| TC-20 | Level unlock | FR-17 | Complete Level 1 | Level 2 unlocked, star rating stored |
| TC-21 | Persistence | FR-20 | Earn points, change sensitivity, restart app | Progress, unlocked levels, settings restored |
| TC-22 | Note labels | FR-10, FR-11 | Show each Level 1 note | Correct staff position; labels "DO / C", "RÉ / D", "MI / E" |
| TC-23 | Encouragement | FR-18 | Flat, sharp, in-tune, completed, silence states | Matching message for each |
| TC-24 | Latency | NFR-01 | Tone onset to gauge update | ≤ 100 ms (target) |
| TC-25 | Offline packaging | Section 6 | Run the `.exe` with network disabled on a clean Windows machine | App launches and works fully |

## Notes

- TC-01 and TC-02 use different written notes on purpose: 349.23 Hz is concert F4, which is written C5 on Horn in F, while written C4 sounds F3 at 174.61 Hz.
- TC-09: a B♭ instrument sounds a major 2nd below written, so written C4 gives concert B♭3 = 233.08 Hz.
