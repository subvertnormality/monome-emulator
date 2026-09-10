# Experimental independent MIDI input

The opt-in controlled-05 native candidate supports real-time and logical
`midi_schedule` and `midi_schedule_cancel` actions. The accepted installation is unchanged. Neither
this candidate nor controlled time has passed M5/P5 admission.

```python
import time
start = time.monotonic_ns() + 500_000_000
ack = session.action({"type": "midi_schedule", "schedule_id": 1, "events": [
    {"port": 1, "bytes": [248], "at_monotonic_ns": start + i * 25_000_000}
    for i in range(100)
]})
assert ack["status"] == "accepted"
# Controls and observations can proceed while these inputs arrive.
state = session.observe()["state"]["midi_input_schedule"]
session.action({"type": "midi_schedule_cancel", "schedule_id": 1})
```

Timestamps use the backend's Linux CLOCK_MONOTONIC domain. The example assumes
the Python client runs in the same WSL/Linux environment. This is an absolute
timeline: neither control acknowledgements nor observations re-anchor it.
Controlled sessions reject this wall-time action explicitly. For a controlled
session, supply `time_domain: "logical"` on the schedule action and use
`at_logical_ns` for each event, measured from `state.clock.logical_ns`. Advance
then visits queued input deadlines along with native timer deadlines. The
previous immediate MIDI action is unchanged when no schedule is active.

One batch is active per session: up to2048 events,32768 raw bytes in total,
4096 bytes per event, and60 seconds into the future at native acceptance.
Deadlines must be future and nondecreasing; equal deadlines retain supplied
order. Ports must exist. Schedule IDs are positive increasing31-bit integers.
The bounded512KiB HTTP body limit also applies. Validation rejects a whole batch
atomically; it never partially installs a valid prefix. The independent decoder
validates the byte stream before submission. Immediate MIDI is rejected while a
batch is active so decoder state cannot race with a previously validated stream.
Controls and snapshots remain available.

The API acknowledgement says `accepted`, meaning the runtime owns the
batch, not that the Lua callbacks ran. Observations retain the batch, status,
delivery indices, bytes, ports, and intended/actual native arrival timestamps.
`completed` means bytes reached the native decoder. Lua callback/MIDI output
assertions must still observe the corresponding output; a busy Lua callback can
delay it. Cancellation waits for the device thread, preserves already delivered
bytes, and reports the discarded count. Cancelling the current completed batch
is allowed with zero discarded events. Unknown IDs fail. Cancellation does not
emit note-offs or undo prior input. Session EOF discards pending events, and the
existing owned native process cleanup terminates the input thread.

Real-time delivery uses the existing native input thread with a monotonic
`ppoll` deadline. Logical delivery occurs in controlled advancement before
servicing timers at the same instant. Equal-deadline inputs retain their supplied
order. Queue access and cancellation are serialized with a mutex; acceptance is
reported before delivery can occur. Both modes use `dev_midi_emu_receive`, the
existing native stream parser, clock-message update, and Lua event posting. It
does not replace the sequencer or introduce a second decoder thread. Late host
wakeups are delivered with the original deadline and actual arrival time, so
tests can fail their declared timing bound without hiding lateness.

Internal packets9/11 install monotonic/logical schedules and10 cancels;
reports13/15 confirm acceptance/cancellation;14/17 record monotonic/logical
delivery;16 rejects a schedule without aborting the runtime. Logical delivery
records contain `intended_logical_ns` and `actual_logical_ns`, never relabelled
wall time. Normal
native control acknowledgements keep their existing meanings.

Validate with `scripts/probe_scheduled_midi.py --installation INSTALLATION
--output NEW_DIRECTORY`. It runs a generic script with no Mosaic dependency,
holds a Lua key callback for150ms, and requires native arrivals during that
pending acknowledgement, exact MIDI echo bytes, timing, cancellation, and clean
shutdown. This focused test does not establish the full emulator release or
Mosaic musical handoff acceptance.

`scripts/probe_logical_midi.py` takes the same arguments and checks exact arrival
and Lua callback output times across a large advance, a one-nanosecond deadline
boundary, wrong-domain rejection, and cancellation. Both probes are development
evidence; their required repeat/admission integration remains open.

The2048-event bound admits a continuous16-bar24PPQN external-clock test, including
warm-up and post-Stop pulses, in one atomic batch. Longer endurance runs still need
an explicit larger bound or a gap-free refill protocol; tests must not insert gaps
or re-anchor time to work around admission limits.
