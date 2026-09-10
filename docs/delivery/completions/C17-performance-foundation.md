# C17 performance foundation checkpoint

Status: scoped foundation passed; C17 and A25 remain in progress.

This checkpoint adds generic measurements needed before Mosaic performance
workloads are admitted. It does not claim physical-norns equivalence or complete
the PERF-001–008 matrix.

## Delivered

- `emu performance-capabilities` records the host, affinity, memory, a versioned
  deterministic CPU calibration, and the constrained-lane capability.
- `--require-constrained` fails with the exact missing capability instead of
  silently running on an unrestricted host.
- Performance arithmetic reports nearest-rank p50/p95/p99/max timing, final
  phase, service-time fractions of the shortest musical deadline, CPU per
  musical event, peak RSS, final-window RSS slope, queue high-water and one-bar
  recovery.
- Candidate comparison enforces the plan's 10% p99 timing and 15% CPU/event
  budgets.
- The process-tree sampler retains CPU and context-switch counters from exited
  descendants and rejects PID reuse as the same process.
- A native smoke exercises the sampler around 40 key transitions through the
  actual official-runtime path and generic `probe-a` script.

## Evidence

- Full contracts: 92 collected, 92 passed, zero skips.
- Native sampler: 42 samples; seven processes; 65–66 threads; 110,000,000 ns
  observed CPU delta; 544,677,888-byte peak aggregate RSS; no runtime errors.
- Direct WSL constrained lane: correctly unavailable with
  `cgroup_controllers_missing`; the mounted cgroup v2 root delegates none of
  `cpu`, `memory`, or `cpuset` to this shell.
- Existing local Docker Engine 20.10.17 uses cgroupfs v1 and an ephemeral
  emulator-container probe demonstrated exact enforcement of quota 50000/100000,
  memory and memory+swap 805306368 bytes, and cpuset `0`. The new aggregate sampler then read those exact limits inside the constrained image and returned CPU, current/peak memory, and throttling counters.
- Raw native sample: `artifacts/performance/sampler-native-mainline-03.json`, SHA-256
  `ff4373226c7cee211b38897f381e03b8c167850a845d98756950eafc3c57be0e`.
- Durable summary: `docs/delivery/performance-foundation-validation.json`.

## Remaining C17 work

Integrate the metrics into the current container/release line so the complete
owned runtime group runs under the verified Docker envelope. Then implement the
generic PERF-001 workload and establish adjacent quiet/dense baselines before
adding Mosaic stress cases. Every workload still needs exact MIDI/grid/screen
oracles; full pairwise coverage, overload recovery, the ten-minute run, and
measured optimization remain outstanding. Toolkit/Matrix stays deferred.

The `/proc` sampler can miss a child that starts and exits entirely between two
samples. The constrained lane must therefore use cgroup CPU and memory counters
as its authoritative aggregate, retaining `/proc` samples for process/thread
diagnostics.
