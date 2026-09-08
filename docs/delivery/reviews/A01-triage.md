# Tranche 1 review triage

Review: `A01-branch-raw.json`, Codex session `01a081de-87db-7723-b4dd-0382f7977dbc`, committed snapshot `a7dd08c`. One bounded medium branch critique completed. Four major findings accepted; no scope expansion.

1. **Diagnostic errors:** ii-enabled global printf/puts wrappers marked every diagnostic fatal. The adapter now classifies the explicit error formats in the pinned sources (including optimized puts without trailing newline); normal CASL redundant-release and ii help diagnostics remain stderr diagnostics. Caw error handling and ii unsupported-operation failures remain explicit. `tests/crow_callbacks.py` demonstrates redundant release failing on host-15 and passing on host-16; standalone ii core retains overflow/error negatives.
2. **Instant completions:** persist pending completion counts rather than comparing counts only around sample stepping. Drain after commands and sample blocks, with a 4096-entry per-channel bound, a 4096-dispatch/.5-second batch limit, and explicit runaway errors. Reset clears pending outputs. `tests/crow_callbacks.py` proves missing instant completion and accepted runaway chain on old host, then exact completion/ii delivery and explicit runaway failure on new host. Native `tests/crow_callbacks_native.py` verifies exactly one real norns callback through the serial/native driver, without a follow-up Crow command.
3. **Callback ii starvation:** service official ii leader queue after callbacks and each sample block, independent of serial reception. The host test leaves stdin open and idle; real Detect stream callbacks must emit >=20 packets before EOF, all exact JF wire bytes. Old host overflows; host-16 passes. Native callback test also verifies stream stop. Existing 2000-reply/native fault test passes.
4. **Lua re-baselining:** `scripts/crow_source.py` binds every recursive Crow Lua file to Git HEAD bytes during the validated pinned host build. Both composition tools verify and carry that identity; they never create new expected hashes from mutable source. Native launch compares the carried manifest identity, including nested Lua files. Historical experiments remain readable using their older root-only identity; new composition refuses manifests without build-bound identity. `tests/crow_source_identity.py` uses disposable copies to prove mutation rejection through both actual composition CLIs. No shared source was changed.

Evidence:

- Baseline failures: `artifacts/crow/callbacks-20260908-174025/report.json` (all four expected regressions fail).
- Fixed host: `artifacts/crow/callbacks-20260908-174132/report.json`.
- Serial/reset/deadline: `artifacts/crow/serial-20260908-174233/report.json`.
- Native callbacks: `artifacts/crow/callbacks-native-20260908-174317/report.json`.
- Native transport/2000 replies/error: `artifacts/crow/native-20260908-174336/report.json`.
- Trace bounds: `artifacts/crow/ii-limits-20260908-174354/report.json`.
- Runtime identity: `artifacts/crow/identity-20260908-174414/report.json`.
- Actual composition negatives: `artifacts/crow/composition-identity-20260908-174421/report.json`.
- Stable pre-fix contract suite: all 68 tests pass, `artifacts/audio/tranche1-contracts.log`. Re-run affected identity contracts after the source-binding change.

Test corrections, without weakened oracles: reset now starts a one-second action before resetting it; the previous zero-time assignment correctly delivers its callback before the following reset command after the fix. An attempted native test before its chained preparation completed failed with an absent installation; no native success was claimed. First updated composition failed because the launch verifier still enumerated only root Lua; recursive identity verification now matches the build-bound manifest. These failures are retained.

Historical teardown residual: the old `external-engine-20260908-140607` native log reaches `matron shutdown complete` then records SIGSEGV, with no retained stack. Cause remains unlocalized. Fresh same-engine deliberate SC error acceptance passes with matron exit 0 at `artifacts/audio/external-engine-20260908-173449/report.json`; numerous normal/failed-session exits above pass. No exit code is waived. Retain as a non-reproduced historical teardown risk, with an explicit next-recurrence obligation to capture a native stack before changing shutdown ordering.

Final canonical build and affected Mosaic/Crow regressions are running. No merge/admission yet. The focused follow-up should judge these fixes, not repeat the whole branch review or introduce queued broader-script/desktop scope.

Standalone ii encoder/queue regression after the diagnostic fix passes all seven
check groups: `artifacts/crow/ii-core-20260908-174509/report.json`.
