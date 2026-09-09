# H03 review triage

Initial Codex review: `01a08472-ee92-7113-ab09-9a5481e03330`, candidate
`0abf891`, base `7d56cf0`, raw response `H03-raw.json`. The reviewer inspected
code and matched all five evidence hashes; it did not run tests. Three major
and two minor findings are accepted. One focused follow-up remains available.

| Finding | Fix | Validation |
|---|---|---|
| Major: arc ownership fixture lacks audio lock | Initialize the newly required lock in the existing fixture | All 24 top-level units pass, including the three arc contracts |
| Major: onset may precede stimulus and mute is not verified | Require an actual rendered silence window before every onset, then finite positive sample-clock and notification delays | Tightened two-rate run `latency-1788929100884` passes; broken mute `latency-1788929263930` and early timestamp `latency-1788929282617` are rejected |
| Major: browser launch/close failure skips native cleanup | Move module load, executable launch and option validation into owned try/finally; independently attempt page close, browser close, native stop and report persistence | Bad executable `latency-1788929246718` and close rejection `latency-1788929301660` stay failed and independently verify all native services reaped |
| Minor: automatic/pending-start stop races with new Listen | Share a pending stop promise, keep Listen disabled until it resolves, and prevent an older startup finally from re-enabling it | Both rates pass real worklet underrun with delayed HTTP stop, plus explicit pending-native-start cancellation and fresh listening |
| Minor: successful early response leaves body unread | Reject declared GET bodies/transfer encoding and restrict early editor endpoints to GET | Expanded persistent HTTP framing test passes; eight native Maiden transport checks pass in `transport-20260909-054938` |

The pending-start cancellation probe calls the same browser stop function used
by the visibility handler while a real native start response is delayed. It does
not claim a physical visibility event. The automatic-stop probe induces a real
worklet underrun by withholding PCM, then verifies recovery; its intentional
underrun is separate from the uninterrupted continuity window.

Earlier failed buffer/transport experiments remain failed. The tightened
latency oracle supersedes earlier latency measurements for admission; the older
every-sample continuity evidence remains useful. No new platform, engine,
physical speaker or arbitrary-duration reliability claim is made.

All four negative reports are indexed in `artifacts/audio/h03-negative-results.json`.
They deliberately retain `passed:false`; independent cleanup verification does
not turn failed browser tests green. To repeat a negative case, start a fresh
owned fixture with `tests/audio_browser_start.py`, set `H03_PROBE_FAULT` to
`browser-launch`, `mute`, `early-onset` or `browser-close` for the Node runner,
and expect a nonzero exit and the exact corresponding error. Verify cleanup
with `audio_browser_cleanup.py --expected-browser-error <expected-message>`.
Ordinary verification still requires a passing browser report.

The final 120-second-per-rate run with the corrected oracle passed in
`latency-1788929454875/report.json`: 24 rendered silence windows and positive
onsets, six reconnect/cancellation checks, no network failures, and independent
native cleanup. P95 notification upper bounds were 142.2/149.1 ms; the earlier
corrected short run reached 158.2 ms. No interactive-playing claim follows.
Focused review `01a08487-d467-7911-b68f-2ae849c0b448` closes all five findings
at `e7136a9`, with no remaining substantive issue. It independently recomputed
all seven hashes and verified the saved negative cleanup records and PID absence;
it did not rerun tests. The planned review budget is complete. H03 is admitted
for its tested opt-in subset; commit/merge and main-source smoke follow.
