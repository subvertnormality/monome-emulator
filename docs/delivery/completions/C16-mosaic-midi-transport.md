# Mosaic native MIDI clock and transport

M-TIM-003 uses the native PARAMETERS > CLOCK controls to select MIDI clock,
supplies24PPQN MIDI input at100BPM, starts and stops through FA/FC, returns to
internal clock and explicitly edits tempo to90BPM. Assertions cover menu pixels,
silence during clock-only warmup and between Start and the next pulse, literal
note bytes,150ms onset spacing and note lengths, complete stop drain, and
166.667ms internal onset spacing after the tempo edit. Mosaic's test driver now
checks MIDI input bytes/port/order against the retained native input trace.

Controlled run `7ac20f985d0947b3a77fc33e7445ffef` and real-time run
`58bc1394a5ad47599f273d4e67d89206` passed. Real time uses scheduled native-client
input requests; controlled time supplies pulses through advance and MIDI input.
The established2ns/10ms musical bounds remain unchanged.

Two earlier test errors are retained, not classified as application defects:
`ffa1d680142641b9bf9b2a74d574330d` navigated SYSTEM instead of PARAMETERS;
`04a86356f4674ca0ad3175b821ecac2a` incorrectly expected an implicit return to90BPM.
Pinned norns clock.lua's external-tempo update loop writes clock_tempo every
second; selecting internal applies that adopted value. The corrected test
asserts100BPM in the menu, then explicitly edits90BPM. Native clock_midi.c delays
transport Start until the following pulse. No production Mosaic/runtime change
was made to obtain these results.

This covers stopped-source changes and external transport, not a live source
switch with pending notes. That edge case remains required. M5 now requires
thirteen case/profile comparisons including this case; its final fresh-source
three-repeat matrix and Codex P5 follow-up remain incomplete. Twelve named
Mosaic cases are partial manual coverage, not the exhaustive campaign.
