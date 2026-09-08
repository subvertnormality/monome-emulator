# P01 progress: official Crow core runs on the host

2026-09-08, `codex/audio-monitor`. P01 is in progress, not admitted.

Official monome/crow `b340579d94e57e2b43336611b2c4037cff74bb80` and pinned
Lua `32ffee2104c3a19ad2122dbfc5d4a018c273afc7` plus wrDsp
`e1eb9c533fbdec9d68438b22b5cdf179247fd02b` compiled on the existing Ubuntu 20.04
host. `scripts/build_crow_host.py` builds unchanged CASL, slopes, shapes, wrBlocks
and Lua source. A small C adapter binds CASL entrypoints, explicitly advances
samples, observes voltage and records completion events. The STM32 header adapter
supplies fixed-width types only; no peripheral behavior is replaced with no-ops.
Firmware warnings about M_PI constants are preserved in the build log.

Commands:

```sh
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --output .runtime/crow-host-02
python3 tests/crow_core.py --build .runtime/crow-host-02
```

Build manifest: `.runtime/crow-host-02/manifest.json` includes exact pins, command,
adapter digests and executable digest. Evidence:
`artifacts/crow/core-20260908-143755/report.json` and stdout/stderr.
Five assertions execute actual Crow `output.lua`, `asl.lua`, `asllib.lua`, CASL
and slopes: 0-to-5V/100ms ramp (maximum error 0.002170372V), 10ms gate (479 high
samples at 48kHz, within one sample of the 480-sample specification), dynamic
voltage update, a two-stage envelope with exactly one completion event, and
channel independence. A separate intentional Lua error exits nonzero.

These are software CV trajectories, not physical DAC/electrical certification.
No norns connection, Crow input modes, scale quantization, ii, firmware script
upload, realtime scheduler or delivered Lua done callback is claimed yet. The
host currently records queued completion counts and runs bounded test scripts.
The firmware's full embedded startup and C bindings have not been ported.

Next: create an owned PTY/serial endpoint with identity/reset/reply handling and
connect via norns `dev_list_add(DEV_TYPE_CROW, path, ...)`, preserving native
`device_crow.c` and Lua Crow command/event formatting. Current host.lua only
reports absent commands; remove no absent behavior until an explicit optional
device is connected. After the native path works, extend firmware-backed input
and ii adapters, including JF commands, with independent conformance checks.
