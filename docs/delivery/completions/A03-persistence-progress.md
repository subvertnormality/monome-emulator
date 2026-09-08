# A03 persistence progress

2026-09-08, audio-monitor worktree; not persistence admission.

Added `audio_directory` to the Python launcher and `--audio-directory` to the CLI.
It snapshots regular files and nested/empty directories into owned session audio,
preserving relative paths and per-file copied-byte hashes. Preflight rejects
conflicts, missing directories, symlink entries and unsupported filesystem entries.
Streaming copy retains existing source-change checks and never overwrites imports.
Two focused directory tests pass (`python3 tests/test_audio_directory.py`).
Generic native directory-import acceptance passes five checks at
`artifacts/audio/file-import-20260908-191416/report.json`. It uses the CLI for one
session and the Python client plus official nested file picker for another.
Actual 440/880 Hz output stays independent; one session keeps playing after the
other closes. Copied relative paths/hashes, original preservation and exported
identities pass. Run with `python3 tests/audio_file_import.py --install
.runtime/sampler-tools-01/installation.json --directory`.
Retained attempts: `file-import-20260908-190958` explicitly rejected one xrun;
`file-import-20260908-191154` passed root playback then failed nested selection.
Official fileselect inserts `../` at depth > 0; the corrected native recipe
advances E2 past it before choosing the file. Runtime code/oracles are unchanged
by this recipe correction.

The actual cheat codes recording test now has `--save` to select the collection
parameter group through native controls, enable collection of live buffers and
enter the disposable name A through official text entry. Initial recipe
`artifacts/audio/cheat-codes-record-20260908-190355/report.json` did not reach
the save trigger: menu E2/E3 sensitivity is two input ticks per step. Corrected
recipe `cheat-codes-record-20260908-190758` reaches the save routine and writes
collection/parameter files but fails the native acknowledgement deadline.

Native event sequence 34 was submitted at 2141957344392469 ns. Its real ack
arrived at 2141959435177610 ns: 2.090785141 seconds. The adapter timed out at
two seconds before receiving that ack. Matron log records saving all three MIDI
patterns; shutdown is clean. This is evidence of a valid callback exceeding the
fixed deadline, not proof of complete restoration. No application patch or
suppressed timeout was used. The retained native event trace proves the timing.

Next: specify and implement a bounded opt-in session input timeout for long
file operations, preserving default behavior and musical timing assertions;
test actual slow callback completion and an over-budget callback rejection.
Then rerun save and restore the saved data/audio into a fresh session, use the
app's native Load collection picker, and assert actual retained PCM plus isolation.
Arc and broader-tranche review follow; desktop work remains queued.

Implemented `input_timeout` / `--input-timeout`, range 0.1–30 seconds, default 2.
The native wait and public action HTTP deadline use the same session setting;
exports retain it. Musical metrics and actual native ack timestamps are unchanged.
Generic `tests/slow_input_native.py` passes at
`artifacts/audio/slow-input-20260908-191822/report.json`: a real blocking 5.2-second
OS call completes with its MIDI marker in 5.334 seconds under an eight-second
setting (also exceeding the old five-second HTTP wait), while default two-second
waiting rejects in 2.051 seconds. Invalid types/ranges reject before launch;
both native sessions cleanly stop. No app dependency is present in this probe.
The collection save/reload test now selects ten seconds and implements fresh
session restoration using generic data seeds and audio-directory imports. It
checks silence before Load, uses the app's native collection picker, verifies
660 Hz retained playback, and checks the saved source tree was not modified.
That restoration path has not yet executed successfully: fresh runs
`cheat-codes-record-20260908-192015` and `cheat-codes-record-20260908-192326`
failed earlier, during the 9.5-second recording capture, with four and five xruns
respectively. No xrun was waived; both failures and native cleanup are retained.

Host inspection between runs showed WSL load averages 8.21/7.97/7.64, several
busy pytest-xdist workers and a busy Python process. This is a scheduling-pressure
clue, not attribution of a particular xrun to a particular process. The concurrent
Mosaic task was asked to coordinate a quiet capture window if it owns those
workers. No other task's processes were stopped. All audio test handles are now
terminal. Recheck host pressure/coordination before another full capture; do not
turn repeated identical retries into passing evidence. Persistence/arc/review
remain incomplete, and desktop work is still queued.

## Successful fresh-session persistence

The quiet 660 Hz run `cheat-codes-record-20260908-194334` reached Save but failed
whole-file phase coherence. Its eight-second saved PCM is retained under session
`5706d08716b14eda9cde330023d8e889`; `saved-buffer-windows.json` and
`saved-buffer-phases.json` show strong local tone and a phase change. Unchanged
app source initializes its recording loop at `end_point - 0.01`: 7.99 seconds
contains 5273.4 cycles at 660 Hz. This explains why a coherent whole-file oracle
is inappropriate across that recording wrap. No runtime or app fix was made.

The documented recipe now uses 600 Hz, which fits both the 7.99-second record
loop and half-second playback pad in integer cycles. All existing signal
thresholds, xrun rejection and negative controls remain unchanged. Run:

```sh
PYTHONPATH=src python3 tests/cheat_codes_record.py --save --install .runtime/sampler-tools-01/installation.json
```

Five checks pass at `artifacts/audio/cheat-codes-record-20260908-200106/report.json`:
unrecorded buffer rejects the positive oracle; live recording persists after
input-helper disconnect; a second capture retains it; native collection Save
writes audio and params; fresh-session native Load restores playback. Saved PCM
coherent-energy fraction 0.9949, restored output 0.9851 with RMS 0.1317. Sources
and saved collection hashes remain unchanged; both sessions cleanly stopped.
Actual saved collection/audio and identities are retained in the artifact.
The JACK memory-lock warning was emitted, but the capture/process/cleanup gates
passed; no xrun was ignored. This establishes scoped persistence, not click-free
arbitrary live loops or physical device equivalence. Broader-tranche review and
remaining arc integration are still pending; desktop work remains queued.

The same five-check `--save` recipe also passes on the composed
`.runtime/arc-tools-01/installation.json` at
`artifacts/audio/cheat-codes-record-20260908-201053/report.json`, with arc disabled
for the baseline app profile. Sources remain unchanged and both native sessions
cleanly stop. This closes the composed-runtime persistence regression.
