# Mosaic restart phase edges

Mosaic-owned M-TIM-002 edits the existing eight-step phrase through physical
inputs, then starts playback at five clock phases. Read-only native beat reports
locate a future96PPQN boundary at90BPM; requested offsets are-100,-1,0,1,100ns.
Controlled mode verifies the measured phase within2ns before starting. Each
restart then checks complete MIDI phrases and six note durations against literal
musical expectations. Real time retains the10ms duration bound and records phase
as approximate; it makes no nanosecond input-placement claim.

Controlled run `d6ffb42b6d8b4f35bed8f0f5e66cc82e` passed. Measured offsets were
-99.111111,-1.555556,0,0.888889,99.777779ns. Real-time run
`ee322cb6482b4d41bc60e21aa6aae341` also passed. This extends the phase-preserving
Mosaic candidate's evidence; it does not remove historical timing failures.
Source-transition semantics and three fresh repeats remain required.

The M5 external application contract now includes M-TIM-001 and M-TIM-002:
twelve case/profile comparisons in total. Five admission contracts pass with
that expanded inventory. No current or future gate may omit the new timing
cases to obtain admission. The complete final-source matrix and Codex P5
follow-up have not run. Eleven named Mosaic cases remain partial manual
coverage; the exhaustive campaign and later release stages are still required.
