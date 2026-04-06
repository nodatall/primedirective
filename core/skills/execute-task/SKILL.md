---
name: execute-task
description: Use when the user starts implementation with `begin task <task-id> in <plan-key> [--preserve-review-artifacts]` or `begin one-shot in <plan-key> [--preserve-review-artifacts]` and needs end-to-end execution from required PRD, TDD, and tasks-plan artifacts.
---

# Execute Task Skill

Implement task work from the required planning artifact set:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

## Triggers

Accept:

- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]`

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
   - One-shot mode: treat the entire unchecked remainder of the task plan as the execution scope; if kickoff carried uncommitted planning artifacts, commit them before the first implementation sub-task, then for each sub-task in file order the main agent spawns one worker subagent, waits for completion, then owns integration, review, task updates, and commit before moving to the next sub-task.
5. For each completed sub-task:
   - create/update `tasks/tmp/plan-task-<task-id>.md` with the sub-task contract before coding, then keep it current as implementation and review findings refine the slice
   - identify repo-local implementation and test reference patterns before coding, record the chosen pattern in the sub-task contract, and justify any deliberate deviation
   - write or update the targeted test first when the slice is practically testable
   - run the targeted test command and confirm the intended failure before implementation begins
   - implement the change using PRD + TDD + tasks-plan + exact sub-task block + the chosen local pattern
   - rerun the targeted verification until the slice passes, then expand to any additional relevant checks
   - run one `sub-task` review round automatically using the active prompt profile from `review-protocol.md`; in one-shot mode, defer Prompt G to the final `full-branch` review
   - apply fixes from review findings and rerun relevant tests
   - keep temp review artifacts under `tasks/tmp/` when `--preserve-review-artifacts` is enabled; otherwise clean them up per protocol
   - mark checklist updates in `tasks/tasks-plan-<plan-key>.md`
   - create a dedicated commit for the sub-task
   - in one-shot mode, immediately re-open `tasks/tasks-plan-<plan-key>.md` after the commit, identify the next unchecked sub-task in file order, and continue directly when one exists
6. In one-shot mode, after all sub-tasks are complete, run one final `full-branch` review round automatically using the active prompt profile from `review-protocol.md` before finalization. This is the review round that must satisfy Prompt G for frontend-facing work.
7. Run finalization from `review-protocol.md` Step 9 rules only after all unchecked sub-tasks in the task plan are complete.
8. Before any terminal handoff in one-shot mode, re-open `tasks/tasks-plan-<plan-key>.md` and confirm there are no remaining unchecked sub-tasks anywhere in the file. If any remain, continue execution instead of handing off unless a real blocker prevents further progress.
9. In one-shot mode, do not stop after an intermediate sub-task merely to report status, preserve a clean commit boundary, or hand off remaining work. Only stop early for a real blocker that cannot be resolved inside the current run.
10. In one-shot mode, do not emit terminal-style progress summaries such as “implemented through task X”, “remaining work is Y”, or “resuming from here” while unchecked sub-tasks still remain. Any optional progress update must be explicitly non-terminal and must name the next sub-task that execution is already continuing into.
11. In one-shot mode, do not expose internal worker handoffs as user-visible stopping points. Message shapes like “Completed and committed now: ...”, “Latest passing verifies: ...”, “I've already started X ...”, or “Remaining unchecked work is ...” are invalid as the last user-visible content while unchecked sub-tasks remain, even if the message also says execution is still in progress.

## Mode behavior

- Standard mode (`begin task ...`): single-agent execution, pause for approval between sub-tasks.
- One-shot mode (`begin one-shot ...`): sequential worker-subagent loop across the entire remaining unchecked task file, no approval pauses between sub-tasks, one main-agent integration/review/commit cycle per sub-task, defer frontend browser evidence to the final branch-wide review, then run one final full-branch review before finalization. The run is terminal only after finalization or an explicit unresolved blocker.

## Execution defaults

- Treat a failing-test-first red/green loop as the default for code-bearing, practically testable slices.
- A test-first exception is allowed only when a failing-first loop is not practical for that exact slice; record the exception reason in `tasks/tmp/plan-task-<task-id>.md` before implementation starts.
- Before coding, search the repo for similar implementations and tests, follow an existing local pattern when it is a good fit, and record why any new pattern or deviation is necessary.

## Review relationship

Task execution includes automatic review rounds. Manual review runs through `review-chain` triggers (`begin review` or `begin review <task-id>`).
