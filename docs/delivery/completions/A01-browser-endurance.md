# A01 progress: browser continuity on the combined runtime

2026-09-08, experimental. Candidate `.runtime/audio-reliability-01` adds the
identified monitor/capture helpers to `.runtime/mosaic-audio-01`. Native source
and Crow remain the combined profile already tested with Mosaic and nb_jf.

`tests/browser_audio.cjs` now accepts AUDIO_CONTINUITY_SECONDS (10–600). With
120 seconds it samples rendered analyser data every approximately 20ms plus
automation overhead, checking the sine recurrence residual across each window.
This is repeated rendered-window sampling, not an exhaustive capture of every
sample or a physical sound-device measurement. The browser is headless and its
speaker output is muted; the actual native signal reaches Web Audio rendering.

Evidence:

- `artifacts/audio/browser-086edd1ca1ec43e29ff1bf3814a967e2/report.json`: all eight
  browser checks pass, including 120.015 seconds / 4,056 sampled windows. Worst
  residual 0.0000384148 is below the unchanged 0.0001 threshold. Observed underrun
  count is zero. Silence, 440/880Hz, volume, listener stop and restart pass.
- `artifacts/audio/monitor-native-086edd1ca1ec43e29ff1bf3814a967e2.json`: monitor
  ownership, explicit retention-gap errors and native port removal on disconnect.
- The browser evidence directory's `session/` export retains runtime/application
  identity and clean owned-process shutdown. The user's older demo was untouched.

Initial sandbox launch was rejected by Windows process creation (EPERM). The
same existing test succeeded with the normal tool escalation; no runtime change
was made to bypass that launch restriction.

The continuous worklet renderer avoids separately scheduled transport blocks
and retains resampling phase. These results support that implementation under
the measured host/browser profile. They do not independently localize the
user's original faint clicks, prove arbitrary-duration clock drift, or establish
physical output latency. Engine-init readiness, OSC isolation and remaining
admission checks still precede tranche-1 commit/merge.
