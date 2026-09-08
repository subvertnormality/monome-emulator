# P02 progress: public CV capture through native norns

2026-09-08, `codex/audio-monitor`; experimental, no default promotion.

The Crow host now captures four channels of actual pinned slopes output through
an owned control socket. Capture allocates a bounded buffer, retains finite
samples, writes an exclusively created file and acknowledges completion. It
supports cancellation and its completion race. The native backend owns the
socket/helper lifecycle. The public HTTP/Python API validates requests, permits
one active capture/eight jobs, checks byte counts, hashes output and exports
completed data and manifests. Shutdown cancels active capture before teardown.
See `docs/architecture/crow-capture-api.md` for format and limits.

Candidate: `.runtime/crow-capture-02/installation.json`, composed from the
identified `.runtime/crow-norns-04` native build and `.runtime/crow-host-06`.
Composition verifies both and records the parent installation digest, avoiding
recompilation of unchanged native sources. Crow output/ASL/CASL/slopes remain
official pinned dependencies, not reimplemented trajectories.

Evidence:

- `artifacts/crow/capture-host-20260908-152459/report.json`: captured 100 ms ramp,
  10 ms pulse, channel independence, cancellation and restart. Ramp maximum error
  0.0000941595 V; gate 479 samples at 48 kHz (within one sample of 480).
- `artifacts/crow/capture-api-20260908-152622/report.json`: native script key
  events produce captured ramp/gate; the same gate oracle rejects a deliberately
  absent trigger. Invalid durations and overlapping jobs fail. Cancellation,
  restart, active-job shutdown cancellation and exported files pass. Four grouped
  checks; actual native byte/frame/log/identity evidence is exported under session/.
- `artifacts/crow/core-20260908-152727/report.json`: existing five firmware CV
  assertions and explicit core Lua failure propagation still pass.
- `artifacts/crow/native-20260908-152725/report.json`: the capture-enabled helper
  preserves 2,000 ordered native callbacks and explicit serial error propagation.

Commands:

```sh
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --output .runtime/crow-host-06
python3 scripts/prepare_crow_runtime.py --install .runtime/crow-norns-04/installation.json --crow-build .runtime/crow-host-06 --output .runtime/crow-capture-02
python3 tests/crow_capture_host.py --build .runtime/crow-host-06
python3 tests/crow_capture_api.py --install .runtime/crow-capture-02/installation.json
python3 tests/crow_core.py --build .runtime/crow-host-06
```

Build outputs must be fresh directories. The standalone host test waits for its
identity reply and then 40 ms: pinned slopes retain up to 1024 idle samples as
overflow immediately after initialization. The initial two probes, 151826 and
151917, started too early and failed ramp tolerance; they are retained failures.
The native test requires no such exclusion because native script startup already
waits for the device/runtime. This does not establish a first-millisecond Crow
power-on guarantee, electrical timing, or controlled-time DSP behavior.

Next: CV input injection and official detection callbacks, then clock and selected
ii/JF profiles. Keep incomplete-command EOF, nonterminating Lua command bounds,
full-reset semantics, long-run timing/load and shared-console observability on
the remaining list. The public capture API is not a complete Crow profile or
Mosaic workflow pass; admission review and A01 audio obligations remain open.
