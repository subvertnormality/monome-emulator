# Targeted real-time profiling results

The matron-only process sampler completed M-TIM-001 successfully:
`7d0958915644404f8324aaf8b7684c5b`, with wrapper evidence under
`artifacts/c16/thread-timing-03`. All20 phrases,61 onset expectations and60
durations passed; maximum independent sample gap was27.97ms. This is a complete
passing real-time run of the longer case, unlike the earlier failure during its
initial phrase. It does not erase earlier failures or prove endurance stability.

The generic `/usr/bin/perf` launcher is missing a binary matching the WSL kernel,
but the installed `/usr/lib/linux-tools-5.4.0-77/perf` successfully measured a
disposable child with `stat -e task-clock:u`. No package or kernel setting changed.
The subsequent99Hz userspace stack profile used `cpu-clock:u` and4096-byte DWARF
stacks, profiling only the diagnostic command and descendants. Its M-TIM-001 run
`3f0d6e0072514c2d9f91742a6405e620` also passed, with4.026MB retained perf data and
641 samples, zero reported lost samples. Evidence is under
`artifacts/c16/perf-timing-01`.

Process-level CPU sample distribution was python39.94%, sclang28.39%,
matron24.65%, crone3.28%, scsynth1.87% and jackd1.09% (remaining samples in Qt).
These percentages include startup and are **not** a playback-only callback
profile. The initial2% symbol filter hid individual matron entries; reducing it
showed Lua and SDL hotspots. Internal Lua symbols are stripped, so offsets must
not be presented as identified Lua functions or garbage collection. Reproduction:

```sh
/usr/lib/linux-tools-5.4.0-77/perf report --stdio --no-children \
  --sort comm --call-graph none --percent-limit 0 \
  -i artifacts/c16/perf-timing-01/perf.data
/usr/lib/linux-tools-5.4.0-77/perf report --stdio --no-children \
  --comms matron --sort dso,symbol --call-graph none --percent-limit 0.5 \
  -i artifacts/c16/perf-timing-01/perf.data
```

The phase candidate now has a passing full20-phrase controlled run and two full
real-time runs. Earlier real-time misses remain recorded. Next narrow sampling to
playback and obtain usable Lua callback attribution if investigating those
misses; do not introduce a guessed garbage-collector or scheduler change.
Phase/source-transition edge coverage, fresh M5 evidence inventory and Codex
follow-up remain required, alongside the exhaustive manual campaign. No active
runners remain and no default runtime promotion occurred.
