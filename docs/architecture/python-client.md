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
