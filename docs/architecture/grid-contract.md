# Virtual 128 grid

The physical surface is always 16 columns by 8 rows. Public input coordinates
are 1-based physical positions; the native packet uses zero-based physical
positions. Native libmonome-equivalent rotation maps those to logical script
coordinates. For physical zero-based `(x,y)`, rotations 0–3 produce `(x,y)`,
`(7-y,x)`, `(15-x,7-y)`, `(y,15-x)`. The LED snapshot is always the physical matrix.
This follows the pinned official libmonome rotation input contract. The native
rows/cols queries swap for odd rotations; upstream Lua device objects retain
their discovery-time cached dimensions until the next discovery event.

Native norns retains the LED buffers and Lua grid API. Single and bulk changes
are staged until refresh. Relative writes clamp to 0–15. The snapshot keeps raw
0–15 LED values plus independent intensity metadata; intensity does not rewrite
the application buffer. A browser must use both when rendering brightness.

`grid_connection` is a native device-lifecycle action with a Boolean `connected`
field. Disconnect first releases each held grid key through the usual native
input callback, then removes the device through the native weaver callback.
Reconnect clears the buffer and runs native discovery again, preserving physical
identity. The virtual native allocation remains owned by the session during
disconnect, preventing stale queued redraws from addressing freed memory.

In real-time mode, an individual grid transition may include `at_monotonic_ns`
within the next two seconds. The automation server waits until that deadline,
then sends the ordinary native grid packet and returns its acknowledgement. This
schedules the input transition rather than a script callback; native event
timestamps and application output remain the evidence. Key and encoder actions
use the same optional deadline. Controlled time rejects wall-clock deadlines and
uses `advance` followed by ordinary input.

For a physical gesture whose press and release must both be accepted before the
first deadline, native real-time sessions also accept one bounded
`native_input_schedule` action. It has a strictly increasing `schedule_id` and
one to 64 ordered `key`, `grid`, or `enc` events, each with
`at_monotonic_ns`. The server
validates the complete transition sequence, native grid connection, deadline
horizon and browser-input ownership before acknowledging the schedule. It then
delivers each event through the ordinary native input path at its deadline. The
snapshot exposes submitted events, native packet sequence, planned and applied
timestamps, explicit `callback_completed_monotonic_ns`, and terminal status in
`state.native_input_schedule`; the retained
`native-input-schedules.jsonl` records admission and every terminal outcome.

The first deadline must be at least 100 ms after admission. This conservative
lead gives the automation acknowledgement time to return before delivery; it is
not a claim about later deferred Lua work, redraw, or MIDI latency. The callback
completion timestamp is a FIFO native-event fence: the bridge posts the native
input event before its acknowledgement event, and Matron calls the input Lua
handler synchronously while draining that queue. Schedule IDs are
strictly increasing rather than retained in an unbounded identity set.

Only one native control schedule can be active. Immediate key/grid/encoder and
release-all actions fail with `schedule_busy` until it completes, and a schedule
cannot coexist with browser-owned held controls. Contract-fixture and controlled
sessions explicitly reject it. Delivery timing ends at native input submission;
Lua callback, redraw, and MIDI latency remain separately observable and are not
represented as a successful deadline. Shutdown records an explicit cancelled
terminal schedule record before closing the native backend.

Duplicate down/up transitions and input to a disconnected grid fail explicitly.
Multiple keys remain independently held until released; `release_all` uses the
same input path. Physical tilt is unsupported and produces a named Lua error.
Out-of-range LED coordinates fail instead of addressing unrelated backing cells.
Levels follow pinned norns int8 storage and official libmonome mext four-bit
packing: absolute -4 displays 12, 31 displays 15 and 260 displays 4. Relative
addition retains the upstream clamp to 0–15. Patch 0010 corrects C03's overly
strict level validation; actual Mosaic playback exposed that fidelity defect.
See `native-grid-level-conversion.json` and `tests/grid_native.py`.

The full conformance probe checks all 128 positions through native callbacks and
literal MIDI coordinate reports, and separately asserts the raw transport
coordinates. Its expected brightness and rotation tables are fixed independently
of emulator output. Two disposable probe variants swap coordinates and omit
releases; the same checks must reject them. Mosaic acceptance selects its actual
pages and checks their documented menu LED levels, including after reconnect.
