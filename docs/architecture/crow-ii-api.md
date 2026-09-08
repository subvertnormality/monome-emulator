# Experimental Crow ii trace

Available with the identified Crow ii candidate; no default-runtime claim.
The Python session client exposes `crow_ii_read(cursor=0)`, corresponding to
authenticated POST `/crow/ii/read` with `{"cursor":0}`. Each call returns up to
256 complete records and a byte cursor for the next call. Partial writes remain
pending. Invalid, negative, non-integer and mid-record cursors fail explicitly.

Host-12 records `sequence`, `monotonic_ns`, `address` and `bytes`. The clock is
host CLOCK_MONOTONIC at the I2C transmit boundary, not DSP sample time, controlled
Lua time or physical bus timing. The file is limited to 100,000 packets; the next
packet fails the backend rather than silently dropping evidence. Session close
exports `crow-ii.jsonl`, including on explicit backend failure. A dead backend
fails live reads; its final trace remains available in exported evidence.

The pinned official Crow ii Lua descriptors, lookup, wire encoder and queue
produce packet bytes. The host records JF addresses 0x70/0x75. Reads and other
module addresses are unsupported and fail. No downstream synthesis or module
response is fabricated. Address-setting packets are recorded, not simulated as
hardware state changes. New sessions start their own file and sequence.

`tests/crow_ii_trace.py` exercises pagination, partial record completion, cursor
validation and oversized-record rejection. `tests/crow_ii_native.py` exercises
native key input, JF bytes, monotonic timestamps, cursor use, unsupported-read
failure and owned cleanup. Restart/isolation and limit exhaustion acceptance
remain required before admission.
