# Source-transition comparison and repeat verification

The same native probe now runs a reset followed by a 50BPM MIDI input stream,
with internal clock at120BPM. At MIDI beat2 it arms quarter-beat sync, whole-beat
sync and a0.6s sleep, then selects MIDI. Switching back to internal preserves
the sleep deadline and reschedules the beat-synced work. This is generic norns
API evidence; Mosaic code and its timing expectations were not changed.

Real-time MIDI is submitted ahead of time through the existing native scheduled
input API. Native delivery timestamps, rather than HTTP acknowledgement receipt,
must stay within10ms of the input schedule. Keys are held during the stream and
released after the assertions so their round trips cannot delay pulse submission.
Reset uses encoder3; key1 belongs to the native menu and was an invalid initial
probe gesture. These harness corrections did not relax the10ms output bound.

Relative to the reset marker, independent expected sync times are2.75s,2.875s
and3s; the sleep is0.6s from its arming marker. Real-time maximum error is4.100ms
on the default runtime and3.725ms on controlled-03 running in real-time mode.
The controlled lane uses the same nominal pulse/reset schedule and literal
nanosecond expectations, with native rounding bounded by1ns. Three fresh native
processes pass and their normalized results agree exactly. Physical input
application latency remains real in the real-time lane; no exact wall-time replay
claim is made.

The repeat runner now retains the candidate installation descriptor and invokes
an independent evidence verifier. `verify-evidence` recognizes controlled-repeat
packages and checks source/runtime identity, the selected native probe and seed,
three distinct sessions, complete hashed artifacts, native cleanup, ordered
inputs/acks, raw emission trace against observed MIDI, and recomputed normalized
equality. It rejects stale implementation evidence by default. Seven focused
contracts pass: three normalization sensitivity checks and four evidence checks
covering missing/reused artifacts, failed children, wrong runtime and MIDI altered
despite a refreshed file hash. Unit fixtures are not native acceptance evidence.

Retained manifests and hashes are in `C16-transition-comparison-evidence.json`.
Reproduce with:

```sh
python3 tests/transition_realtime_native.py
python3 tests/transition_realtime_native.py --install <candidate>/installation.json
python3 scripts/repeat_controlled_probe.py --probe transition --install <candidate>/installation.json
python3 -m unittest discover -s tests/contracts -p test_controlled_evidence.py
python3 -m unittest discover -s tests/contracts -p test_controlled_repeats.py
./dev/emu verify-evidence <fresh-controlled-repeat>/manifest.json
```

P5-06 has focused controlled and real-time evidence. The M5 milestone aggregator,
full source-current admission regression set and remaining Codex follow-up are
still required. The new verifier checks a repeat package, not a full milestone,
and does not promote the default installation or declare D admitted. Mosaic's
opening-note issue, full manual coverage and remaining release stages stay open.
