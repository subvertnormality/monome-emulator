# P02 progress: native Crow clock following

2026-09-08, `codex/audio-monitor`; experimental, no default promotion.

The stock Crow driver searches each serial read for one clock substring. That
cannot reliably count split messages or several messages in one read. The
candidate now retains a bounded per-device framing state and counts complete
canonical `^^change(1,1)` lines, including CRLF. Other input states/channels,
printed substrings and invalid long lines do not become clock pulses. Each
counted pulse enters the existing official norns clock implementation.

`src/devices/crow_clock_frames.h` is copied into the isolated native source by
the declared Crow patch builder, with its diff and build-input identity retained.
Candidate: `.runtime/crow-norns-06/installation.json`, existing host-10. Build 05
failed strict unused-function checks when the helper was included by shared
headers; the corrected helper is inline. No compiler gate was disabled.

Evidence:

- `artifacts/crow/clock-frames-20260908-155248/report.json`: five framing groups,
  including every split point, byte-at-a-time input, grouped pulses, non-clock
  lines and recovery after an overlong invalid line.
- `artifacts/crow/clock-native-20260908-155615/report.json`: 80 actual injected CV
  pulses, a 100-to-150 BPM change, native clock callbacks and native MIDI output
  produced by the script's ordinary `clock.sync(1)`. A below-threshold input does
  not add a pulse. Stable tempo must stay within 10% of each requested rate and
  MIDI intervals within 10% of 600/400 ms, with at least four intervals per phase.
  Both tempos differ from the default internal clock, preventing that false pass.
- `artifacts/crow/native-20260908-155826/report.json`: ordinary Crow CV replies,
  2,000 ordered callbacks and explicit Lua failure propagation still pass.

```sh
python3 tests/crow_clock_frames.py
python3 scripts/build_audio_candidate.py --output .runtime/crow-norns-06 --crow-build .runtime/crow-host-10
python3 tests/crow_clock_native.py --install .runtime/crow-norns-06/installation.json
```

Build output must be fresh. This proves real-time software clock following under
the recorded WSL profile, not hardware timing. Serial framing recovers pulse
counts but cannot recover original timing from arbitrarily delayed/batched data;
the official clock sees reception time. Controlled time, stop/restart policies,
long-run drift and additional clock profiles remain outside this scoped pass.

Next: selected ii/JF support. Canonical `l_ii_mod.c` already maps module commands
and addresses and calls `ii_leader_enqueue`; descriptors live in `lua/ii/jf.lua`
(addresses 0x70/0x75). Official generators `util/ii_mod_gen.lua` and
`util/ii_c_layer.lua` produce metadata and command types. Reuse these and the
official encoder/queue where practical, with a small explicit I2C host boundary.
Assert serialized command correctness independently; do not imply downstream
hardware synthesis. Existing command EOF/deadline/reset, load, console and A01
audio/Mosaic obligations remain open.
