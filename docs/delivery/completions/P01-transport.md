# P01 progress: Crow transport regression and source verification

2026-09-08, `codex/audio-monitor`; still experimental and not promoted.

The native burst test exposed a stock driver defect: events referenced one
mutable device buffer. A 200-reply burst lost middle replies and repeated its
tail. Evidence: `artifacts/crow/native-20260908-145621/report.json`. The first
ownership-only candidate removed duplication, but its console-based assertion
still reported one missing reply at
`artifacts/crow/native-20260908-150100/report.json`. That run is not a pass or
proof of remaining transport loss: later evidence distinguishes console loss
from actual callback delivery.

`scripts/crow_native_patch.py` now gives each queued Crow event an owned copy of
its bytes. It also repairs the inspected boundary defects: accepts one-byte
reads, reserves space for the terminator, keeps `read` results signed, retries
EINTR and fails explicitly for other read errors. Optional raw RX hex tracing
retains the bytes actually received by matron. No script-specific behavior is
introduced. The generated diff and all patched inputs are recorded by the
candidate builder; official checkout sources remain unchanged.

Candidate `.runtime/crow-norns-04/installation.json` uses the same identified
Crow host `.runtime/crow-host-04`. Its native test passes 600 callbacks in three
bursts, requiring exact order and agreement with captured serial bytes, plus
positive/negative CV replies, one pulse completion and normal teardown:
`artifacts/crow/native-20260908-150750/report.json`. The earlier 200-reply fault
run passed at `artifacts/crow/native-20260908-150623/report.json`. Tests do not
claim electrical timing or input/ii support.

The final strengthened run passes 2,000 ordered callbacks, native-byte agreement,
CV values, pulse completion and error propagation at
`artifacts/crow/native-20260908-151404/report.json`. `crow-callbacks.txt` is written
and flushed by the actual script callbacks into its isolated data directory;
`crow-rx.bin` retains the native serial bytes. Both sequences must match exactly.
The test requires the byte evidence; its absence cannot pass.

This replaces per-callback console assertions after a diagnosed reporting
failure. At `native-20260908-151231`, the final callback ledger contained every
value 1..2000, while the shared console omitted the separate line for 682. The
earlier `native-20260908-150903` similarly received all 600 serial replies but
its console lacked 94. Those runs remain failed diagnostics; the final test
uses the script's externally written result rather than assuming lossless
per-line console output. Investigation of shared console logging remains an
observability obligation, not a reason to weaken callback or byte assertions.

Independent serial contracts pass seven checks at
`artifacts/crow/serial-20260908-145720/report.json`: fragmented identity,
multiline code and 200 ordered responses; explicit errors for unsupported
input, ii, version and upload, overlong lines and syntax errors. Four source
identity checks pass at `artifacts/crow/identity-20260908-145938/report.json`:
exact copies accepted, modified firmware/adapter and missing firmware rejected.
Verification runs before native services start, and again when opening Crow.
Only disposable source copies are changed by those tests.

Commands (fresh output directories required for builds):

```sh
python3 scripts/build_audio_candidate.py --output .runtime/crow-norns-04 --crow-build .runtime/crow-host-04
python3 tests/crow_serial.py --build .runtime/crow-host-04
python3 tests/crow_identity.py --install .runtime/crow-norns-04/installation.json
python3 tests/crow_native.py --install .runtime/crow-norns-04/installation.json --fault none
python3 tests/crow_native.py --install .runtime/crow-norns-04/installation.json
```

Next: CV capture and input injection, official detection/clock and selected
ii/JF protocol profiles. Also retain explicit obligations for incomplete commands
at EOF, nonterminating Crow Lua commands and full reset semantics; these are not
proven by the serial tests above. Profile review remains required before support
is advertised. A01 audio admission and actual Mosaic audio/device workflows are
still outstanding; this progress does not narrow those requirements.
