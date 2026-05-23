# Review Protocol

Mandatory review behavior for task execution and explicit review commands.

Use `skills/shared/references/review/review-calibration.md` as calibration context for task-based review rounds. The calibration examples are guidance for reviewer judgment; they do not add user-facing approval steps.
Use `skills/shared/references/review/finding-disposition.md` when reporting material findings, assigning disposition, or deciding whether a repair is authorized.

See `skills/shared/references/contract-ownership.md` for shared contract ownership. This file owns review topology, prompt profile selection, review logs, and final review/finalization sequencing.

## Step 1: Kickoff (task execution only)

Default branch-creation kickoff:

```text
Please fetch the latest `origin/main` from github.
We are going to work on task <task-id> in [tasks/tasks-plan-<plan-key>.md], using [tasks/prd-<plan-key>.md] and [tasks/tdd-<plan-key>.md] as planning context. If local `main` and `origin/main` differ in either direction, stop and ask before creating the feature branch. Otherwise, please create and switch to a new branch from `origin/main`. If the only uncommitted changes are those required planning artifacts for this plan, carry them onto the new branch and commit them there before implementation starts.
```

Current-branch kickoff for legacy task execution:

```text
Please fetch the latest `origin/main` from github.
We are going to work on task <task-id> in [tasks/tasks-plan-<plan-key>.md], using [tasks/prd-<plan-key>.md] and [tasks/tdd-<plan-key>.md] as planning context. Keep the current branch. Do not create, switch, or rename branches. If the current branch is `main`, `master`, the resolved local base branch, or detached `HEAD`, stop and ask before implementation starts. If the only uncommitted changes are those required planning artifacts for this plan, commit them on the current branch before implementation starts.
If the current branch already has an open PR, do not treat PR title/scope mismatch as a kickoff blocker. Continue locally, do not push or update that PR by default, and report the mismatch in the final handoff.
```

Default branch-creation operational translation:

- `git fetch origin main`
- Compare local `main` and `origin/main` after fetch.
- If local `main` is missing, continue from `origin/main`.
- If local `main` and `origin/main` differ in either direction, stop and ask before creating branch.
- If the working tree is clean, create/switch the feature branch from `origin/main`.
- If the only dirty files are `tasks/prd-<plan-key>.md`, `tasks/tdd-<plan-key>.md`, and `tasks/tasks-plan-<plan-key>.md` for the current plan, create/switch the feature branch from `origin/main`, carry those files onto the branch, and commit them before implementation starts.
- If the working tree contains unrelated changes, stop and ask before creating branch.
- Create/switch `nodatall/<short-task-name>` from `origin/main`.
- If `main` is checked out elsewhere in another worktree, create branch directly from `origin/main`.

Current-branch operational translation:

- `git fetch origin main`
- Identify the current branch with `git branch --show-current`.
- Stop and ask if the current checkout is detached `HEAD`.
- Stop and ask if the current branch is `main`, `master`, or the resolved local base branch.
- Keep the current branch. Do not create, switch, or rename branches.
- If the current branch already has an open PR, continue locally anyway. A PR title/scope mismatch is not a reason to stop before implementation.
- Skip the local-`main` versus `origin/main` divergence gate because no new branch is being created from main.
- If the working tree is clean, continue on the current branch.
- If the only dirty files are `tasks/prd-<plan-key>.md`, `tasks/tdd-<plan-key>.md`, and `tasks/tasks-plan-<plan-key>.md` for the current plan, commit them on the current branch before implementation starts.
- If other dirty files exist, inspect them before editing. Continue only when they are clearly current task work on the active branch; otherwise stop and ask before editing overlapping files.
- Full-branch reviews and finalization still use `origin/main` as the branch base.

## Review context for task-based work

For task-based execution or task-scoped review, evaluate changes against:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`
- `tasks/tmp/plan-task-<task-id>.md` when it exists for the reviewed sub-task

Use those artifacts to judge scope alignment, missing work, and regression risk.
Also verify, when `tasks/tmp/plan-task-<task-id>.md` exists, that the implementation followed the recorded local reference pattern, used a failing-test-first loop when practical, recorded credible `test_first_evidence`, and justified any exception or trust-boundary handling recorded there.
Use the contract's `acceptance_checks` as the reviewer-facing behavior list. Treat missing, vague, or unexercised acceptance checks as a review issue when they affect confidence in the slice.

## Review scopes

Use one of these scopes for each review round:

- `sub-task`: only the current sub-task delta since the last committed branch state, plus current uncommitted changes
- `full-branch`: all branch changes compared to `origin/main`, including current uncommitted changes

Default scope rules:

- Standard task execution review: `sub-task`
- End-of-one-shot final review: `full-branch`
- Explicit `$review-chain` review runs: `full-branch`

## Review agent topology

When subagents are available, execute each review round in one fresh dedicated review subagent/thread.

- The fresh review subagent owns the prompt sequence for that review round.
- The fresh review subagent should use the strongest appropriate reasoning tier for the selected model family or budget, following `skills/shared/references/reasoning-budget.md`.
- The review round is the unit of isolation. Do not split Prompt A, Prompt B, Prompt C, and so on into separate threads.
- During one-shot execution, the main agent must spawn the review subagent after all implementation workers return.
- Review subagents are siblings of implementation workers. Do not have a worker spawn, direct, or review itself through its own child agent.
- For task-based `sub-task` review rounds, pass the review subagent:
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
  - `tasks/tmp/plan-task-<task-id>.md` when it exists
  - the exact sub-task ID and the current `sub-task` review scope
- For task-based `full-branch` review rounds, pass the review subagent:
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
  - any still-relevant `tasks/tmp/plan-task-<task-id>.md` file that remains available and materially informs branch-wide review
  - the current `full-branch` review scope
- The main agent still owns review orchestration, review-log updates, decisions about findings, fixes, tests, task-list updates, and commits.

## Artifact preservation flag

Supported trigger suffix:

- `--preserve-review-artifacts`

Behavior when present on `$review-chain` or a legacy task execution workflow:

- Keep review logs under `tasks/tmp/` after successful completion instead of deleting them.
- For task execution modes, also keep per-sub-task temp plan docs created under `tasks/tmp/`.
- Include the preserved artifact paths in the final user-visible summary.

## Prompt profile selection

Detect the active review prompt profile before each review round:

- `codex-short` when the current agent identifies as Codex or is running on an OpenAI GPT/Codex-family model.
- `full-chain` otherwise.

Use these prompt sets:

- `codex-short`: Prompt A, then Prompt G when required, then Prompt H when required, then Prompt I.
- `full-chain`: Prompts A-I in order, treating Prompts G and H as conditional when not applicable.

Repo-wide skills may override the default prompt profile when their contract requires deeper coverage. `$repo-sweep` forces `full-chain`; `$repo-sweep --swarm` also includes the nitpick-depth maintainability lane owned by `skills/repo-sweep/references/nitpick-depth.md`.

Rationale:

- Codex review runs tend to produce most useful findings in the first broad review plus the closing audit, with Prompt G still valuable for frontend evidence and Prompt H still valuable for deploy-bound changes.
- Non-Codex agents should continue to use the full redundant multi-pass chain.

## Required review checks

Every applicable review round must explicitly verify:

- whether the slice was driven by a failing targeted test first when the work was practically testable
- whether the sub-task contract includes `test_first_evidence` for practically testable work, including the pre-change command, observed failure, exercised production path, and post-change command
- whether any skipped red/green loop has a recorded and justified exception in the sub-task contract
- whether an existing repo-local implementation or test pattern was followed when one existed
- whether any newly introduced pattern or deliberate deviation is justified by the actual slice constraints
- whether the contract's acceptance checks were exercised with meaningful evidence, not just asserted
- whether the core user or system interaction is actually wired end-to-end rather than display-only, stubbed, or mocked away
- whether any recorded `trust_boundary_notes` are still true in the implemented change
- for `full-branch` task-based reviews, whether any material code finding points to a reusable agent-loop failure that should be changed in future planning, worker packets, validation cadence, or review prompts

## Prompts A-I

### Prompt A

```text
Please review all changes in the current review scope, including current uncommitted changes.
```

### Prompt B

```text
Review a second time over the same review scope.
```

### Prompt C

```text
Code Quality Pass: Detect Maintainability Findings
Goal: Ensure the current code is high quality and fully finished.
Criteria:
Compact: Remove dead code, redundancy, and over-abstraction.
Concise: Simplify verbose logic and use idiomatic patterns.
Clean: Maintain consistent naming, clear structure, and proper formatting.
Capable: Handle edge cases, fail gracefully, and perform well.
Structurally improving: Do not approve changes that pass tests but make future work harder by moving complexity instead of deleting it, growing already-large files without a clear cohesion reason, leaking domain logic across boundaries, or adding shallow pass-through layers.
Action: Report only concrete maintainability findings with evidence, impact, and smallest safe fix path. Do not refactor, rewrite, delete, or edit code in the review subagent.
```

### Prompt D

```text
LARP Assessment: Critical Evaluation
Goal: Critically evaluate whether the code is real or performative.
Check For:
Stubbed functions returning fake data.
Hardcoded values masquerading as dynamic behavior.
Tests that mock away the actual logic being tested.
Error handling that silently swallows failures.
Async code that doesn't actually await.
Validation that doesn't validate.
Any code path that hasn't been executed and verified.
Action: Report findings honestly, flagging anything functional but unproven. Do not fix issues in the review subagent. Include the evidence needed for the main agent to decide whether each finding is `fix`, `needs human decision`, `residual risk`, or `no action`.
```

### Prompt E

```text
Clean Up Slop: Remove Cruft
Goal: Remove AI-generated cruft and over-engineering.
Target:
Unnecessary abstractions and wrapper functions.
Thin pass-through modules, adapters, hooks, or services that do not remove complexity and only hide where logic lives.
Complexity moved into helpers, configuration, callbacks, generated glue, or call sites instead of being simplified.
Domain logic leaked into UI, routing, storage, CLI, test fixtures, or orchestration layers where an existing boundary should own it.
Files pushed past roughly 1,000 lines, or already-large files made larger, without a strong locality reason and a credible split-or-delete path.
Verbose comments that restate the obvious.
Defensive code for impossible conditions.
Over-generic solutions for specific problems.
Redundant null checks and type assertions.
Enterprise patterns in simple scripts.
Filler words and hedging in strings/docs.
Action: Report only cruft that creates real maintenance cost, review confusion, behavior risk, or user-facing quality loss. Do not delete or rewrite code in the review subagent. Defer cosmetic cleanup unless it blocks acceptance or keeps a material fix coherent.
```

### Prompt F

```text
Thorough Testing: Coverage and Verification
Goal: Verify the change is actually exercised beyond the happy path.
Review For:
Boundary conditions and edge cases.
Invalid inputs and failure paths.
Integration points with real dependencies where practical.
Concurrent or async behavior where relevant.
Actual outputs and side effects, not just passing assertions.
Tests should exercise the same interface callers use and should usually survive internal refactors.
Do not count tests that simply restate implementation details, constants, helper internals, or copied literals as meaningful coverage or red/green evidence.
Action: Identify missing or weak coverage, name the highest-value test or probe to add, and record exactly what was executed and what remains unverified. Do not add tests in the review subagent.
```

### Prompt G

```text
Frontend Evidence Review
Goal: Verify all user-facing changes through actual visual inspection, not code inspection alone.
Required When:
Any change affects UI, layout, styling, interaction flows, responsive behavior, animations, or rendered content.
Default Scope Rule:
Require this prompt for frontend-facing `full-branch` review rounds and for explicit review runs that cover frontend work.
Action:
Use Playwright MCP by default to open the changed UI, exercise the affected flows, resize for relevant breakpoints, and capture screenshots of all changed screens and states.
For changed interactive controls, record interaction evidence instead of relying on screenshots alone: click affected buttons, select relevant menu options, exercise changed keyboard shortcuts, and confirm the resulting UI, API, storage, or log state when applicable.
When motion, timing, or multi-step interaction matters, also capture video or trace evidence using the Playwright CLI workflow.
After evidence is captured, close transient browser tabs, windows, and contexts opened only for review. Preserve only sessions that are explicitly named as persistent, such as manual-login, debugging, or long-running external workflows.
Review the captured evidence for visual regressions, broken layout, missing states, incorrect copy, and obvious accessibility issues visible in the UI.
Grade the result explicitly on four criteria: design quality, originality, craft, and functionality.
Use the sub-task contract when present to judge whether the intended screens, states, and design direction actually shipped.
Be skeptical of merely functional but generic output. If the task is meaningfully user-facing, do not approve work that meets functional checks while still reading as template-level or incoherent.
Fail Prompt G when functionality is below 4/5, craft is below 3/5, or design quality/originality is below 3/5 for work whose value includes the user experience.
Record exactly what was captured, what was reviewed, and what remains unverified.
Do not mark frontend-facing work complete without visual evidence.
```

### Prompt H

```text
Production Readiness Validation
Goal: Verify the change is ready for real deployment with evidence, not assertions.
Check:
Error handling and logging for realistic failure modes.
Configuration externalization and absence of hardcoded secrets.
Rollback, migration, or backfill safety where relevant.
Destructive database or data operations in tests, migrations, seeds, resets, backfills, and maintenance CLIs: they must be environment-scoped, prefer test-only connection strings where applicable, positively verify target database names or hosts before mutating data, and fail closed outside approved disposable targets.
Performance under expected usage where relevant.
Dependency and security hygiene.
Monitoring and alerting visibility where relevant.
Whether the change can access private data.
Whether the change accepts or is exposed to untrusted input.
Whether the change can send data externally or invoke outbound tools/actions.
For deployable web/API services, also check applicable go-live risks: load or capacity evidence, horizontal-scale assumptions, server-memory sessions, direct app-server uploads, synchronous email or slow third-party calls in request paths, queue/worker retries and idempotency, database indexes and multi-step-write transactions, startup migration race safety, backup/restore evidence, compression/CDN/static asset handling, health checks, graceful shutdown, outbound HTTP timeouts, circuit breakers or degradation behavior, centralized logs, alerting, websocket state handling, and incident runbooks.
Action: Report concrete evidence for each applicable item and flag gaps explicitly. Do not patch in the review subagent. Fail this prompt when the change combines access to private data, exposure to untrusted input, and outbound capability without a hard separation boundary or a human approval gate.
```

### Prompt I

```text
Final Completion Audit
Goal: Confirm the work is complete, solves the original problem, and has no silent gaps.
Ask:
Does this actually work based on executed verification?
Does it solve the original problem end-to-end or only part of it?
Are the core interactions and state transitions real, or is anything display-only, stubbed, mocked away, or disconnected from persistence/API/runtime behavior?
Can a realistic user complete the primary workflow without hidden setup knowledge?
Do UI, API, database, CLI, logs, or other relevant system states agree after the interaction?
Could any test, seed, reset, migration, bootstrap, or maintenance path mutate shared dev or production data by env/config accident?
Was anything skipped, deferred, or left implicit?
What assumptions remain and should be documented?
What is most likely to break in production?
Which part of the agent loop, if any, made the most important remaining issue more likely?
Action: Give an honest assessment, list any remaining issues or accepted risks explicitly, and do not mark the review complete while unresolved in-scope issues remain. For task-based `full-branch` reviews, also include the Agent-Loop Backprop output described below.
```

## Agent-Loop Backprop

For task-based `full-branch` review rounds, include a short Agent-Loop Backprop section after the code findings.

Purpose:

- Identify which upstream agent step made a material code defect, spec miss, weak verification, or confidence gap more likely.
- Propose the smallest future workflow change that would reduce recurrence.
- Keep process critique tied to evidence from this branch, not generic advice.

Classify each entry by likely source:

- `spec_intake`: original plan/spec was incomplete, ambiguous, or not preserved.
- `task_decomposition`: PRD/TDD/tasks-plan failed to carry a required behavior, invariant, or acceptance check.
- `worker_packet`: the sub-task packet omitted context, local pattern, trust boundary, or done condition needed by the worker.
- `implementation_loop`: the implementation skipped or weakened red/green, local pattern matching, focused validation, or integration checks.
- `review_context`: the final review lacked artifacts, diff scope, runtime evidence, screenshots, or validation output needed for confidence.
- `finalization_loop`: checklist, archive, commit, PR, baseline, or cleanup sequencing allowed a premature handoff risk.

For each agent-loop entry, record:

- linked code finding or confidence gap
- source classification
- evidence from the branch or review log
- proposed future loop change
- whether it is `blocking_via_code_finding`, `advisory`, or `workflow_patch_candidate`

Blocking rule:

- Agent-loop findings do not block terminal handoff by themselves.
- If an agent-loop finding explains a blocker/material code issue, the underlying code issue controls the stop/fix decision.
- Advisory process nits without a linked material defect, spec miss, or confidence gap should be omitted.
- Do not edit Prime Directive skills or repo workflow docs from inside a target repo run unless the task itself is to change those workflow docs. Record workflow changes as proposals for a later Prime Directive maintenance task.

## Prompt execution protocol (required)

For each prompt required by the active prompt profile, execute one-by-one in sequence:

1. Run prompt.
2. Record findings using the shared material finding shape when a finding affects completion, safety, correctness, or verification confidence.
3. Record repair authorization and fixes made by the main agent, or `none during review` when the review phase is read-only.
4. Record tests run (or `not run` + reason).
5. Move to next prompt.

Rules:

- Do not ask permission between prompts.
- Complete one full round per review cycle.
- Review subagents must not edit files, refactor, delete code, or add tests. They discover findings and evidence only.
- The main agent owns disposition and repair. Repairs are authorized only when the parent workflow permits them: legacy task execution review, `$deliver` final review for in-scope correctness fixes, `/goal $repo-sweep`, or repo-sweep after explicit user approval. A standalone `$review-chain` is report-first unless the user explicitly asked for fixes.
- If the main agent repairs a finding during an authorized execution context, rerun the relevant checks and continue to remaining prompts in the same round.
- Do not mark prompts complete retroactively from one combined pass.
- If a prompt is outside the active prompt profile, mark it `not applicable` with a short reason rather than leaving it incomplete.
- Compare the implementation against the task contract when `tasks/tmp/plan-task-<task-id>.md` exists; treat unexplained contract drift as a finding.
- When the task contract exists, verify `acceptance_checks`, `reference_patterns`, `test_first_plan`, and any `trust_boundary_notes` against the actual implementation and recorded verification evidence.
- Use the calibration examples in `review-calibration.md` to stay skeptical of superficial approvals, especially when a feature renders but does not deliver the promised interaction.
- Prompt G is required only for frontend-facing work or changes that affect rendered content, interaction flows, layout, styling, or responsive behavior.
- Otherwise mark Prompt G `not applicable` with a reason.
- Prompt H is required for deploy-bound work, for changes that materially affect operations, infrastructure, migrations, security posture, or runtime observability, and for any change touching agents, private data, secrets, untrusted input, or outbound actions/tools. Otherwise mark it `not applicable` with a reason.

## Review log protocol (required)

Create and maintain log files:

- Task review: `tasks/tmp/review-task-<task-id>.md`
- One-shot final review: `tasks/tmp/review-task-final-<plan-key>.md`
- Ad-hoc review: `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`

Activation-to-log mapping:

- `$review-chain` with a specific `<task-id>`: use `tasks/tmp/review-task-<task-id>.md`
- `$review-chain` without a task ID: use `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`
- One-shot final automatic full-branch review: use `tasks/tmp/review-task-final-<plan-key>.md`

Round behavior:

- If the target review log does not exist, create it and start `review_round: 1`.
- If the target review log exists, append a new round and increment `review_round`.

Initialize each new log with:

- `review_mode: task | ad-hoc`
- `branch_base_ref: origin/main | HEAD`
- `review_prompt_profile: codex-short | full-chain`
- `review_round: 1`
- `review_scope: sub-task | full-branch`

Checklist (in order):

- [ ] Prompt A: Review current review scope
- [ ] Prompt B: Review second pass on current review scope
- [ ] Prompt C: Code quality pass
- [ ] Prompt D: LARP assessment
- [ ] Prompt E: Clean up slop
- [ ] Prompt F: Thorough testing
- [ ] Prompt G: Frontend evidence review (or mark not applicable with reason)
- [ ] Prompt H: Production readiness validation (or mark not applicable with reason)
- [ ] Prompt I: Final completion audit

Per prompt entry include:

- `finding_count: 0` or `finding_count: <n>`
- concrete findings, using the shared material finding shape when applicable
- `agent_loop_findings: none` or concrete Agent-Loop Backprop entries for task-based `full-branch` rounds
- disposition and fixes made by the main agent, or `none during review`
- tests run
- `harness_lift` entries only when a harness component changed implementation, caught a real issue, prevented likely drift, or provided meaningful confidence not available from cheaper checks
- applicability when prompt is optional

Scope metadata rules:

- For `sub-task` review rounds, set `branch_base_ref: HEAD` and record the exact sub-task ID being reviewed.
- For `full-branch` review rounds, set `branch_base_ref: origin/main`.

Completion gates:

- All prompts required by the active prompt profile and all otherwise applicable conditional prompts completed.
- Minimum 1 full round complete.
- No unresolved LARP remediation TODO items.
- No unresolved final-audit issues without explicit accepted-risk or blocked status.
- No unresolved blocker/material code findings hidden as agent-loop findings.
- Tests passing or explicitly justified.

Deletion gate:

- Provide user-visible summary of latest round.
- Delete review log after all required checks and any requested harness drift report complete unless `--preserve-review-artifacts` is active for the parent trigger.

## Branch stability for explicit review activation

For `$review-chain` task or ad-hoc runs:

- Do not create, rename, or switch branches.
- Start at Prompt A.
- Run the active prompt profile, treating Prompts G and H as conditional when not applicable.
- Review scope is full branch diff vs `origin/main`, including uncommitted edits.
- Keep the review log when `--preserve-review-artifacts` is present.

## Automatic review behavior during execution

For standard task execution:

- After each completed sub-task and before its commit, run one review round in `sub-task` scope.
- When subagents are available, execute that `sub-task` review round in one fresh review subagent spawned by the main agent after implementation completes.
- Review only the current sub-task delta against `HEAD`, not the entire branch history.
- Apply fixes and rerun relevant tests before creating the sub-task commit.
- Delete sub-task review logs and temp plan docs after successful completion unless `--preserve-review-artifacts` is active or `--check-harness-drift` still needs them for final reporting.

For one-shot execution only:

- Do not run automatic per-sub-task review chains.
- After all sub-tasks are complete and before finalization, run one review round in `full-branch` scope.
- When subagents are available, execute that final `full-branch` review round in one fresh review subagent spawned by the main agent.
- This final round must review the entire branch diff vs `origin/main`, including all committed sub-task work.
- Unlike one-shot worker handoffs, final review must receive full PRD, TDD, task plan, and still-relevant temp contracts so it can check global intent, cross-task coherence, and accepted risks.
- Start final review scope discovery with concise commands such as `git diff --stat`, `git diff --name-only`, and targeted hunk reads. Do not re-dump every large diff or replay every historical focused test unless evidence is missing, stale, or contradicted.
- Review the focused verification evidence recorded during the implementation loop, then run the strongest practical broad validation needed for final confidence.
- Include Agent-Loop Backprop in the final review log. This is required only for task-based `full-branch` review rounds, and should stay tied to material code findings or confidence gaps rather than producing generic process commentary.
- If the branch includes frontend-facing work, Prompt G must be executed in this final round before completion.
- Keep the final full-branch review log through the hard finalization gate so the gate can verify that review actually happened. Keep it afterward only when `--preserve-review-artifacts` is active or when a requested harness drift report still needs it.
- Do not issue a terminal user handoff before this final full-branch review and Step 9 finalization are complete, unless a real blocker prevents continuation.
- After implementation validation passes, a user-facing recap of changed files, tests, generated artifacts, or sources is treated as a terminal handoff. Suppress it until the final review log exists, all required review prompts are checked off, material findings have disposition, and Step 9 finalization has completed.
- If an implementation summary has already been drafted before final review, discard it as stale and continue with final review; the final handoff must be written only from post-review and post-finalization evidence.

## Step 9: Finalization

```text
Please pull the latest main from github and rebase. If this is task-based work, mark the task complete. When all tasks are complete, archive the PRD, TDD, and task plan into `tasks/archive/<yyyy-mm-dd>-<plan-key>/`, then open a pull request unless the current parent workflow explicitly documented an existing non-base branch exception. If this is ad-hoc work, skip task completion and open a pull request with ad-hoc scope notes.
```

Operational translation:

- `git fetch origin main`
- `git rebase origin/main`
- Resolve conflicts and rerun relevant tests.
- For task-based work, update checklist and relevant files.
- Confirm the current branch is a dedicated feature branch, not `main`.
- For one-shot task-based work, re-open `tasks/tasks-plan-<plan-key>.md` immediately before terminal handoff and confirm no unchecked sub-tasks remain anywhere in the file.
- Treat this re-opened task-file check as a hard liveness gate, not as an invitation to summarize partial progress. If unchecked sub-tasks remain, return to execution immediately.
- Treat user-visible recap patterns such as completed-item lists, passing-verify lists, "already started X", or "remaining unchecked work is Y" as terminal-style handoff attempts when they would be the last message before more execution. If unchecked sub-tasks remain, do not emit that recap; continue execution instead.
- Treat any user-visible one-shot message before this Step 9 finalization completes as potentially terminal or stall-inducing. Do not emit mid-run progress updates; only interrupt the run early for a real blocker that requires explicit user action.
- Treat "What Changed", "Validation", "Planning/Artifacts", "Sources used", and similar completion-shaped sections as final-handoff sections. They are invalid before final review, review remediation, task/archive updates, commits, and the hard finalization gate are complete.
- If all checkboxes in task list are complete, archive:
  - Create `tasks/archive/<yyyy-mm-dd>-<plan-key>/` using the local current date in ISO format (`YYYY-MM-DD`)
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
- Run the hard finalization gate from `skills/shared/references/execution/finalization-gate.md`, including unchecked-task search, archive verification, final `git status --porcelain=v1`, and comparison against `tasks/tmp/finalization-baseline-<plan-key>.status`.
- If archiving, checklist updates, cleanup, implementation, or tests created uncommitted changes, commit them before terminal handoff. Pre-existing dirty entries from the kickoff baseline may remain, but no new uncommitted run work may remain.
- If the last user-visible message would only explain that final review, commit, PR creation, or finalization remains, suppress it and keep executing those closeout steps. That message is a failed terminal handoff unless an external blocker prevents continuation.
- Push the feature branch to `origin` if it is not already published, for example with `git push -u origin <branch-name>`, unless the current parent workflow explicitly documented an existing non-base branch exception.
- Open the pull request using the environment's native GitHub/PR integration when available, otherwise use a concrete CLI flow such as `gh pr create`, unless the current parent workflow explicitly documented an existing non-base branch exception.
- Exception: a parent workflow may explicitly document that it started on an existing non-base branch and will not open a PR by default. In that case, final handoff may complete with branch name, commits, validation, review result, archive path, and working-tree status instead of a PR URL. This exception skips PR creation only; it does not skip commits, checklist completion, final review, archiving, validation, final status checks, or baseline comparison.
- If the existing non-base branch already has an open PR, do not push to it, update it, or require its scope to match the new plan by default. Report any visible PR scope mismatch in the final handoff so the user can decide whether to push later, move the commits, or close/update the PR.
- Include summary, test evidence, and known risks/follow-ups in the PR body.
- Include material Agent-Loop Backprop proposals in the terminal handoff or PR body when they explain a defect that was fixed, a residual accepted risk, or a workflow patch candidate worth preserving.
- Treat PR creation as a hard completion gate: do not produce the terminal handoff until a PR exists and its URL is available, unless a real blocker prevents PR creation or the current parent workflow explicitly documented an existing non-base branch exception.
- Only after these steps, or a documented existing non-base branch exception path, may one-shot execution produce its terminal completion handoff.

## Step 10: Post-Merge Branch Cleanup

```text
If the current work has already been merged into `main`, clean up the merged feature branch locally and on GitHub.
```

Operational translation:

- `git fetch origin --prune`
- Confirm the feature branch tip is reachable from `origin/main`.
- Do not delete `main`, any currently checked out branch, any branch with unmerged local commits, or any branch tied to an open PR.
- Delete the remote branch on GitHub with `git push origin --delete <branch>` when it still exists and is safe to remove.
- Switch to `main` or another safe branch/worktree before deleting the local branch.
- Delete the local merged branch with `git branch -d <branch>`.
