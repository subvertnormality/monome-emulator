# Lightweight native action acknowledgements — candidate

The HTTP action path previously built a full frame/grid/MIDI snapshot and then
discarded it in favour of its native acknowledgement. NativeBackend.query now
offers ack_only=False; HTTP native actions and internal recursive releases opt
in. Existing default query and explicit snapshot behavior remain unchanged.
Release-all and MIDI schedule/cancel do not expose a stale native acknowledgement.
No application-specific condition or native-clock change is included.

Validation:115 contract tests pass, including3 focused regressions; syntax and
diff checks pass. Actual candidate-image generic grid conformance passes all128
cells, levels, rotations, holds, release-all and disconnect/reconnect. The existing
container performance-recorder contract passes40 native actions.

Evidence root: /home/andy/projects/mosaic-behaviour-runs/ack-only-candidate
- native-recorder-01/result.json
- grid-native-01/command-output.txt and c03/conformance artifacts
- build-source.json and build/ack-only.patch

Image:sha256:9edeb040630bc7423d9a6d475e870c67ab8ccf9e70acdf89c1589e59fc352a9a.
This derives from measured baseline38b516ef with only the two-file patch; it
deliberately does not add the worktree's unrelated startup-lock change.

Performance benefit is not yet measured. Full snapshot serialization is unchanged.
This candidate is not promoted to the default installation and is not full
emulator acceptance or a Mosaic/physical-norns timing fix.

## Constrained rendering-pressure result

Mosaic9a4e8a3, `r13-render-pressure-ack-only-01`, failed the unchanged step
count and timing limits:18steps,288balanced note-ons/releases,16complete
slide cycles, p99 4770.504ms and final4770.955ms. Playback-window throttling
was400.403ms. Host load was6.57/6.97/5.76 at start. This one run does not
establish a performance benefit, nor isolate the failure to this patch. The
candidate remains unpromoted; no threshold is relaxed.

Further source inspection shows full snapshots also queue `_norns.emu_observe()`
on the Lua thread. The retained Mosaic setup has27 parameter roots traversing
3352parameter entries via group skips, not3352loop iterations. Full diagnostic
snapshots therefore remain intrusive to musical work. A separate display-only
read of already-exported state is being implemented and must be independently
validated before use in performance evidence.

## Display-only candidate validation

Authenticated native GET /display returns only the latest exported frame/grid
and their revisions, without enqueuing Lua diagnostics, copying MIDI history or
writing the framebuffer artifact. It does not replace full snapshot semantics.
No frame file path is exposed because the returned bytes are sampled independently
of the optional on-disk convenience copy.

All118 contract tests pass (including3 focused display regressions). Native
`tests/display_container.py` passes26 display observations, exact frame hashes,
grid feedback, held release and reconnects, monotonic revisions and a direct
check that20 display polls add zero native type5 diagnostic inputs. Evidence:
`ack-only-candidate/native-display-01/result.json`, observations and native events
under the Mosaic run evidence root.

Image:sha256:feab2bb7dce3860cd97a4580fe41598f3fae1663818ff13735bec25b201f1d43.
Exact baseline-plus-patch inputs: `ack-only-candidate/build-display/`.
The constrained Mosaic comparison is running at `r13-render-pressure-display-01`.
No performance acceptance or default-runtime promotion is claimed.

`native-display-02` additionally binds the actual launched container image ID;
the generic native regression passed. Bounded review found no remaining defects:
the initial concurrency concern was withdrawn because app.lock serializes the
display/snapshot/action HTTP routes. Wording now distinguishes normal process/log
checks from the skipped Lua diagnostic request.

`r13-render-pressure-display-01` delivered49steps/784balanced notes/48slide
cycles, all30 gestures and60display reads, without CPU throttling. P99 11.377ms
remains above10ms (maximum13.711ms, final9.764ms). Full snapshot overhead no longer
caused a comparable collapse in this run; no calibrated speedup or timing pass
is claimed. The original snapshot and ack-only failures remain recorded.
