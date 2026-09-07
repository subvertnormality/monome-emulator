# Thread profiling and longer Mosaic timing regression

The diagnostic wrapper can sample descendant Linux threads with `--threads`.
`--thread-process matron` restricts collection to matron processes descended from
the command; it does not inspect another running emulator. Two contract tests
cover process-name parsing, ancestry, optional filtering and PID reuse. Samples
include CPU time, state, wait channel and per-thread sample timestamp. This WSL
kernel reports scheduler wait accounting disabled; zero runnable-wait counters
cannot establish absence of scheduling delay. No kernel setting was changed.

The first all-service profile, `artifacts/c16/thread-timing-01`, passed real-time
M-LEN-001 (`957e0a480f43455bacb49aaa23685e06`). Mosaic now also owns M-TIM-001:
an edited eight-step phrase at90BPM, restart,61 onsets and60 durations over20
complete phrases. Oracles use literal step offsets and durations; manual
MAN-030/MAN-050 mapping remains partial, not complete clock-family coverage.

Its real-time profile `artifacts/c16/thread-timing-02` failed in the initial
phrase check (`e3d81b0c466e48419d7dae50b3f72a9b`), before the20-phrase stage.
One note was23.515ms too short; its onset was23.327ms late. Near that onset,
matron's main thread accumulated36.495ms CPU time. This suggests main-thread
callback work is relevant, but the all-service sampler took13–39ms per batch
around the event. It cannot pinpoint the responsible Lua function or cleanly
separate measurement overhead. Collection now supports matron-only filtering
and per-thread timestamps; the next profile must use those refinements.

Do not call the real-time timing problem fixed, blame garbage collection without
profiling, or widen the10ms oracle. The new case is being run in controlled mode
to exercise its complete longer assertion sequence. M5 and exhaustive manual
coverage remain incomplete; this is diagnostic progress only.
