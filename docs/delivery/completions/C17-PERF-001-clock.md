# C17 slice — PERF-001 internal-clock capacity (generic probe)

Status: partial PERF-001 evidence. Not C17 completion, not a physical-norns claim.
Compact per-run data and SHA-256 digests: [C17-PERF-001-clock.json](C17-PERF-001-clock.json).
Raw per-run `result.json`, `samples.json`, `native-events.jsonl` and container logs
are under the ignored `artifacts/performance/container/<batch>/`.

## What was measured

Generic probe `fixtures/probes/performance-clock/performance-clock.lua` on the
official internal clock: K3 selects 20/100/120/300 BPM, E1 selects density (1–64
simultaneous voices), K2 starts transport. Each of 120 pulses at 24 PPQN emits a
Note On/Off pair per voice. The oracle is the independent plan in
`src/automation/performance_clock.py`: exact bytes/order for every emission in the
complete native export, the D20 10/50/20 ms event profile, and the PERFORMANCE.md
service gates (p99 burst ≤ 50% and maximum ≤ 100% of the 1/24-beat deadline).
Three fresh containers per point on `monome-emulator:perf-recorder-02`
(`sha256:38b516ef…`, built from `c0d3185`), cgroup v1 envelope 50000/100000 µs
CPU quota, 768 MiB memory+swap, cpuset 0.

## Results under the settled protocol (500 ms observer poll, 1 s settle)

| BPM | Densities passing 3/3 | First failing point |
|---|---|---|
| 300 | 1, 4, 8, 12, 16, 24, 32 | 40 (1/3 fail: hard service 13.0 ms > 8.33 ms); 48 fails 3/3 on hard service; 64 fails 3/3 with throttling and +40 to +118 ms permanent phase |
| 120 | 1, 16, 32 | not searched |
| 100 | 1, 16, 32 | not searched |
| 20 | 1, 16, 32 | not searched |

The highest reproducible passing ceiling at 300 BPM is 32 voices (64 MIDI
messages per 8.33 ms pulse, 7,680 messages/s). Every passing run had exact bytes
and order and no held note. Worst passing p99 3.71 ms, maximum 4.79 ms.

## Diagnosis of the handover's failing repeats

`perf-001-repeat-01` (16 voices, 300 BPM) failed two of three dense repeats with a
constant +25 to +34 ms offset. Measured cause, in two parts:

1. **Harness load inside the quota.** The runner polled `/snapshot` every 10 ms;
   each call serialises and validates the observation inside the container. A/B
   (`perf-001-poll-10-01` against `perf-001-poll-500-01`, same commit) moved CPU
   per run from ~240 to 80 ms (quiet) and ~444 to 198 ms (dense) and removed all
   throttling. Separately, setup CPU (the calibration `docker exec` and
   configuration actions) shared a CFS period with transport start and throttled
   the first ticks (`perf-001-poll-500-density-01` density 8 repeat 3). A 1 s
   recorded settle removed it.
2. **Stock runtime consequence of a stall.** Upstream `clock_internal.c` skips
   ticks when more than one tick behind. Each throttle over ~two ticks left all
   later events late by whole ticks: 29.6 ms throttle → +25.0 ms (3 ticks),
   28.5 ms → +32.9 ms (4 ticks); a 7.2 ms throttle caused one late tick and then
   recovered. The old point is therefore not PERF-008 overload evidence of the
   workload; the tick-skip behaviour is recorded as R19 for PERF-008.

The failed batches are retained unchanged; none is reclassified as a pass.

## Harness changes (no runtime or threshold change)

- `performance_metrics()` reports cumulative CFS throttling deltas and moving
  intervals; unavailable counters are named, regressions rejected. Diagnostic only.
- `performance-capabilities` schema 2 separates `enforced_envelope` from
  `delegation`; Docker's v1 envelope now reports `constrained.mechanism =
  enforced_envelope` with no violations.
- Runner: encoder acceleration disabled in the probe (driver overshoot defect in
  `perf-001-density-01`); oracles built from the complete native export rather
  than the 4096-message snapshot tail (`perf-001-overload-01`); poll interval,
  settle interval, raw samples and source identity recorded.

## Commands

    PYTHONPATH=src python3 -m unittest discover -s tests/contracts -q
    python3 tests/performance_clock_container.py --image monome-emulator:perf-recorder-02 \
      --output artifacts/performance/container/<batch> --tempos 300 \
      --densities 1,4,8,12,16 --repeats 3

## Limitations and remaining PERF-001 obligations

External-clock follower, 24 PPQN clock output, Start/Stop/Continue and tempo
changes are not covered here. Ceilings at 20/100/120 BPM were not searched above
32 voices. No queue metric beyond scheduled native MIDI input exists (R21), so no
queue-recovery claim is made. Per D23, measured overload is regression evidence
for the refactor; no optimisation is attempted now.
