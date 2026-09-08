# Real-time deadline evidence: partial native validation

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
- The selected runtime's actual native source is in WSL. The earlier
  `Wsl/Service/E_ACCESSDENIED` sandbox restriction was resolved using the
  explicitly authorised WSL execution path. Actual source inspection and the
  scoped origin decisions below replace that operational blocker.

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

The arithmetic helper's four unit tests verify arithmetic and malformed/count/order
rejection. They do not establish runtime admission. Source review, the scoped
input-origin verifier and its native fault probes are recorded below. The
application musical oracle, forced-release partition and long-duration admission
remain pending; historical timing failures remain failed evidence.

## Source-based arbitration, 2026-09-08

Codex session `01a07fe2-356c-7462-8b55-fb74e2a30de2` inspected exact copies of
five files from the selected native build. Their hashes are retained in ignored
`artifacts/c16/runtime-origin-source/source-identity.json`; the raw decision is
`artifacts/c16/realtime-origin-arbitration-retry.json`. The first query failed
because the build snapshot had no Git metadata; it made no source changes.

The native system clock uses JACK frame-derived time. Beat references are
published using the actual current JACK time. Existing syncs advance from their
stored desired beat, while a first sync uses the observed beat; the dispatched
resume value is the observed beat, not its desired target. Repeatedly converting
through each newly published reference would hide publication drift. These facts
rule out treating every observed reference update as a new ideal origin.

Implement the oracle with a declared causal deadline for the first immediate
pulse: the transport/input deadline or the scheduled parent's deadline. An
unscheduled coroutine-entry marker supports only invocation-relative latency.
Neither first emitted MIDI nor a later sync target establishes the earlier
transport deadline. External fixtures own musical intent and pulse numbering.

The recommended minimal observational trace covers coroutine entry/causality,
sync registration and target mutations, and internal epoch/effective tempo.
Capture values actually used under existing scheduler locks into a bounded
buffer; drain outside those locks and reject overflow. Include cancellations,
resets and source changes. Derive ideal ticks independently from the declared
epoch/tempo schedule, cross-check traced native targets, and keep that ideal
fixed across ordinary reference publications and catch-up jumps.

JACK/monotonic mapping needs bracketed actual reads, frame/sample-rate identity
and explicit epochs. Later samples check stability rather than refitting origin
or tempo. Codex proposed a 1 ms total uncertainty budget and 100 microsecond read
brackets; these are probe targets, not measured guarantees or an amendment of
D20's existing thresholds. Frame quantisation and observed mapping variation must
be included. Acceptance near a threshold must use the uncertainty envelope.

Before native admission, fault probes must show that delayed registration,
delayed Lua entry, shifted targets, late reference publications, catch-up, lost
trace records and JACK discontinuities fail without moving expected deadlines.
No native instrumentation or mapping validation has been completed by this
source review. The required 45-second and ten-minute runs remain outstanding.

## Fixed-tempo input-origin refinement

Codex follow-up `01a08003-98ce-72f0-876a-c64013958292` accepted a smaller
solution for fresh, stopped, fixed-tempo application fixtures whose independently
specified clock preserves the phase of its immediate first pulse. Declare the
identified backend Play submission as the intended initial deadline. Count all
serialization, logging, dispatch and application latency after that timestamp
as scheduling error. Derive subsequent pulse deadlines from that unchanged
origin and the declared tempo. Do not move it to an acknowledgement, coroutine
entry, first MIDI emission, or subsequent clock reference publication.

This is an external fixture contract, not a general claim that all norns scripts
have this phase behavior. Global-grid sync, tempo/source changes and native-clock
conformance retain their separate mapping obligations. Native clock disturbances
remain observable against the monotonic ideal, although independent errors can
occasionally cancel each other. The review accepted the design, not admission.

`src/automation/input_origin.py` binds a preidentified public action and its
native sequence to one input record, one native acknowledgement and one timing
record. It verifies the exact key/grid arguments and monotonic ordering. The
declared origin must equal the identified submission; an unrelated earlier input
cannot become the origin. Its unit faults exercise shifted, missing, duplicate,
unapplied and contradictory evidence, and show that delayed application does not
move deadlines. These are evidence-verifier tests, not native timing fault probes.

## Native input-origin fault results

The independent `input-deadline` probe declares twenty alternating onsets/releases
four native pulses apart at 120 BPM. Its triggering action is identified before
observing output, with unrelated earlier grid inputs present. The emitted bytes,
order, complete capture, empty final note/input state and source identity are
checked. The origin is never fitted to MIDI. A one-nanosecond origin substitution
is rejected against the input evidence.

All four WSL runs passed their intended assertions:

| Mode | Maximum scheduling error | Expected result |
|---|---:|---|
| Normal | 1.58 ms | Within the unchanged profile |
| 80 ms delay before coroutine entry | 114.54 ms | Profile failure detected |
| 80 ms delay before first sync registration | 65.19 ms | Missed-period delay detected |
| Actual 60 BPM against declared 120 BPM | 398.13 ms | Tempo error detected |

The source-bound compact record is [input-origin-validation.json](../testing/input-origin-validation.json).
These short generic probes establish fault sensitivity for this relative-phase
contract. They do not admit Mosaic timing, arbitrary global-grid scripts, or
tempo/source transitions. The verifier/arithmetic unit suites contain eight
tests; a separate three-test package verifies startup-error preservation when
cleanup also fails.

Remaining application admission work: bind each independently declared pulse
table and its runtime/application identity; verify fresh stopped state and
settled fixed tempo; account for every scheduled onset/release and separately
bounded forced Stop release; run the 45-second fixtures and ten-minute profile.
Retain all historical failures. Thresholds remain 10/50/20 ms.
