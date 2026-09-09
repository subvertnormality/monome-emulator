# H02 review triage — implementation3365fe3

Codex Paranoia01a08423-7f43-7511-907e-748513213b36, one bounded branch pass.
Four majors and three minors (including build recovery) are accepted. H02 remains
unadmitted. One focused follow-up remains after fixes and actual regressions.

1. Major linked-app mapping: preserve the runtime's lexical declared entry under
   its code root instead of dereferencing the application link first. Add a
   generic linked-profile native launch/save/reopen test; no Mosaic modification.
2. Major failed Save: official HTTP500 must retain dirty editor text, show the
   error and suppress Run. Add a narrow separately GPL patch and browser failure
   regression against a disposable unwritable target, then successful recovery.
3. Major cleanup retry/ownership: distinguish stopped admission from completed
   cleanup, retry unfinished closers, retain the dataset lease while native or
   Maiden writers survive, and keep the server available for cleanup retry.
4. Major lifecycle coverage: inject bounded cleanup and replacement-start failure;
   prove explicit failure, lock retention/recovery, no surviving old services and
   unaffected peer state. Hold a native input across switching/restart and verify
   old input cannot leak to the replacement or peer.
5. Minor root links: official root listing must follow reopened dust/data, with
   actual browser navigation after restart.
6. Minor re-verification: reset report passed before checking and remove stale
   verification_error only after success; exercise missing WAV rejection.
7. Build recovery risk: remove weak finalization; every build starts in a new
   directory from the pinned archive plus declared patches, rebuilds both outputs
   and rejects changed source/patch inputs before recording.

No finding is waived on review-budget grounds. Preserve failing evidence and
state exact boundaries. No H03 or Docker implementation before H02 admission.

## Applied fixes and evidence for the focused follow-up

1. `datasets.mapping` now uses the declared lexical code-root/relative entry,
   matching NativeBackend. Generic linked-profile launch/save/reopen passed all
   seven checks at artifacts/datasets/native-20260909-041703/report.json. The
   application target is external to the selected profile root; Mosaic is absent.
2. GPL patch0004 checks HTTP success and catches network errors before success
   callback. A real read-only Linux file baseline042202 failed visibly in the
   regression (HTTP500 was silently accepted). Fixed browser043214/save-failure.json
   passes: explicit dialog, dirty text retained, disk unchanged, no extra old-file
   native init, then permission recovery saves exact text and emits changed CC43.
3. `Application.closed` rejects new input while `cleanup_complete` tracks actual
   cleanup. Failed closers retain retryable handles; the dataset lease remains
   until native/editor writers have stopped. Their processes inherit its FD.
   Native retries skip completed service groups and do not resend quit to reaped
   services. Maiden completion is distinct from a reported abnormal exit.
4. restart-failures-20260909-043519/report.json passes three actual native cases:
   injected failure before cleanup leaves writers alive and dataset busy; retry
   reaps exact old services then reopens, with held inputs absent in replacement;
   a missing-script replacement-start failure releases ownership, then restoring
   the script allows retry. Peer-held input remains unchanged throughout. The
   test-only wrapper arms its injection only after startup; no production hook.
   lifecycle043344 additionally passes real browser held-key switching/release.
5. GPL patch0005 fixes root links. lifecycle043344 navigates data→maiden-probe→
   counter.txt after restart and observes the persisted counter in the editor.
6. The PCM verifier resets passed before checking and clears old errors only on
   success. `tests/maiden_reverification.py` passes using lifecycle043344: a copied
   previously-green report pointing at missing PCM fails and records passed:false,
   preserving original evidence and WAVs.
7. Weak --finalize was removed, not grandfathered. Fresh automated buildmaiden-03
   passed with the original three patches; freshmaiden-04 passed with all five
   patches and source/patch identity checks (Yarn275.89s, Go and frontend success).
   Current optional bundle is maiden-tools-05; no manual finalization was used.

Final smoke043913/report.json passes eight browser/REPL/reload/stereo PCM/cleanup
checks with the new bundle. lifecycle043344 passes ten checks including audio.
Transport044208 passes seven: actual unit GET refusal, authentication/framing,
broken links, and a killed owned Go process. The latter reports cleanup_failed,
still reaps services/stops HTTP, and releases the dataset for a new lease.
The 24 top-level tests pass; existing shutdown-error contract passed after the
cleanup changes. No claim of arbitrary engine, hardware or platform support.
