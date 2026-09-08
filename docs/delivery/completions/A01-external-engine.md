# A01 progress: application-owned engines and SC failures

2026-09-08, `codex/audio-monitor`, base `319e3a0`; A01 remains in progress.

Experimental audio sessions now include their selected code root in SC class
discovery. Application identity already records those SC files alongside Lua.
The default MIDI runtime retains its existing search scope. Generic fixture
`fixtures/audio-code/voice-probe` owns its engine under its own `lib` directory;
there are no Mosaic or n.b. imports in the runtime adapter.

`python3 tests/audio_external_engine.py --install
.runtime/audio-monitor-01/installation.json` passed four native checks, recorded
in `artifacts/audio/external-engine-20260908-140736/report.json`: initialization
command produces 440 Hz without a post-start retry, native key produces 660 Hz,
key stops the sound, deliberately invalid synth-node command produces public
`audio_engine_error`. Captured JACK PCM and logs accompany the report. Existing
startup diagnostic tone is excluded with a documented thirteen-second wait.

The runtime now incrementally reads SC errors because a failed server command
need not kill sclang/scsynth. Error and missing-engine reports fail subsequent
health/actions instead of becoming misleading healthy sessions. The negative
test accepts error delivery from either its action or following health query.
Three existing startup-error preservation tests also passed.

Failed development runs are retained: `140505` incorrectly checked error code
inside the message, and `140607` assumed failure could only arrive during health.
The latter also encountered matron SIGSEGV during cleanup; its session artifacts
remain authoritative even though that older test failed to finish its report.
The final run passed cleanup; shutdown-race investigation remains an A01 residual,
not a waived exit code. A concurrently launched default smoke hit JACK's finite
server registry limit; default tests must run serially on this host for now.

Next substantive integration gap: unchanged DoubleDecker n.b. mod uses the
normal norns localhost:57120 SC endpoint and Server.default. Our isolated runtime
uses dynamic ports and a named Server. Preserve those endpoint semantics with
generic session routing/default-server adaptation, not edits to the mod. Source
is pinned in `fixtures/apps/nb-audio.lock.json`. Then prove its actual mod hooks,
n.b. voice registration, note/release, velocity, polyphony, modulation and panic.
An external probe alone does not establish those application/mod contracts.

Before A01 admission, review engine-source identity/search exclusions, browser
queue behavior, SC error propagation, port routing and the cleanup residual.
