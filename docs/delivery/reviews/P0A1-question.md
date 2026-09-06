Perform one focused structural review of a user-authorized architecture amendment:
this must be a general-purpose norns/grid utility using proper official monome
repos as dependencies for easy updates. Mosaic is the first comprehensive test
fixture, not a runtime dependency or hardcoded app. Review current UPSTREAM.md,
PLAN.md, ACCEPTANCE.md and DECISIONS.md; previous P0 packets are historical.

Check only material gaps in: independence of core build/install/load from Mosaic;
generic script names/include paths/data; official-source pins vs community forks;
runtime/app dependency lock separation; meaningful generic conformance; explicit
upstream update, failure rejection and rollback; ownership of these in existing
cards. Preserve the earlier complete Mosaic acceptance and MIDI-only WSL-first
scope. Host feasibility is explicitly C00 work, not an established fact.

Stakes: trusted single-user local development utility. No hostile multi-tenancy,
financial correctness, audio promise or universal third-party-script certification.
We want small adapters around official norns, not a complete parallel Lua runtime
or a new package manager. Flag concrete blocker/major gaps only, with actionable
file/section citations. No need to rerun the earlier complete P0 review, demand
dual-vendor convergence, or request minor speculative hardening. This is a scoped
review for newly requested product boundaries, not a third round on old findings.
