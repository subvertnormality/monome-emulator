# P1 integration review and bounded follow-up

Initial reviewed commit: `0442385`, base `20e66d2`. The 600-second MCP
call timed out (`P1-raw.json`); diagnosis found the Claude response completed
at 23:20:06.837 UTC, nine seconds after client cancellation. The complete final
response is retained verbatim in `P1-recovered.md`, from session
`42320688-61c0-4db5-9d7f-7309be75ccc6`. No second cold critique is planned.
A focused Paranoia query must confirm the recovered review and material fixes
before P1 is marked done. This is not tracked convergence.

| Finding | Disposition and evidence |
|---|---|
| Major: no independent Mosaic screen-content oracle | Fix now. `tests/frame_oracle.py` renders literal titles, positions, six tab indicators and levels from the pinned public page layout using the pinned font and Cairo, without calling Mosaic or capturing a golden. `mosaic_slice.py` requires the initial Note Masks header and post-edit Device Config header. A blank-frame fault must fail. Every intervening snapshot is retained; browser still checks actual pixel propagation. |
| Major: stale/incomplete final evidence | Fix now at card close. All four selections (API, browser, cancellation probe, contracts) are refreshed after implementation freezes, then recorded in C06-evidence.json and state. Historical failure/baseline artifacts remain labelled historical. Commit identity alone is not a content change; the verifier enforces content digest. |
| Minor: shutdown error leaves HTTP server alive | Fixed: `/stop` schedules shutdown in `finally`, while retaining the failing response. Focused contract injects native-style cleanup failure after closing an actual owned backend and requires the HTTP thread to exit. |
| Independent probe: first health failure and initialization deadline leak native groups | Fixed: launcher exception path signals the exact server and waits for bounded cleanup; SIGTERM unwinds both initialization and serving. Actual native regressions interrupt before discovery and after first health, retain cleanup records and require process completion. |
| Independent probe: browser navigation failure leaks driver/browser | Fixed: constructor closes its owned browser/driver and pipes on failed open. Actual Chromium unsafe-port regression requires driver exit 0. |
| Minor: parser described as unchanged upstream | Fixed documentation and capabilities. Patch 0009 is a deliberate, tested correction of the pinned realtime-byte parser defect; passing interleaved realtime here is not hardware equivalence. |
| Minor: clock cancellation correction hides a stock-runtime race | Explicit same divergence in documentation/capabilities and D16. Both failing stock baseline and fixed native trace retained. C14 update rehearsal checks whether official candidate eliminates the patch. Upstream publication is not authorized or needed for local acceptance. |
| Minor: immediate stop-note assertion can race draining clocks | Fixed: bounded observation wait for empty counted notes (3 seconds), retaining intermediate snapshots. A persistent R08 mismatch still fails; no retry or tracker relaxation. |
| Minor: scheduled MIDI blocks lock up to 2 seconds | R10, C07 timing/lease interaction; M1 recipe does not use future scheduling. No claim of concurrent scheduled-input responsiveness yet. |
| Minor: isolated F7/status interruption rejected more strictly than stock | R11, C10 native MIDI input contracts. Explicit unsupported capability until verified/aligned. No mandatory release exemption. |
| Minor: obsolete patch/schema generators and spike duplicates | R12, C14 packaging cleanup. These are historical preparation tools, not runtime dependencies; delete superseded unsafe tools before distribution. Not an M1 correctness blocker. |
| Minor: personal Windows browser paths | Existing C14 portability owner; C06 reproduction explicitly names the dependency. |

P1/M1 remain pending until the focused response and refreshed evidence are recorded.

## Completion

Focused query returned 2026-09-06T23:40:55Z, Claude session 7d8cabfc-54e2-4053-bf5d-a428a1787ee6 (P1-followup-raw.json): no remaining substantive M1 blockers. Both final native slices and the cancellation probe verified against e2c452f content; C06-evidence.json records all digests, 28 contracts and three actual startup cleanup regressions. The table formatting notes are fixed. First-signal-during-close is recorded as R13 for C11; pixel-font antialias modes are equivalent for this literal title oracle, with no claim for arbitrary fonts. P1 is complete with one recovered critique and one focused follow-up, not convergence.
