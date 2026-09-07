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

Further diagnostic implementation adds an `input_timing` record after each send
attempt finishes, retaining socket submission start/end and the native ack (null
on timeout). Existing input records and the two-second deadline remain intact.
`scripts/diagnose_host_timing.py` runs the selected command as a child and samples
its own independent process every10ms, retaining samples in memory until exit.
It propagates the child status and never grants an acceptance waiver.

The first controlled diagnostic under this wrapper passed M-LEN-001:
`074828c929ce4c39b9f8a9e084d82740`; wrapper evidence is
`artifacts/c16/host-timing-01/heartbeat.json`. Maximum host sample gap was16.1ms.
The subsequent repeat is running under `artifacts/c16/host-timing-02`; at the
recording checkpoint its terminal handle27476 remained live and no heartbeat
completion file existed. An independent WSL invocation failed with service
connection timeout `Wsl/Service/0x8007274c`. This establishes current WSL service
unavailability, not causation of the earlier timing failures. Do not restart
the repeat solely because observation is slow, or shut down a shared WSL host
without establishing that doing so is appropriate. Resume by polling27476 and
inspecting the wrapper artifacts. The post-submission/heartbeat changes remain
uncommitted at this checkpoint while that source-bound run is active.

The handle subsequently completed normally: controlled repeat
`repeat-e5e596679fbc41d4878fadd5eafcb1a0` passed all three children and normalized
equality. `host-timing-02/heartbeat.json` records a2220.22ms maximum independent
sample gap. No host restart or timeout change occurred. This diagnostic window
therefore includes a substantial scheduling pause, while exact-time outputs
remained repeatable. It does not retrospectively explain every earlier failure.

A current-source real-time comparison under `host-timing-03` failed:
`d5fa2557a53844ecb997a956c6ceb82d`. One note's duration error was14.732634ms;
all177 native actions acknowledged, maximum socket-send duration0.296907ms,
submission-to-native-ack50.847642ms, and event-log write1.976550ms. Independent
heartbeat samples around the missed note-off deadline remained10.12–10.15ms
apart, including across the expected deadline. The host-wide pause hypothesis
does **not** explain that particular late note. Next investigate native scheduler
thread delay and Mosaic callback execution near that deadline, with per-thread
CPU/runnable-wait evidence or bounded profiling. Do not simply repeat until green.
No active runners remain. M5 remains incomplete despite passing D repetition.
