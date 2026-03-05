# Review Protocol

Mandatory review behavior for task execution and explicit review commands.

## Step 1: Kickoff (task execution only)

```text
Please fetch the latest `origin/main` from github.
We are going to work on task <task-id> in [tasks/tasks-plan-<plan-key>.md], please create and switch to a new branch from `origin/main`.
```

Operational translation:

- `git fetch origin main`
- If working tree is dirty, stop and ask before creating branch.
- Create/switch `nodatall/<short-task-name>` from `origin/main`.
- If `main` is checked out elsewhere in another worktree, create branch directly from `origin/main`.

## Prompts A-E (full review round)

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

## Prompt execution protocol (required)

For each prompt A-E, execute one-by-one in sequence:

1. Run prompt.
2. Record findings.
3. Record fixes made.
4. Record tests run (or `not run` + reason).
5. Move to next prompt.

Rules:

- Do not ask permission between prompts A-E.
- Complete one full round per review cycle.
- If a prompt introduces code changes, continue to remaining prompts in same round.
- Do not mark prompts complete retroactively from one combined pass.

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

Per prompt entry include:

- `finding_count: 0` or `finding_count: <n>`
- concrete findings
- fixes made
- tests run

Completion gates:

- All prompt checkboxes completed.
- Minimum 1 full round complete.
- No unresolved LARP remediation TODO items.
- Tests passing or explicitly justified.

Deletion gate:

- Provide user-visible summary of latest round.
- Delete review log after all required checks complete.

## Branch stability for explicit review triggers

For `begin review` and `begin review <task-id>`:

- Do not create, rename, or switch branches.
- Start at Prompt A.
- Run full sequence A-E.
- Review scope is full branch diff vs `origin/main`, including uncommitted edits.

## Step 9: Finalization

```text
Please pull the latest main from github and rebase. If this is task-based work, mark the task complete. When all tasks are complete, archive the task plan and any optional PRD/TDD docs into `tasks/archive/<plan-key>/`, then open a pull request. If this is ad-hoc work, skip task completion and open a pull request with ad-hoc scope notes.
```

Operational translation:

- `git fetch origin main`
- `git rebase origin/main`
- Resolve conflicts and rerun relevant tests.
- For task-based work, update checklist and relevant files.
- If all checkboxes in task list are complete, archive:
  - `tasks/tasks-plan-<plan-key>.md` (required)
  - `tasks/prd-<plan-key>.md` (if present)
  - `tasks/tdd-<plan-key>.md` (if present)
- Open PR with summary, test evidence, and known risks/follow-ups.
