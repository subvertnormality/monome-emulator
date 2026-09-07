# Required queue evidence and a real-time baseline

M5 now requires ten generic check groups: the previous seven plus
`queue-default`, `queue-candidate`, and `queue-controlled`. The controlled group
requires three fresh native sessions with identical normalized MIDI/grid/frame
output. `collect_midi_schedule_check.py` collects these groups;
`midi_schedule_admission.py` independently verifies the native inputs, delivery,
callback bytes and timing, bounded cancellation, expected negative cases, busy
Lua acknowledgement interval, final observation, and four-service cleanup.
Acceptance summaries alone are insufficient. The normal M5 assembler accepts
these manifests through its existing `--check` argument.

Seven admission contracts pass, including mandatory queue groups and binding
public applied timestamps to actual native acknowledgements. Seven rehashed
faults are rejected by `tests/schedule_admission_faults.py`: changed callback
bytes, missing delivery, early arrival, wrong domain, missing advance boundary,
reused session and omitted check.

## Default runtime adapter

Separated the queue from the controlled engine. The device-only candidate
changes only `emu_bridge.c`, its build entry, and the two queue files. It has no
experimental clock implementation. Controlled initialization can explicitly
register a logical clock before input threads start; ordinary runtime startup
never does. An explicit controlled-mode request against the device-only build
is rejected.

The device candidate passed its13-check queue group
`queue-check-d363ab881edc4f9bbce10991b06329bf`, the three real-time clock
regressions in `check-9de209e2b64f4253a87c4fb0dfa7cf5d`, and
`device-adapter-conformance-01`: all128 grid cells, levels/rotations/holds/
reconnect,1189 MIDI round-trip emissions, overflow detection and controlled-mode
rejection. The conformance wrapper changes only the public installation argument
and artifact destinations. A subsequent defensive cleanup change stops an
unexpectedly opened session before failing that negative check.

`pin_midi_adapter.py` reconstructed official pinned Git inputs plus the proposed
patch and required every source byte and executable mode to match the recorded
compiled inputs. Patch0012 is now in the lock; local default lock prefix is
`8b84937d7d187387`. The previously tested binaries were selected without rewriting
any binary or shared library. Previous lock/installation and provenance are
preserved in `.runtime/admissions/device-queue-ebaefa0977e146e594abd7700b50f710`.
This is local device-adapter promotion, not controlled-time or release admission.

The controlled overlay was rebuilt on that baseline as controlled-06. Fresh
required groups, all passed:

- Default real-time queue: `queue-check-0d545aab35bb4020bad08493a6dd8748`.
- Three controlled queue repeats: `queue-check-9b03928104da49918bc577e32bdf19a2`.
- Candidate real-time queue: `queue-check-1f267a510dba4a9496e492e9bcebc50b`.

All group paths are under `artifacts/c16/` with `manifest.json`, hashed native
artifacts and per-phase logs. The seven-fault checker passed on the fresh
controlled group. Earlier05 groups remain historical development evidence.

## Handoff oracle correction

Device-candidate Mosaic run `d0d302945a314c7b9946a50f6596be4d` failed its
forward release prediction by12.435ms. The input queue itself met its arrival
bound. Native evidence showed the chosen pre-grid snapshot was26.907ms before
the first note sounded; its elapsed-tick estimate did not describe the audible
start or actual source-selection instant. This was a test-oracle defect, not a
confirmed Mosaic or adapter defect. The failed run is retained.

Native action responses now expose the actual native acknowledgement sequence
and monotonic timestamp. Mosaic's real-time prediction uses emitted MIDI onset
and runtime-applied control time, interpolating the read-only clock references.
The10ms bound was not relaxed. Logical predictions retain exact logical time.
Corrected device-candidate run `234790227daf49c8bc350c9b2dcb1d6c` passed.
Both directions then passed on the actual default in
`c579bae284e246908c84ae872cb395ca` and on controlled-06 in
`b5007ebc38304abe9ea494e4d6988cd7`. No Mosaic production code changed.

## Remaining work

Collect the remaining seven generic groups, eight legacy controlled probe
families with three repeats, and all14 application/profile comparisons on the
current lock/source. Complete the source-bound Codex P5 follow-up and M5 index;
none is implied by the queue groups passing. Additional handoff phases and
internal tempo-publication edges, queue refill for long continuous MIDI input,
full manual reconciliation, and later delivery stages remain required.
