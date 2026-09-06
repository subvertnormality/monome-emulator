# Automation protocol v1

`dev/emu` is the CLI entry point. In C01 only `--backend contract-fixture` is
available. Its counter is a test of the runner, never an emulation of norns.
Every capability, observation and manifest names that limitation. The default
native backend fails explicitly until C02 implements it.

A session has a random identity and token, a loopback HTTP port assigned by the
OS, owned server/backend processes, and an isolated dust directory. Session
metadata lives under `.runtime/sessions/<id>/`; logs and data are retained after
stop. `--data` supplies a parent for a fresh session-specific directory, never a
tree to overwrite. Scripts/code roots are external selected inputs; C02 attaches
them through the native loader. No application-name dispatch exists in the core.

Requests require the session token. Cross-origin writes are rejected; browser
integration will use the same origin in C04. Bodies are limited to 64 KiB. Keys
and encoders are 1–3. Public grid coordinates are **1-based**, x=1–16/y=1–8;
native wire conversion is an adapter responsibility. Key/grid state is 0 or 1.
Encoder deltas are bounded to -127…127 and represent discrete input units, not
absolute angles. MIDI has a 1-based port and bounded byte array.

`POST /action` accepts `schemas/action.schema.json`. Sequences start at 1 and
must be consecutive. Action IDs must be unique. Wrong-session, duplicate or
out-of-order actions fail rather than being silently replayed. An `applied` ack
means the backend completed that input operation. C02 must place this ack after
the native event callback; enqueue-only acknowledgment is insufficient.
Monotonic timestamps use integer nanoseconds; frame/grid revisions are counters,
not timestamps. Later musical assertions use explicitly named beat units.

`GET /health`, `/snapshot`, `/capabilities` and `POST /stop` expose the running
session. `POST /fixture-fault` exists only for the C01 contract subprocess; crash
and stall must cause failed scenario evidence. Unknown endpoints/fields fail.
The schema validator supports exactly the keywords used by the versioned schemas
and rejects unsupported schema keywords instead of ignoring constraints.

Scenarios contain physical-style actions, immediate assertions or bounded waits.
Each has a whole-run deadline and at least one observable assertion. A wait polls
an actual observation and fails on timeout; it never sleeps then declares success.
Expected values are literal recipe data. C02 onward expands observations to real
frames/grid/MIDI rather than using the fixture counter for application tests.

Each run writes its resolved scenario, input/ack trace, observations, failure
record and logs under `artifacts/runs/<id>/`. The manifest records source-file
digests including dirty/untracked implementation changes, test selection/counts,
platform/kernel, backend fidelity, timestamps and artifact hashes. Verification
rejects missing/changed artifacts, stale source, failed/empty/incomplete results,
identity/order mismatches and a fixture masquerading as native E evidence.
Replay verifies provenance and reruns the captured recipe in a fresh session.

`release-check` currently enforces missing family/scenario/generic coverage and
**cannot certify a release**. Final A20/A21-specific meaning, checkpoint reviews
and cross-platform release gates remain explicitly unimplemented until their
owning cards; the command fails closed even if preliminary coverage is supplied.
This prevents a temporary C01 verifier from announcing an unsupported release.
