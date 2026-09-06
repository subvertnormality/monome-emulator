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

Duplicate down/up transitions and input to a disconnected grid fail explicitly.
Multiple keys remain independently held until released; `release_all` uses the
same input path. Physical tilt is unsupported and produces a named Lua error.
Out-of-range LED writes fail in the virtual device profile instead of wrapping
into unrelated backing cells. See patch 0008 and `tests/grid_native.py`.

The full conformance probe checks all 128 positions through native callbacks and
literal MIDI coordinate reports, and separately asserts the raw transport
coordinates. Its expected brightness and rotation tables are fixed independently
of emulator output. Two disposable probe variants swap coordinates and omit
releases; the same checks must reject them. Mosaic acceptance selects its actual
pages and checks their documented menu LED levels, including after reconnect.
