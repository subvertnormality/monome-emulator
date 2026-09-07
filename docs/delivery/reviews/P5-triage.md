# P5 controlled-clock review: findings open

Codex-only one-shot branch review returned on 2026-09-07. Reviewed implementation
base `ce812e7` through `d1ba402`; medium effort, 600-second limit, no convergence
or class-closure campaign. Session reference
`01a07b23-6fec-7440-869a-a5017f253f65`; reviewed packet SHA-256
`197d9ced993ddbe10098051b9d8ee1fe4060e00e5c2288f5816af77c2b7f8e0a`.
Complete raw response remains in ignored `artifacts/c16/P5-raw.json`; its digest
is recorded in the accompanying receipt. Review inspected evidence and source;
it did not run the native tests. This is not M5 admission or full release review.

| ID | Finding | Disposition and required evidence |
|---|---|---|
| P5-01 major | `_norns.wall_time_start_timer/get_delta` still uses host CLOCK_MONOTONIC | Accept, fix C16. Bind the wall timer to logical time, retaining real-time semantics; native frozen/advance/reset checks must prove it. CPU profiling is a separate API. |
| P5-02 major | Candidate builder copies native files that are not all bound to the claimed official source identity | Accept, fix C16. Reconstruct from pinned official source plus declared patches, or verify the complete build-input tree. A modified untouched C file must be rejected or excluded by reconstruction. Do not infer that the existing candidate actually had such a modification. |
| P5-03 minor | Expected Link abort tolerates any sclang exit | Accept, fix C16. Only existing normal sclang exits 0/-15 may pass; reject unrelated crashes. Existing recorded -15 evidence remains valid. |
| P5-04 minor | Real-time 10ms tolerance encompasses the known 4.722ms first-note shortening | Accept as interpretation correction. Preserve the exact-time failing oracle and investigate Mosaic start phase independently. A real-time pass cannot establish that the controlled adapter caused the discrepancy. |
| P5-05 major | M5 release gate unimplemented | Accept, already recorded C16 work. Require source-bound D repeats, affected E/R regressions, resolved P5 and declared supported scope. Continue to fail closed. |
| P5-06 major | No internal-to-MIDI-to-internal test with pending callbacks | Accept, fix C16. Add independent native sync/sleep transition schedule and real-time comparison before admission. |
| P5-07 minor | Phase probe has only two off-boundary starts | Accept, extend C16 with starts around 96PPQN boundaries and restart; preserve literal native absolute-sync expectations separately from Mosaic musical-duration expectations. |

One focused follow-up remains available after substantive fixes and gate
implementation. Do not spend it on an unchanged branch or label these findings
resolved from source edits alone. The source-bound repeat runner added after the
reviewed commit is additional evidence plumbing, not a disposition of P5-05.

## Focused fix evidence

`../completions/C16-P5-clock-fixes.md` and its evidence JSON record an isolated
controlled-03 build and native checks. P5-01 has a failing old-candidate
reproducer, passing exact logical freeze/advance/reset, three repeats and both
real-time binaries. P5-02 reconstructs the locked Git graph and records every
native input; a dirty-input exclusion regression passes. P5-03's restricted
cleanup passes both native fault cases. P5-07's boundary/restart probe passes
three repeats. These findings have focused fix evidence, pending the final
admission regression set and the remaining Codex follow-up.

P5-06 now also has a shared-probe controlled/real-time comparison, including
three identical controlled repetitions and passing10ms timing bounds on both
real-time binaries. See `../completions/C16-transition-comparison.md` and its
evidence JSON. P5-04's Mosaic musical-policy investigation and P5-05's admission
gate remain open. No finding is waived and P5 is not complete.

P5-05 now has an implemented M5 aggregator, collectors and rejection contracts;
see `../completions/C16-admission-gate.md`. Required native clock/fault packages
have focused passing evidence. Full final-source collection, external comparison
validation and the resolved follow-up receipt remain outstanding, so this does
not close P5 or admit controlled time.
