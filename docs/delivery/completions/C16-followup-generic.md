# Fresh generic evidence after the P5 follow-up fixes

Emulator `85245b9` passes all ten required generic check groups and all eight
controlled probe families, each with three native sessions. The completed batch
is `artifacts/c16/m5-generic-06d-batch.json`. The verified, hashed evidence index
is `artifacts/c16/m5-generic-06d-index.json`, SHA-256
`c75f94eacf30679ac81ad23ed748441b91c35fe60e1e9766e8dac63b57452cb9`.
Source digest:
`ae9a9964d34aad51728704acbf0521e269617d7789eaf9475be89e18cdb1da09`.

The batch runs wall timers, pending-callback clock transitions and real-time
clocks against both installations; source faults; queued MIDI against default
and candidate real-time runtimes and controlled time. Controlled repetitions
cover boundaries/runaway, clock, phase, phase boundaries, MIDI, tempo, wall timer
and source transitions. The default runtime remains real-time only; the
controlled candidate remains explicit and experimental until M5 admission.

Collection command: `python3 artifacts/collect_m5_generic06d.py`.
Verification/index command: `python3 artifacts/index_m5_generic06d.py`.
Both exited zero. The indexer invokes the current generic validators and repeat
verifier against retained native artifacts and the current source digest.

This evidence follows the P5-08/09 verifier fixes and their reproduced rejection
tests in `../reviews/P5-triage.md`. It does not establish exhaustive Mosaic
coverage or full emulator delivery. Fresh Mosaic comparisons and the final M5
aggregate remain outstanding.
