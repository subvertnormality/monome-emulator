# Runtime-stall fault injection

`runtime_stall` is a native-automation-only action for testing application behavior when the
Lua event thread is temporarily overloaded. It is available only with a runtime candidate that
includes `patches/norns/0014-runtime-stall.patch`.

```python
session.action({"type": "runtime_stall", "milliseconds": 250})
```

The integer duration is bounded to 1–1000 ms in the public schema and again in the native
bridge. The action busy-waits on the same Lua event thread that runs script callbacks. Native
MIDI scheduling and other native worker threads continue, so events can accumulate at their
original deadlines and exercise the script's backlog handling. The action acknowledgement is
returned after the Lua thread resumes.

Browser-owned and fixture sessions reject this action. It is a deliberate test fault and does
not model CPU speed, memory pressure, audio load, or every real norns overload mechanism. Its
contract is limited to blocking Lua callback processing while preserving native scheduler
progress.
