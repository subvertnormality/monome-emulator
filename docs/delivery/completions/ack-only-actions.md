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
