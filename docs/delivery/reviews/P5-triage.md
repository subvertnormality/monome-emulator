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
