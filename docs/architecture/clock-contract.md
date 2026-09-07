# Native real-time clock and replay contract

Native matron clocks, JACK time, coroutine scheduling and metros remain active.
The current host profile uses dummy JACK at 48 kHz / 1024 frames, non-realtime,
system clock. A native three-period probe found approximately -362.3/-4.2/-0.7 ms
frame-clock drift against monotonic over ten seconds at 128/512/1024 frames.
The 128-frame setting inherited from C00 produced xruns and could both gain and
lose musical phase. Increasing the dummy audio period addresses that host source
of drift without substituting the native time source or changing MIDI/control
thresholds. The full 10-minute supported-profile gate remains C12 work.
Probe evidence: `artifacts/c07-jack-periods.json`; inspected official JACK v1.9.12
commit `c1647819eed6d11f94b21981d9c869629299f357`, `JackTimedDriver.cpp` and
`JackFrameTimer.cpp`. Dummy cycles restart their timing anchor after missed
deadlines; frame count is therefore not inherently a wall-clock oracle under
xruns. Clock-source selection alone cannot correct that behaviour.

The optional `--random-seed` controls only Lua's native PRNG seed, including later
`math.randomseed(os.time())` calls; it never replaces clock/time sources or the
PRNG algorithm. Session metadata and native configuration retain the seed, and
matron logs every requested/applied reseed. Omitting the option preserves normal
behaviour and ignores any inherited emulator seed environment variable.

`anchor` samples a named native beat/time/tempo/transport generation. `wait_beats`
and an action's `at_beat` wait for that anchor plus a beat offset, bounded by their
own timeout and the scenario's deadline. Native transport restart invalidates
old anchors rather than accidentally waiting for a later cycle. Observations and
timeline.json retain native emission-time samples. Replaying a recipe creates a
fresh process and fresh anchors; exact wall-clock replay is not claimed.
Replay validates retained artifact hashes but permits failed or older-source
input bundles: it always executes against the current implementation and creates
new evidence. Ordinary scenario runs retain the prior run reference in replay.json.
Registered procedural packages rerun their current declared test entrypoint, with
the origin printed explicitly; they do not replay an old binary or accept old
results. `verify-evidence` still rejects failed or stale acceptance evidence.

Future MIDI timestamps still acknowledge only after native application. Waiting
occurs outside the shared observation/heartbeat lock, with external actions
serialized separately. The original requested timestamp remains in actions.jsonl;
the native bridge receives the bytes when due. A timestamp already in the past or
more than two seconds ahead fails explicitly. Scheduled-action latency includes
its intentional delay; immediate-input latency is measured separately.

Clock probe expectations are literal: at 120 BPM, quarter-beat sync emits at
125/250/375/500 ms from transport start. Metros emit at 20/40/60 ms, a sleep wakes
at 50 ms, cancelled work never emits, and two same-deadline jobs preserve native
slot order. Distinct overlapping notes must retain on/on/off/off order and drain.

The pinned internal clock publishes references at 24 pulses per beat. A tempo
setter sampled before or after the next thread iteration yields two allowed
120→60 BPM transition phases: nominal or one old-tempo tick (1/48 second) earlier.
The probe retains nominal intent and tests one consistent branch for all following
events with the same 10 ms scheduling bound. It does not use a broad tolerance or
sort events to absorb errors. C12's fixed-120-BPM ten-minute thresholds remain
unchanged; this short probe is not that endurance gate.

Mosaic's independent lattice has 96 pulses per quarter note (192 pulses/second at
120 BPM). A sixteenth is 24 pulses; +25% swing alternates 30 and 18 pulses, with
literal onset positions 0,30,48,78,96,… . All are integral, so intended and rounded
times coincide in this case. The actual UI sets a half-step length mask: 15/9
intended pulses. The pinned lattice starts phase at one and increments it before
checking fractional delayed actions, giving `ceil(period*length)-2` elapsed
pulses: literal 13/7 here. The report retains both ideal intent and this earlier
native dispatch, rather than calling the phase convention scheduling jitter or
hiding it in a tolerance. Broader fractional swing/articulation cases belong to
C09. Generic overlap probes use positive native sleep durations.
The actual Mosaic transport test sets 120 BPM via its native CLOCK parameter
menu, builds its notes via grid input, sets Swing via controls, tests stop silence,
then restarts and checks the same MIDI content. R08's equal-pitch aggregation is
still mandatory separate work.

Seed 42's probe expectations (42,88,54,26,32,81,110,38) come from a standalone
Lua 5.3 PRNG invocation, not Mosaic or a captured emulator golden. Three fresh
processes must agree despite application startup reseeding. A normal unseeded
Mosaic boot is also required.

The capture-cost probe compares a 1,000-iteration no-I/O Lua loop with 1,000
captured native MIDI emissions. The incremental time is a conservative combined
Lua/native emission/capture cost, not an isolated hardware transport benchmark.
Event count, ordering endpoints and drop detection are checked independently.
Native scheduling error and observation latency are reported alongside that cost.
