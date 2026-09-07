# C16: injected MIDI clock and tempo/reset boundaries

Experimental candidate recipe `artifacts/c16/integrated-02` enables the official
norns MIDI clock receiver in controlled mode. Link/Crow still fail explicitly.
The generic native adapter continues to use official clock references and
scheduler code; it does not implement a replacement MIDI clock estimator.
The ignored current-candidate locator selects this separate installation.
The default runtime lock/installation is unchanged.

The candidate also preserves the real-time MIDI packet limit of32760 bytes;
only controlled packets reserve the extra8-byte logical timestamp.

## Automated evidence

Run each named test with `--install /path/to/candidate/installation.json`.
All paths below are relative to `artifacts/c16`.

| Test | Evidence | What it proves |
|---|---|---|
| controlled_midi_native.py | 93b931b69c544480ba2f270a470f2fbb | 25ms native MIDI input pulses settle to100BPM; ignored port cannot trigger transport; Start, Stop, sync and sleep emit independently expected bytes/times |
| controlled_tempo_native.py | f40572f95f404453b92ed11ba6266b3d | Same script as real-time C07: native reset, tempo setter with pending old tick, sync order, cancellation, metro and stop; ≤2ns rounding error |
| controlled_source_faults.py | fbe63823a882483081a3d0727761a060 | Duplicate startup pulses fail with structured invalid-clock diagnostic; Link selection fails with its native reason; exact deliberate abort and remaining process cleanup checked |
| controlled_clock_native.py | a631c213628143798dfd04806a389901 | Existing clock/sleep/sync/wall-time/grid/frame regression on new candidate |
| controlled_boundaries_native.py | 559d0242df0348f8a2815231f4f28a65 | Existing cached-time, cancellation, zero-time work and runaway regression |
| controlled_phase_native.py | b00b3cb5f77c4ed4bd7cb045e48c7c79 | Existing independent absolute-sync phase oracle |

MIDI input warm-up uses49 pulses, replacing the native24-entry estimator's
startup buffer before asserting100BPM. This is explicit setup, not a new estimator
or permission to ignore startup in future Mosaic external-clock tests. A first
diagnostic run08bc0e08 failed a rational sleep deadline by1ns: native double
seconds round upward when converted to nanoseconds. The test now documents that
one-nanosecond bound; musical discrepancies are not absorbed into a jitter margin.
First fault-run63de9962 correctly produced native errors but the harness wrongly
required stderr for a structured error and treated its deliberate abort as an
unexpected shutdown. The final harness requires the actual native reason and
allows only that specific abort in the unsupported-Link case.

Three fresh processes per new positive scenario also passed. Comparison includes
ordered port/bytes/logical timestamps, complete grid, framebuffer hash, final
logical time and outstanding notes. Only host timestamps/process identifiers and
unrelated diagnostic counters are excluded. Exact arrays agree, beyond the small
numeric bounds used by the independent musical oracles.

- MIDI:77dc42c7cd9c41a7855cd4482c60a4a2,
  8393018e81c9439ba5d5e710852b493b,f682e269645048c994faeb624f685e84.
- Tempo:73d684b3343d449ca39760701f4906d8,
  6022c68f57e944fab4ac3d6131f39286,831a3b9721b943fb9011b29315e62db7.
- Comparison report:integrated-02/repeats.json.

## Application time-source audit

Mosaic branch25afe57 uses native metro for autosave/tooltips; clock.sleep for
redraw, blinking, debounce and MIDI housekeeping; clock.sync in its96PPQN lattice;
util.time and clock.get_tempo for recorded MIDI duration; os.time for seed,
scheduler metadata and quantiser cache age. These sources are handled by the
candidate. Its profiler uses os.clock but its inclusion and controls are commented
out in mosaic.lua; CPU profiling is not musical-time acceptance.

Pinned matrix41e11286 uses clock.sleep(0) for deferred parameter bangs and native
beats for modulation timestamps. Toolkit2e9fb56 uses native beats/beat duration
for LFO phase and clock.sync for rhythm alignment; its required upstream lattice
uses the native clock scheduler. The source audit finds no additional active
wall-clock source in those mod paths. This audit is not workflow evidence: actual
modulated MIDI output, startup/autosave determinism and full Mosaic transport
tests still need execution.

P5/M5 remain incomplete. Before admission, complete the remaining application
and mode-gate checks, measure feedback speed, run the bounded Codex-only review,
and retain the real-time lane. The Mosaic opening-note timing failure remains an
open application investigation with its exact-time oracle unchanged.

The three unchanged real-time `tests/clock_native.py` cases pass in37.360s.
Existing subprocess handoff ResourceWarnings remain the recorded C11 obligation;
they were not treated as failed native assertions or hidden by the test runner.
