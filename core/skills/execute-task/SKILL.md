---
name: execute-task
description: Use when the user starts implementation with `begin task <task-id> in <plan-key>` or `begin one-shot in <plan-key>` and needs end-to-end execution (branch setup, per-subtask build, automatic review chain, tests, commits, and finalization).
---

# Execute Task Skill

Implement task work from `tasks/tasks-plan-<plan-key>.md` and optional PRD/TDD context.

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
2. Run kickoff branch setup from `review-protocol.md` Step 1 rules.
3. For each sub-task:
- Create/update `tasks/tmp/plan-task-<task-id>.md`.
- Build using `tasks/tasks-plan-<plan-key>.md` plus optional `tasks/prd-<plan-key>.md` and `tasks/tdd-<plan-key>.md` when present.
- Run one full review round (A-E) automatically using `review-protocol.md`.
- Apply fixes from review findings and rerun relevant tests.
- Mark checklist updates in `tasks/tasks-plan-<plan-key>.md`.
- Create a dedicated commit for the sub-task.
- Standard mode: pause for user go-ahead between sub-tasks.
- One-shot mode: continue automatically to next sub-task.
4. Run finalization from `review-protocol.md` Step 9 rules:
- fetch + rebase on `origin/main`
- rerun relevant tests
- archive plan artifacts when all tasks are complete
- open PR

## Mode behavior

- Standard mode (`begin task ...`): wait for approval between sub-tasks.
- One-shot mode (`begin one-shot ...`): no approval pauses between sub-tasks; run finalization once after all subtasks are done.

## Review relationship

Task execution includes automatic review rounds. Manual ad-hoc or resumed review runs through `review-chain` skill triggers.
