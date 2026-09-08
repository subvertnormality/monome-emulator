# H01 desktop routing — in progress, not admitted

H00 plan checkpoint completed at `97ab62b`. H01 must be tested, reviewed,
committed and merged before H02/H03. Default installation and old demo remain
unchanged. No Maiden/browser/Docker feature implementation has started.

Implemented uncommitted: independently authored bounded-ring JACK-to-Pulse
helper, explicit `--desktop-audio-server` and `--desktop-audio-sink` options,
native owned process lifecycle, optional identified candidate builder and a
generic per-stream sink-monitor acceptance runner. Candidates `.runtime/desktop-01`
and `.runtime/desktop-02` preserve `.runtime/arc-tools-01/installation.json`.
Build uses existing GCC/JACK/PulseAudio 13.99.1 SDK, strict compiler warnings.
No runtime/reference code copied or official runtime replaced.

## Recorded probes

- `artifacts/audio/desktop-20260908-211849/report.json`: startup failure before
  PCM, helper exit 2, all other native services cleaned up. Initial diagnostic
  only reported Pulse OK/JACK faults 0; precise failed stage not established.
  Desktop-02 adds stage/context/stream state diagnostics; subsequent startup
  succeeds. Do not call the original startup failure fixed without explanation.
- `desktop-20260908-212001`: old audio-tone default-engine amplitude caused
  initial silence failure. Official TestSine allocates at 220 Hz / amp 0.5.
- `desktop-20260908-212124`: actual K3 stop still leaves decaying residual
  (RMS .077 over the measured window); retained WAV and complete cleanup.
- `desktop-boundaries-20260908-212404`: paired native JACK and selected WSLg
  RDPSink monitor captures for the same real K3/K2 actions. Playing 440 Hz is
  clean at **both boundaries**: RMS ~.141418, tone energy fraction >.9999999,
  JACK capture xruns 0. Stopped residual exists already at JACK (RMS .01746)
  and at sink (.01824), so desktop transport is not its origin. Diagnostic
  reproduction script: `artifacts/audio/desktop-boundary-probe.py` (ignored).
- `desktop-20260908-212821`: fresh generic desktop-tone explicitly initializes
  amp 0 and reverb return 0, but initial stop capture still fails (.03349 RMS).
  This is **not** a passing package and changing fixture did not resolve it.

Important existing evidence clue: `tests/browser_audio.cjs:24` waits **13 seconds**
before initial K3/silence measurement. H01 currently tests immediately after
session readiness. Investigate native startup/parameter restoration and the
audio settling boundary, rather than weakening the RMS threshold or calling
the residual a transport defect. Snapshot diagnostics include `menu_mode`;
the paired probe proves later K2 produces clean actual 440 Hz.

## Remaining before admission

2026-09-08 root cause established: `startup-stages-20260908-213429` captures
SC and crone together. The same residual fades linearly to zero in both, with
SC silent from second 7 onward. Pinned official `sc/core/Crone.sc` plays a
separate 218/223 Hz chime with `Env.linen(2,4,6)` at boot. Current official HEAD
`1d7209428841bc2b38619c8238ba0d2788bdbe68` still has the chime (2,3,6) and no
disable switch. Git objects inspected in `.runtime/deps/norns`; its checkout
remains at the pin. Reverb/mixer/desktop transport hypotheses are rejected.

Refinement: add an optional `--no-startup-chime` control, default preserving
official behavior. A small independently authored conditional patch against
official `14bbeae8646c6717f6bb44c8cd60250bf94b6042` guards only this boot synth;
the engine and transport remain unchanged. Runtime manifest binds patch bytes
and advertises support; requesting it with an old build must explicitly fail.
Clear inherited override environment values. Removal condition: upstream adds
an equivalent supported switch and passes the same native tests. Acceptance
must prove immediate silence with suppression, actual engine tone/stop afterward,
and retained 218/223 Hz boot audio by default. Do not weaken silence thresholds
or add a fixed warm-up delay. Include the explicit patch in integration review.

Explain startup residual/readiness and initial helper failure; then complete
generic signal, routing, two-session, stop/restart, cleanup tests. Add missing
sink and owned sink-loss failure checks without stopping the shared WSLg server.
Check Pulse underflow/overflow reporting (currently JACK faults are explicit,
Pulse underflow callbacks are not yet counted). Attempt Windows endpoint
loopback separately; current proof is selected sink monitor only, not Windows
endpoint or physical speaker audibility. Update user guide and identities, run
focused contracts and required bounded integration review. Do not merge this
in-progress helper as admitted audio or move to H02/H03.

Reproduction: `python3 tests/desktop_audio.py --install
.runtime/desktop-02/installation.json` in the audio-monitor WSL worktree.
All mentioned runner handles are terminal; no new owned session remains live.

2026-09-08 follow-on evidence: candidate `.runtime/desktop-tools-03/installation.json`
adds stream-start readiness and explicit Pulse underflow reporting. Native chime
checks pass (`startup-chime-20260908-215318`): default 218/223 Hz audio retained,
explicit suppression immediately silent, old candidate explicitly rejected.
Desktop lifecycle suite passes all ten checks (`desktop-20260908-215629`),
including simultaneous isolated 440/880 Hz sessions, stop, restart and cleanup.
The preceding 215435 failure was the test sending one encoder pulse instead of
four pulses required by official sensitivity; the signal oracle correctly failed.
Windows endpoint loopback passes four signal/silence checks
(`windows-desktop-20260908-220118`), RMS approximately .141418, tone energy
fraction above .9999999 at 440/880 Hz, exact captured silence before/after.
Boundary: Windows default WASAPI render endpoint, not physical speaker output.
Optional isolated test dependency PyAudioWPatch 0.2.12.8; installation provenance
is `.runtime/windows-audio-install.json`. No manual listening was required.
Private Pulse test server uses extracted Ubuntu packages with hashes in
`.runtime/pulse-test-packages/manifest.json`; no system daemon or WSLg changes.
Initial private-server probe 220612 failed to locate libprotocol-native.so;
added private module directory to its process-local library path.

Private failures: 220659 test incorrectly expected startup_failed; native preserves
specific backend_dead code, now asserted. 220757 and 220904 confirm both bad-route
failures and reaped processes, but private per-stream capture is silent. 221020
paired capture proves JACK440 RMS .141418 with tone fraction .99999997 while
private per-stream monitor is exactly zero. Fixture key trace confirms K2 delivery.
Investigating whole isolated sink monitor separately; do not label this audio-route
success or relax signal thresholds. All those runners terminal, owned server exit0.

Private monitor diagnosis: `desktop-failures-20260908-221354` six-second paired
recording has first signal at 1.8199375 s. Subsequent complete one-second windows
have RMS .141418 and tone fraction above .99999999; JACK is clean immediately.
This is startup padding from the newly opened private null-sink monitor, not a
silent runtime route. The sink-loss test now retains full six seconds and uses
unchanged signal thresholds on the final two seconds, reporting first-signal time.
This fixture-only refinement does not change the WSLg/Windows latency claim or
accept startup silence there. Integration review must inspect this evidence.

`desktop-failures-20260908-221516` passes all three failure scenarios, with
actual paired JACK/private-sink tone, no silent fallback on selected sink loss,
and all owned service PIDs reaped. Private daemon exit0. Top-level22 tests pass.

A repeat Windows endpoint probe `windows-desktop-20260908-221650` failed while
contract tests ran concurrently: 440Hz RMS .14139, tone energy .6889. Cleanup
passed and desktop helper reported no JACK fault/Pulse underflow. Offline WAV
has two large adjacent-sample jumps at .539433 and .54 seconds (.15646/.14835),
and one125-sample rising-zero-crossing interval against normal100/101 at44.1k.
This is a retained discontinuity, not a passing noisy tolerance. Localize with
simultaneous boundary capture before admission; prior isolated endpoint pass
220118 remains narrowly valid. Do not label the original user's clicks solved.
