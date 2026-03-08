# Review Protocol

Mandatory review behavior for task execution and explicit review commands.

## Step 1: Kickoff (task execution only)

```text
Please fetch the latest `origin/main` from github.
We are going to work on task <task-id> in [tasks/tasks-plan-<plan-key>.md], using [tasks/prd-<plan-key>.md] and [tasks/tdd-<plan-key>.md] as planning context. Please create and switch to a new branch from `origin/main`.
```

Operational translation:

- `git fetch origin main`
- If working tree is dirty, stop and ask before creating branch.
- Create/switch `nodatall/<short-task-name>` from `origin/main`.
- If `main` is checked out elsewhere in another worktree, create branch directly from `origin/main`.

## Review context for task-based work

For task-based execution or task-scoped review, evaluate changes against:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

Use those artifacts to judge scope alignment, missing work, and regression risk.

## Prompts A-I (full review round)

### Prompt A

```text
Please review all changes in this branch compared to origin/main, including current uncommitted changes.
```

### Prompt B

```text
Review a second time over the same branch-wide scope.
```

### Prompt C

```text
Code Quality Pass: Review and Refactor
Goal: Ensure the current code is high quality and fully finished.
Criteria:
Compact: Remove dead code, redundancy, and over-abstraction.
Concise: Simplify verbose logic and use idiomatic patterns.
Clean: Maintain consistent naming, clear structure, and proper formatting.
Capable: Handle edge cases, fail gracefully, and perform well.
Output: Show the refactored code with brief explanations of changes.
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
Action: Report findings honestly, flagging anything functional but unproven. Immediately fix every issue, from most complicated to simplest, using review-log TODO items to track progress.
```

### Prompt E

```text
Clean Up Slop: Remove Cruft
Goal: Remove AI-generated cruft and over-engineering.
Target:
Unnecessary abstractions and wrapper functions.
Verbose comments that restate the obvious.
Defensive code for impossible conditions.
Over-generic solutions for specific problems.
Redundant null checks and type assertions.
Enterprise patterns in simple scripts.
Filler words and hedging in strings/docs.
Action: Keep what adds value; delete what adds noise.
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
Action: Identify missing or weak coverage, add the highest-value tests, run them, and record exactly what was executed and what remains unverified.
```

### Prompt G

```text
Frontend Evidence Review
Goal: Verify all user-facing changes through actual visual inspection, not code inspection alone.
Required When:
Any change affects UI, layout, styling, interaction flows, responsive behavior, animations, or rendered content.
Action:
Use Playwright MCP by default to open the changed UI, exercise the affected flows, resize for relevant breakpoints, and capture screenshots of all changed screens and states.
When motion, timing, or multi-step interaction matters, also capture video or trace evidence using the Playwright CLI workflow.
Review the captured evidence for visual regressions, broken layout, missing states, incorrect copy, and obvious accessibility issues visible in the UI.
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
Performance under expected usage where relevant.
Dependency and security hygiene.
Monitoring and alerting visibility where relevant.
Action: Report concrete evidence for each applicable item, flag gaps explicitly, and fix any production-readiness issues that are in scope for this change.
```

### Prompt I

```text
Final Completion Audit
Goal: Confirm the work is complete, solves the original problem, and has no silent gaps.
Ask:
Does this actually work based on executed verification?
Does it solve the original problem end-to-end or only part of it?
Was anything skipped, deferred, or left implicit?
What assumptions remain and should be documented?
What is most likely to break in production?
Action: Give an honest assessment, list any remaining issues or accepted risks explicitly, and do not mark the review complete while unresolved in-scope issues remain.
```

## Prompt execution protocol (required)

For each required prompt, execute one-by-one in sequence:

1. Run prompt.
2. Record findings.
3. Record fixes made.
4. Record tests run (or `not run` + reason).
5. Move to next prompt.

Rules:

- Do not ask permission between prompts.
- Complete one full round per review cycle.
- If a prompt introduces code changes, continue to remaining prompts in same round.
- Do not mark prompts complete retroactively from one combined pass.
- Prompt G is required only for frontend-facing work or changes that affect rendered content, interaction flows, layout, styling, or responsive behavior. Otherwise mark it `not applicable` with a reason.
- Prompt H is required only for deploy-bound work or changes that materially affect operations, infrastructure, migrations, security posture, or runtime observability. Otherwise mark it `not applicable` with a reason.

## Review log protocol (required)

Create and maintain log files:

- Task review: `tasks/tmp/review-task-<task-id>.md`
- Ad-hoc review: `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`

Trigger-to-log mapping:

- `begin review <task-id>`: use `tasks/tmp/review-task-<task-id>.md`
- `begin review`: use `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`

Round behavior:

- If the target review log does not exist, create it and start `review_round: 1`.
- If the target review log exists, append a new round and increment `review_round`.

Initialize each new log with:

- `review_mode: task | ad-hoc`
- `branch_base_ref: origin/main`
- `review_round: 1`
- `review_scope: full-branch`

Checklist (in order):

- [ ] Prompt A: Review full branch diff vs origin/main
- [ ] Prompt B: Review second pass on full branch diff
- [ ] Prompt C: Code quality pass
- [ ] Prompt D: LARP assessment
- [ ] Prompt E: Clean up slop
- [ ] Prompt F: Thorough testing
- [ ] Prompt G: Frontend evidence review (or mark not applicable with reason)
- [ ] Prompt H: Production readiness validation (or mark not applicable with reason)
- [ ] Prompt I: Final completion audit

Per prompt entry include:

- `finding_count: 0` or `finding_count: <n>`
- concrete findings
- fixes made
- tests run
- applicability when prompt is optional

Completion gates:

- All required and applicable prompt checkboxes completed.
- Minimum 1 full round complete.
- No unresolved LARP remediation TODO items.
- No unresolved final-audit issues without explicit accepted-risk or blocked status.
- Tests passing or explicitly justified.

Deletion gate:

- Provide user-visible summary of latest round.
- Delete review log after all required checks complete.

## Branch stability for explicit review triggers

For `begin review` and `begin review <task-id>`:

- Do not create, rename, or switch branches.
- Start at Prompt A.
- Run full sequence A-I, treating Prompts G and H as conditional when not applicable.
- Review scope is full branch diff vs `origin/main`, including uncommitted edits.

## Step 9: Finalization

```text
Please pull the latest main from github and rebase. If this is task-based work, mark the task complete. When all tasks are complete, archive the PRD, TDD, and task plan into `tasks/archive/<plan-key>/`, then open a pull request. If this is ad-hoc work, skip task completion and open a pull request with ad-hoc scope notes.
```

Operational translation:

- `git fetch origin main`
- `git rebase origin/main`
- Resolve conflicts and rerun relevant tests.
- For task-based work, update checklist and relevant files.
- If all checkboxes in task list are complete, archive:
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
- Open PR with summary, test evidence, and known risks/follow-ups.

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
