# A01 progress: unchanged n.b. audio player

2026-09-08, `codex/audio-monitor`. A01 remains in progress.

The host maps standard local `osc.send` port 57120 to the session's sclang port
only in experimental audio sessions. Native OSC encoding/delivery remains in
use. The separate `.runtime/audio-mod-01` candidate makes Crone's named server
the SC default, matching assumptions of ordinary norns mods. Its sole SC change
is recorded as `default-server.patch` and in interpreted-source identity. Build
binaries are unchanged. Reproduce with `scripts/prepare_audio_mod_runtime.py
--install .runtime/audio-monitor-01/installation.json --output <fresh-directory>`.

`python3 tests/nb_audio.py --install .runtime/audio-mod-01/installation.json`
passed eight checks in `artifacts/audio/nb-player-20260908-141836/report.json`:
baseline silence, note 69 at 440 Hz, release, quarter-velocity amplitude,
per-note octave bend, note-off sweep, two simultaneous notes (523.251 and
659.255 Hz), and complete polyphonic release. All actions use native keys and
encoders; results measure JACK PCM rather than Lua player state. Both chord
fundamentals account for approximately half the signal energy; release windows
are zero. Sessions stopped cleanly. Raw WAVs, source identity and logs retained.

Dependencies are unchanged: DoubleDecker
`8729b9ceee71d2b07067e89fbef5d8b98d6a0c89`, n.b.
`503be3ae9a7f4368a8bc35d6081795e0a130cadf`. The successful run uses n.b.'s
independent checkout under `.runtime/nb-player/dependencies/nb`, not Mosaic.
Acquisition URLs and pins are in `fixtures/apps/nb-audio.lock.json`.
The probe includes n.b., adds its voice parameter and selects the mod normally;
the real system/script mod hooks perform registration and initialization.

Failure `nb-player-20260908-141431` is retained. Its release waveform exposed
a probe error: system `params:bang()` restored reverb after dry routing was set.
Dry routing now follows that bang; the strict silence oracle remains unchanged.

Important supported-subset distinction: this pinned DoubleDecker implements
note_off but inherits n.b.'s empty stop_all. The test proves a 128-note note-off
sweep (the sequencer-relevant path); it does not claim nb:stop_all works or alter
the mod to hide this limitation. Pressure modulation, longer endurance, real
Mosaic audio workflows, generic OSC isolation negatives and A01 admission review
remain to be completed. The default installation and live demo were preserved.

SC class discovery now shares excluded directories with application identity;
an additional native generic probe deliberately places invalid SC syntax under
node_modules to check exclusion. Its separate result belongs to the next
recorded checkpoint, not the eight-player-check report above.

Follow-on `artifacts/audio/nb-player-20260908-165033/report.json` passes eleven
checks on the combined `.runtime/mosaic-audio-01/installation.json`: the eight
existing checks plus per-note pressure at half amplitude (ratio constrained to
0.4–0.6), zero-pressure silence and release after restoring pressure. Native
encoder input selects pressure-to-amplitude routing in the generic fixture and
calls the unchanged player's `modulate_note` method. Actual JACK PCM supplies
the amplitude and silence evidence. This closes the scoped pressure check;
OSC isolation, readiness/click endurance and admission still remain open.
