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
- V5 reduced test and review cost but still classified Queuectl RF-002 as targeted. The user approved a v6 contract iteration that keeps the v5 policy and adds a deterministic scope-record validator; the frozen scenarios, outcome ledger, and correctness expectations remain unchanged.
- The user-approved v6 rerun preserved correctness and the blinded judge preferred the candidate. The hard category gate still stopped the run because the mechanical rule classified Queuectl RF-001 as full instead of targeted; no v6 tuning or rerun is authorized inside that frozen comparison.
- The user approved a v7 iteration that keeps v6's successful test-value behavior and RF-002 protection, but distinguishes a genuinely fallible output step after committed mutation from a repair that merely touches mutation and reporting in the same command.
- V7 proved that ordered-failure distinction, but RF-001 and RF-003 were still escalated by the broader `public_contract` flag. The user approved continued versioned iteration through a passing, merge-ready result. V8 keeps the frozen evaluator and narrows that flag to an actual change to the approved external contract, not a repair that restores already-approved behavior.
- V8's scope schema worked in the historical holdout, but the Queuectl runner did not treat its staged fixed remediation packet as the initial completed review, so it never used the scope record and performed one full review after all repairs. It also kept a permanent extreme-depth serialization regression. The blinded judge preferred the baseline and the hard gate rejected RF-001 full, RF-003 permanent, and RF-003 full; v9 must revise only the candidate contract while every evaluator-owned surface stays frozen.

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
- [x] Require measurable improvement on both cost axes—fewer unjustified permanent test cases and fewer unnecessary full rereviews—plus no material correctness loss in either scenario and a combined blinded `candidate_better` verdict before calling the new gate useful.
- [x] Treat any ledger-axis failure or any verdict other than `candidate_better` as a stop with preserved evidence: do not tune the frozen suite or contract to the observed result inside this run, and require a new user-approved, versioned evaluation iteration before revising or rerunning.
- [x] Record the comparison, costs, limitations, judge evidence, and completion stamp in the normal durable `$skill-review` state document, while keeping native-plan and Pro runs outside this required regression lane.

### 5.1 Run The User-Approved V5 Iteration

- [x] Add full Deliver rereview escalation for repairs that change cross-process coordination, lifecycle or completion semantics across concurrent or asynchronous boundaries, or the ordering of irreversible mutation relative to user-visible output or diagnostics; keep isolated repairs targeted and leave non-Deliver workflows unchanged.
- [x] Update the frozen expected-outcome ledger for a new v5 iteration so the no-test-harness holdout expects `probe_only` for PF-001 and PF-002, PF-002 still expects `full`, and the Queuectl mutation/output boundary requires a full rereview.
- [x] Validate and adversarially review the v5 contract and evaluator changes, install the plugin, and commit the exact candidate/evaluator state before any shadow run.
- [x] Run fresh baseline and candidate arms for both unchanged scenarios with `gpt-5.6-sol`, `xhigh`, identical 5,400-second budgets, preserved evidence, and no reuse of v4 outcomes.
- [x] Freeze and normalize all four arms, obtain a fresh blinded verdict before identity reveal, then run candidate compliance and the v5 outcome gate.
- [x] Stop without tuning if v5 is not `candidate_better`; continue to closeout only if correctness is preserved, both cost axes improve, and the ledger passes.

### 5.2 Add The User-Approved V6 Mechanical Scope Gate

- [x] Add one bundled Deliver validator that derives each repair action's required rereview scope from an explicit, complete risk-flag record and rejects a targeted action or grouped round when any full-review trigger applies.
- [x] Require Deliver to run the validator before starting a repair rereview and again after recording the executed round; keep the test-value policy, existing trigger semantics, and all non-Deliver workflows unchanged.
- [x] Add focused validator tests for isolated targeted repair, cross-process completion, mutation plus user-visible output, grouped widest scope, malformed or incomplete records, and incomplete executed-round evidence.
- [x] Validate the skill contract and bundled script, install the exact v6 candidate, and commit the change without rerunning the expensive comparison unless separately approved.
- [x] Run the separately approved fresh two-scenario comparison using original baseline `a4116bb`, exact v6 candidate `733810b`, and fresh `gpt-5.6-sol` `xhigh` runners.
- [x] Freeze and normalize all four official arms, obtain a fresh blinded verdict before identity reveal, then run candidate compliance and the unchanged outcome gate.
- [x] Record that the blinded judge preferred v6 and both cost axes strictly improved, but the hard gate rejected RF-001 `full` versus expected `targeted`.
- [x] Stop without tuning or rerunning v6; require a separately approved v7 iteration for any narrower mechanical rule.

### 5.3 Add The User-Approved V7 Ordered-Failure Gate

- [x] Add one explicit risk flag for a fallible user-visible output or diagnostic step that occurs after irreversible mutation, and require it to agree with the existing mutation and output flags.
- [x] Derive `full` from that ordered-failure flag, while allowing mutation plus unchanged safe reporting to remain `targeted`; preserve every other v6 full-review trigger and grouped-round rule.
- [x] Add focused tests proving the RF-001 shape is targeted, the RF-002 shape is full, inconsistent records fail closed, and grouped rounds still use the widest action scope.
- [x] Update only the Deliver-owned scope schema, shared review-protocol summary, and validator mirrors needed to enforce the rule; leave the frozen evaluator and outcome ledger unchanged.
- [x] Validate, forward-test, adversarially review, install, commit, and record the exact v7 candidate before any official arm starts.
- [x] Run four fresh `gpt-5.6-sol` `xhigh` arms against original baseline `a4116bb`, then freeze, normalize, blind-judge, reveal identity, and apply candidate compliance plus the unchanged hard gate.
- [x] Stop without tuning if v7 is not `candidate_better`; otherwise continue to exact-candidate merge review and closeout.

### 5.4 Add The User-Approved V8 Approved-Contract Change Gate

- [x] Replace the ambiguous `public_contract` risk flag with `changes_approved_public_contract` in schema v3; reject v2 records and old/new key mixtures.
- [x] Add one required `approved_contract_basis` assessment per repair with `effect: none | restore | change | uncertain` and a concise source or evidence citation. Require `changes_approved_public_contract` to be true if and only if `effect` is `change`; require `uncertain` to set `isolation_unproven` and derive full independently. Fail closed when a claimed restoration lacks support.
- [x] Define `change` as changing, expanding, withdrawing, or otherwise revising the approved caller-visible contract; define `restore` as bringing implementation back into agreement with a pre-repair approved contract without changing that contract.
- [x] Add focused tests covering every contract-effect/Boolean combination, proving approved-contract restoration is targeted, a genuine approved-contract change and an uncertain assessment are full, unsupported restoration plus v2 and mixed schemas fail closed, RF-002 remains full through the ordered-failure flag, PF-002 remains full through the cross-process flag, and grouped rounds still use the widest action scope.
- [x] Update only the Deliver-owned scope schema, shared review-protocol summary, contract validator mirrors, and focused tests; leave the frozen evaluator, outcome ledger, scenarios, and cost gates unchanged.
- [x] Validate and forward-test the actual candidate workflow on RF-001 restoration, RF-003 restoration, a genuine approved-contract change, and an ambiguous contract case; then run a fresh adversarial review, install, commit, and record the exact v8 candidate before any official arm starts.
- [x] Run four fresh `gpt-5.6-sol` `xhigh` arms against original baseline `a4116bb`, then freeze, normalize, blind-judge, reveal identity, and apply candidate compliance plus the unchanged hard gate.
- [x] Use `gpt-5.6-sol` `xhigh` for implementation review, all arm runners, and the blinded judge.
- [x] Apply the frozen failure-transition table in the v8 state document. A valid arm terminal seal closes that arm's rerun window; later normalization may resume only from its sealed output. A frozen judge verdict likewise cannot be rerun. Only an external interruption before the relevant seal may restart the same version with unchanged inputs. If v8 passes, continue to exact-candidate merge review and closeout.

### 5.5 Add The User-Approved V9 Fixed-Packet And Pathological-Probe Gate

- [x] Import a fixed remediation packet as the initial completed full review only when a fail-closed attestation records active-workflow provenance, exact unchanged base commit/tree/diff, completed full-branch prompt profile, fresh reviewer, final quality audit, finding evidence, repair authorization, and fixed stop boundary; copy that evidence into the normal Deliver final-review log. Otherwise preserve the ordinary mandatory fresh full review.
- [x] For every fixed-packet repair, create the schema-v3 action scope record before the first post-repair review. An ordinary mandatory full review may also satisfy the grouped repair round when it covers every action and is at least the validator-derived widest scope; an imported attested review requires a subsequent targeted/full repair rereview. Never omit the action-level required scopes.
- [x] Clarify the Deliver test-value owner so the exact extreme depth, size, recursion, interpreter-limit, or resource-limit trigger defaults to `probe_only` even when deterministic; determinism alone is insufficient. Preserve permanent/table-driven coverage for a distinct uniquely uncovered, stable, economical semantic or safety boundary with explicit contract or credible-harm value.
- [x] Prefer existing stronger coverage or one small supported-path boundary case when it already protects the general error contract, and do not also retain the pathological trigger as duplicate permanent coverage.
- [x] When a disposable or historical fixture has no established test path, keep supplied shell checks as `probe_only` instead of inventing a permanent harness. Execute the bundled scope validator in place from the loaded Deliver skill root; do not copy it into the target repo or target diff.
- [x] Update only candidate-owned Deliver and test-value contract wording plus the narrow validator mirrors that enforce ownership; leave schema v3, every evaluator-owned surface, and all non-Deliver workflows unchanged.
- [x] Validate and independently forward-test: attested packet import, missing attestation, base drift, normal no-packet review, Queuectl RF-001/RF-002/RF-003 action scopes, RF-003 pathological proof, historical PF-001/PF-002 probe-only handling without a new harness or copied validator, RF-004 no-test/no-rereview, and a hostile-input credible-harm boundary that still merits economical permanent coverage. Then run a fresh adversarial review, install, commit, and record the exact candidate before official arms start.
- [x] Before official arms, record and verify `beb346a:evals/deliver` tree `d7da128ff8aef384e49cdfc8ccd593129d82b8e4`, require zero diff from `beb346a` under `evals/deliver/**`, and rerun frozen harness/ledger checks so only candidate-owned contract files may differ.
- [x] Run four fresh `gpt-5.6-sol` `xhigh` arms against original baseline `a4116bb`, freeze every arm, obtain a fresh blinded verdict before reveal, and apply candidate compliance plus the unchanged hard gate.
- [x] Apply the version-neutral v9 transition table with the v8 precedence and seal/verdict restart limits. V9 was a conclusive hard-gate regression and is preserved before candidate-only v10 work.

### 5.6 Add The V10 Exact Category And First-Pass Verification Gate

- [x] Preserve every v9 correctness and test-value improvement while clarifying mechanism-based decisions: keep one standalone `permanent` regression for any uniquely uncovered material semantic invariant that does not share its boundary, expected result, and failure mechanism with a coherent table (chronology that determines irreversible selection is one example); derive `full` from the pre-repair mutation/output failure boundary even when the repair moves validation earlier; and keep an isolated restoration `targeted` when no other full trigger or new material finding applies.
- [x] Clarify that repair-scope flags describe the defect boundary changed or protected by the repair, not only the post-repair control flow. Add one consolidated validator case proving a repair that prevents fallible reporting after mutation still sets the ordered-failure flag and derives `full`.
- [x] Add a compact first-pass verification reminder for parser/validation repairs: verify accepted-looking values against the downstream consumer grammar, not just the new guard. For shell numeric state, include empty, non-digit, leading-zero/base-sensitive, and bounded-length cases as probes when relevant; do not turn them into a permanent harness in a disposable fixture.
- [x] Add a compact cross-process worker reminder to inspect active owner, concurrent waiters, failed/stale owner recovery, completion ordering, and default-versus-foreground behavior before the first full review. Prove that a synchronous caller cannot return while protected work or its live owner/lock remains active, even after an intermediate throttle/readiness signal, without expanding beyond the approved lifecycle contract.
- [x] Update only candidate-owned Deliver/shared contract wording, worker packet, scope-validator tests, and narrow contract-validator mirrors. Leave evaluator-owned surfaces and schema v3 unchanged.
- [x] Run fresh `gpt-5.6-sol` `xhigh` plan review, focused validation, and independent forward tests proving all frozen outcomes: RF-001 `permanent/targeted`, RF-002 `table_case/full`, RF-003 `probe_only/targeted`, RF-004 `no_test/null`, PF-001 `probe_only/targeted`, and PF-002 `probe_only/full`. Include negative controls where a same-mechanism chronology case remains `table_case` and mutation plus unchanged reporting remains `targeted`, plus parser-consumer grammar and synchronous cross-process completion cases with concurrent waiters and failed/stale owners. Then run adversarial implementation review, plugin install, exact candidate commit, and evaluator-tree zero-diff check before official arms.
- [x] Run four fresh sealed v10 arms, a fresh blinded judge before reveal, candidate compliance, and the unchanged hard gate. Apply the version-neutral transition table with `current_version=v10` and `next_candidate_version=v11`.

### 5.7 Repair Cross-Run Evaluator Isolation And Rerun V11

- [ ] Preserve exact Deliver baseline `a4116bb` and exact candidate `8a489bc`. Restrict evaluator changes to the eight exact paths named in the v11 state, require zero candidate-owned diff, and record exact extracted package hash manifests.
- [x] Deny all of `/private/tmp` in the runner Seatbelt profile and narrowly re-allow only the current arm stage. Create and pre-verify a canonical regular external sentinel outside every arm, add it to the mandatory first-tool gate, and re-verify it unchanged after each runner. Retain it through final merge rereview, then delete the exact sentinel/runtime only during terminal closeout after preserved evidence and the merge-ready result are committed.
- [x] Prove current-stage reads/writes and denial of external reads/writes through `/private/tmp`, `/tmp`, relative traversal, and an allowed-stage symlink escape. Run the full harness suite outside the enclosing sandbox so every Seatbelt assertion executes rather than skips.
- [x] Complete fresh adversarial plan and implementation reviews. Commit and record evaluator commit, `evals/deliver` tree, and canonical manifest digest; bind the evaluator/comparison identity and exact upstream hashes through preflight, phase metadata, freeze, seal, normalization, blind packet, judge record, reveal, compliance, outcome gate, and final verdict. Freeze evaluator bytes when arm 1 starts; allow later result-only commits outside `evals/deliver` to advance `HEAD` while requiring the frozen evaluator tree and manifest to remain exact.
- [ ] Create a frozen comparison manifest whose canonical SHA-256 is the comparison identity and durable attempt state that enforces this order: retry-failed baseline, retry-failed candidate, holdout baseline, holdout candidate. Under an exclusive lock, allow exactly one unsealed-to-sealed transition per attempt; reject out-of-order starts, duplicate/concurrent seals, and any repeated sealed arm. Record only a byte-identical externally interrupted unsealed restart. Resume only normalization after sealing or reveal/gates after a frozen verdict. Apply the exact v11 verdict/stop-reason/merge-readiness matrix and preserve v10 as superseded evidence without reusing its normalized outputs.

### 6. Review And Close Out

- [ ] After a `candidate_better` comparison, run a fresh Deliver final full-branch review against the exact evaluated candidate state. If remediation changes the candidate contract or another candidate-owned evaluated surface, freeze it as a new version with every evaluator-owned surface unchanged, rerun Step 4 and the complete Step 5 comparison, then review that newly evaluated state. If review instead finds an evaluator, fixture, ledger, scenario, rubric, harness, hidden-check, probe, prompt, approval, stop-boundary, timeout, or cost-gate defect, stop for separate authorization rather than changing it inside the continue-to-pass loop.
- [ ] Require the latest comparison to be `candidate_better`, the latest final review to cover that exact candidate state, and no evaluated-surface changes afterward before archiving or claiming completion.
- [ ] Preserve all pre-existing worktree changes, archive this plan, commit only this plan's implementation and closeout artifacts, and complete the Deliver finalization gate before handoff.
