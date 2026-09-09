# Experimental audio capture API

Use an identified real-time audio build containing `audio_capture`. Prepare one
without replacing the current installation:

```sh
python3 scripts/prepare_audio_monitor.py --install .runtime/audio-mod-01/installation.json --output .runtime/audio-api-01
```

The authenticated session endpoints are:

| POST endpoint | JSON fields | Result |
|---|---|---|
| `/audio/capture/start` | `seconds`, optional `input` | Job ID, capturing status, output path and readiness metrics |
| `/audio/capture/status` | `job_id` | Capturing, complete, failed or cancelled; completed WAV digest and native metrics |
| `/audio/capture/cancel` | `job_id` | Cancelled status after helper termination |

`GET /audio/status` has `capture_available` separately from browser monitoring's
`available`. Missing helpers and controlled-time sessions do not support capture.
Duration is 0.25–30 seconds; one active job and at most eight jobs per session.
Input must be a stereo WAV at the runtime sample rate, no longer than the
capture, and under the session's data directory. It is copied into the job's
evidence directory before injection. Malformed, oversized or nonfinite input is
an error. Cancellation is not a successful capture. Output is stereo float WAV
from crone outputs 1/2; input feeds crone ADC inputs 1/2. Script routing still
controls what is heard or recorded. This does not supply microphone hardware.

The public `automation.client.Session` exposes `capture_start(seconds,
input=...)`, `capture_status(job_id)` and `capture_cancel(job_id)`. For example,
with an existing native `session` client and seeded `stimulus.wav`:

```python
job = session.capture_start(3, input="stimulus.wav")
# Normal session.action(...) calls may run while capture is active.
while job["status"] == "capturing":
    time.sleep(0.05)
    job = session.capture_status(job["job_id"])
assert job["status"] == "complete", job
# Assert independent signal properties of job["output"].
```

Add a test deadline to polling loops. Completion requires the native helper to
exit successfully, produce its completion record and WAV, and report no xruns,
missing frames, nonfinite output or server death. The manifest records input and
output digests, frame counts and monotonic timing; start acknowledgement is a
readiness boundary, not a sample-accurate action trigger. Public native runtime
errors still fail the session's health/action/status path.

Session close cancels any active capture before stopping audio services.
`Session.close(artifact_directory)` exports capture inputs, outputs, manifests and
logs alongside ordinary runtime evidence. No capture writes into the selected
script source. Browser monitoring may run independently, with its own ownership
and buffering rules. Generic tests live in `tests/audio_capture_api.py` and use
actual softcut recording through native keys; they do not import Mosaic.

## Browser monitor intervals (reviewed opt-in H03)

The existing authenticated POST routes accept `client_id`: `/audio/start`,
`/audio/read` (also `after`, initially -1), and `/audio/stop`. The browser now
also sends a fresh `stream_id` for each listening interval:1–64 ASCII letters,
digits, underscores or hyphens. Start and read echo that identity. Retrying
start with the same identity is idempotent; a different active identity fails
with `audio_generation`. Stop the old interval before starting a new one.
Another browser owner still fails with `audio_owner`.

Legacy automation can omit `stream_id` throughout its interval. It cannot read
or stop an interval started with an identity. Tagged clients must supply their
identity on every request; delayed old operations cannot replace or stop a newer
interval. The identity supplements the session token and browser ownership.

Audio lifetime/read operations have a separate lock from native actions, so a
synchronous Lua callback does not block PCM reads. Disconnect/session cleanup
uses that same audio lock. PCM buffers remain bounded and retained sequence gaps,
native xruns and browser underruns fail explicitly; reconnect starts fresh.
These changes do not make a slow Lua callback concurrent with another device
action, or hide a native error.
