# Native clock phase trace

The emulator can record an opt-in diagnostic stream for the official norns
clock path. Start a native session with `clock_trace=True`, or pass
`--clock-trace` to `emu start`. A runtime without
`patches/norns/0014-clock-phase-trace.patch` rejects the option.

Each `kind: 26` record in `native-events.jsonl` has an increasing `ordinal`
and one of these stages:

- `schedule`: a Lua coroutine supplied a sync beat or sleep deadline.
- `post`: the native scheduler found that deadline due and queued
  `EVENT_CLOCK_RESUME`.
- `dispatch_begin` and `dispatch_end`: matron entered and returned from the Lua
  resume callback.
- `internal_publish`: the internal clock published one musical tick.
- `internal_skip`: the official internal-clock loop advanced past overdue JACK
  deadlines after a stall.

The packet header's `monotonic_ns` is sampled beside the record. JACK-domain
values remain seconds because that is the domain used by norns. A skip record
retains the overdue `target_jack_s`, the measured `observed_jack_s`, the exact
`resumed_jack_s`, the musical `tick`, its beat duration in `value`, and the
number of `skipped_deadlines`. The expected invariant is:

```
resumed_jack_s - target_jack_s
    == skipped_deadlines * (value / 24)
```

Tracing is disabled by default. The patch adds observation calls and a fixed
88-byte transport record; it does not alter clock deadlines, tick counters,
resume ordering, or catch-up policy. Trace-enabled measurements include the
small cost of emitting those records and therefore remain diagnostic evidence,
not a performance acceptance result.

Run the bounded probe with an identified trace runtime:

```
python3 tests/clock_phase_native.py \
  --install /path/to/installation.json \
  --output /tmp/clock-phase-run
```

The probe briefly stops only its owned matron process, resumes it in a `finally`
path, and requires a complete schedule/post/dispatch/internal trace with no
ordinal gaps. It uses a generic fixture and contains no Mosaic dependency.
