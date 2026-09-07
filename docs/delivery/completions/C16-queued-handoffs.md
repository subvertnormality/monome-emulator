# Logical queued input and bidirectional Mosaic handoff

The isolated controlled-05 candidate supports explicit logical MIDI schedules.
Its controlled advance visits queued input deadlines before timer work at the
same instant. Native decoder/clock updates and Lua event delivery are retained;
there is no Mosaic logic in the adapter. A queue mutex serializes acceptance,
delivery and cancellation. Wall-time scheduling remains a distinct wire/domain
contract. The accepted/default installation has not changed.

The public client, Mosaic driver and M5 application reader now distinguish
acceptance from delivery. `midi_schedule_evidence.py` rejects missing delivery,
changed bytes/deadlines/ports, early or reordered arrival, wrong time domains,
unknown acceptance, and delivery after cancellation. Failed native submissions
cannot be presented as a successful application run.

Evidence:

- `artifacts/c16/logical-midi-01/results.json`: all11 generic checks pass.
  Forty MIDI arrivals and their actual Lua callback outputs occur at the exact
  intended logical nanoseconds across a large advance. The probe includes the
  one-nanosecond deadline boundary, wrong-domain rejection and cancellation.
- `artifacts/c16/scheduled-midi-05/results.json`: all13 real-time queue checks
  pass on the same candidate, including arrival while Lua acknowledgement is
  pending, byte/order/timing assertions and four-service cleanup.
- Thirteen affected MIDI contracts and five M5 admission contracts pass.
- Mosaic `M-TIM-004` controlled run `00527347d069477f9b84580814f07cc6`
  and real-time run `34898ce5ea29477a9091300c00303668` both pass both directions.
  Each direction submits84 clock/transport events on an uninterrupted timeline.
  Both pending notes meet independently calculated remaining-tick deadlines.
  MIDI Stop is ignored after switching to internal clock; the fourth note of
  the next phrase proves continued playback, then physical grid Stop drains it.
  Source menus and exact MIDI sequences are asserted.
- Earlier forward-only queue runs: `354c11799a0543fcb10d32b6d79228ec` on04,
  and `e27cdf265e7d4baa874bd48ca8317463`/`a12a5a86a5c747ff82154c42f42c5f1f`
  on05, were also successful development evidence.

Reproduce the generic probes with `scripts/probe_logical_midi.py` and
`scripts/probe_scheduled_midi.py`, supplying `--installation INSTALLATION` and
`--output NEW_DIRECTORY`. In the Mosaic worktree run `tests/behaviour/run.py
--case M-TIM-004 --experimental-install INSTALLATION`; add `--clock-mode
controlled-experimental` for D and set `MONOME_EMULATOR` to this checkout.
Real-time use of an experimental candidate is explicitly marked diagnostic.

The reverse test establishes the internal100BPM reference while stopped, then
tests MIDI100 to internal100 phase transfer. Forward transfer covers90 to100BPM.
Changing internal tempo while a note is pending has a further native24PPQN
reference-publication transient; that and additional phases/tempos remain
uncovered edges. The manual requirement remains partial. No Mosaic production
code changed in this slice.

Next, make these queued-input probes and controlled repeats mandatory in M5's
source-bound inventory. The current M5 baseline expects the default real-time
installation, which cannot execute the new queued action yet. Integrate/admit
the real-time device adapter with its required conformance before the final
baseline/candidate matrix; do not silently substitute an unsupported baseline
or waive comparisons. Record the chosen adapter/clock separation in the P5
follow-up. Queued batch extension/refill also remains necessary for longer
continuous external-clock endurance. Final repeats, Codex review receipt, full
manual campaign and remaining release stages are not complete.
