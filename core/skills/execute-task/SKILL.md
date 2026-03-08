---
name: execute-task
description: Use when the user starts implementation with `begin task <task-id> in <plan-key>` or `begin one-shot in <plan-key>` and needs end-to-end execution from required PRD, TDD, and tasks-plan artifacts.
---

# Execute Task Skill

Implement task work from the required planning artifact set:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

## Triggers

Accept:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`

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
   - One-shot mode: for each sub-task, the main agent spawns one worker subagent, waits for completion, then owns integration, review, task updates, and commit before moving to the next sub-task.
5. For each completed sub-task:
   - create/update `tasks/tmp/plan-task-<task-id>.md`
   - build using PRD + TDD + tasks-plan + exact sub-task block
   - run one full review round (A-I) automatically using `review-protocol.md`, treating Prompts G and H as conditional when not applicable
   - apply fixes from review findings and rerun relevant tests
   - mark checklist updates in `tasks/tasks-plan-<plan-key>.md`
   - create a dedicated commit for the sub-task
6. Run finalization from `review-protocol.md` Step 9 rules after the active execution scope is complete.

## Mode behavior

- Standard mode (`begin task ...`): single-agent execution, pause for approval between sub-tasks.
- One-shot mode (`begin one-shot ...`): sequential worker-subagent loop, no approval pauses between sub-tasks, one main-agent integration/review/commit cycle per sub-task.

## Review relationship

Task execution includes automatic review rounds. Manual review runs through `review-chain` triggers (`begin review` or `begin review <task-id>`).
