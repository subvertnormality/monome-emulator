# P03 virtual arc implementation progress

2026-09-08; no native arc admission yet.

The card depends on C03, already delivered. Work proceeds inside tranche 2 while
A03 persistence capture waits on host pressure; neither gate is waived and no
desktop/Maiden/Docker work starts. A03's restore path was inspected: saved params
are loaded before `collect_live` decides whether to read collected recordings.
Its test now snapshots the saved collection/audio into evidence before restoring,
so it does not depend on retaining the original runtime session directory.

Added `scripts/arc_native_patch.py` and generated
`patches/norns/experimental-arc.patch`. Pinned official norns base:
`14bbeae8646c6717f6bb44c8cd60250bf94b6042`, applied after existing documented host
patches. This is a locally authored physical-device transport adapter; official
Arc Lua, LED/all/segment routines and matron encoder callbacks remain unchanged.
No community fork implementation was copied.

The optional build flag `scripts/build_audio_candidate.py --arc` adds the patch
and records its digest/profile in the candidate manifest. The patch registers a
separate virtual arc only when explicitly enabled in the native environment,
routes four native encoder deltas/keys and connection events, emits all 256 LED
levels plus connection/intensity metadata, and distinguishes arc size/refresh/
intensity from grid. Existing runtime installations are untouched.

Verified generation and strict C syntax/type compilation of both modified C
translation units against actual pinned build headers (`-Wall -Wextra -Werror`):

```sh
python3 scripts/arc_native_patch.py --source .runtime/sampler-01/norns --output patches/norns/experimental-arc.patch --check
```

Exit 0. The helper patches temporary copies, preserving the supplied source.
This is compilation evidence only, not native behavior, lifecycle or browser
acceptance. Remove/rework the adapter when official upstream provides an
equivalent virtual-device boundary or an update changes these interfaces; require
the same generic native/browser arc checks before doing so.

Implemented strict action/snapshot schemas, input ownership and release/reconnect
policy, opt-in `arc_enabled` / `--arc`, capability reporting, native packet
decoding, browser rings/controls and the generic fixture. Native launch clears
inherited `NORNS_EMU_ARC` and enables it only for an explicitly configured,
identified arc candidate. Browser implementation is not yet browser-validated.

Built `.runtime/arc-01/installation.json` and composed its monitor/capture tools
as `.runtime/arc-tools-01/installation.json`; both remain experimental, not admitted
defaults. Build log: `artifacts/audio/arc-build-01.log`.

`tests/test_arc_contract.py`: three contract checks passed. Actual native command:

```sh
PYTHONPATH=src python3 tests/arc_native.py --install .runtime/arc-tools-01/installation.json
```

Eight checks passed with strict cleanup in
`artifacts/arc/native-20260908-195446/report.json`: all rings and independent grid,
relative LED levels, signed/wrapped deltas and MIDI callbacks, disconnect key-up
and rejected disconnected input, reconnect/release-all, independent intensity,
official angular segment wrap, two simultaneous sessions and independent cleanup.
The first six-check run also passed at `native-20260908-195122`. Intermediate
`native-20260908-195330` failed because the test mistakenly used Session as a
context manager; corrected to explicit try/finally close. Its identified orphan
`7c835d76a00d43e5afd0c563ce45ba4e` was explicitly stopped before the passing run.

Windows Chromium browser acceptance now passes five checks at
`artifacts/arc/browser-20260908-195938/{report.json,browser-report.json}`:
all 256 native LED levels/computed fills, all four rings' +/- plus wheel/keyboard
native callbacks, virtual key and device reconnect, intensity and independent
grid, offline transport lease release and browser reload. Screenshot `arc.png`
was also inspected. Command:

```sh
PYTHONPATH=src python3 tests/arc_browser.py --install .runtime/arc-tools-01/installation.json --browsers /mnt/c/Users/andy/Documents/ChatGPT/monome-emulator/.runtime/browsers
```

The initial browser-195807 run failed before browser launch because it assumed
the worktree had its own browser binary. The runner now accepts an explicit
pinned browser directory; native cleanup passed on that failure.

`tests/arc_presence.py` now passes three checks at
`artifacts/arc/presence-20260908-200325/report.json`: the pre-arc sampler runtime
rejects an explicit arc request, a disabled session has zero actual official Lua
arc devices despite inherited `NORNS_EMU_ARC=1`, and an enabled session has one.
The probe emits device count through actual MIDI CC61. Both native sessions
cleanly stop. `python3 -m unittest discover -s tests -p 'test_*.py'` also passes
22 tests (`artifacts/audio/broader-contracts-01.log`); this is the discoverable
unit suite, not every integration script.

Optional unchanged cheat codes arc workflow now passes seven checks at
`artifacts/audio/cheat-codes-sampler-20260908-200640/report.json`. Command:

```sh
PYTHONPATH=src python3 tests/cheat_codes_sampler.py --arc --install .runtime/arc-tools-01/installation.json
```

The imported eight-second sample has 440/880 Hz halves. Native file picker and
grid establish pad-2 playback; half/double/restored-rate controls pass. Three
native +127 deltas on ring 1 move the selected playback window into 880 Hz,
with changed native arc LEDs; three -127 deltas restore 440 Hz. Captured tone
fractions 0.9897 and 0.9728 respectively. Sources remain unchanged and cleanup
passes. This proves the app's default window mode, not every arc mapping.

Remaining gates: relevant composed-candidate integration regressions and
the broader-tranche review. A03 collection persistence has now passed with a
phase-compatible 600 Hz stimulus and unchanged thresholds; see
`A03-persistence-progress.md`. Historical diagnosis: the quiet
run `artifacts/audio/cheat-codes-record-20260908-194334/report.json` passed retained
live playback and wrote three recordings, then failed the whole-file tone oracle.
`artifacts/audio/saved-buffer-windows.json` measures all fifteen half-second
interior windows of the eight-second first recording: tone energy fraction
0.9057–1.0, while the whole-file value is 0.0819. Phase diagnostics are in
`artifacts/audio/saved-buffer-phases.json`. This suggests recording-loop phase
changes; it does not prove complete continuity or justify waiving the gate.
Inspect recording behavior and establish a justified saved-buffer oracle before
rerunning fresh-session restoration. Desktop/Maiden/Docker remain deferred.
