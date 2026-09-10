# C17 constrained resource recorder checkpoint

Status: passed on a committed container image; C17 and A25 remain in progress.

The authenticated native session server now records the complete container
cgroup at 10–1000 ms intervals for at most ten minutes. It returns bounded,
paginated raw samples with CPU, current and peak memory, throttling and the
currently observable native MIDI input queue. Recording failure, invalid cursors,
unsupported hosts and duplicate jobs are explicit failures.

## Validation

- Current-main contract suite: 96 collected, 96 passed, zero skips.
- Development-overlay container run passed before image construction.
- A committed snapshot at `986c2055f271365e00f070b47d89994cbdfb2300`
  built as image ID
  `sha256:cfa09761bdd3b6212894bd51bd56fcfc371248075005892f2343afcac668f5b0`.
- The no-overlay run drove 40 ordinary K2 transitions through `probe-a` and
  captured 43 ordered samples. The kernel reported 0.5 CPU, 768 MiB memory,
  no additional swap and CPU set 0 exactly. Peak memory was 371,208,192 bytes;
  32 periods were throttled. MIDI/runtime errors and held inputs were empty.
- The container and its data lease were stopped and removed automatically.
- Raw result: `artifacts/performance/container/recorder-image-01/result.json`,
  SHA-256 `26f0d8f2ff9c3eee8ffe6311ab5bce1bb7e568538a473d74a69932d774e4de98`.
- Durable summary: `docs/delivery/performance-recorder-validation.json`.

This proves the resource-capture path and enforced envelope, not PERF-001 or a
physical-norns throughput equivalence. The current queue counter observes native
scheduled MIDI input only. Lua scheduler/application queue instrumentation must
be added before those queue-recovery claims are admitted.
