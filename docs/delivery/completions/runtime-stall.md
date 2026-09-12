# Runtime-stall native fault boundary

The emulator now has a generic, bounded `runtime_stall` action that blocks the native Lua event
thread for 1–1000 ms without blocking scheduled MIDI delivery. It does not import or name
Mosaic; Mosaic consumes it only as an opt-in behavior-test fixture.

Validation:

- `PYTHONPATH=src python3 -m unittest tests.contracts.test_contracts tests.contracts.test_native_identity`
  passed 25 tests.
- `python3 tests/runtime_stall_native.py --install
  /home/andy/projects/monome-runtime-candidates/runtime-stall-02/installation.json` passed. Forty
  CC events scheduled at 5 ms intervals were delivered by the native scheduler during a 250 ms
  Lua stall, in order, with maximum deadline error below 15 ms; all 40 Lua callbacks ran after
  the stall and no event was lost.
- Invalid duration, type and additional-property inputs are rejected. Fixture/browser ownership
  is rejected before reaching the runtime.
- `git diff --check` passed.

The passing native result is under `artifacts/runtime-stall/`. This demonstrates the intended
fault boundary on WSL2; it is not a physical-norns performance equivalence claim.
