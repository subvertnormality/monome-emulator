# Native receiver timing diagnostics

Mosaic real-time run `5c45def0995f4dd6b9c665b26a65eeda` failed its unchanged
duration oracle: one later note was about585ms too long, amid a726.58ms gap
across native event types. This gap alone cannot distinguish a native stall,
host scheduling pause or transport backpressure. No cause is certified.

The receiver now records three diagnostic fields in retained native events:
`received_monotonic_ns`, `receiver_lock_wait_ns` and `previous_log_write_ns`.
These measure receipt, waiting for the receiver condition, and the preceding
event log write. MIDI and timing assertions still use native emission timestamps;
these diagnostics are not substituted for musical time. They also do not enter
controlled repeat normalization.

The instrumented real-time M-LEN-001 run
`472830eabb394150ae1144bbb08c9e4b` passed. Across720 received events, maximum
native-to-receiver lag was7.936497ms, previous log write6.878636ms, and receiver
lock wait1.115903ms. The old long stall did not recur. This establishes a passing
candidate run and useful diagnostics, not a diagnosis or resolution of the old
failure. Native event logging remains synchronous; do not claim that logging
latency has been removed. C11/C12 own its lifecycle/endurance implications.

Both application run manifests and native traces are retained in the external
Mosaic behaviour evidence directory. Mosaic's bug record retains the failing
run alongside the passing diagnostic run. Final M5 requires its full fresh
evidence inventory and P5 follow-up; neither this note nor one passing rerun
admits controlled time or certifies real-time endurance.

The subsequent three-run package `repeat-639ebffcc6a247c995e19b529ad18a3e`
failed on its second child `bd4676fcad0f4a54974a6e49e04f3b33`, after the first
child `b1449e387a644674b95c3531affdf569` passed. The failed child timed out
waiting for advance691, rather than failing its musical duration assertion.
Its input trace timestamp was2027916829217483ns; the native report and ack
were2027921958179506ns and2027921958207357ns. Receipt of the ack lagged native
emission by19.329432ms. Maximum receiver log write in this run was87.145901ms.
Thus the approximately5.13-second interval cannot be attributed solely to
receiver delay after native acknowledgement. The input timestamp precedes
input-log writing and socket submission, so it does not prove5.13seconds of
native execution either. Next add post-submission timing and an independent
host heartbeat before another diagnostic attempt. Preserve the failed package;
it earns no repeat or M5 credit.
