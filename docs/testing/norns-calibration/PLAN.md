# Physical-norns performance calibration: preparation record

Status 2026-09-15: preparation complete, **physical-device access paused**. Nothing
below has been run on the norns in this task. Device facts marked *(recorded
2026-09-13)* come from retained evidence and must be re-confirmed from the device.

## 1. Identities

| Item | Identity |
|---|---|
| Emulator product baseline | GitHub `subvertnormality/monome-emulator` `main` = `05fe7a1743f8517eaabb9184f2541e8bd6586935` (verified with `git ls-remote`, 2026-09-15). The Windows checkout's local `main` (`bd5b898`) and its stale `origin/main` ref (`b672873`) are both ancestors. |
| Calibration worktree | `/home/andy/projects/monome-emulator-norns-calibration`, branch `codex/norns-performance-calibration`, based on `05fe7a1` |
| Windows checkout | `bd5b898`, 192 dirty/untracked paths, untouched |
| Emulator default runtime | official norns `14bbeae8` + `patches/norns/0001`–`0014` (lock `dependencies.lock.json`); JACK dummy 48 kHz/128, non-RT |
| Mosaic | `/home/andy/projects/mosaic-behaviour-tests`, `codex/behaviour-validation` `5bef186a`; tracked tree clean (3 untracked review files) |
| Evidence | `/home/andy/projects/mosaic-behaviour-runs` (performance runs uncompressed; `ARCHIVED.md` covers suite payloads only) |
| Emulator host | AMD Ryzen 9 5900X (12C/24T), 32 GiB, WSL2 kernel 6.6.87.2, Docker 20.10.17, cgroup v1/cgroupfs; load avg 2.28/2.04/1.65 at survey |
| Existing proxy image | `monome-emulator:perf-recorder-02` = `sha256:38b516ef…`, built from `c0d3185` (not current main) |
| Physical norns *(recorded 2026-09-13)* | host `norns`, kernel `5.10.92-18-g458e2253667a` SMP PREEMPT, `armv7l`; norns `42961b9c` (release 240911); stock `clock.lua` `60791d2c…`; ALSA MIDI clients Grid, Norns2sinfonion, ESI M8U eX (16 ports), matron virtual RawMIDI clients 128/129; services jack, matron, crone, sclang, maiden, watcher. CPU model, RAM, CM3 vs CM3+ **not recorded** |

Worktrees `monome-emulator-performance-integration`, `-native-clock-recovery`,
`-perf008-clock-trace`, `-native-clock-phase-probe`, `-runtime-stall`, `-midi-clock`,
`-release-integration`, `-final-qualification`, `-ci-combined` are clean and hold
unmerged candidate work; `ci-combined` HEAD equals GitHub main. None is used as a
baseline.

## 2. Findings that change the calibration design

1. **The device and emulator do not run the same norns.** Device `42961b9c` is
   70 commits older than the emulator pin. Timing-relevant differences:
   - `clock_internal.c`: the device has **no skip-ahead**. A late tick makes the
     next `nanosleep` argument negative, so missed ticks are published as a
     catch-up burst that preserves beat position. The emulator pin skips ahead
     and loses whole ticks. The 722 ms skip / 744 ms lag and PERF-008's 67.76 ms
     phase residue arise from this mechanism, and cannot occur on the device's
     stock clock in that form. PERF-008 phase conclusions therefore do not
     transfer by construction until tested.
   - `jack_client_get_current_time` (clock time base) gained 64-bit wrap handling.
   - Screen command queue 1024 on device vs 16384 in the pin.
   - Grid LED API gained relative levels; `clock.set_source` reschedule rules changed.
   - The emulator default includes `0011-clock-cancel-queued-resume`; stock device
     does not, so Stop produces queued-resume Lua errors on the device.
2. **The 2026-09-13 "physical" PERF-002 runs used candidate `clock.lua`
   `d9ac8d5c…`**, not stock (their saved `stock-clock.lua` is the candidate).
   They are not baseline evidence. They also ran at 122 BPM vs emulator 90 BPM,
   inherited tempo from device state, and report identical `grid_writes`/
   `grid_refreshes` (3618/27) for 1 and 16 channels, which suggests a reporting defect.
3. **Observation boundaries differ.** Device MIDI times come from a Lua wrapper
   around `_norns.midi_send` using `util.time()` = `gettimeofday` (wall clock,
   subject to NTP slew; the field is misnamed `monotonic_seconds`). The wrapper
   iterates `midi.vports` per message, adding Lua cost inside the measured path.
   Emulator times are native `CLOCK_MONOTONIC` at the MIDI bridge. A fair
   comparison needs the same wrapper in both lanes, or native capture on both.
   The device's matron virtual RawMIDI ALSA clients allow native capture
   (`aseqdump`/ALSA seq) and native MIDI ingress without kernel modules.
4. **Observed cost ratio.** Device 16-channel dense: consecutive note-ons ≈1.16 ms
   apart at the Lua boundary, intra-step span p99 24.1 ms, onset p99 36.1 ms, no
   skipped deadlines, matron 40% of one core. Emulator at 0.5 CPU: span ≈4 ms,
   p99 ≈3 ms. Density amplification is 10.2× vs 1.9×.
5. **The CFS quota proxy injects a mechanism the device lacks.** A 50 ms/100 ms
   quota pauses the whole process group (JACK xruns, clock skip-ahead). A 5/10 ms
   period at the same budget removed the PERF-008 phase failure. The device has 4
   cores and slower per-core execution, not time slices. A single-cpuset quota
   also serialises matron, crone, sclang and JACK, which run in parallel on norns.
6. **Emulator main has the recorder** (`src/automation/performance.py`,
   `/performance/*`) and runtime stall injection, but no launcher CPU/memory
   options. Limits exist only as `docker run` flags in test runners.
7. The existing hardware deploy path uses `rsync -a --delete` into a staging
   directory and then `rm -rf` of the installed Mosaic. The replacement procedure
   in §7 avoids both.

## 3. Workload inventory

| Category | Executable today | Device adaptation | Selected use |
|---|---|---|---|
| PERF-001 clock/event capacity | `fixtures/probes/performance-clock` + `tests/performance_clock_container.py` (generic; internal clock only, 20–300 BPM, 1–64 voices); Mosaic M-SYNC/`external_clock_long.py` (functional) | Probe runs unmodified as a norns script. External follower needs ALSA-seq ingress to matron's virtual port | **Calibration**: internal-clock density sweep. **Held-out**: external 24 PPQN follower, tempo change |
| PERF-002 dense sequencing | `perf_dense.py --workload dense`; `hardware_performance.py` PERF-002-HW-1/16 | Exists; needs stock clock, explicit tempo, shared trace, 4/8 channel cases | **Calibration** |
| PERF-003 parameter pressure | `perf_dense.py --workload slides`; PERF-003-HW-16 (never run) | Exists; add 1/8 channel cases | **Calibration** (slides). Scale/transpose merge pressure has no perf recipe; not added unless knees disagree |
| PERF-004 input pressure | `perf_input.py` (512 scheduled events, 216 actions, external clock) | Blocked: needs native ingress ledger. ALSA-seq sender on device supplies it; grid/enc actions via Maiden | **Held-out** |
| PERF-005 rendering | `perf_dense.py --render-pressure` (partial) | Maiden-driven gestures; no frame counters on stock norns (screen-thread CPU via sampler instead) | **Held-out** |
| PERF-006 storage | `perf_storage.py` (partial; no timing oracle) | Excluded unless a storage stall affects output | Characterise SD latency only (diskstats during save) |
| PERF-007 long mixed | `endurance.py` M-ENDURANCE-001 (10 min) | Composition build is long via Maiden; use 10 min of the PERF-003 8-ch + render schedule | **Endurance confirmation**, last |
| PERF-008 overload/recovery | `perf_overload.py` (in-cgroup CPU burners), `internal_clock_stall_phase.py` / `runtime_stall` | Device: bounded 4-process burner (1.5 s) and a Lua-thread busy stall via Maiden | **Held-out** |
| Unseen mix | none | PERF-003 8-ch + render pressure + 200 ms Lua stall | **Held-out** |

## 4. Observables

Captured on both lanes with the same schema. Monotonic time everywhere; realtime
is paired only to map device `util.time()`.

- Musical: independent deadline per step/pulse; MIDI onset/release time at the
  Lua send boundary (shared wrapper) and at the native boundary (emulator bridge;
  device ALSA-seq capture of the virtual port); p50/p95/p99/max; final phase;
  inter-onset jitter; skipped or burst-published ticks (intervals <0.5 or >1.5
  deadlines); note-on/off ownership balance and outstanding notes.
- Scheduling: per-thread CPU ns and run-queue wait (`schedstat`) for matron (main
  Lua thread, clock threads, screen thread, MIDI threads), crone, jackd, sclang;
  voluntary/involuntary switches; JACK xruns from the journal.
- Subsystems (generic probe, §5): Lua kernel time, `midi_send` per message, screen
  command/update cost, grid `led`+`refresh` cost, metro/clock wakeup lateness,
  event dispatch latency for injected input.
- System: per-CPU jiffies, load, PSI where present, MemAvailable, swap in/out,
  major faults, `mmcblk0` diskstats, thermal, `vcgencmd get_throttled`, CPU freq,
  sampler self-cost.
- Errors: Maiden/matron Lua tracebacks (stock queued-resume errors recorded and
  counted, never patched), JACK/crone/sclang journal.

Samplers: `scripts/calibration/thread_sampler.py` (JSON lines, read-only /proc,
same file inside the container) and `scripts/calibration/norns_identity.sh`.

## 5. Competing causes and the smallest distinguishing experiments

| Question | Experiment | Decides |
|---|---|---|
| Is dense-step cost Lua execution, MIDI write, or tracer? | Generic probe on device: pure-Lua kernels; `midi_send` bursts to the virtual port with/without wrapper; same on emulator | Per-subsystem cost ratios; whether one Lua rate factor explains PERF-002/003 |
| Does one rate factor hold across Lua kinds? | Kernels: arithmetic, table churn/GC, string formatting, closure calls | Scalar vs per-kind cost |
| Is contention (4 cores) relevant? | Run-queue wait for matron threads quiet vs with burners | Whether a CPU-share term is needed beyond rate |
| Catch-up burst vs skip-ahead | Generic 24 PPQN probe + 200 ms Lua busy stall, on device and on emulator default | Whether calibration must use a device-matched clock implementation |
| Wrapper vs native egress | Simultaneous wrapper and ALSA-seq capture on device | Observation offset; which boundary Mosaic gates use |
| Internal vs external clock | PERF-001 follower via ALSA-seq clock | Held-out validation |

Candidate profile mechanisms, selected only by calibration fit and then frozen:
(a) short-period CFS quota plus cpuset sized to the device's cores; (b) Lua VM
execution dilation (native count hook scaling thread CPU time by a measured
factor) plus native MIDI/screen/grid per-operation costs; (c) (a)+(b). All opt-in,
inactive by default, stored as a versioned profile. No Mosaic-specific or MIDI-only
delay.

## 6. Minimum device runs

Order runs so quiet and stressed points of each block are adjacent. Stock runtime
throughout, Mosaic `5bef186` exported clean. Repeats: 1 warm-up + 3 measured.

| Block | Runs | Est. device time |
|---|---|---|
| D0 identity, read-only | 1 | 5 min |
| D1 generic probe (Mosaic cleared): Lua kernels, MIDI send, screen, grid, metro, clock density sweep at 300 BPM (1, 8, 16, 32, 48 voices), 200 ms stall catch-up | 3 × each | 30 min |
| D2 PERF-002 dense at 90 BPM: 1, 4, 8, 16 ch | 4 points × (1+3) | 40 min |
| D3 PERF-003 slides at 90 BPM: 1, 8, 16 ch | 3 × (1+3) | 35 min |
| D4 held-out: PERF-005 (16 ch), PERF-008 burner and Lua stall (16 ch), unseen mix (8 ch) | 4 × 3 | 45 min |
| D5 held-out: external-clock follower (PERF-001/004) via ALSA seq, only if D0 confirms the virtual client | 2 × 3 | 25 min |
| D6 endurance (PERF-007 substitute), after the profile is credible | 1 × 10 min | 20 min |

Extra repeats only where noise straddles a pass/fail or knee decision. If a knee
falls between 8 and 16 channels, add 12 channels for that block only.

## 7. Device procedure (after reauthorization only)

Credentials stay in an interactive SSH ControlMaster; nothing records the password.

```sh
ssh -MNf -S /tmp/norns-cal.sock -o ControlPersist=4h we@192.168.0.3   # interactive password
S="ssh -S /tmp/norns-cal.sock we@192.168.0.3"
RUN=/home/andy/projects/mosaic-behaviour-runs/norns-calibration-$(date +%Y%m%d-%H%M)
mkdir -p "$RUN/d0"
$S bash -s < scripts/calibration/norns_identity.sh > "$RUN/d0/identity.txt"
sha256sum "$RUN/d0/identity.txt" > "$RUN/d0/identity.sha256"
```

Confirm the share maps to the device path before any copy:
`$S sha256sum /home/we/dust/code/mosaic/mosaic.lua` vs
`sha256sum /mnt/z/code/mosaic/mosaic.lua` (or `Z:\code\mosaic` from Windows).

Deployment without `rsync --delete` and without deleting the existing install:

```sh
# 1. Record installed hashes (before).
$S 'cd /home/we/dust/code/mosaic && find . -type f -not -path "./.git/*" -print0 | sort -z | xargs -0 sha256sum' > "$RUN/installed-before.sha256"
# 2. Export clean Mosaic HEAD with its lib/nb gitlink and manifest (real_norns.export_head).
# 3. Stream into a fresh staging dir and verify.
tar -C "$EXPORT" -cf - . | $S 'set -eu; D=/home/we/dust/code/.mosaic-cal-staging; test ! -e $D; mkdir $D; tar -C $D -xf -'
$S 'cd /home/we/dust/code/.mosaic-cal-staging && sha256sum -c --quiet -' < "$EXPORT_MANIFEST"
# 4. Swap, keeping the previous install intact for restoration.
$S 'set -eu; B=/home/we/.cache/mosaic-real-norns/calibration-backup; test ! -e $B; mkdir -p $(dirname $B); mv /home/we/dust/code/mosaic $B; mv /home/we/dust/code/.mosaic-cal-staging /home/we/dust/code/mosaic'
# 5. Record installed hashes (after); restore at the end by the reverse two moves.
```

Persistent changes expected: none beyond the Mosaic swap above, restored at the
end; `/home/we/dust/data/mosaic` and `system.state` are backed up by the existing
runner. Probe files go under `/home/we/dust/code/emu-calibration-probe` and are
removed at the end. ALSA-seq subscriptions are non-persistent and removed. MIDI
test traffic goes to matron's virtual port, not the ESI/sinfonion outputs.

## 8. Decisions required before or at reauthorization

1. **Runtime identity for calibration.** Findings 1–2 mean the emulator default
   runtime is not the device's runtime. Options: (i) build an opt-in
   *device-matched* emulator runtime from norns `42961b9c`. Applied in order to that
   revision's files, patches 0002, 0003, 0004, 0005, 0007, 0008 and 0010 have
   rejected hunks, so 7 of 14 need backporting (a substantial but contained effort); (ii) calibrate only execution-cost terms on
   the current pin and report the clock-behaviour differences as untransferable.
   Recommended: (ii) first, since D1 measures whether the catch-up/skip
   difference matters for any selected workload, and escalate to (i) only if it does.
2. Whether the device may receive ALSA-seq subscriptions to matron's virtual MIDI
   client (for native capture and external-clock ingress). Non-persistent.
