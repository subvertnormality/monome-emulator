# MIDI clock startup candidate

Experimental upstream-compatible patch against official norns
14bbeae8646c6717f6bb44c8cd60250bf94b6042. Not in the default dependency lock.
It has no Mosaic imports or emulator clock hooks and can be applied to the
same upstream source for norns. Hardware operation has not been measured.

Stock cold Start is delayed one Clock: Mosaic M-SYNC-002 fails by 25 ms at
100 BPM in controlled time and 28.369 ms in real time. The independent native
probe reproduces the delay without Mosaic. Warm M-SYNC-001 passes.

The candidate counts the first Clock after pending Start even when no tempo
sample exists. It retains the prior estimate, or the native 120 BPM default,
until an interval can be measured. It also stores unweighted duration samples:
the stock warmup accumulates samples with different divisors and temporarily
reports the wrong tempo even for a perfectly steady input. Restart after a
long clock gap still starts at the first Clock; the gap is not a tempo sample.

Required before admission: native startup/estimator matrices, controlled and
real-time Mosaic cold/warm regressions, duplicate/late/lost clock scenarios,
tempo transitions, Stop/Continue support audit and focused Codex review.
First-interval subdivisions before a measurable tempo exists need an explicit
contract; they cannot be claimed to predict an unknown external tempo.
The separate internal-tempo discontinuity and Mosaic master alignment remain
unfixed. Remove this patch when a verified official update supplies the fix.

## Boundary checkpoint

36 distinct candidate scenarios pass; stock fails 29 of the same scenarios.
See `docs/delivery/completions/C07-midi-clock-candidate.json`. The Codex review
found an equal-timestamp pulse loss regression in the first candidate. It is
corrected: tempo samples and received pulse counts are independent, and a
backwards timestamp does not replace the last valid interval origin. Bunched
clocks, recovery and arithmetic duration smoothing across two forward/reverse
ring wraps are now asserted. Runtime and Mosaic acceptance remain pending.

## Acquisition and source handoff checkpoint

The candidate now advances an unacquired MIDI beat only by received pulse count,
then interpolates once an interval is measured. Atomic acquisition/count state
and a generic clock acquisition API expose this to the controlled deadline
predictor. Sleep and metro deadlines continue while sync waits for measurement.
A native probe fails against candidate02 and passes candidate03.

Mosaic separately counts external-origin pulses exactly once, while local grid
Play retains its local phase. A source change leaves external-origin accounting
without replaying the other source’s historical beat count. The original
32-note handoff burst is retained as a failure; its fixed case passes both modes.
See `docs/delivery/completions/C07-midi-acquisition-progress.json` for exact
source-scoped evidence and unresolved gates. This is not default promotion.
