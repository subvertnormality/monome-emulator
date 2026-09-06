# P0A1 — General-purpose utility and official upstream amendment

Status: complete after the scoped review and targeted textual corrections.
User requested a general-purpose utility, with proper official monome repos as
dependencies for easy updates. This supersedes any Mosaic-only product boundary
in historical P0 packets. Original full Mosaic acceptance remains mandatory;
installation of its fixture is separate from ordinary use of the utility.

Paranoia response: `P0A1-review.json`, engine Claude, session
`8fcec847-fe00-4bb6-b255-bd608e19646d`. One focused query was used for this new
scope amendment, not a new convergence campaign on the earlier P0 findings.
It verified dependency separation, generic loading/conformance and update/rollback
ownership, and identified one material wording gap plus two minor clarifications.

| Finding | Disposition | Applied correction |
|---|---|---|
| A documented community-fork substitution could evade the official-source requirement | Accepted | UPSTREAM requires canonical https://github.com/monome/norns.git for the runtime lock; community runtime changes can only enter as explicit patches against official refs. PLAN architecture repeats this boundary. |
| “Optional” fixture could be read as optional acceptance | Accepted | D11 now says opt-in-installed fixture with mandatory applicable release acceptance. |
| C04 omitted explicit generic probe UI execution despite G02 ownership | Accepted | C04 now runs browser/control/render checks for both generic probes without Mosaic dependencies. |

The material fix is a direct textual closure of the reviewer's named loophole;
no implementation, new architectural choice or extra review cycle was needed.
No substantive finding remains unaddressed. This is structural review, not
evidence that native runtime builds or dependency upgrades have succeeded.

User clarification recorded in UPSTREAM: the intended interface is the actual
norns script screen, three keys/encoders and virtual grid. Unsupported audio or
peripheral dependencies remain explicitly reported. Standalone grid applications
for other host environments are not norns scripts.

G01–G06 add generic gates to the retained 17 cards and 24 Mosaic workflow families.
All implementation cards remain planned. C00 owns remaining empirical premises.
