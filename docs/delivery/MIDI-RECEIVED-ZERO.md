# Received zero boundary and MIDI forwarding

Status: required, unimplemented. Prerequisite: candidate07 and existing boundary
callbacks/epoch claims. Codex arbitration01a087b2-c56f-7d50-8699-ea5b325ede1d.
Source pin remains official14bbeae8646c6717f6bb44c8cd60250bf94b6042; no default
runtime promotion or silent strict-sync change is authorised by this checkpoint.

## Reproduced problem

Clock1 after MIDI Start is received at beat0, but interpolation deliberately
stays frozen before Clock2. Ordinary native sync requires beat>deadline, so the
output waiter at0 misses Clock1 and emits two ticks after Clock2. The generic
native probe fails by25msD/25.486193msR at100BPM without Mosaic. Mosaic also
excludes external Start from its output-boundary adapter, sending notes before
forwarded F8 even when warmed. Retain both negative baselines and their owners.

## Implementation order

1. Add a narrow native output-waiter capability to consume an actually received
   source beat-zero boundary once. Prefer an explicit output tag/private core
   scheduler mode; do not change ordinary clock.sync comparisons to>=. FA alone
   cannot create F8, nor may a guessed tempo create fractional pre-Clock2 pulses.
   Once consumed, the output waiter's next deadline is1/24; Clock2 must not
   replay zero. Preserve all existing sleep/metro/acquisition/legacy parity.
2. Make source-reference/start-epoch publication and output-resume visibility
   consistent. Queue epoch-bearing Start before exposing boundary resumes to
   the scheduler. Preserve lock order and queued-resume claims; never invoke Lua
   while holding the scheduler lock. Test both queued and running callbacks
   crossing Start/Stop/Start and source changes, including stale Start events.
3. Apply these as explicit optional upstream-compatible patches, compose them
   before the verified controlled extraction, build a new immutable candidate,
   and run generic native probes with Mosaic absent. Do not patch the installed
   candidate07 in place. Retain its lock and negative evidence.
4. Route Mosaic incoming Start through the boundary adapter when forwarding is
   enabled. Supply known source origin0 in the new epoch; never adopt a late
   callback deadline as a replacement origin. Retain after-F8 ownership of
   coincident pulses, independent intermediate pulses, cancellation/cleanup and
   repeated external Start reset without echoed cleanup Stop. Source handoff
   without Start preserves receiver progression. No-output behaviour stays
   covered by existing input-clock tests. Preserve stock-runtime loading with
   an explicit capability limitation, not a false synchronization claim.

## Required evidence

- Generic native firstF8 equals the actual input Clock1 in D/R; no tick for FA
  alone, no duplicate zero at Clock2, no speculative fractional subdivisions.
- Atomic Start-before-F8 ordering under delayed/queued delivery; epoch reset,
  source changes, cancellation, fault isolation, and ordinary strict sync parity.
- M-SYNC012/013 cold/warm forwarding pass unchanged absolute note/gate deadlines
  and receiver ticks0,6,12...; no clock on disabled/input-only ports.
- Rerun M-SYNC001..011 and affected timing/recording anchors; later gates,
  fractional rates, wraps, tempo changes, routing/remapping and source handoff.
- Unit/integration matrices for exact boundary ownership and lifecycle; full
  Mosaic unit suite and one focused Codex implementation follow-up.

Literal input-edge forwarding is a separate possible mode, not required for
the minimal constant-tempo repair. Unknown pre-Clock2 fractional intervals
remain unknowable; only the already-received zero boundary is being admitted.
This card does not replace the full manual, emulator release, WSL/Linux or final
unit/integration hardening requirements.
