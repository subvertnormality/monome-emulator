# Tranche 1 combined candidate

2026-09-08, `codex/audio-monitor`; not admitted or merged.

Fresh canonical build `.runtime/tranche1-01/installation.json` succeeded using
official locked sources and host-15. Unlike the earlier separate candidates, it
contains both the default SC server adapter and engine-ready barrier alongside
the native Crow patches. Build inputs, complete patch and helper identities are
retained. `.runtime/tranche1-tools-01/installation.json` adds identified capture
and monitoring helpers without changing those binaries or interpreted sources.

```sh
python3 scripts/build_audio_candidate.py --output .runtime/tranche1-01 --crow-build .runtime/crow-host-15
python3 scripts/prepare_audio_monitor.py --install .runtime/tranche1-01/installation.json --output .runtime/tranche1-tools-01
```

Fresh init-time audio/stop/cleanup passed:
`artifacts/audio/init-20260908-171913/report.json`. Syntax checks passed for the
capability endpoint and build/review helpers. Actual Mosaic and relevant device,
API, browser and generic regression checks remain to be collected on this build.

The capability endpoint now describes available experimental audio/Crow features
from the selected manifest, retaining explicit absent/unsupported distinctions.
`docs/AUDIO-DEVICES.md` documents pinned acquisition, build/launch commands,
Listen/K2/K3 usage, Python API entrypoints and limits. Physical host audio and
arbitrary engine/peripheral support are not claimed. Review tooling now preserves
an explicit --stakes override for branch review rather than silently replacing
it with the historical MIDI-only description.

Next: finish the scoped integration set, inspect Git status and concurrent main
work, then use the local bounded Codex Paranoia checkpoint. Resolve substantive
findings before admission/merge. The user's instruction requires tranche-1
commit and merge before broader script or desktop distribution work begins.

## Combined regression results

All commands below used `.runtime/tranche1-tools-01/installation.json`:

- `tests/mosaic_audio.py`: `artifacts/audio/mosaic-20260908-172035/report.json`.
- `tests/crow_input_api.py`: `artifacts/crow/input-api-20260908-172539/report.json`.
- `tests/crow_capture_api.py`: `artifacts/crow/capture-api-20260908-172556/report.json`.
- `tests/crow_ii_native.py`: `artifacts/crow/ii-native-20260908-172613/report.json`.
- `tests/mosaic_jf.py`: `artifacts/crow/mosaic-jf-20260908-172629/report.json`.
- `tests/audio_capture_api.py`: `artifacts/audio/capture-api-20260908-172700/report.json` (10 checks).
- `tests/audio_generic.py`: `artifacts/audio/generic-20260908-172917/report.json` (two independent generic scripts, copied into an app-free code root; native services, MIDI, key/grid/frame and capability assertions).
- `tests/crow_clock_native.py`: `artifacts/crow/clock-native-20260908-172946/report.json`.
- Windows `tests/browser_audio.cjs artifacts/audio/tranche1-browser-session.json`: `artifacts/audio/browser-8209c64b13644d59896f8070c3a4db36/report.json` (8 checks). Existing 120-second endurance evidence still applies to the unchanged renderer; this fresh-build check uses 10 seconds.
- `tests/audio_monitor_native.py artifacts/audio/tranche1-browser-session.json`: `artifacts/audio/monitor-native-8209c64b13644d59896f8070c3a4db36.json` (3 checks). Session closed and exported under browser evidence.
- `tests/crow_serial.py --build .runtime/crow-host-15`: `artifacts/crow/serial-20260908-172645/report.json` now also verifies CV/input reset and reuse, without claiming a full VM reboot.

Initial broad `unittest discover` invocation omitted `PYTHONPATH=src`, causing two import errors. Its required-evidence test also correctly rejected source changes made while the suite ran (retained manifest `artifacts/runs/7c52e8d4b61c427da0be175175d14061/manifest.json`, error `source_changed`). The explicit-path focused rerun passes all five affected tests: `artifacts/audio/tranche1-contract-focused.log`. No acceptance threshold or evidence check was weakened. A stable full rerun follows the review snapshot.

Git inspection before the snapshot: main is `319e3a0`, only its delivery `state.json` is modified by concurrent work. This branch does not change that file. The other worktrees remain present. Review uses the local runbook's bounded Codex checkpoint and the explicit audio/device stakes in `reviews/A01-branch-spec.json`.
