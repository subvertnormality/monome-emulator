# Native virtual MIDI

`emu start --midi-config fixtures/midi/three-ports.json` creates ordered, named
virtual ports through norns' native device list. The default is one `Emulator
MIDI` port. Configurations declare 1–16 unique names; `none` and `virtual` are
reserved by upstream vport discovery. Both source configuration and actual native
discovery are tested. Mosaic fixtures remain outside the generic runtime.

MIDI actions carry a physical port number and raw bytes. Channel information is
encoded in those bytes. Native input uses the pinned upstream parser, including
running status and three-byte SysEx callbacks, rather than calling application
MIDI handlers directly. Interleaved realtime messages leave partial parser state
intact in the virtual profile. Undefined statuses, orphan data and malformed
streams fail before entering the native parser. Partial messages may span actions.

Optional `at_monotonic_ns` schedules injection on the backend monotonic clock,
within the next two seconds; absent values apply immediately. Acknowledgement
follows native callback processing. This uses real time and does not replace
norns clocks. C07/C12 own the full timing and endurance thresholds.

Output records include unchanged raw bytes, physical port identity, native
emission sequence and native monotonic timestamp. A separately implemented stream
decoder adds semantic messages; its note tracker distinguishes ports/channels and
normalizes velocity-zero note-on as note-off. The original bytes remain available.

`native-events.jsonl` retains the complete stream. Snapshot `midi` is explicitly a
4096-event tail; `midi_capture` reports its first index, total count, complete-log
name, limit, dropped count and outstanding notes. The configurable total capture
limit defaults to one million events. Reaching it, a sequence gap or backwards
source time fails the session, with the offending emission preserved in the log.
The reader continues draining transport so cleanup cannot deadlock on this error.

Required JSON data seeds are validated before runtime startup. The Mosaic fixture
declares this policy because upstream's config loader can otherwise print invalid
JSON and continue. Missing/malformed fixtures fail explicitly; generic scripts'
application code is not altered or intercepted to select musical outcomes.

Boundary reproduction: `python3 tests/midi_native.py`, the `native-midi-stream`
scenario, and `emu test --suite contracts --require-all`. Mosaic coverage uses
actual encoders, grid and key confirmation to select port/channel and change
root/scale; literal MIDI tables are the oracle. No device or manual test is needed.
