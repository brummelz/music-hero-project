# Test Cases: Horn Hero

Traces to [SPECIFICATIONS.md](SPECIFICATIONS.md). All cases are automatable with synthetic signals or injected frequency streams (no microphone needed) and a simulated clock. Defaults: tolerance ±15 cents (Normal preset), hold time 3.0 s, reset-on-loss.

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
| TC-06 | Zone boundaries | FR-03 | Default tolerance; offsets −16, −15, 0, +15, +16 cents | Flat, Green, Green, Green, Sharp |
| TC-07 | Flat/sharp side | FR-03, FR-04 | Offsets −30 and +30 cents | Needle left / right of center; flat-side / sharp-side zone |
| TC-08 | Reference table | FR-19 | Written C4, D4, E4, C5 on Horn in F | 174.61, 196.00, 220.00, 349.23 Hz (±0.01) |
| TC-09 | Alternate profiles | FR-01 | Written C4 with B♭ profile (−2 semitones) and C profile (0) | 233.08 Hz and 261.63 Hz (±0.01) |
| TC-10 | Silence | FR-05 | Silence/noise for 5 s | Idle gauge state, timer stays 0, no points |
| TC-11 | Timer just short | FR-06 | In Green 2.9 s, then out | No point |
| TC-12 | Grace period | FR-08 | In Green 1.5 s, 100 ms dropout, back in Green | Timer continues, not reset |
| TC-13 | Dropout beyond grace | FR-07, FR-08 | In Green 1.5 s, 300 ms dropout | Timer reset to 0 |
| TC-14 | Pause setting | FR-07 | Pause mode on; Green 1.8 s, out 1 s, Green again | Timer resumes from 1.8 s; point after a further 1.2 s |
| TC-15 | Consecutive points | FR-09 | 6.0 s continuous in Green | Exactly 2 points |
| TC-16 | Octave error | FR-03 | Sine one octave above/below target | Not Green; no point |
| TC-17 | Practice session end | FR-14 | Complete 10 holds | Session completes at 10/10; summary shown; no 11th point |
| TC-18 | Practice target fixed | FR-13 | Start session on Ré | Target stays written D4 (≈196.00 Hz) throughout |
| TC-19 | Level 1 sequence | FR-15, FR-16 | Play Level 1 | 6 prompts, only Do, Ré, Mi; each note at least once; no immediate repeat; level completes after 6 holds |
| TC-20 | Level unlock | FR-17 | Complete Level 1 | Level 2 unlocked, star rating stored; Level 3 still locked |
| TC-21 | Persistence | FR-20 | Earn points, change sensitivity, restart app | Progress, unlocked levels, settings restored |
| TC-22 | Note labels | FR-10, FR-11 | Show each Level 1 note and each practice note | Correct staff position; labels "DO / C", "RÉ / D", "MI / E"; practice notes also "FA / F", "SOL / G", "LA / A", "SI / B" |
| TC-23 | Encouragement | FR-18 | Flat, sharp, in-tune, completed, silence states | Matching message for each |
| TC-24 | Latency | NFR-01 | Tone onset to gauge update | ≤ 100 ms (target) |
| TC-25 | Offline packaging | Section 6 | Run the `.exe` with network disabled on a clean Windows machine | App launches and works fully |
| TC-26 | Tolerance presets | FR-21 | Offset +20 cents under Easy, Normal, Strict | Green, Sharp, Sharp |
| TC-27 | Custom tolerance | FR-21 | Custom ±5 and ±50; try 4 and 51 | ±5 and ±50 accepted; 4 and 51 rejected or clamped |
| TC-28 | Tolerance live effect and persistence | FR-21, FR-20 | Change tolerance mid-session, then restart | Applies immediately to gauge and timer; restored after restart |
| TC-29 | Level note frequencies | FR-15, FR-19 | Every note in the §4.1 table, Horn in F | Target frequencies match the table (±0.01 Hz) |
| TC-30 | Level prompt generation | FR-16 | Generate prompts for Levels 1–5 over many random seeds | 6 prompts, all level notes appear, no immediate repeats, no note outside the level |
| TC-31 | Stars: 3 | FR-22, FR-23 | Complete a level with 0 and with 2 misses | 3 stars |
| TC-32 | Stars: 2 | FR-23 | Complete a level with 3 and with 6 misses | 2 stars |
| TC-33 | Stars: 1 | FR-23 | Complete a level with 7 and with 20 misses | 1 star |
| TC-34 | Miss counting | FR-22 | 10 s of silence before playing, then a clean hold | 0 misses |
| TC-35 | Best stars kept | FR-17 | Replay a level with a worse result | Stored best stars unchanged |
| TC-36 | Practice has no stars | FR-24 | Complete a 10-point practice session | Total stars unchanged |
| TC-37 | Single profile | FR-25 | Launch fresh and after a restart | No profile selection; same progress shown |
| TC-38 | Reset progress | FR-25 | Reset progress: cancel, then confirm | Cancel keeps data; confirm clears progress and stars, only Level 1 unlocked |
| TC-39 | Counter starts on entering range | FR-06 | Silence, then at t = 2.0 s the correct note enters the Green zone and stays | Timer is 0 until t = 2.0 s, starts at that instant, completes at t = 5.0 s (±1 detection frame), 1 point |
| TC-40 | Wrong note does not start counter | FR-06 | A different note (not the target, including octave-off) sustained for 5 s | Timer stays 0, no point |
| TC-41 | Practice note choices | FR-12 | Open Practice mode | Seven choices, in order: written C4, D4, E4, F4, G4, A4, B4 (Do to Si), no sharps or flats |

## Notes

- TC-01 and TC-02 use different written notes on purpose: 349.23 Hz is concert F4, which is written C5 on Horn in F, while written C4 sounds F3 at 174.61 Hz.
- TC-09: a B♭ instrument sounds a major 2nd below written, so written C4 gives concert B♭3 = 233.08 Hz.
