# Norns-class performance qualification

This lane prevents a fast development machine from hiding workloads that would
damage musical timing on norns-class hardware. It is fully automated and runs the
same official norns runtime and external-script path as functional acceptance.
It measures the emulator and Mosaic separately: generic probes establish runtime
capacity, then Mosaic stress cases identify application hot paths.

## Hardware facts and limits of the proxy

Monome documents standard norns as a quad-core 1.2 GHz system with 1 GB RAM, using
a CM3 or CM3+ and a Linux real-time kernel:
<https://monome.org/docs/norns/#specifications>. The official norns build uses an
ARMv8/Cortex-A53 release target:
<https://github.com/monome/norns#quick-reference>. Monome also recommends disabling
unused Wi-Fi for CPU performance:
<https://monome.org/docs/norns/help/hardware/>.

Clock frequency and RAM alone do not define executable performance. An x86 CPU
quota is not evidence of Cortex-A53 equivalence, and QEMU wall time is not device
wall time. The release therefore reports `norns-class proxy qualification`, not
measured physical-norns throughput. The proxy becomes a hardware-equivalence claim
only if a future automated CM3/CM3+ lane supplies a locked calibration result.

## Required lanes

1. **Pinned-host regression lane.** Run each workload on an otherwise idle WSL
   host, record CPU time, wall time, voluntary/involuntary context switches, peak
   RSS, allocation/queue high-water marks and all musical latency metrics. Compare
   candidates with the accepted baseline on the same host and runtime lock.
2. **Constrained native lane.** Put the complete owned process group in a cgroup
   or equivalent launcher-owned envelope. Use one event-worker CPU affinity, a
   documented conservative CPU quota, 768 MiB memory maximum and 256 MiB device/OS
   headroom. Calibrate and record the host benchmark on every run; never reuse a
   raw quota across different hosts as though it described a 1.2 GHz A53.
3. **Deterministic cost lane.** Measure work per musical operation independent of
   sleeps: dispatched clock events, Lua callbacks, parameter actions, redraws,
   emitted bytes, queue depth and optional instruction/allocation samples. This
   catches algorithmic regressions even when host load makes wall time noisy.
4. **Real-time musical lane.** Re-run the stress workload in wall time. Controlled
   time can prove order and exact phase, but only this lane can qualify scheduling
   latency, starvation and recovery under contention.

If cgroup CPU control is unavailable in the declared WSL profile, the launcher
must fail that lane with a named capability error. Background load or `nice` alone
does not count as a calibrated limit. Memory limits and affinity remain mandatory.

## Workload matrix

All rows run first as generic probe scripts and then through Mosaic where the
feature exists. Each scenario has a quiet baseline, isolated-axis sweep and at
least one combined worst-case run.

| ID | Workload | Sweep and important combinations |
|---|---|---|
| PERF-001 | Clock/event ceiling | Internal master and external follower; 20, 100, 120 and 300 BPM; smallest supported division; 24 PPQN input/output; Start/Stop/Continue and tempo changes |
| PERF-002 | Dense sequencing | 1, 4, 8 and 16 active channels; every step active; chords; shortest and longest gates; simultaneous note releases/onsets |
| PERF-003 | Parameter pressure | 0, 1, half and all eligible locks per step; trigless locks; slides; trig parameters; repeated values; scale/transposition/octave locks and scale merges |
| PERF-004 | Input pressure | External clock plus live notes/chords, CC and supported device messages; grid holds/combos and encoder edits during playback; bounded valid and rejected floods |
| PERF-005 | Rendering pressure | Maximum meaningful dirty screen cadence, full-grid LED changes, page changes and tooltips while dense playback continues |
| PERF-006 | Storage/lifecycle | Autosave, explicit save/load, project change and reload while stopped; any supported save-during-play path; corrupt/slow storage fault with musical drain checks |
| PERF-007 | Long mixed run | Ten minutes with dense sequencing, locks, edits, display/grid updates, clock-source changes, reconnects and periodic persistence |
| PERF-008 | Overload/recovery | Increase one axis until a declared limit is crossed; require bounded failure diagnostics, no stuck notes, no unbounded queue/RSS growth and recovery after load removal |

The matrix must include pairwise combinations of clock source, channel count,
lock density, output density and rendering pressure. Use covering arrays for the
larger finite domain and explicit three-way cases for external clock + dense locks
+ rendering, and live recording + playback + parameter updates. Toolkit/Matrix
modulation is deferred by current user priority and does not block the base-MIDI
performance lane.

## Musical oracles

Every stress run asserts exact MIDI bytes, ports, note ownership and transport
order before considering performance. It then records p50/p95/p99/max onset and
release error, inter-onset jitter, final phase error, external-clock pulse-to-note
latency, output-clock interval error, input acknowledgement latency, frame age,
grid propagation latency, queue high-water marks and drain time. No event may be
lost or reordered, no note may remain outstanding, and post-Stop clocks must not
restart playback.

The existing ten-minute contract remains the initial musical gate: p99 absolute
event error at most 10 ms, maximum 50 ms and final phase error 20 ms. A performance
candidate must also avoid more than 10% regression in p99 timing or 15% regression
in CPU-per-musical-event against the pinned-host baseline, unless measurement
noise is larger and a recorded calibration justifies a stricter comparison rule.
Peak RSS must remain below the constrained 768 MiB cap and its final five-minute
linear slope must be no more than 1 MiB/minute. Queue depth must return to the
quiet baseline within one bar after transient load. These are engineering gates;
they are not represented as measurements of a physical norns.

For each supported tempo/division pair, calculate the shortest relevant musical
deadline from the independent schedule. Report callback/service time as a fraction
of that deadline. P99 sustained work should consume at most 50% of the interval;
crossing 100% is a hard failure even if buffering temporarily hides missed notes.

## Evidence and optimization loop

Each run records host/kernel/runtime identities, process topology, cgroup values,
calibration score, source digests, workload cardinalities, raw monotonic timestamps,
resource samples and normalized metrics. Run three fresh processes for short
stress cases and one ten-minute run per final tree. Compare a candidate only with
an immediately adjacent baseline under the same profile.

A failing workload produces a minimized reproducer and profile identifying time
by process/thread and by Mosaic callback or Lua function where tooling permits.
Optimize the largest measured cost first, retain the failure as a regression, and
rerun the affected isolated and combined rows. Do not change musical tolerances,
drop redraws/events, or reduce workload cardinality merely to make a candidate pass.
