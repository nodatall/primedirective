# Agents

Primary workflow rules live in `rules/task-management.md`. Follow that first.

## Repo-Specific Norms
- Branch naming: `nodatall/<short-task-name>` (concise, concrete).
- Update `tasks/tasks-prd-<prd-key>.md` after every PRD task sub-task (Relevant Files + checkboxes). Ad-hoc maintenance changes do not require task-list updates unless explicitly requested.
- Update `README.md` only when setup/commands/env requirements change.
- Tests: prefer `npm test`; if skipped, say why.
- Bugs: add regression test when it fits.
- When working on browser E2E tests (especially files under `tests/e2e/**`, `playwright.config.*`, or Playwright CI scripts), use the `playwright` skill by default.

## Task Trigger Workflow
- Accepted trigger phrase: `begin task <task-id> in <prd-key>` (example: `begin task 1.3 in sortinghat`).
- Accepted one-shot trigger phrase: `begin one-shot in <prd-id>`.
- Resolve files from `<prd-key>` (standard mode) or `<prd-id>` (one-shot mode):
  - Task list: `tasks/tasks-prd-<prd-ref>.md`
  - PRD reference: `tasks/prd-<prd-ref>.md`
  - `<prd-ref>` means the provided PRD token (`<prd-key>` in standard mode, `<prd-id>` in one-shot mode).
- Standard mode: if `<task-id>` or `<prd-key>` is missing, or if either file does not exist, stop and ask for clarification.
- One-shot mode: if `<prd-id>` is missing, or if either file does not exist, stop and ask for clarification.
- Execute steps in order. Do not skip, reorder, or merge steps.
- Standard mode gate: pause after Step 2 and wait for plan approval before Step 3.
- Standard mode gate: complete one sub-task at a time and pause for user go-ahead between sub-tasks per `rules/task-management.md`.
- One-shot mode (`begin one-shot in <prd-id>`) behavior:
  - Do not pause for plan approval after Step 2.
  - Do not pause for user go-ahead between sub-tasks.
  - Use one branch for the full one-shot run; do not create a new branch per sub-task.
  - Start from the first not-yet-complete sub-task in `tasks/tasks-prd-<prd-id>.md`, then continue in file order until all are complete.
  - Run Steps 2-8 per sub-task, then immediately continue to the next sub-task.
  - Run Step 9 once, after the final sub-task is complete, and open one PR for the entire run.
- Review Log Protocol is mandatory for all Step 4-9 review activity (task and ad-hoc).
- Review execution rule: during Steps 4-8, run Prompts A-E continuously in sequence without asking for user permission between prompts.
- Branch stability rule for review:
  - During `begin review ...` and `resume review ...`, do **not** create, rename, or switch branches.
  - Keep review work on the current branch being reviewed.
- Review prompts must be executed one-at-a-time in sequence (A, then B, then C, then D, then E). Do not batch multiple prompts into one combined pass.
- Mandatory review-round rule:
  - Run **one full review round** (Prompts A-E) for each review cycle.
  - If a prompt introduces code changes, continue the remaining prompts in the same round (do **not** restart from Prompt A).
- Mandatory task-mode gate: after each completed sub-task, create a dedicated commit summarizing the work before starting the next sub-task.

### Step 1: Kickoff Prompt
```text
Please fetch the latest `origin/main` from github.
We are going to work on task <task-id> in [tasks/tasks-prd-<prd-key>.md], please create and switch to a new branch from `origin/main`.
```
Operational translation:
- `git fetch origin main`
- If there are uncommitted changes in the working tree, stop and ask for guidance before creating the task branch.
- create/switch `nodatall/<short-task-name>` from `origin/main` (for example: `git switch -c nodatall/<short-task-name> origin/main`)
- Worktree rule: when `main` is checked out in another worktree, do **not** run `git checkout main`; create/switch the task branch directly from `origin/main`.
- One-shot rule: run Step 1 only once at the beginning of the one-shot run.

### Step 2: Planning Prompt
```text
Switch to planning mode:
Create a plan for how to implement task <task-id>. Save the approved plan to [tasks/tmp/plan-task-<task-id>.md]. When the task is marked complete in [tasks/tasks-prd-<prd-key>.md], delete the task plan doc.
```
- One-shot rule: do not wait for plan approval; proceed directly to Step 3 for that sub-task.

### Step 3: Build Prompt
```text
To begin coding (switch back to edit mode):
Build task <task-id> from [tasks/tasks-prd-<prd-key>.md] using [tasks/prd-<prd-key>.md] as reference. Keep these quality standards in mind as you work:
- Compact: remove dead code/redundancy/over-abstraction.
- Concise: prefer the simplest implementation that passes tests.
- Clean: keep naming/structure consistent; avoid obvious comments.
- Capable: handle invalid input and key edge cases explicitly.
- No performative code (no fake dynamic behavior).
- Real validation and real tests (execute real logic paths, not only mocks).
- No cruft (remove debug scaffolding/temp code before finalization).
```

### Step 4: Review Prompt A
```text
Please review all changes in this branch compared to origin/main, including current uncommitted changes.
```
Review target rule:
- Round 1 review scope is branch-wide: all changes between `origin/main` and current branch state.
- Include both committed branch changes and current working-tree edits.
- For task-mode `/review`, always provide:
  - `tasks/tmp/plan-task-<task-id>.md`
  - `tasks/tasks-prd-<prd-key>.md`

### Step 5: Review Prompt B
```text
Review a second time over the same branch-wide scope.
```

### Step 6: Review Prompt C (Code Quality Pass)
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

### Step 7: Review Prompt D (LARP Assessment)
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

### Step 8: Review Prompt E (Clean Up Slop)
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

### Step 9: Finalization Prompt
```text
Please pull the latest main from github and rebase. If this is task-based work, mark the task complete, then open a pull request. If this is ad-hoc work, skip task completion and open a pull request with ad-hoc scope notes.
```
Operational translation:
- `git fetch origin main`
- `git rebase origin/main`
- Resolve conflicts and rerun relevant tests.
- Update task checklist/relevant files only for task-based PRD work.
- Open PR with task id, summary, test evidence, and known risks/follow-ups.
- For ad-hoc reviews, open PR with ad-hoc scope summary, test evidence, and known risks/follow-ups.
- One-shot rule: run Step 9 once after all queued sub-tasks are complete; open one PR that summarizes the full one-shot scope.
## Review Trigger Commands
- `resume review <task-id>`:
  - Continue review for an existing task after additional edits.
  - Stay on the current branch. Do not rename/create/switch branches during review.
  - Start at Step 4 and run **all of Steps 4/5/6/7/8** in order.
  - Append a new round in `tasks/tmp/review-task-<task-id>.md` and re-review full branch scope.
- `begin review ad-hoc`:
  - Start review for non-PRD maintenance work or work begun without a task ID.
  - Stay on the current branch. Do not rename/create/switch branches during review.
  - Create `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`.
  - Start at Step 4 using full-branch scope.
  - Task-list updates are not required for non-PRD maintenance docs/workflow/tooling changes.
- `resume review ad-hoc`:
  - Continue ad-hoc review after additional edits.
  - Stay on the current branch. Do not rename/create/switch branches during review.
  - Start at Step 4 and re-review full branch scope.
  - Run **all of Steps 4/5/6/7/8** in order.

## Prompt Execution Protocol (Required)
- Treat each prompt (A-E) as a separate operation:
  - Run prompt.
  - Record findings.
  - Record fixes made.
  - Record tests run (or `not run` + why).
  - Then move to the next prompt.
- Do not pause for user permission between Prompts A-E; complete the full sequence in one continuous run.
- Each prompt entry must explicitly say either:
  - `finding_count: 0`, or
  - `finding_count: <n>` with concrete findings.
- Do not mark a prompt complete retroactively from a single combined review pass.
- Before deleting a review log, provide a user-visible summary of each prompt result for the latest round.
- After providing the summary, delete the review log file.

## Review Log Protocol (Required)
- For each sub-task, create `tasks/tmp/review-task-<task-id>.md`.
- For ad-hoc review, create `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`.
- Start each log with:
  - `review_mode: task | ad-hoc`
  - `branch_base_ref: origin/main`
  - `review_round: 1`
  - `review_scope: full-branch`
- Use this checklist and mark each prompt complete in order:
  - [ ] Prompt A: Review full branch diff vs origin/main
  - [ ] Prompt B: Review second pass on full branch diff
  - [ ] Prompt C: Code quality pass
  - [ ] Prompt D: LARP assessment
  - [ ] Prompt E: Clean up slop
- Minimum rounds:
  - Code/logic changes: minimum 1 full round (A-E).
  - Docs/copy-only changes: minimum 1 full round (A-E).
- Record for each step: findings, fixes made, and tests run.
- If a step introduces code changes, rerun relevant tests before checking it off.
- Do not append a new round solely because a prompt in the current round introduced code changes; finish Prompts A/B/C/D/E in the same round.
- Append a new round only when additional edits are introduced **after** a completed review round and a new review cycle is started (for example via `resume review ...`).
- Task-mode completion gate:
  - Do not mark the sub-task complete until all review log checkboxes are done.
  - Do not mark the sub-task complete until minimum required rounds are complete.
  - Do not mark the sub-task complete until: review log complete, tests passing (or explicitly justified), task list updated, and no unresolved LARP remediation TODO items in the review log.
- Ad-hoc completion gate:
  - Do not close ad-hoc review until all review log checkboxes are done.
  - Do not close ad-hoc review until minimum required rounds are complete.
  - Do not close ad-hoc review until: review log complete, tests passing (or explicitly justified), and no unresolved LARP remediation TODO items in the review log.
- Deletion gate:
  - Delete `tasks/tmp/review-task-*.md` after providing the latest round summary and completing all required review checks.
- If rebase, test, or review fails, stop progression, log the blocker in the review log, and resolve before continuing.
- Delete `tasks/tmp/review-task-<task-id>.md` only after task review is complete and before closing the sub-task.
- Delete `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md` only after ad-hoc review is complete.
