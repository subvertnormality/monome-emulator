# A01 progress: public capture and injection

2026-09-08, `codex/audio-monitor`. The capture helper now lives under
`src/runtime/audio/jack_capture.c`; the old test path includes it for existing
feasibility runners. `prepare_audio_monitor.py` builds and identifies both monitor
and capture helpers. Candidate: `.runtime/audio-api-01/installation.json`.

The API and public Python client expose finite capture start/status/cancel.
Optional session-data WAV input is copied and hashed before injection; output
WAVs, completion metrics and digests live in session-owned job directories.
One active job, eight jobs per session, 0.25–30 seconds per job. Shutdown cancels
jobs before native audio services stop. Public client close exports job evidence.
Missing/short completion records, frame mismatches, helper failures and reported
xruns/nonfinite samples/server death cannot become successful results.
See `docs/architecture/audio-api.md` for exact endpoint and client contracts.

`python3 tests/audio_capture_api.py --install .runtime/audio-api-01/installation.json`
passed ten native checks in `artifacts/audio/capture-api-20260908-142826/report.json`:
duration rejection, path escape rejection, overlap rejection, retained input
recording, channel routing, disabled-recording silence, the corresponding failing
tone oracle, cancellation, restart after cancellation, and shutdown cancellation
with public-client evidence export. The initial endpoint-only run (142505) passed
nine checks; the public-client run (142628) passed ten before final completion
metric validation was tightened and retested. No hardware/manual acceptance.

Three existing monitor contracts passed. Their existing background Popen
ResourceWarning was retained; it is not new audio acceptance evidence and should
be resolved with the launcher lifecycle residual. A01 admission review, OSC
isolation negatives, pressure modulation, TestSine startup race and the recorded
matron shutdown crash remain obligations. Default installation is not promoted.

Next eligible device work is P01. Official monome/crow source acquired separately
at `b340579d94e57e2b43336611b2c4037cff74bb80` under
`.runtime/crow-feasibility/crow`; selected pinned submodules Lua
`32ffee2104c3a19ad2122dbfc5d4a018c273afc7` and wrDsp
`e1eb9c533fbdec9d68438b22b5cdf179247fd02b` are being prepared.
The firmware exposes separable Lua output/ASL and native casl/slopes components.
Next prove native host compilation/reuse with explicit hardware callbacks; do not
replace the firmware's Lua semantics with broad no-op stubs or claim CV/ii yet.
