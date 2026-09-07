# Public Python client for external test suites

Development interface: add the selected emulator checkout's `src` to Python's
module path and import `automation.client.Session`. Pin the emulator revision
and dependency lock in the consuming test suite. Distribution packaging is C14.
This client takes external script/code/data paths; it knows no application names.

```python
from automation.client import Session
runtime = Session(script="/path/code/my-app/main.lua", code_root="/path/code",
                  midi_config={"ports": ["Emulator MIDI"]}, random_seed=42)
try:
    runtime.action({"type": "key", "n": 2, "state": 1})
    runtime.action({"type": "key", "n": 2, "state": 0})
    observation = runtime.observe()
finally:
    runtime.close("/path/to/new/run/native")
```

The `action` argument follows `schemas/action.schema.json`. Calls use the same
ordered native input path as the CLI and browser. Encoder deltas remain raw
physical pulses. `observe` returns the schema-defined observation including raw
framebuffer, LEDs, MIDI tail/count and runtime diagnostics. An error is an
exception, never a passing empty observation. `capabilities` exposes unsupported
features. Data seeds and enabled mods use the generic session configuration.

`close` stops the session and copies complete native-event/action logs, frames,
diagnostics, cleanup and source identities into a new caller-owned directory.
It exports no authentication configuration. It propagates shutdown errors and
retains available evidence even on failure. Use complete MIDI events for long
phrases: snapshots contain a bounded tail. Assert cleanup.json service results.
The application suite owns its case selection, recipes, independent oracles,
bounded snapshot retention and pass/fail evidence. It must bind those to the
actual loaded identities. Startup errors include their diagnostic session ID;
never treat a missing native bundle as successful startup or cleanup.

## Experimental controlled-time candidate

The default installation and real-time mode remain unchanged. To investigate
controlled time, explicitly select an installation built by
`scripts/prepare_controlled_runtime.py` and `scripts/build_controlled_candidate.py`:

```python
runtime = Session(script="/path/code/my-app/main.lua", code_root="/path/code",
                  clock_mode="controlled-experimental",
                  experimental_install="/path/candidate/installation.json",
                  random_seed=42)
runtime.action({"type": "advance", "nanoseconds": 125000000})
```

This is **not admitted D-mode acceptance**. The snapshot's `state.clock` reports
its mode, logical nanoseconds and `admitted: false`. Native MIDI records retain
wall-clock `monotonic_ns` and add `logical_ns`; experimental MIDI packets have
native kind11. Advance reports use kind12. `advance(0)` drains same-time work.
An advance is bounded to60 logical seconds and200000 work iterations; runaway
callbacks fail explicitly. The native framebuffer queue is flushed before the
advance acknowledgement. Wall time uses2024-01-01 UTC plus elapsed logical time;
`os.time(table)` keeps native conversion semantics, and CPU profiling remains
CPU time. The current candidate supports the internal clock; other clock sources
and blocking micro-sleep are explicitly rejected. Additional source/cancellation,
modulation, musical application and Codex P5 checks remain required.

The newer opt-in candidate also provides [independent real-time MIDI input
schedules](scheduled-midi.md). Schedule acknowledgements report `accepted`;
native arrival records and actual callback outputs establish subsequent delivery.

Native key, encoder, grid, MIDI and advance acknowledgements now additionally
contain `native.sequence` and `native.monotonic_ns`, copied from the actual
runtime acknowledgement. The outer timestamp remains the server response time.
Use native timestamps for physical input timing, and emitted MIDI timestamps for
audible onset timing; an earlier snapshot can precede the actual onset by many
milliseconds. Controlled musical calculations still use logical time. Queue
acceptance does not carry a fabricated application timestamp.
