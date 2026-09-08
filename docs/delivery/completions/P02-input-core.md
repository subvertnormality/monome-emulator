# P02 progress: official Crow input detection on the host

2026-09-08, `codex/audio-monitor`. This is core feasibility, not public input
injection or a native Mosaic/device workflow pass.

The host now compiles unchanged pinned `detect.c`/`detect.h`, wrMeters, wrFilter
and wrMath alongside the existing output core. wrLib is explicitly pinned to
`c44e6b0ff9846ddf69e6f15f3357e2df638fb0f6`. The detect sources are copied byte-for-
byte into the build directory so their hardware frequency header resolves to
the host boundary. Both copied and original source digests are checked by the
test. Original upstream checkouts remain unchanged.

The adapter binds input none/change/stream, voltage readout and deterministic
sample advancement. Detection runs once per 32 samples, as in official IO block
processing. Actual `input.lua` dispatches change/stream callbacks. Frequency
tracking has no implementation: initialization/start/read fail explicitly;
stopping it clears its disabled state. Window/scale/volume/peak/clock bindings
are not exposed yet. There is no electrical ADC model or input noise claim.

Build `.runtime/crow-host-09` and evidence:

- `artifacts/crow/input-core-20260908-153606/report.json`: five grouped checks for
  exact hysteresis boundaries and retained state, stream cadence/query, disabled
  stream, rising-only filtering, and nonfinite/unsupported-input rejection.
- `artifacts/crow/core-20260908-153656/report.json`: existing output CV assertions
  and core Lua-error propagation pass.
- `artifacts/crow/capture-host-20260908-153652/report.json`: ramp/gate capture,
  channel independence, cancellation and restart pass with the input core present.

```sh
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --output .runtime/crow-host-09
python3 tests/crow_input_core.py --build .runtime/crow-host-09
python3 tests/crow_core.py --build .runtime/crow-host-09
python3 tests/crow_capture_host.py --build .runtime/crow-host-09
```

Fresh output directory required. Build 07 failed because the filter source is in
wrDsp rather than wrLib; build 08 diagnosed its additional wrMath link dependency.
Both are preserved build failures. The first input test (153514) assumed an ideal
480-sample interval for `.01`; pinned `Detect_stream` converts the float32 value
and truncates to 14 blocks, or 448 samples. The regression now checks that actual
firmware behavior; it does not change firmware to match an ideal timer.

Next: load the official input module in the serial profile and route public CV
injection through the owned device control socket. Validate native callbacks and
clock behavior, then selected ii/JF. Before changing the serial profile, preserve
interpreted adapters in identified build snapshots so older candidate installations
remain reproducible. Public capture candidate remains `crow-capture-02`/host-06;
host-09 does not expose input injection to native sessions yet.
