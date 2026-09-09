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
