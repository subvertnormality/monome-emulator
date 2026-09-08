# A01 progress: continuous browser rendering

2026-09-08, worktree `codex/audio-monitor`, base `319e3a0`. A01 remains in progress.

User reported faint clicks in the first browser tone. Replaced individually
scheduled AudioBufferSourceNodes with an AudioWorklet stereo PCM ring and
continuous fractional sample position. Transport blocks no longer restart the
browser's resampling operation. Uses linear interpolation when rates differ,
150 ms initial buffering, 600 ms maximum queue, explicit starvation/overflow and
invalid-data failure. This is monitoring, not synchronized deterministic DSP.

Checks:

- `node tests/audio_stream.cjs`: six passed. Five seconds each at 44.1/48/96 kHz,
  stereo frequency oracle, block boundaries and ring wrap; starvation, overflow,
  and nonfinite input fail. Log: `artifacts/audio/continuous-stream-contracts.log`.
- `node tests/browser_audio.cjs artifacts/audio/stream-session.json`: eight passed
  using native TestSine and actual Chromium output. Ten-second steady-tone
  recurrence residual maximum 0.000037248 (threshold 0.0001), no underruns or page
  errors; silence, 440/880 Hz, volume, stop/restart and no autoplay also passed.
  Report: `artifacts/audio/browser-3b6165ca7a8d4c7b85abf191cb93d57d/report.json`.
  Launch source identity is in `artifacts/audio/stream-session.json`; the test
  session was stopped after evidence collection. Browser launch required normal
  escalation after sandbox `spawn EPERM`; the installed headless browser passed.

The user's existing interactive demo was preserved and still runs its original
server. These checks support the replacement but do not prove that block
resampling was the sole cause of the reported clicks. Long-duration clock drift,
browser stalls and engine readiness remain A01 obligations. No default runtime
promotion and no new complete application compatibility claim. Review at A01
admission must include this change and its bounded queue/error semantics.

Next: identified external SuperCollider class discovery and native mod lifecycle,
minimal initialization-race regression, generic player audio contracts, then
Crow CV/ii feasibility. Do not change the shared candidate or another agent's
Mosaic checkout. The official pinned CroneEngine currently calls doneCallback
immediately after alloc; TestSine uses Function.play. Investigate scheduling
before applying a generic readiness workaround.
