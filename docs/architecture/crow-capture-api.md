# Experimental Crow CV capture

Select an identified Crow capture installation, currently constructed with:

```sh
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --output .runtime/crow-host-06
python3 scripts/prepare_crow_runtime.py --install .runtime/crow-norns-04/installation.json --crow-build .runtime/crow-host-06 --output .runtime/crow-capture-02
```

Outputs must be fresh directories. The base must already contain the native
Crow connection and packet ownership patches. Composition preserves its native
binary hashes and records the parent installation digest. The default runtime
does not gain a Crow device implicitly.

Authenticated loopback POST endpoints:

| Endpoint | Payload | Result |
|---|---|---|
| `/crow/capture/start` | `{"seconds":0.6}` | Acknowledged finite capture job |
| `/crow/capture/status` | `{"job_id":1}` | Current job status and completion metadata |
| `/crow/capture/cancel` | `{"job_id":1}` | Cancelled job, or completed job if capture already finished |
| `/crow/input` | `{"channel":1,"volts":2.5}` | Acknowledged input voltage and processing sample index |

Python `automation.client.Session` exposes `crow_capture_start(seconds)`,
`crow_capture_status(job_id)` and `crow_capture_cancel(job_id)`. Start capture,
send ordinary key/encoder/grid/MIDI actions, then poll until complete. API calls
do not evaluate Lua or mutate script globals.

Capture retains actual output from pinned Crow slopes, four interleaved float32
channels in **volts**, at 48,000 samples/second. The raw `.f32` file uses the host
byte order (little-endian on the current WSL/x86 candidate). It is CV data, not
normalized audio. `frames`, `channels`, `sample_rate`, `start_sample`, format,
path and SHA-256 describe a completed result. `start_sample` is relative to the
Crow host's processing epoch, not an absolute wall-clock timestamp or a guarantee
of hardware latency.

Each session permits one active capture and eight jobs total. Duration is
0.01–30 seconds; each job allocates at most 23,040,000 bytes for samples. The
helper uses an owned control socket, bounds requests and checks finite voltages,
file size and writes. Completed files use exclusive creation; cancellation
before completion discards the buffer. Session shutdown cancels an active job
before closing services. `Session.close(artifact_directory)` exports capture
files and manifests alongside native evidence.

Input-enabled candidates additionally expose `Session.crow_input(channel,volts)`.
Channels are 1 and 2; voltages must be finite and representable as float32. Each
value is held until changed again. This models the voltage supplied to the
official detector, without an electrical ADC clamp or noise model. Acknowledgment
means the held voltage was updated; the detector evaluates it on its next
32-sample boundary. Script callbacks remain asynchronous, so wait for a concrete
script response before asserting a workflow result. Injection history is retained
in `crow-captures/inputs.jsonl` and exported with the session.

Current input candidate: `.runtime/crow-input-01/installation.json`, composed from
the frozen `crow-capture-03` base and `crow-host-10`. Build manifests now name an
identified copy of `serial.lua`; interpreted verification and launch use that
copy rather than silently adopting subsequent edits to the development adapter.
The profile exposes none/change/stream modes and voltage query. Frequency,
window, scale, volume, peak and input clock mode are not yet exposed.

The `crow-norns-06` candidate additionally supports norns following Crow input 1
as its clock source: use the ordinary `clock_source=crow` and `clock_crow_in_div`
parameters. This uses Crow change detection, not Crow's separate input clock mode.
Native tests cover 100-to-150 BPM following and `clock.sync`-generated MIDI.
The serial driver frames complete pulses; reception delays still affect timing.

This is an experimental real-time software profile. It does not yet
synchronize to controlled Lua time, certify physical DAC
behavior, or model downstream ii modules' synthesis. Capture export writes can
delay the host; missing one second of processing fails explicitly. Long-duration
load/drift admission remains outstanding.
