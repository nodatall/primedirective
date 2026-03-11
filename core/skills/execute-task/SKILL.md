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
3. Run kickoff branch setup from `review-protocol.md` Step 1 rules.
4. Execute according to mode:
   - Standard mode: implement the requested task/sub-task in the main agent.
   - One-shot mode: treat the entire unchecked remainder of the task plan as the execution scope; for each sub-task in file order, the main agent spawns one worker subagent, waits for completion, then owns integration, review, task updates, and commit before moving to the next sub-task.
5. For each completed sub-task:
   - create/update `tasks/tmp/plan-task-<task-id>.md`
   - build using PRD + TDD + tasks-plan + exact sub-task block
   - run one `sub-task` review round (A-I) automatically using `review-protocol.md`, treating Prompts G and H as conditional when not applicable
   - apply fixes from review findings and rerun relevant tests
   - keep temp review artifacts under `tasks/tmp/` when `--preserve-review-artifacts` is enabled; otherwise clean them up per protocol
   - mark checklist updates in `tasks/tasks-plan-<plan-key>.md`
   - create a dedicated commit for the sub-task
6. In one-shot mode, after all sub-tasks are complete, run one final `full-branch` review round (A-I) automatically using `review-protocol.md` before finalization.
7. Run finalization from `review-protocol.md` Step 9 rules only after all unchecked sub-tasks in the task plan are complete.
8. In one-shot mode, do not stop after an intermediate sub-task merely to report status, preserve a clean commit boundary, or hand off remaining work. Only stop early for a real blocker that cannot be resolved inside the current run.

## Mode behavior

- Standard mode (`begin task ...`): single-agent execution, pause for approval between sub-tasks.
- One-shot mode (`begin one-shot ...`): sequential worker-subagent loop across the entire remaining unchecked task file, no approval pauses between sub-tasks, one main-agent integration/review/commit cycle per sub-task, then one final full-branch review before finalization. The run is terminal only after finalization or an explicit unresolved blocker.

## Review relationship

Task execution includes automatic review rounds. Manual review runs through `review-chain` triggers (`begin review` or `begin review <task-id>`).
