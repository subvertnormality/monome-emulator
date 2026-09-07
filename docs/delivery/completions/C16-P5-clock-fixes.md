# Focused fixes following Codex P5

The controlled-03 candidate fixes the Lua wall timer while preserving the default
runtime. `_norns.wall_time_start_timer()` records logical time in controlled
mode, and `_norns.wall_time_get_delta()` returns logical elapsed nanoseconds.
The original real-time branches and CPU timer remain unchanged.

The independent native regression fails on controlled-02: after a host delay,
the wall timer reports 225236305ns while logical time is still zero. Controlled-03
reports exactly 0, 123456789ns after an advance, and 7654321ns after resetting
and advancing again. Three fresh processes agree. The same test passes in both
the default and candidate real-time lanes, checking elapsed time against host
monotonic brackets around the physical key calls.

Candidate builds now export the official pinned Git objects and all six locked
submodules, verify the recursive Gitlink graph, and apply only SHA-bound declared
patches before the experimental patch. They no longer copy the mutable default
build tree. `build-inputs.json` retains all 2554 reconstructed input files before
configure/build. A focused regression modifies a tracked C input and creates an
extra C file in a disposable source checkout; export preserves pinned bytes,
excludes the extra file, and leaves the dirty checkout intact. Runtime metadata
is derived from that reconstructed provenance. Existing candidate provenance
was verified against the same lock; no contamination of controlled-02 is alleged.

The new source-transition probe arms whole-beat sync, quarter-beat sync and
0.4-second sleep at 1.2s, changes from internal120BPM to warmed MIDI100BPM, then
back at 1.4s. Its literal schedule checks quarter-beat output at 1.35s, both
remaining syncs at 1.5s, and unchanged sleep at 1.6s, within the documented 1ns
native rounding. Three fresh controlled processes agree. A real-time transition
comparison is still required for P5-06.

The expanded phase probe starts 100ns and 1ns before, at, and 1ns/100ns after
96PPQN boundaries. Literal rational deadlines distinguish native FLT_EPSILON
boundary selection from a relative musical-duration policy. An internal
transport restart also checks the next24PPQN publication and subsequent48 syncs.
Three fresh processes agree; no Mosaic musical expectation or tolerance changed.

The expected Link-abort test now permits only sclang exits0/-15 and passes both
native fault cases. Other crashes are no longer accepted by that exception.

Exact retained evidence paths and hashes are in
`C16-P5-clock-fixes-evidence.json`. Default descriptor equality with its original
installation was verified. The candidate locator points at integrated-03;
this is not default promotion. Commands:

```sh
python3 scripts/prepare_controlled_runtime.py --source <default-source> --output <new-recipe>
python3 scripts/build_controlled_candidate.py --candidate <new-recipe> --output <new-candidate>
python3 tests/controlled_wall_timer_native.py --install <candidate>/installation.json
python3 tests/controlled_wall_timer_native.py --install <candidate>/installation.json --real-time
python3 tests/controlled_source_faults.py --install <candidate>/installation.json
python3 scripts/repeat_controlled_probe.py --probe wall_timer --install <candidate>/installation.json
python3 scripts/repeat_controlled_probe.py --probe transition --install <candidate>/installation.json
python3 scripts/repeat_controlled_probe.py --probe phase_boundary --install <candidate>/installation.json
python3 -m unittest discover -s tests/contracts -p test_locked_native_source.py
python3 -m unittest discover -s tests/contracts -p test_controlled_repeats.py
```

P5 remains findings-open until the transition comparison, M5 gate and focused
follow-up are complete. Broader affected real-time/controlled regression evidence
must be refreshed on the final admission tree. Mosaic's opening-note issue and
full manual campaign remain open; these are generic runtime fixes and probes.
