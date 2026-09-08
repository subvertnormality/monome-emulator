# MIDI connection lifecycle checkpoint

The generic runtime now exposes `midi_connection` through the native device input
path. Configured slots remain stable; official norns add/remove callbacks run
before acknowledgement. Disconnected immediate input is rejected and retained
sends emit nothing. Scheduled bytes keep original deadlines and record explicit
drops while disconnected. Reconnect resets input and capture decoder framing,
preserving output history and held-note accounting. No Mosaic code changed.

Pinned patch `0013-midi-connection-lifecycle.patch` contains only the reviewed
device adapter. Native output and connection transitions share the same mutex;
test-only race pauses are in separately generated installations, never this patch.
Official source revision and prior patches remain unchanged.

Validation: 23 focused contracts; native D/R lifecycle, mixed-port drops, repeated
reconnects, held notes, fragmented/running-status/SysEx messages, 96 orphan bytes
and independent clock byte; previous runtime capability rejection. Generic MIDI
round-trip (1189 emissions), overflow detection, full grid conformance and seeded
coordinate/release failures pass on candidate05. Controlled clock/MIDI clock and
real-time input-origin timing pass. Clean locked real-time and equivalent rebuilt
controlled overlay both pass expanded native lifecycle tests.

Codex found stale output SysEx state and a concurrent send/removal race. Each has
a native failing baseline and passing fix; the follow-up closes both findings.
The race probe proves removal submission overlaps a delayed in-flight send, then
requires the MIDI output before disconnect metadata. Raw review and source-bound
run ledgers are recorded in `C05-hotplug-progress.json`; no complete emulator,
manual, musical timing campaign or controlled-time admission is claimed.

Normal source builds use `emu build` with the updated lock. To avoid writing shared
libraries during parallel development, `scripts/build_locked_candidate.py` builds
clean locked norns sources with an explicitly verified existing library prefix:

```sh
python3 scripts/build_locked_candidate.py --reference-install /path/to/installation.json --output /new/locked-build
python3 tests/midi_hotplug_native.py --install /new/locked-build/installation.json
python3 tests/midi_hotplug_native.py --install /path/to/controlled-overlay/installation.json --clock-mode controlled-experimental
```

The build command does not change `current.json`. A runtime built under the previous
lock is preserved but cannot be silently reused under the new lock. Preserve an
older checkout/installation together for legacy testing. Controlled overlays must
be rebased/rebuilt against the new locked source; they remain experimental.

Race sensitivity is reproducible with `prepare_midi_send_race_probe.py --install
/path/to/installation.json --base-source /path/to/locked/norns --output /new/recipe`,
then `build_controlled_candidate.py --candidate /new/recipe --output /new/race-build`
and `tests/midi_send_race_native.py --install /new/race-build/installation.json`.
The generator verifies captured build-input hashes, and marks the pause test-only.
Use the archived pre-fix source/lock together for the failing side.

Remaining: integrate/push the branch, update main runtime consumers, add real
Mosaic removal-before/during-panic and reconnect cases, then continue all existing
manual and emulator acceptance obligations. No refactor or manual testing gate.

Publication checks preserve the three literal blank context lines in the stored
unified patch. These are patch syntax, not trailing spaces introduced into C.
Its bytes match the lock and the clean reconstructed native source; ordinary
source whitespace checks exclude only this verified patch-data file.
