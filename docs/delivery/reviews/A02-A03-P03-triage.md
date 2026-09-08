# Stage 2 review triage

Reviewed commit `abef865`, base `f301e76`, Codex medium bounded branch review.
Completed session `01a08272-9f3e-7df1-b8ff-2729c4b23372`;
raw result `A02-A03-P03-review.json`. Earlier `A02-A03-P03-raw.json` failed before
analysis because Codex was absent from the process PATH; one diagnosed retry
used the installed login PATH. No implementation review was counted for that
tool failure.

Three major findings accepted; all remain open pending regression evidence:

1. Native acknowledgement timeout can be followed by a late callback, leaving
   held-input bookkeeping inconsistent while reporting healthy. Make timeout
   sticky, reject later observations/actions, retain late event evidence and
   prove owned teardown. No silent reconciliation or synthetic release claim.
2. Compound releases renewed each callback deadline while the HTTP client had
   only one deadline. Use one action deadline across native recursive releases
   and per-browser release_all. Exhaustion becomes the same explicit sticky
   fault before the Python HTTP deadline, not an abandoned HTTP response.
3. Heartbeats queued behind app.lock can be mistaken for inactivity. Accept
   authenticated heartbeat receipt independently under a short client lease
   lock; keep device operations under the existing application lock. Prove a
   live browser holding input through an allowed long callback survives, and a
   real offline browser still expires and releases its input/audio monitor.

Python changes implement these choices. Native `query` and compound browser
release operations share a single deadline through every callback; exhausted
native waits append a sticky fault. Heartbeat HTTP handling occurs before the
device lock and updates lease time under `client_lock`. Failed lease cleanup
removes the expired client even on native fault, avoiding a stale lease record.

New evidence:

- `artifacts/arc/deadlines-20260908-202634/report.json`: three native checks pass.
  Late arc key-down rejects at 2.010s; after its real late ack arrives, health,
  explicit key-up and release_all all retain `native_ack_timeout`. Compound
  disconnect fails at 8.010s, submits only the first two releases and never
  submits the third or disconnect; it remains faulty after late completion.
  Two releases succeed in 10.500s with a twelve-second action budget. All three
  sessions cleanly stop.
- `artifacts/arc/browser-20260908-202805/{report.json,browser-report.json}`:
  real Windows Chromium receives an authenticated heartbeat response in under
  1.5 seconds while a 5.2-second native callback is in flight. Held K3 and the
  owned audio monitor survive completion. Real network-offline then releases
  the input and stops the monitor. This proves lease lifetime, not continuous
  PCM playback during a blocking callback; audio reads still share the device
  lock, so continuity across long blocking operations remains a limitation for
  the later browser-streaming work.
- `tests/test_arc_contract.py` now checks that two per-owner implicit releases
  receive the same action deadline. Top-level unit and separate contract
  top-level rerun passes 22 tests (`review-fixes-unit-02.log`). Native normal
  arc rerun passes all eight checks (`arc/native-20260908-203035/report.json`).
  Separate contract and normal browser regressions remain pending.

The strengthened in-flight browser check also passes at
`arc/browser-20260908-203150/{report.json,browser-report.json}`: heartbeat completes
within 2.5 seconds of starting the 5.2-second callback, and completion is still
required after 5.2 seconds. Normal browser arc then passes all five checks at
`arc/browser-20260908-203413/{report.json,browser-report.json}`.

The first 68-test contract rerun had one failure: its otherwise-successful
release-evidence recipe was rejected as `source_changed`
(`artifacts/runs/e9c8808719454b93bd073865a91398de/manifest.json`) because a test file
was edited during the suite. The failure was not waived or blamed on runtime
behavior; a complete source-frozen rerun is in progress, with no code/fixture/
test edits until it terminates. Documentation is outside the source digest.

The source-frozen rerun passes all 68 tests in 198.373 seconds, exit 0
(`artifacts/audio/review-fixes-contracts-02.log`), complementing the 22 top-level
unit tests. Every warned subprocess is checked in
`artifacts/audio/review-fixes-process-check.json`; none remains. All regression
processes are terminal. The three fixes and their focused evidence are ready
for the single allowed follow-up; findings remain open until that response.

## Focused follow-up

Completed response `A02-A03-P03-followup-result.json`, session
`01a08288-7c22-7ac0-a85b-a60aabf415cb`, reviewing `3b94aed`: findings 2 and 3
resolved. Finding 1 retained one exact case: a browser-owned release_all with
no recorded inputs skipped native health and falsely acknowledged success after
a timed-out key-down. The reviewer recommended a health check and regression
for that case. Added the native health check before the empty-owner branch;
expanded actual native deadline tests with a browser-owned late key-down and
both owned/ownerless release attempts. Top-level 22 tests pass at
`artifacts/audio/final-owner-unit.log`; native final regression is running.

Both planned review calls are complete. This final change implements the
follow-up's explicit recommendation within the already-reviewed failure policy;
close it only after the concrete native regression passes. No extra cold review
or architecture change is needed, and no finding is waived on budget grounds.

Final native regression passes all four cases at
`artifacts/arc/deadlines-20260908-204420/report.json`: ownerless late-down 2.022s,
browser-owned late-down 2.016s, compound exhaustion 8.024s, compound success
10.496s. Both owned and ownerless release attempts remain explicitly faulty
after the actual late native acknowledgement. All sessions cleanly stop.
Finding 1 is closed by the follow-up's recommended health guard and this exact
native regression. Findings 2 and 3 were confirmed resolved by the follow-up.
There are no remaining substantive review findings and no third review call.

Required tests originally identified:
late arc key-down with post-timeout health/release rejection; several held arc
keys whose individually bounded releases exceed one action budget; a successful
compound release within budget; actual browser heartbeat during a 5.2-second
native callback plus subsequent offline cleanup; affected native/browser and
contract regressions. Add source/evidence identities and results here before
the single allowed focused follow-up. No merge or stage-3 work yet.
