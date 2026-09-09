This is the single focused follow-up to H04-retry.json, session
01a084d0-347a-7e13-a7ec-ab749760b36c; do not perform a new whole-branch review.
Trusted single-user local norns/grid emulator; audio explicitly authorized.
Review the accepted startup-cancellation and diagnostic-retention fixes and the
narrow JACK lifetime race correction their actual native regressions uncovered.
Read H04-triage.md and H04-evidence.json. Verify reported evidence and inspect
scripts/container/entrypoint.py, src runtime startup/cleanup changes since d875402,
tests/container_startup_cancel.cjs and container_failures.cjs. Startup SIGTERM is
accepted only before readiness with explicit requested_termination metadata;
normal ready shutdown must still succeed, and SIGSEGV/SIGKILL remain failures.

For the JACK patch, inspect scripts/jack_lifetime_patch.py, its explicit stored
patch, builder identity integration, tests/jack_lifetime.{py,c}, and the recorded
GDB stack. It extends the existing non-audio-thread time mutex over frame reads
and destruction, returns frozen time after close, and guards CPU load. Current
official upstream was inspected at its moved .cpp path; no equivalent fix exists
there. Is the synchronization narrow and correct for this captured shutdown
race, and do actual lifecycle plus deterministic baseline-failure/candidate-pass
evidence adequately close the failure? Do not infer every historical crash was
this race or every original audible click is fixed. Old failures remain false.

Report only substantive unresolved issues with these fixes or their evidence,
otherwise state which original findings are resolved. Do not require physical
hardware/manual listening or admit macOS/native Linux from this Windows host.
Do not modify files or launch concurrent native/audio tests; inspect evidence.
