# P02 progress: native CV input injection

2026-09-08, `codex/audio-monitor`; experimental, no default promotion.

The owned Crow control socket accepts held float32 input voltages, applies them
to the official detector and acknowledges the processing sample index. The
serial profile loads pinned `input.lua`, which delivers change/stream events
through the native Crow driver into script callbacks. None/change/stream and
queries are exposed; unimplemented modes remain explicit errors.

`/crow/input` and `Session.crow_input(channel,volts)` validate channel/value,
retain an input trace and work alongside CV capture. The actual native probe
reacts to a rising input callback by setting output 1 to 5 V; independent output
capture proves that full input-to-script-to-output round trip. Tests also check
strict hysteresis boundaries, falling state, channel 2 stream values, native-key
selection of rising-only mode and invalid-channel/value rejection. Script results
are written to an owned file, not inferred from lossy console lines.

Candidate: `.runtime/crow-input-01/installation.json`, host `.runtime/crow-host-10`.
The builder now stores an identified serial adapter copy. The composer freezes
older adapters before development changes, and runtime verification/launch read
the selected snapshot. `crow-capture-03` preserves the pre-input serial profile.
Official firmware Lua files remain independently identified and verified.

Evidence:

- `artifacts/crow/input-api-20260908-154223/report.json`: four grouped native input
  checks, input trace, measured CV response, clean teardown and exported identity.
- `artifacts/crow/serial-20260908-154434/report.json`: seven serial framing/error
  checks using the frozen input-enabled adapter; frequency remains unsupported.
- `artifacts/crow/identity-20260908-154434/report.json`: copied/changed/missing
  interpreted dependency acceptance/rejection checks.
- `artifacts/crow/capture-api-20260908-154434/report.json`: existing native CV
  capture, missing-trigger rejection, validation/cancellation and shutdown export
  still pass with the input-enabled profile.

```sh
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --output .runtime/crow-host-10
python3 scripts/prepare_crow_runtime.py --install .runtime/crow-capture-03/installation.json --crow-build .runtime/crow-host-10 --output .runtime/crow-input-01
python3 tests/crow_input_api.py --install .runtime/crow-input-01/installation.json
python3 tests/crow_capture_api.py --install .runtime/crow-input-01/installation.json
python3 tests/crow_serial.py --build .runtime/crow-host-10
python3 tests/crow_identity.py --install .runtime/crow-input-01/installation.json
```

Fresh output directories required. This does not establish physical ADC behavior,
scheduled waveform injection, norns Crow-clock synchronization, full firmware
reset, ii/JF or Mosaic integration. Next: clock framing/timing and selected ii/JF,
retaining command EOF/deadline, reset, load and console obligations. A01 audio
admission and broader app workflows remain open.
