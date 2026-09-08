# A03 native sampler controls and live recording

2026-09-08; worktree implementation, broader-tranche review pending.
Candidate: `.runtime/sampler-tools-01/installation.json` (official pinned runtime
plus documented host patches and explicit softcut read bounds). Unchanged locked
cheat codes 2 is optional and external; these tests configure no Crow.

Commands:

```sh
python3 tests/cheat_codes_sampler.py --install .runtime/sampler-tools-01/installation.json
python3 tests/cheat_codes_sampler.py --install .runtime/sampler-tools-01/installation.json --sequence
python3 tests/cheat_codes_record.py --install .runtime/sampler-tools-01/installation.json
```

Evidence:

- `artifacts/audio/cheat-codes-sampler-20260908-185127/report.json`: five checks
  pass. Own file picker, grid pad/loop control and native rate selector produce
  440 Hz, 880 Hz at double speed, 220 Hz at half speed, then restored 440 Hz.
- `artifacts/audio/cheat-codes-sampler-20260908-185546/report.json`: seven checks
  pass with asymmetric 220/330/440/550 Hz markers. Native loop-end editing,
  forward/double/half/restored rates and reverse playback produce the expected
  order in captured PCM. The same reverse oracle rejects forward audio. Analysis
  reuses the independent generic sequence oracle, including its original energy,
  correlation, transition-order and minimum-window assertions.
- `artifacts/audio/cheat-codes-record-20260908-185756/report.json`: three checks
  pass. Unrecorded live pad is silent and fails the positive audio oracle. Grid
  starts/stops real recording around nine seconds of identified 660 Hz injection.
  The eight-second live buffer is filled before freezing; the injection helper
  exits and its ports are absent before two separate retained-playback captures.
  Both captures use no input source and satisfy the original tone oracle.

All tests assert clean native shutdown and unchanged external application and
submodule identity. Controls go through the public automation/native input path;
no app globals, mocked softcut, or application edits are used.

Retained failed recipe: `cheat-codes-sampler-20260908-185308` rejected marker
order `[0,1,0,1,...]`. Inspection showed the app scales starts but preserves
half-second pad duration. The corrected test uses K3 detail, E3 five 0.1-second
steps, K3 overview to extend the pad to one second. No oracle was relaxed.
The recording run's `jack_lsp` prints the usual nonfatal memory-lock warning;
native capture validates zero xruns/nonfinite samples/server failures.

Collection save/reload across isolated sessions now passes; see
`A03-persistence-progress.md`. Virtual arc and its app window-control integration
also pass; see `P03-progress.md`. Still required: the bounded broader-tranche
review and composed-candidate integration closure. Attached
Crow ii module reads remain an explicitly unsupported profile. Desktop/Maiden/
Docker remains queued. These results do not constitute full A03 admission.
