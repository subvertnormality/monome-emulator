# P01 progress: native Crow CV serial round trip

2026-09-08, `codex/audio-monitor`. Experimental feasibility only; no default
runtime promotion or full Crow compatibility claim.

The unchanged native norns Crow driver opens a session-owned PTY and performs its
identity handshake. An optional build hook supplies this device path. The host
runs pinned Crow output/ASL/CASL/slopes and quote code with a small CV-only serial
startup adapter. All four slopes advance at 48 kHz against monotonic elapsed
time; Lua completion callbacks run after each block of at most 32 samples.
Falling over one second behind fails explicitly. This is not controlled-time
DSP or a hardware latency guarantee.

The adapter supports the identity handshake, CV reset, ordinary Lua serial
commands, output queries and completion replies. It preserves Crow's raw Lua
argument formatting in `tell`, including norns' dynamically registered callbacks.
Unsupported input, scale, clock, ii and firmware-control operations fail; the
profile does not invent a complete firmware version. Full firmware VM reset,
upload/persistence and embedded startup remain unimplemented.

The launcher owns the host process and PTY descriptors, clears inherited device
paths, verifies the helper binary and interpreted Crow Lua/serial adapter digests,
and closes the device with its session. An exited host fails native health checks.
SIGTERM is expected on normal Crow service teardown; a Lua failure remains a
nonzero exit in cleanup evidence.

Reproduction:

```sh
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --output .runtime/crow-host-04
python3 scripts/build_audio_candidate.py --output .runtime/crow-norns-02 --crow-build .runtime/crow-host-04
python3 tests/crow_core.py --build .runtime/crow-host-04
python3 tests/crow_native.py --install .runtime/crow-norns-02/installation.json
python3 tests/crow_native.py --install .runtime/crow-norns-02/installation.json --fault none
```

Build outputs must be fresh directories. Core evidence:
`artifacts/crow/core-20260908-145110/report.json` (five firmware CV assertions and
Lua failure propagation). Native evidence:
`artifacts/crow/native-20260908-145126/report.json` (connection, +5 V, -3 V, pulse
completion, intentional error propagation), and
`artifacts/crow/native-20260908-145233/report.json` (exact numeric replies, single
completion and normal teardown). Inputs enter through public native key/encoder
actions; replies travel through Crow serial and the norns event callbacks.
The generic fixture imports neither Mosaic nor its dependencies.
The strengthened five-check fault run also passes at
`artifacts/crow/native-20260908-145354/report.json`, including exported native
event evidence, exact voltage assertions and single-callback verification.

Earlier native attempts 144825 and 144957 failed because one encoder tick was
below norns' default sensitivity; the fixture now uses four ticks. The first
attempt also exposed a test-finally reporting bug, fixed before recorded passes.
Those attempts are not acceptance evidence.

Remaining P01 obligations: bounded serial overload/fragmentation and unsupported
operation negatives, interpreted-source rejection tests, multi-channel reply
ordering and native driver's shared-buffer behavior under bursts, and profile
review before advertising support. P02 then needs independent CV capture and
input injection, official input detection, clock and selected ii/JF protocol
conformance. Physical downstream synthesis is outside a CV/ii assertion.
