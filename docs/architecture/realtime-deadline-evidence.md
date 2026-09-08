# Real-time deadline evidence: pending implementation

D20 requires an independently established transport origin, planned musical
positions, native pulse deadlines, and actual MIDI emission timestamps. The
arithmetic in `src/automation/scheduling_metrics.py` implements only the final
comparison. Its `within_event_profile` result is not runtime admission evidence.

## Verified source facts

- `patches/norns/0004-virtual-device-spike.patch` captures `CLOCK_MONOTONIC`
  in the native bridge's `emit()` function, before sending the MIDI packet.
  `src/runtime/native.py` retains the native timestamp separately from receiver
  and log-write timing. Receiver timestamps must not replace emission timestamps.
- `tests/mosaic_timing.py` uses its first emitted note as the swing origin and
  tests individual errors against 10 ms. That historical test is not an
  implementation of D20's independent-origin event profile.
- `src/automation/midi_schedule_evidence.py` validates scheduled MIDI input
  submissions and actual deliveries. Input deadlines alone do not establish
  the internal sequencer clock's phase or its Note On/Off deadlines.
- The selected runtime's actual native source is in WSL. Inspection of the
  checked-in bridge patch does not establish the current internal clock's
  transport mapping. Native execution currently fails with
  `Wsl/Service/E_ACCESSDENIED`; no native mapping claim has been made.

## Next executable slice

1. Inspect the pinned, patched runtime's internal-clock start/reset, tempo
   changes, scheduler wakeup, and Lua resume paths. Identify the existing
   monotonic reference and the exact phase reset used by a transport input.
   Do not infer either from the first emitted note or a Python acknowledgement.
2. If existing observations cannot establish that mapping, add the smallest
   generic native trace at its authoritative clock boundary. Include epoch,
   phase/reference timestamp, source and tempo, and bind it to the runtime
   source identity. Keep application names and musical rules out of the bridge.
   Do not substitute callback execution time for its planned deadline.
3. Use independent probe scripts to test start/reset, nonzero starting phase,
   tempo and source transitions, and delayed callback execution. A delayed
   callback must increase measured error without moving the expected deadline.
   Missing or contradictory epoch evidence must reject the timing claim.
4. Build each application fixture's full ordered Note On/Off plan from its
   inputs and independent musical expectations. Preserve both unrounded intent
   and the explicitly selected native quantisation rule. Same-pitch overlap,
   release-before-retrigger and exact bytes remain separate mandatory checks.
5. Bind forced Stop releases to the Stop input and cleanup contract. Account
   for every emission; do not silently filter unmatched or late notes out of
   the metric population. Feed only the declared scheduled population into
   `scheduling_metrics` after exact count/data/order verification.
6. Integrate the report with source-bound run artifacts and required gates.
   Exercise a false origin, one dropped release, a deadline shift, and a stalled
   callback. Each must fail its intended assertion. Run the 45-second fixtures
   and the separate ten-minute C12 profile, retaining failed runs.

The helper's four Windows unit tests verify arithmetic and malformed/count/order
rejection. They do not verify the native mapping, musical oracle, forced-release
partition, Linux/WSL runtime, or Paranoia checkpoint. Historical timing failures
remain failed evidence. Native implementation and Codex review remain pending.
