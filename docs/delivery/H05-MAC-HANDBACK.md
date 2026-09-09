# H05 final Mac-side verification

Continue in the existing Mac worktree after inspecting its status and preserving
uncommitted work. Fetch `origin/codex/audio-monitor`, which descends from Mac
head5366789 and contains the Windows integration/review fixes. Fast-forward your
worktree only if appropriate; do not overwrite concurrent work or rewrite history.
Read AGENTS.md, the delivery runbook, H05-triage.md and H05-evidence.json.

Windows ran all six host gates on the Mac shared changes. Review
01a08641-8f92-7152-9ac6-1bd3809feb98 found two code defects and the known Mac
evidence gap. Code fixes are committed atfd82a09: Docker target/runtime architecture
guards and a JACK diagnostic that requires actual activated client connections.
Follow-up01a08653-d2f7-73f2-ac92-5998bb021691 closed both code defects and verified
the Windows evidence. No DSP/input/lease change followed the six Windows passes.
Do not restart that completed code review or require copying Windows artifacts.

The Mac evidence may stay on the Mac. Complete these remaining checks there:

1. Read the six `native_arm64.reports` in H05-evidence.json and the nested
   `audio_report` (seven JSON files total). Recompute their recorded SHA256 values
   and inspect actual statuses, native exits, script/mount/data isolation checks,
   image/source identities and audio signal/continuity/latency results. Hashes
   alone are not a replacement for reading the reports. Use retained logs only
   if a discrepancy needs explanation. Preserve all prior failed reports.
2. Export a fresh committed `linux/arm64` context and build with matching target
   using the new guards. Verify actual image architecture and package inventory.
   A deliberate mismatched target must fail at the first architecture guard,
   before package installation. Do not admit a falsely labelled image.
3. Run `tests/container_startup_cancel.cjs` against the rebuilt native arm64 image
   to verify startup, persisted reopen and normal cleanup. Earlier six-gate native
   Mac evidence covers the unchanged runtime; do not repeat full endurance merely
   because build guards or documentation changed. Diagnose any new failure.
4. Commit a compact Mac-side verification record with the inspected report paths,
   actual hashes/statuses, source/image/build identities and smoke result; update
   H05 state and push the verification branch. No large report/log/audio transfer
   is necessary if this check is performed where the artifacts reside.

If any original artifact is missing, state that precisely rather than regenerating
its old identity or claiming it inspected. A fresh run may supply new identified
evidence if required. Keep amd64-on-Apple-Silicon failure, untested Intel Mac/native
Linux lanes, physical-device limits and monitoring-only latency claims explicit.
Main has not received these Mac integration changes yet; final integration follows
the completed evidence gate. No additional code review is needed for a pure
hash/result verification record; new material fixes require the runbook policy.
