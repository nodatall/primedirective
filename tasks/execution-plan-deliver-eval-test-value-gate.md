# Reusable Deliver Eval And Test-Value Gate

Goal: Turn the Retry Failed Jobs pilot into a reusable Deliver regression eval and make review remediation preserve only valuable permanent tests while using the narrowest trustworthy rereview.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## Context

- The historical pilot is recorded in `tasks/eval-deliver-retry-failed.md`. Its runnable fixture and evaluator are still disposable under `agent-scratch/deliver-eval/retry-failed/`.
- The normal regression lane will compare the previous Deliver contract with the candidate Deliver contract through `$skill-review`. Native Plan mode is an occasional absolute calibration lane, and Pro analysis remains a separate optional lane.
- Retry Failed Jobs is a known-case regression scenario because it generated this policy hypothesis. A replay of the real May 2026 preflight/session-updater remediation, which predates this hypothesis and exercises a different operational boundary, must corroborate it before this plan can claim the policy is useful beyond Queuectl.
- Fixing a verified defect and preserving a permanent regression test are separate decisions. A finding may still require a fix when its proof belongs in a temporary probe or is already covered.
- The branch starts from local commit `a4116bb`, which is ahead of `origin/main`. At planning time the historical eval report and this plan are the only untracked files; preserve any later user or updater changes and inspect validator overlap before editing.
- Proportional rereview will apply only to Deliver final-review repairs. `$review-chain`, `$merge-review`, and `$repo-sweep` behavior remain unchanged; changing those public workflows would require their own skill reviews.
- This stays within the existing Deliver, skill-review, finding-disposition, and review-protocol boundaries. It does not add a public modifier or require a new architecture document.
- The user-approved v3 rerun stopped with a frozen `candidate_regression`: Queuectl baseline completed and normalized in 4,101 seconds, while the candidate exhausted the identical 5,400-second arm budget before remediation finalization. Per the no-tuning rule, another contract or evaluator revision requires a new user-approved versioned iteration.
- The user approved a v4 iteration after reviewing the v3 result. V4 keeps the evaluator, scenarios, baseline, expected outcomes, and 5,400-second arm budget unchanged. Its candidate-only contract change must move the test-value decision before any Deliver test is made permanent, reject environment-dependent permanent regressions, and prevent repair closeout from restarting broad planning or full-review work when a targeted rereview is sufficient.
- V4 proved the early test-value gate reduces test bloat, but its narrow rereview rule missed cross-process completion races and mutation-before-output failures. The user approved a v5 iteration that keeps the early gate and adds only those missing full-rereview triggers.
- The historical two-script holdout has no tracked test harness. V5 records PF-001 and PF-002 as `probe_only` instead of requiring invented permanent coverage, while PF-002 still requires a full rereview because it changes cross-process completion semantics.

## Steps

### 1. Freeze A Fair Reusable Eval Suite

- [x] Create `evals/deliver/suite.md` and `evals/deliver/retry-failed/` with a clean Queuectl fixture containing the original repository files, public tests, source bullets, acceptance contract, fixed approval text, local-only stop boundary, and the required `gpt-5.6-sol` `xhigh` run condition; add deterministic fixture preparation that gives both arms the same fresh git snapshot without creating a second workflow runner.
- [x] Add the original seven frozen Retry Failed Jobs hidden acceptance checks without expanding them from later reviewer discoveries, and keep evaluator files outside both arm worktrees and undisclosed until the staged evaluation step that needs them.
- [x] Add `evals/deliver/preflight-remediation-holdout/` as a historical replay pinned to Prime Directive commit `27103d3`, using the real corrupt-throttle and asynchronous-Codex-preflight findings later repaired in `2e0c019`; include the approved paused-at-remediation plan, original finding evidence, exact failing probes, local-only stop boundary, and expected fixed behavior from `tasks/merge-review-deliver-repo-sweep-swarm-nitpick.md`.
- [x] Freeze an evaluator-owned outcome ledger before editing the contracts. Across the known case and historical replay it must include at least one defensible `permanent`, `table_case`, `probe_only`, `no_test`, `targeted`, and `full` outcome, including mixed-offset selection, grouped malformed-input boundaries, rare integer/deep-structure probes, an unreachable helper concern, an isolated repair, and the session-updater/preflight operational-boundary repair.
- [x] Give both arms each fixed review packet only after their pre-packet implementation or starting state and validation evidence are snapshotted, then freeze the post-remediation code, tests, probes, review logs, and timing evidence before evaluation.
- [x] Add post-review challenge probes derived from the pilot, label them as post-hoc diagnostic evidence rather than unbiased acceptance checks, and keep evaluator-owned expected outcomes out of the arm prompts and artifacts.
- [x] Give each runner an allowlisted, hashed input manifest containing only its fixture, scenario stage, and extracted contract; reject symlinks, paths that escape the staging root, evaluator or ledger paths, and any run whose recorded tool trace accesses evaluator-owned files before output freeze.
- [x] Normalize both arms deterministically from actual diffs, test changes, probe evidence, and review actions into one evaluator-owned behavior schema; enforce an identity-clue denylist, prove the blind packet is invariant under swapped Run A/Run B labels, and check candidate field compliance separately after identity is revealed.
- [x] Add a blinded judge rubric that scores material correctness first, then permanent-test value, related-case consolidation, rereview breadth, test count and size, full review-round count, wall time, and unnecessary ceremony without imposing a hard line-count cap.
- [x] Document one repeatable `$skill-review skill=deliver scenario=evals/deliver/suite.md baseline=<ref> candidate=<ref-or-worktree> --preserve-review-artifacts` command and the artifacts, isolation checks, measurements, and staged packet handoff required from both arms.
- [x] Update `tasks/eval-deliver-retry-failed.md` to remain the historical native-versus-Deliver pilot while pointing future behavior-change comparisons to the tracked two-scenario baseline-versus-candidate suite.

### 2. Add The Shared Test-Value Decision

- [x] Extend `skills/shared/references/review/finding-disposition.md` with a Deliver-scoped test-value vocabulary: `test_disposition: permanent | table_case | probe_only | no_test` plus a concise evidence-backed rationale for material `fix` findings and investigated `no action` concerns during Deliver final-review remediation; require `rereview_scope: targeted | full` only when Deliver authorizes a repair.
- [x] For Deliver remediation only, require permanent or table-driven coverage to be reachable through a supported path, materially tied to the explicit contract or credible harm, uniquely uncovered, deterministic, and economical to maintain.
- [x] For Deliver remediation only, require related cases to share the smallest coherent table-driven test, use `probe_only` for useful one-run evidence under `agent-scratch/`, and use `no_test` when stronger coverage already exists or permanent reproduction would add no durable protection; every repaired finding still needs recorded verification evidence.
- [x] State explicitly that `test_disposition` does not weaken the existing `Disposition: fix` rule: every verified, in-scope, safely repairable defect is still fixed.

### 3. Make Rereviews Proportional

- [x] Update `skills/shared/references/review/review-protocol.md` so Deliver's initial final review remains full-branch, while an isolated authorized Deliver repair defaults to one fresh targeted rereview of the finding, repair diff, repaired boundary, adjacent callers, and relevant tests.
- [x] Require a targeted rereview record to name the finding IDs, exact pre-repair base state, repair boundary and diff, adjacent callers and tests inspected, originating review prompt plus testing prompt, conditional trust-boundary prompt when applicable, validation reruns, and fresh reviewer evidence.
- [x] Escalate a repair to a full rereview only when it crosses architecture or trust boundaries, changes a public contract, affects security or data integrity broadly, cannot be shown to be isolated, or the targeted rereview discovers a new material defect; use the widest required scope when several repairs are grouped.
- [x] Qualify unconditional resweep wording only for Deliver final-review remediation, while preserving the rule that completion requires no unresolved verified `fix` findings and leaving review-chain, merge-review, and repo-sweep behavior unchanged.
- [x] Add one short consumer hook in `skills/deliver/SKILL.md` that enforces the shared test-value and rereview decisions without copying their rubric.
- [x] Update `skills/shared/references/contract-ownership.md` so finding disposition owns the Deliver-scoped test-persistence vocabulary and review protocol owns Deliver rereview topology, without imposing either behavior on other consumers.

### 4. Enforce And Validate The Contracts

- [x] Add a focused validator check for the Deliver-scoped shared enums, permanent-test criteria, repair/test independence, targeted/full escalation rules, and Deliver consumer hook, including tokens that keep other shared-reference consumers outside the requirement; inspect and preserve any validator edits that appear after planning.
- [x] Validate the Queuectl fixture's existing public tests, reproduce the two historical preflight/session-updater failures at the pinned holdout state, prove the Retry Failed Jobs hidden suite fails closed against the unimplemented base where expected, and test the evaluator normalizer, manifest/path isolation, trace contamination audit, identity-clue denylist, swapped-label invariance, and challenge-probe entry points.
- [x] Run `python3 scripts/validate-skill-contracts.py`, `git diff --check`, and `./scripts/install-codex-plugin.sh`.
- [x] Run one fresh full-branch implementation review of the contract and eval-harness changes before the expensive comparison, apply any authorized fixes, rerun all contract and deterministic harness checks, reinstall the plugin, and record the exact evaluated candidate state.

### 5. Run The Reusable Eval And Judge The Change

- [x] Apply the user-approved v4 candidate change: gate permanent-test work before implementation workers receive it, treat approved fixed remediation packets as implementation resumes without another refinement loop, and count their recorded completed full review as the initial full round.
- [x] Validate the v4 contract, run a fresh adversarial review, install the updated plugin, and freeze the exact candidate commit before starting the unchanged expensive comparison.

- [x] Run the tracked two-scenario suite with `a4116bb` as the pre-change Deliver baseline and the recorded candidate state, using fresh `gpt-5.6-sol` `xhigh` runners, identical fixture snapshots, approvals, tools, staged review packets, and stop boundaries, with artifacts preserved.
- [x] Run the frozen hidden checks and diagnostic challenge probes unchanged against both outputs, normalize and redact both artifact sets, and give a fresh blinded judge the behavior evidence before revealing contract identity, candidate-only compliance checks, and process-cost measurements.
- [x] Apply the frozen outcome ledger as a hard programmatic gate after the blinded verdict and identity reveal, as required by the frozen suite order: retain every expected high-value `permanent` or `table_case` protection, retain every safety-required `full` rereview, and allow no regression in any pre-registered disposition or rereview category.
- [ ] Require measurable improvement on both cost axes—fewer unjustified permanent test cases and fewer unnecessary full rereviews—plus no material correctness loss in either scenario and a combined blinded `candidate_better` verdict before calling the new gate useful.
- [x] Treat any ledger-axis failure or any verdict other than `candidate_better` as a stop with preserved evidence: do not tune the frozen suite or contract to the observed result inside this run, and require a new user-approved, versioned evaluation iteration before revising or rerunning.
- [x] Record the comparison, costs, limitations, judge evidence, and completion stamp in the normal durable `$skill-review` state document, while keeping native-plan and Pro runs outside this required regression lane.

### 5.1 Run The User-Approved V5 Iteration

- [ ] Add full Deliver rereview escalation for repairs that change cross-process coordination, lifecycle or completion semantics, or the ordering of irreversible mutation relative to user-visible output or diagnostics; keep isolated repairs targeted and leave non-Deliver workflows unchanged.
- [ ] Update the frozen expected-outcome ledger for a new v5 iteration so the no-test-harness holdout expects `probe_only` for PF-001 and PF-002, PF-002 still expects `full`, and the Queuectl mutation/output boundary requires a full rereview.
- [ ] Validate and adversarially review the v5 contract and evaluator changes, install the plugin, and commit the exact candidate/evaluator state before any shadow run.
- [ ] Run fresh baseline and candidate arms for both unchanged scenarios with `gpt-5.6-sol`, `xhigh`, identical 5,400-second budgets, preserved evidence, and no reuse of v4 outcomes.
- [ ] Freeze and normalize all four arms, obtain a fresh blinded verdict before identity reveal, then run candidate compliance and the v5 outcome gate.
- [ ] Stop without tuning if v5 is not `candidate_better`; continue to closeout only if correctness is preserved, both cost axes improve, and the ledger passes.

### 6. Review And Close Out

- [ ] After a `candidate_better` comparison, run a fresh Deliver final full-branch review against the exact evaluated candidate state; if remediation changes a contract, fixture, evaluator, consumer hook, or other evaluated surface, rerun Step 4 and the complete Step 5 comparison, then run another fresh final review of that newly evaluated state.
- [ ] Require the latest comparison to be `candidate_better`, the latest final review to cover that exact candidate state, and no evaluated-surface changes afterward before archiving or claiming completion.
- [ ] Preserve all pre-existing worktree changes, archive this plan, commit only this plan's implementation and closeout artifacts, and complete the Deliver finalization gate before handoff.
