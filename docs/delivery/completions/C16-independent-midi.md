# Independent native MIDI input queue

Implemented the C16-live-handoff input scheduling slice in an isolated
controlled-04 candidate. The default installation and dependency lock are
unchanged. The public API is documented in
[scheduled-midi.md](../../architecture/scheduled-midi.md).

Inspection confirmed that physical `dev_midi_start` reads ALSA bytes and calls
`dev_midi_consume_buffer` on its device thread. Virtual immediate input already
uses that same parser from the bridge receive thread. The new bounded queue
uses monotonic `ppoll` on that thread, delivering bytes and updating native MIDI
clock references independently of Lua acknowledgements. It adds no application
logic and no second decoder thread. Ordered cancellation and EOF cleanup belong
to the same thread. Acceptance, arrival, and callback output are distinct.

Validation:

- Five compiled C queue contracts passed: atomic rejection, capacity, deadline
  boundaries, stable order, late delivery without retiming, cancellation, and
  queue/identity lifecycle.
- Candidate generation and pinned-source build succeeded with
  `prepare_controlled_runtime.py --source .runtime/builds/da993410f493edec/norns
  --output artifacts/c16/integrated-04` and `build_controlled_candidate.py`.
  Build installation is the local sibling runtime-candidate `controlled-04`.
- `probe_scheduled_midi.py --installation INSTALLATION --output
  artifacts/c16/scheduled-midi-02` passed all13 checks on final source. Forty
  events echoed exact bytes/order, with at least four native arrivals while a
  deliberately150ms Lua key callback kept its acknowledgement pending. It also
  checked late/horizon rejection, immediate-input exclusion while scheduled,
  cancellation after one delivery, restored immediate input, pending schedule
  disposal, and clean shutdown of all four services. Raw native inputs,
  deliveries, callbacks, frames, and source identities are retained in the bundle.
  Earlier `scheduled-midi-01` also passed before a report-index validation guard.
- Contract discovery passed53 actual tests but initially reported one failed
  module import because the command omitted `PYTHONPATH=src`. Running
  `PYTHONPATH=src python3 -m unittest discover -s tests/contracts -p
  test_clients.py -v` passed that remaining client test. This establishes54
  passing contracts across those runs, not a claim that the first command passed.
  Existing subprocess ResourceWarnings were printed; lifecycle assertions passed.

Next: integrate scheduled input with Mosaic's M-TIM-004 recipe and evidence
verifier, preserving one continuous intended timeline across UI work. Execute
that real-time case against this explicit candidate. Add logical-domain queued
input where needed to exercise the same timeline under controlled advancement,
then reverse pending-note handoff. The API currently rejects wall-time scheduling
in controlled mode and rejects concurrent immediate MIDI while a batch is active.
Do not relabel the previous Mosaic failure as passed from this generic result.

P5 follow-up must review the queue, public acceptance/cancellation semantics,
native evidence binding, and subsequent musical results. M5 still requires the
fresh differential/three-repeat matrix and resolved review receipt. This does
not complete C16, the manual campaign, or the later release stages.
