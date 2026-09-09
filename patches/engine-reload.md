# Optional Crone engine lifecycle patch

Official monome/norns base: `14bbeae8646c6717f6bb44c8cd60250bf94b6042`.
Inspected newer official revision: `1d7209428841bc2b38619c8238ba0d2788bdbe68`;
both free/load handlers still fork independently and retain engine until sync.
No community runtime code is copied. This locally authored change modifies the
official runtime under its existing licence; engine implementations stay intact.

Browser Run baseline `artifacts/maiden/browser-20260909-033657/report.json`
and session e8aa652532924bd9a4866149c1c7e4d1/sclang.log show two frees of the same
TestSine instance followed by `/n_free Node 1011 not found`. Lua script cleanup
sends free before loading its engine; SC server sync yields between them.

`scripts/engine_reload_patch.py` serializes free and load through one semaphore,
held through server cleanup and asynchronous allocation completion. It emits
the explicit diff into the opt-in build; installation identity covers changed
SC bytes and patch digest. Errors remain visible. An allocation exception still
requires explicit session restart; this patch does not claim arbitrary-engine
recovery. Remove when pinned official upstream passes repeated browser reload
and post-reload signal checks without duplicate cleanup or leaked nodes.

Acceptance pending: this is a candidate, not an admitted default runtime fix.
