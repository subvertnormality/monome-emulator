# Optional official Maiden patches (GPL-3.0)

These patches modify the separately built official monome/maiden program, whose
source and GPL-3.0 licence remain in the optional bundle. They are not MIT core
server code. Patch context derives from official monome/maiden and carries its
GPL-3.0 terms; no Winder or Schollz implementation was copied.

Base: 2e64f7d59284962ac68055dd556e3fd8515462f8.
0001 makes dust directory responses follow directory links while preserving the
visible entry name. Broken links return explicit HTTP400 errors. The original
pin labels symlinked application directories as files, preventing editor tree
navigation. This does not alter catalog/project-manager semantics.
Remove when an official upstream implementation passes the same linked-folder
browser navigation/edit/save/run and broken-link regression tests.

0002 deduplicates in-flight reads of a selected buffer. Official HEAD checked
2026-09-09 remains the base above. Repeated selection notifications can trigger
two GETs; a late response resets the dirty flag and replaces user edits. The
browser regression deliberately delays the second response; unpatched evidence
is artifacts/maiden/browser-20260909-034056/report.json. Remove this patch when
upstream passes the same delayed-read/edit/save regression. Read errors remain
explicit and release the in-flight guard so a later selection can retry.

0003 propagates every Ace edit to its controlled buffer value. The old handler
only propagates the first change: replacing a selection emits deletion then
insertion, leaving the parent value empty. A later render restores that stale
value and Save writes an empty file. Evidence034725 shows one GET, dirty flag
preserved, PUT sent, but empty disposable file and editor. No user file was used.
Remove when official upstream preserves multi-change edits through parent renders
and saves the exact changed contents in the same browser regression.
