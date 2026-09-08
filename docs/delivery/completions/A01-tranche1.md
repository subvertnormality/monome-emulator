# Tranche 1 admission — native audio and virtual Crow

2026-09-08. Implementation commits `a7dd08c` and `f66bb22` on
`codex/audio-monitor`. The implemented audio/Crow subset is admitted for opt-in
use on the tested Ubuntu 20.04 WSL2 host. The default MIDI installation is not
replaced. This completes the first delivery tranche; broader scripts and then
Maiden/desktop/Docker remain separate subsequent work, after integration to main.

## Delivered boundaries

- Actual pinned norns/JACK/SuperCollider engine output and bounded WAV
  capture/injection, readiness and native error reporting.
- Identified external n.b. mods, session-local standard OSC routing, actual
  Mosaic playback through unchanged DoubleDecker and stop-to-silence evidence.
- Continuous browser PCM with phase-preserving conversion and explicit gaps,
  automated rendered-audio checks and two-minute sampled continuity evidence.
- Pinned Crow ASL/CASL CV, change/stream voltage inputs, real-time Crow clock,
  native serial callbacks and bounded capture; Just Friends ii write encoding,
  trace isolation, native Mosaic JF command evidence. Instant/asynchronous
  callbacks and reset/reuse are included in the tested subset.
- Generic controls/grid/MIDI/services and capability discovery pass using an
  app-free code root; neither Mosaic nor its mods are core dependencies.

Build from the pinned sources using `docs/AUDIO-DEVICES.md`. The final identified
candidate on this host is `.runtime/tranche1-final/installation.json` **inside the
audio-monitor worktree**. Its fresh canonical parent is `.runtime/tranche1-02`,
with Crow host-16. For launch from the main checkout, pass
`--experimental-install .runtime/worktrees/audio-monitor/.runtime/tranche1-final/installation.json`.
Retained bulky evidence below also resides in that worktree, which is preserved
at `.runtime/worktrees/audio-monitor`; do not remove it as ordinary scratch data.

## Verification and review

`A01-tranche1-candidate.md` indexes the combined native audio, Mosaic, generic,
CV/input/ii/clock, browser/capture/lifecycle results. `A01-triage.md` and its two
raw Codex review records document the bounded critique and focused follow-up.
All four major findings were reproduced, fixed and dispositioned as resolved by
Codex session `01a081ea-72e9-7521-ac5e-9ac599a96703`; this is a focused review,
not whole-product or hardware certification.

The stable initial snapshot passed all **68 contract tests** in
`artifacts/audio/tranche1-contracts.log`. After the Crow fixes, all **6 affected
identity/monitor contracts** passed in `tranche1-postreview-contracts.log`.
Additional native/host regressions and composition mutation negatives are indexed
in the triage. Final canonical build integration passes:

- Mosaic JF: `artifacts/crow/mosaic-jf-20260908-174750/report.json`.
- Native CV input/response: `artifacts/crow/input-api-20260908-174834/report.json`.

Audio native binaries and interpreted SC sources are unchanged from the preceding
combined candidate; the final build composes the reviewed Crow helper and bound
Lua identity. Prior engine, recording, OSC isolation and browser evidence applies
to those unchanged components. No required failure was reclassified as a pass.

## Remaining limitations

The original faint-click source is not independently localized. The new renderer
passes a two-minute sampled continuity check with no observed underruns; this is
not an every-sample, physical-speaker or arbitrary-duration drift guarantee.
Direct host audio/latency measurement belongs to the queued desktop tranche.

One historical matron teardown SIGSEGV remains unexplained. Fresh same-path
negative and subsequent cleanup tests pass with strict exit checks. Capture a
native stack on recurrence; do not waive unexpected exits or call it fixed.

Full Crow firmware/reset/upload, unsupported input modes, ii reads/follower
callbacks/downstream JF sound, electrical timing and arbitrary audio engines
remain outside the supported subset. Full cheat codes 2, arc, Maiden and Docker
are not delivered by this tranche. Queue order remains binding.
