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
