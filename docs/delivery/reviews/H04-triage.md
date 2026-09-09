# H04 review triage

Initial launch failed because Codex was absent from the subprocess PATH; raw
`H04-raw.json` is a tool error, not a completed review. A diagnosed process-only
PATH correction produced the completed one-shot review in `H04-retry.json`,
session `01a084d0-347a-7e13-a7ec-ab749760b36c`, at candidate `d875402`, base996c67c.
The reviewer inspected existing evidence and matched all14 report hashes; it did
not rerun tests. One focused follow-up remains available.

The major finding, missing regression, and suggested improvement describe one
startup-cancellation gap. Accepted: the container SIGTERM handler set an event
which the synchronous startup loop did not inspect. The fix passes that event
into the launcher's polling loop and routes cancellation through its existing
owned termination and30-second cleanup wait. It checks recorded native exit
statuses before reporting a clean cancellation. The default caller path and
existing input/browser protocols remain unchanged.

`tests/container_startup_cancel.cjs` blocks a disposable real Lua init after
writing a data marker, stops before readiness, requires bounded clean cancellation,
then edits that disposable script and reopens the same container/data identity.
The pre-fix image h04-05 fails this regression in
`artifacts/docker/startup-cancel-1788935125472/report.json`: stopping took20.292s
and reported an init timeout/exit1 instead of cancellation. It was not killed
by Docker's40-second timeout in this experiment. The failure remains retained.
Candidate verification is pending.

The first corrected polling candidate h04-06 failed in
`artifacts/docker/startup-cancel-1788935401515/report.json`: matron exited SIGSEGV
while the old normal-quit sequence interrupted unfinished Lua init. This remains
a failed native result; its exact crash site is not claimed localized. The
adapter now skips the queued EVENT_QUIT path only when startup is explicitly
interrupted before readiness, sends SIGTERM to that owned matron group, and
records `requested_termination: startup_sigterm`. Only that requested signal
exit is accepted in this phase; SIGSEGV and unexpected SIGKILL remain errors.
Ready-session graceful cleanup is unchanged. No Lua cleanup-hook execution is
promised when initialization is aborted. This is a deliberate startup shutdown
behavior, not reclassification of the observed crash as a pass. The focused
follow-up must review this refinement and its actual regression evidence.

Candidate h04-07 still required SIGKILL after the requested SIGTERM and remains
failed (`startup-cancel-1788935729335`). The installed SDL2 header and
[official SDL documentation](https://wiki.libsdl.org/SDL2/SDL_HINT_NO_SIGNAL_HANDLERS)
explain the remaining interference: SDL normally translates SIGTERM/SIGINT into
a window-quit event. The headless native adapter now sets SDL_NO_SIGNAL_HANDLERS=1
before SDL initialization, leaving OS termination with the launcher. This does
not replace the browser/native input path or patch SDL/norns code. Ready-session
EOF shutdown is unchanged. The SIGSEGV's exact crash site is still unlocalized;
neither observed failure is reclassified as success.

Accepted minor: negative-test failures must retain diagnostics. The runner now
saves stdout/stderr before its oracle, removes only a fully verified case, and
retains/stops unexpected failures with fallback logs. An injected assertion
failure will verify that retention path without changing runtime code.

Additional bounded coverage: a real two-container Windows bind-mount lease test
passed in `artifacts/docker/lease-1788934709341/report.json`; a conflicting writer
was rejected while the original runtime stayed healthy. The final browser runner
also checks the entire captured MIDI sequence/port for each session, alongside
its existing per-action assertions and raw event/frame exports. These strengthen
the original H04 data/MIDI contract without expanding product scope.

Review-fix validation and newly localized shutdown defect:
- h04-08 startup-cancel-1788936027308 passed in1017.654ms, explicit startup
  SIGTERM and all service exits recorded; same-container data reopen passed.
- Normal browser-1788936073027 failed with matron SIGSEGV. GDB capture
  gdb-1788936476185/matron-gdb.log localizes a JACK close/read race: scheduler
  jack_time_to_frames against main-thread jack_client_close/munmap.
- Current upstream1d720942 still has this race in jack_client.cpp. The optional
  audio builder now applies an explicit lifetime-lock patch (patch README gives
  base and removal condition). Native acceptance is pending. Deterministic
  tests/jack_lifetime.py fails baseline (-6) and passes patched source (0),
  including post-close time/CPU access and repeated close. This does not replace
  actual native lifecycle checks or establish all historical crash causes.
- Diagnostic retention fault verification passed in retention-verification.json;
  the deliberately failed report5312554 remains false and its stopped container
  remains retained. No failed native signal is reclassified as success.
The one focused follow-up remains unused and must cover this additional fix.

Candidate434c2da, imageh04-09
sha256:02ecaa29d325a2af10c0f63c713c60fccf1da699fddf6211265b1d4305805a8a
built from context10 (build-10.log). Real regressions passed: startup-cancel
1788937216973 (1212ms and clean persisted reopen), browser1788937235104 (eight
checks/four sessions including full MIDI sequences and all native exits),
failures1788937280992, restart1788937290470, and lease1788937312920. Report paths
and hashes are in references/H04-evidence.json. These execute the actual normal
shutdown path that previously faulted; the clock boundary regression additionally
forces the overlap and rejects the unpatched baseline. Audio endurance is running
before the focused follow-up; H04 remains unmerged until that checkpoint closes.

Final candidate audio passed in artifacts/docker/audio-1788937348729/report.json
and artifacts/audio/latency-1788937356231/report.json:120seconds per rate,
5,347,584/5,821,056 samples, RMS0.03534482/0.03535464, normalized residual
1.3322e-5/6.918e-8, zero unintended underruns, all24 onset/silence measurements,
six reconnect/cancellation checks and actual native cleanup. P95 notification
bounds176.9/162.1ms exceed the150ms monitoring target. Preserve this observed
range: delayed monitoring only, no ceiling or interactive-playing claim. No
threshold was relaxed and earlier passing/failing evidence remains unchanged.
No native tests are active at the focused-review checkpoint.

Focused review completed: H04-followup.json, Codex session
01a084ff-7d71-7d03-b387-b4b1c4d12547. No substantive unresolved issues. It verified
all25 report hashes/statuses, GDB/upstream/harness hashes, strict signal gates,
and deterministic plus native lifecycle evidence. It resolved both startup
findings and diagnostic retention and accepted the captured JACK race fix.
The one-critique/one-focused-follow-up budget is now closed. H04 is admitted for
the recorded Windows Docker Desktop/amd64 image and Windows Chromium boundary.
This is not all-engine, hardware, native-Linux or macOS admission.
