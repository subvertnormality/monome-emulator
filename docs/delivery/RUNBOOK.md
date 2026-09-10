# Autonomous delivery, scaled for a development emulator

You are the execution agent. Deliver the cards in PLAN.md in dependency order;
make routine engineering decisions, test them, and leave a resumable record.
This document governs execution here. Parallax's policy does not apply by
inheritance.
The product boundary and official-dependency update policy are in UPSTREAM.md.
Generic runtime conformance and Mosaic compatibility are separate mandatory
delivery evidence layers; the application must never become a core dependency.

## Source and deliberate simplifications

Adapted on 2026-09-06 from
`\\wsl$\ubuntu-20.04\home\andy\parallax\docs\operations\COMPLEX_DELIVERY_RUNBOOK.md`,
especially sections 2–5, 9, 12, 14, and 16.6, and from the installed
`/home/andy/tools/paranoia-local/docs/tool-reference.md`.

| Retained from Parallax | Application here |
|---|---|
| Fresh-context executable specification | Self-contained cards with inputs, procedures, acceptance, outputs, and recovery |
| Dependency graph and premise ledger | Foundational runtime claims get empirical probes before downstream work |
| Evidence-based completion | Commands, exit codes, test inventory, versions, and reproducible artifacts |
| Adversarial plan and integration review | One scoped Paranoia pass at named checkpoints, with bounded follow-up |
| Focused validation during development | Package tests per card; broader suites at milestones |
| Durable decisions and failure recovery | Local Git-tracked state and short completion notes |
| Challenge consequential absence claims | Verify canonical paths and upstream interfaces before declaring a dependency impossible |

We omit issue-marker authorization, certificate registries, cloud evidence trust
roots, signed-commit gates, mandatory dual-vendor review, indefinite convergence,
per-card mutation campaigns, exhaustive mutation seals, and human certification.
GitHub issues/PRs may be added if requested; local progress does not depend on
them. Do not build a delivery orchestration platform as a prerequisite.

## Autonomy and card loop

1. Read `state.json`, the card, its dependencies' completion notes, and relevant
   acceptance rows. Inspect current Git status. Preserve unrelated edits.
2. Validate that dependency evidence still applies. Select the first eligible
   card. Mark it `in_progress` and record start revision and next concrete step.
3. Verify card-owned unknown premises before relying on them. A failed proof
   blocks its dependent work, not unrelated cards. Record a diagnosis and owner.
4. Implement one coherent slice, using the narrowest meaningful automated checks.
   Add tests for behavioural changes and realistic regressions, not mirror tests
   for simple wiring. Keep the real Mosaic runtime path in integration checks.
5. Run the card's declared package suite. Resolve errors and inventory omissions.
   At a review checkpoint, apply the review procedure below.
6. Write `docs/delivery/completions/<ID>.md`: result, changed files, source identity,
   exact commands, evidence paths/digests, limitations, accepted decisions, and
   any downstream obligation with a named owner. Update state only after checks.
7. Continue to the next eligible card. At context boundaries, record the exact
   next action and active process/artifact paths. Resume by inspecting these,
   not by rerunning every completed stage.

Card states: `planned`, `in_progress`, `blocked`, `done`. `blocked` names the
specific failed prerequisite and recovery action. A timeout, tool error, empty
test selection, skipped required test, or lost runner is never `done`.
Milestones additionally distinguish `not_run`, `failed`, and `passed`.

Routine implementation choices, defect fixes within the contract, and retrying a
diagnosed transient error are autonomous. User input is needed for changed product
scope, genuinely missing credentials/permissions, or destruction of user data.
Do not repeatedly ask about already-decided scope. Do not turn a manual setup
problem into a manual acceptance test.

After two attempts with the same failure cause, stop blind retries: inspect the
cause, switch to an evidence-backed alternative within scope, or record a precise
block. A retry budget is not permission to mark failure as success.

## Proportionate Paranoia

Stakes: a trusted, single-user local norns/grid utility processing user-selected
scripts and separate test fixtures, initially Mosaic. Consequences are wasted development time, misleading
green tests, incorrect MIDI, and accidental changes to local projects. Priorities
are runtime fidelity, real input/output coverage, reliable replay, and honest
release gates. No remote multi-tenancy, hostile insiders, financial certification,
or hard real-time hardware equivalence. Keep loopback binding, bounded inputs,
isolated project data, and process cleanup; do not invent enterprise governance.

Required checkpoints:

| Checkpoint | Review unit | Maximum planned calls |
|---|---|---:|
| P0 | This complete plan, runbook, acceptance contract, dependency graph | 1 critique + 1 focused follow-up |
| P1 | C06 first real Mosaic vertical slice and runtime boundary | 1 critique + 1 focused follow-up |
| P2 | C12 complete MIDI workflow and failure-verification package | 1 critique + 1 focused follow-up |
| P3 | C14 WSL release candidate, generic/app separation, official-dependency update/rollback, false-green gates and LLM workflow | 1 critique + 1 focused follow-up |
| P4 | C15 Linux portability diff and platform-specific evidence only | 1 critique + 1 focused follow-up |
| P5 | C16 controlled-clock adapter, before admitting D to the Mosaic timing campaign (D18) | 1 critique + 1 focused follow-up |

Use only the Opus Paranoia engine for all reviews after the user's 2026-09-10
instruction (D21). Earlier Codex and other historical reviews remain evidence; do
not rerun them solely to change engines. Pass explicit stakes,
focus, repository path, and round; never inherit Parallax's financial stakes.
Use medium effort and a 10-minute wall-time limit by default. A timed-out call
does not count as a completed review and must be diagnosed before retrying.
Use one-shot `critique_plan` with `class_closure: false`. Set
`claim_verification: false` for the structural plan review because unverified
external premises are explicitly assigned empirical cards; this does not verify
those premises. For one-shot branch review use `converge: false` and
`class_closure: false`. Confirm installed tool schema before invoking.

Capture complete raw response, session reference, reviewed input digest, and
triage in `docs/delivery/reviews/`. Use a focused `query` or `rebut` for follow-up
on accepted fixes or a disputed claim instead of another whole-plan cold pass.
Do not describe one-shot review as tracked convergence or as proof of correctness.

Fix reproducible in-scope blockers and major issues. Record minor suggestions as
backlog with an owner or decline with a reason. A second call is needed only if
fixes materially affect architecture/gates or a blocking dispute remains. Stop
review when substantive findings are resolved; do not spend the second call just
because the allowance remains. If substantive blockers remain at the cap, the
milestone remains blocked: use focused experiments to resolve them and request
a narrowly explained extra review only if necessary. Never waive a blocker on
budget grounds or narrow acceptance to obtain a green result.

If Paranoia fails, retain diagnostics and make one diagnosed retry. Continue
independent work but do not call that checkpoint reviewed. Report the exact
missing tool/authentication action if user intervention is actually required.
No generic substitute is labelled a Paranoia review.

## Validation cadence and evidence

During a card run focused tests; at completion run its package suite once.
After changes, rerun affected tests. Full acceptance is required at C12/C14 and
on each claimed platform in C15; avoid re-running every matrix combination after
documentation edits. Pin inventory counts and require nonzero collection.

Use selected failure injection to prove the tests can detect the failures they
claim to detect: wrong grid coordinates, a missing release, a dropped MIDI event,
wrong channel, stale screen, broken save, or swallowed Lua exception. Run these
against disposable fixtures/builds and assert that the intended check fails.
Do not run a whole-repository mutation campaign.

Every acceptance run records: emulator source revision and dirty patch digest,
official runtime and selected app/submodule revisions, dependency image/tool versions, platform facts,
scenario version and seed, logical and wall-clock mode, test selection and counts,
results including skips, input trace, output evidence, errors, and exit status.
Use a run-specific directory under `artifacts/runs/<run-id>/` and a schema-checked
`manifest.json`. Prevent stale manifests being reused for a different tree.

Keep compact completion/review summaries and small fixtures in Git. Keep bulky
frames/logs in ignored artifacts or CI artifacts, with a retention policy and a
reproduction command. Required release evidence must survive ordinary temporary
directory cleanup; default CI retention is 30 days, while small release manifests
and scenario fixtures remain versioned. Local evidence must exist when claiming
completion; a digest of a missing file is insufficient.

No screenshots must be inspected by a person. Images and machine-readable states
are debugging aids for an LLM and automated assertions. Every required UI outcome
must have an executable assertion, not a checklist saying “looks correct”.

## Change control without bureaucracy

Keep decisions in `docs/delivery/DECISIONS.md` and residual work in
`docs/delivery/RESIDUALS.md`. Each residual has an ID, impact, disposition
(`fix-now`, `fold:<card>`, `later`, `declined`), reason, and a promotion condition.
No separate card is needed for a small fix owned by an existing card.

An executor may refine steps and paths while preserving acceptance and scope;
record the reason. A changed runtime boundary, unsupported-feature policy, oracle,
or timing threshold needs an explicit contract amendment and focused review.
Changing a threshold solely because a candidate fails is prohibited. Product
scope reductions need the user; ordinary technical refinement does not.

The absence of physical hardware limits the claim to tested software-level
compatibility. Real hardware is neither a final gate nor an unpaid task for the
user. Report unsupported physical behaviours as outside scope from the outset.
