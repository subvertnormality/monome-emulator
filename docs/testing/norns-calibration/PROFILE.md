# norns performance profile `cm3plus-norns-260102` v1.0.0

An opt-in emulator runtime and profile that make the emulator's Lua thread take
about as long as a physical norns (CM3+, release 260102) does, on any Linux host.
The default emulator runtime and launch path are unchanged.

## Use

```sh
python3 scripts/build_performance_profile_runtime.py --output .runtime/performance-profile
./dev/emu start --script <app.lua> --code-root <code> \
  --experimental-install .runtime/performance-profile/installation.json \
  --performance-profile profiles/norns/cm3plus-norns-260102.json
```

Python client: `Session(..., experimental_install=..., cost_profile=load_profile(path)[1])`.
Every run on a new host should first pass the probe check, which fails closed:

```sh
python3 scripts/calibration/native_probe_run.py --output <dir> --repeats 3 \
  --experimental-install <installation.json> --performance-profile <profile.json>
python3 scripts/calibration/profile_check.py --profile <profile.json> --probe-run <dir>
```

CI does this in `.github/workflows/norns-profile-check.yml`
(`scripts/calibration/ci_profile_check.sh`).

## What it models

Measured on the device first (`d1-probe-*`). A CPU quota was rejected as a
mechanism: bursts shorter than the quota period run at full host speed, so a
0.5-CPU quota did not slow Lua at all. The quota's 100 ms pauses also caused
JACK xruns and clock skips that the device does not have.

| Mechanism | Model | Evidence |
|---|---|---|
| Lua-thread execution | Host time inside each event dispatch (outside wrapped bindings) × Lua factor; repaid by busy-waiting before native outputs, clock reads and at dispatch end | Device kernels 18–20× host for CPU-bound Lua, 7× for memory access |
| Code-shape blend | Factor = geometric blend of six probe kernels (half memory-bound, half CPU-bound), calibrated in-runtime on every host (two passes must agree within 10%) | Mosaic step processing measured about 11× on the reference host |
| MIDI, grid/arc, screen bindings | Absolute device cost per call (4.30, 0.14, −0.65 µs), replacing host native time | Device probe bursts; host native cost does not follow host Lua speed |
| Clock scheduling, catch-up after stalls | Not scaled: same norns clock source as the device | Stall bursts identical on device and emulator |
| Host preemption | Measured per dispatch and reported, not charged | `host_wait_ns` |

Tools in the profile runtime:

- **`runtime_lua_load` action.** Fixed-iteration Lua load, identical to the device burst.
- **`lua_profile_instructions` session option.** Instruction-sampling profiler; it
  writes `lua-profile.json` with deterministic per-line and per-function work.
  Profiled sessions are not timing runs.

## Validation

Device: stock norns 260102, Mosaic `5bef186` app code, 90 BPM, `cc_device`,
3 measured windows after a warm-up. The emulator used frozen v1.0.0 with
self-calibration on each host. Onset p99 is in ms.

| Case | Set | Device | Desktop (Ryzen 5900X, WSL2) | CI (GitHub EPYC 9V74) |
|---|---|---|---|---|
| PERF-002 1 ch | calibration | 2.2 pass | 2.2 pass | 1.9 pass |
| PERF-002 4 ch | calibration | 12.8 fail 3/3 | 8.9 fail 1/3 | 13.1 fail 3/3 |
| PERF-002 8 ch | calibration | 25.4 fail | 18.5 fail | 24.0 fail |
| PERF-002 16 ch | calibration | 41.3 fail | 34.3 fail | 42.0 fail |
| PERF-003 16 ch slides | calibration | 44.8 fail | 44.1 fail | 50.3 fail |
| PERF-005 1 ch + rendering | held out | 1.9 (one 12.0 window) 2/3 | 2.6 pass | 3.1 pass |
| PERF-005 4 ch + rendering | held out | 14.6 fail | 14.2 fail | 14.1 fail |
| PERF-008L 4 ch Lua overload recovery | held out | recovered 2/3 | 2/3 | 3/3 |
| MIX 8 ch slides + rendering + load | held out | 392 fail | 161 fail | 154 fail |

Evidence: `/home/andy/projects/mosaic-behaviour-runs/norns-calibration-20260915`
(`d2/cc-*`, `d2/ho-*`, `emulator-mosaic/p14-*`, `emulator-mosaic/v1-*`,
`ci/run-34964481525`, `ci/run-34969015205`).

## What transfers to a physical norns

- Pass/fail of the unchanged 10/50/20 ms timing gates for Lua-thread-bound
  sequencing, slides and UI rendering at 1–16 channels. The knee is at the same
  or an adjacent tested point.
- Relative change in Lua work: less Lua per step gives proportionally less
  lateness. The instruction-sampling profiler shows where that work goes.
- Recovery behaviour after a Lua-thread overload.
- Magnitudes within about 0.7–1.4× for application-shaped work.

## What does not transfer

- **Pure arithmetic Lua loops** run 1.7–2.4× faster than on the device, and
  cache-heavy table access about 2× slower. One factor blends code shapes.
  Treat optimisations that only remove numeric loops, or only remove table
  lookups, as screening results.
- **Intermittent device spikes** (about one window in four, 12–16 ms) are not
  reproduced. Likely sources are device background load: mods, Wi-Fi and audio.
- **Background CPU contention** (the PERF-008 burner style), the screen render
  thread, JACK/crone audio load, SD storage latency and memory pressure are not
  modelled.
- **Screen bindings** are within 2× only (sub-microsecond glue). They are
  diagnostic in the probe check.
- **Timestamp boundary.** Emulator timestamps come from the native MIDI boundary
  and device timestamps from a Lua send wrapper. The bias is under 1 ms per step.
- **MIDI port load.** The device ran with its real ESI USB MIDI output and ten
  mods loaded; emulator sessions have neither.

Confirm any accepted Mosaic performance change on hardware
(`tests/behaviour/real_norns.py performance`).
