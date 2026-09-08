# Focused follow-up: stage 2 slow callbacks

Follow up the three major findings from Codex review session
`01a08272-9f3e-7df1-b8ff-2729c4b23372` of `abef865`.
Read `A02-A03-P03-review.json` and `A02-A03-P03-triage.md` in this directory.
Inspect the current committed fixes and cited regression artifacts. This is the
single allowed focused follow-up, medium effort, ten-minute maximum; do not
repeat a whole-branch cold review or invent new platform scope.

Stakes: trusted single-user norns/grid emulator on Ubuntu 20.04 WSL2, primarily
automated testing. Audio and device work is authorized. Relevant failures are
misleading healthy state, incorrect held-input ownership, lost acknowledgements,
unexpected process lifetime and damage to local projects. No finance, hostile
multitenancy, manual listening or physical hardware certification.

Determine whether these three findings are resolved, or identify a concrete
remaining defect in the fixes:

1. Native acknowledgement timeout is sticky; late completion does not restore
   health or permit further actions. Check the actual late arc callback evidence
   and successful teardown. No fake held-state reconciliation is claimed.
2. A single action deadline now passes through every native release and through
   per-browser release_all, within the existing HTTP budget. Check exhausted
   compound release stops further submission, plus successful compound release
   within its deadline. MIDI events use the same deadline route.
3. Authenticated heartbeat receipt bypasses the device lock using a short lease
   lock; stateful input/audio operations stay serialized. Check the actual
   browser in-flight heartbeat timing, retained K3/monitor ownership and later
   real offline cleanup. This verifies lease lifetime, not uninterrupted browser
   PCM during a long blocking callback. That existing audio-read lock limitation
   remains explicit and is assigned to the queued browser-streaming work.

The triage names all focused and normal regression results and retained failures.
Do not treat an intentionally rejected source-changed evidence run as a waived
runtime failure. Report whether each original finding is resolved; cite exact
code and evidence for any substantive remaining issue. Do not spend this query
on style, optional refactoring or capabilities outside these fixes.
