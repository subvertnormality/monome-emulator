# Proposed chord voice lifetime fix

Status: user explicitly approved application and thorough unit, integration and
behavior testing. Candidate applied; initial broad sweep117/122 passed. One stimulus-delivery
failure was repaired and passes targeted checks in both modes; four explicit
pre-existing failures remain. Both chord regressions, fresh controlled repeats,
unit and integration checks pass. This is not full acceptance. The initial
automatic rejection below is retained as history.
Mosaic baseline: `4501e6a`, branch `codex/behaviour-validation`.
Affected implementation: only the note-on chord bookkeeping block in `lib/m_midi.lua`.

## Reproductions

Both tests play C/E, release one voice at40ms, then add G at80ms while another
voice remains held. Final release is500ms after the first press. Recording is
disarmed after all three presses. Independent replay expects C/E/G and a500ms
shared length; existing D/E/F pattern steps must remain unchanged.

| Case | Failure | Controlled baseline | Real-time baseline |
|---|---|---|---|
| M-REC-030 | Releasing the root before G arrives loses the original chord | f1eafea8ff1041ad9219773d5a38fa0f | ea725b0d1f60410c8745567649d336f8 |
| M-REC-031 | Releasing E before G arrives causes G to overwrite E's recorded slot | c1ecad7dd0bf446cb619a982fe8aac28 | da110957937449d8ac2b6806421c91ed |

## Exact proposed replacement

Replace the block from `-- Handle chord state for this step` through its
`recorder.handle_note_midi_message` branches, immediately before note-off handling,
with:

```lua
    -- The chord survives individual releases while another voice is held.
    -- Preserve its root and onset independently of the root key's lifetime.
    if chord_state.chord_number == 0 then
      chord_state.chord_one_note = data[2]
      chord_state.root_note = note
      chord_state.start_time = input_notes[data[2]].start_time
      chord_state.voice_count = 0
      chord_state.length_recorded = false
    end
    chord_state.chord_number = chord_state.chord_number + 1
    -- Recorded voice slots do not become reusable when a key is released.
    chord_state.voice_count = chord_state.voice_count + 1
    chord_state.notes[data[2]] = true

    local chord_degree = quantiser.get_chord_degree(note, chord_state.root_note, step_scale_number)
    if chord_degree < -14 or chord_degree > 14 then
      chord_degree = nil
    end
    recorder.handle_note_midi_message(note, velocity, chord_state.voice_count, chord_degree)
```

The existing code uses held-key count as a recorded voice index and looks up
the root through a key entry deleted at release. This replacement retains the
root pitch in chord state and separates recorded voice count from held-key count.
It changes41 lines to21 in this block. No runtime/emulator special case is proposed.

## Validation before publication

Run both new regressions and affected simultaneous/staggered/disarm/channel
regressions in controlled and real time, fresh controlled reproducibility and
the474 existing unit tests. Preserve baseline manifests and an isolated candidate
patch. Failed validation prevents claiming the fix passed or publishing it as
validated. Repeated same-pitch overlap, voice overflow and cross-source chord
aggregation remain required coverage; this candidate does not claim those done.

## Approval-review reason

Automatic approval review rejected application because the replacement changes
core Mosaic chord/MIDI bookkeeping and could cause unvalidated behavior
regressions. The read-only diff preview succeeded. User approval is requested
for applying and testing this exact candidate in the authorized worktree.
