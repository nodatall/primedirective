---
name: execute-task
description: Execute planned work from existing `prd`, `tdd`, and `tasks-plan` artifacts. Supports standard task mode, `--one-shot`, and `--preserve-review-artifacts`.
---

# Execute Task Skill

Implement task work from the required planning artifact set:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

## Activation

Invoke explicitly with `$execute-task`.

Required request context:

- standard mode: a specific `<task-id>` plus `<plan-key>` when it cannot be inferred
- one-shot mode: `--one-shot` plus `<plan-key>` when it cannot be inferred

Supported modifiers:

- `--one-shot`
- `--preserve-review-artifacts`

Activation examples:

- Standard mode with explicit key: `$execute-task task-id=<task-id> plan-key=<plan-key>`
- Standard mode with inferred key: `$execute-task task-id=<task-id>`
- One-shot with explicit key: `$execute-task --one-shot plan-key=<plan-key>`
- One-shot with inferred key: `$execute-task --one-shot`

## Required references

Load these files before running:

- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/execution/task-management.md`
- `skills/shared/references/review/review-protocol.md`

## Workflow

1. Resolve artifact files from trigger using `task-file-contract.md`.
2. Require PRD, TDD, and tasks-plan before doing any execution work.
3. Run kickoff branch setup from `review-protocol.md` Step 1 rules, carrying and committing the required planning artifacts on the new branch when they are the only uncommitted kickoff files.
4. Execute according to mode:
   - Standard mode: implement the requested task/sub-task in the main agent.
   - One-shot mode: treat the entire unchecked remainder of the task plan as the execution scope; if kickoff carried uncommitted planning artifacts, commit them before the first implementation sub-task, then for each sub-task in file order the main agent spawns one worker subagent, waits for completion, integrates the result, spawns one fresh review subagent for that review round with PRD, TDD, tasks-plan, the temp sub-task contract when it exists, and the exact review scope, applies findings, and owns task updates and commit before moving to the next sub-task.
5. For each completed sub-task:
  - create/update `tasks/tmp/plan-task-<task-id>.md` with the sub-task contract before coding, then keep it current as implementation and review findings refine the slice
  - identify repo-local implementation, test, and validation reference patterns before coding, record the chosen pattern in the sub-task contract, and justify any deliberate deviation
  - write or update the targeted test first when the slice is practically testable
  - run the targeted test command and confirm the intended failure before implementation begins
  - implement the change using PRD + TDD + tasks-plan + exact sub-task block + the chosen local pattern
  - rerun the targeted verification until the slice passes, then expand to any additional relevant repo-defined checks for the touched surface such as lint, format-check, typecheck, test, or build
  - run one `sub-task` review round automatically using the active prompt profile from `review-protocol.md`, in a fresh review subagent when subagents are available; in one-shot mode, defer Prompt G to the final `full-branch` review
  - apply fixes from review findings and rerun relevant tests
  - keep temp review artifacts under `tasks/tmp/` when `--preserve-review-artifacts` is enabled; otherwise clean them up per protocol
  - mark checklist updates in `tasks/tasks-plan-<plan-key>.md`
  - create a dedicated commit for the sub-task
  - in one-shot mode, immediately re-open `tasks/tasks-plan-<plan-key>.md` after the commit, identify the next unchecked sub-task in file order, and continue directly when one exists
6. In one-shot mode, after all sub-tasks are complete, run one final `full-branch` review round automatically using the active prompt profile from `review-protocol.md` in one fresh review subagent before finalization. This is the review round that must satisfy Prompt G for frontend-facing work.
7. Run finalization from `review-protocol.md` Step 9 rules only after all unchecked sub-tasks in the task plan are complete.
8. Before any terminal handoff in one-shot mode, re-open `tasks/tasks-plan-<plan-key>.md` and confirm there are no remaining unchecked sub-tasks anywhere in the file. If any remain, continue execution instead of handing off unless a real blocker prevents further progress.
9. In one-shot mode, do not stop after an intermediate sub-task merely to report status, preserve a clean commit boundary, or hand off remaining work. Only stop early for a real blocker that cannot be resolved inside the current run.
10. In one-shot mode, do not emit user-visible mid-run progress updates while unchecked sub-tasks remain. Keep executing silently across sub-task boundaries instead of reporting intermediate completion, verification, or “continuing into X” status.
11. In one-shot mode, do not expose internal worker handoffs as user-visible content. Message shapes like “Completed and committed now: ...”, “Latest passing verifies: ...”, “I've already started X ...”, or “Remaining unchecked work is ...” are invalid while unchecked sub-tasks remain, even if they say execution is still in progress.
12. Assume any user-visible one-shot message before finalization can be treated as the run's terminal output. Only send a user-visible message early when a real blocker prevents continuation and the exact required user action is stated.

## Mode behavior

- Standard mode: single-agent execution, pause for approval between sub-tasks.
- One-shot mode: sequential worker-subagent loop across the entire remaining unchecked task file, no approval pauses between sub-tasks, one main-agent integration plus fresh-review-subagent cycle per sub-task, defer frontend browser evidence to the final branch-wide review, then run one final full-branch review in a fresh review subagent before finalization. The run is terminal only after finalization or an explicit unresolved blocker.

## Execution defaults

- Treat a failing-test-first red/green loop as the default for code-bearing, practically testable slices.
- A test-first exception is allowed only when a failing-first loop is not practical for that exact slice; record the exception reason in `tasks/tmp/plan-task-<task-id>.md` before implementation starts.
- Before coding, search the repo for similar implementations and tests, follow an existing local pattern when it is a good fit, and record why any new pattern or deviation is necessary.
- Before coding, inspect the repo's actual validation commands and config rather than assuming standard names exist.
- Do not invent lint, format, hook, or similar repo tooling mid-execution unless the planned task explicitly includes introducing that tooling or the user asks for it.

## Review relationship

Task execution includes automatic review rounds. Manual review runs through explicit `$review-chain` activation, optionally scoped to a specific `<task-id>`.
