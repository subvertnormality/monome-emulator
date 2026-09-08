# H01 review triage

Codex medium critique completed, session01a082eb-1578-7722-a282-0505faf28671.
Raw response H01-raw.json binds reviewed commit eadeb73 from97ab62b.

Accepted major1: negative lifecycle tests now require the exact expected helper
exit (2 startup,1 sink loss), the complete five-service inventory, allowed normal
exits for every other service, absent PIDs, and private daemon exit0. A unit
regression rejects unrelated service SIGSEGVs and missing service records.
Accepted major2: a phase-independent sampled-sine recurrence checks continuity
on both channels through the final sample, excluding only initial250ms for the
commanded transition. Threshold1%peak+.0001 covers PCM quantization/resampling.
Independent tests reject25sample phase-preserving zeros in the interior and tail.
Existing broad RMS/frequency checks remain. Windows tests also check both saved
JACK and WSLg boundary recordings, resolving that minor suggestion.
Accepted minor: nonfinite input returns before publishing the JACK block.
Candidate rebuilt desktop-tools-04; native acceptance pending rerun.

Retain the unlocalized Windows dropout as a limitation; no claim it is solved.
Asymmetric stereo stimulus is a follow-on H01 improvement: current TestSine is
mono duplicated, now asserted on both channels, and cannot prove channel order.
No arbitrary engine/hardware equivalence claim. Focused follow-up will review
major oracle/lifecycle changes and native evidence; no additional whole review.

Post-fix native Windows223232 passes all checked JACK/sink/endpoint continuity.
The retained221650 WAV fails the new continuity check directly (residual.15646,
limit.0021). Native desktop223330 failed explicitly on startup: JACK reports
110us scheduling xrun, helper jack_faults1/underflows0; all other services exited
normally and owned processes reaped. One fresh run pending, no fault suppression.
Strict native failures223531 passed all3 scenarios with exact service exits and private daemon0. Desktop223421 passed10. Top-level24 tests passed. Both major findings fixed; focused review pending.
Focused follow-up01a082f4-2e55-7a62-b9fc-b2c306271401 confirms both major gaps closed, no substantive remaining issue in552e4a1. Review budget complete (one critique, one focused query). Residuals remain recorded; admission is scoped opt-in desktop support.
