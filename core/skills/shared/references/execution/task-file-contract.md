# Task File Contract

Canonical path and trigger contract for planning, build, and review skills.

## Accepted triggers

- Planning: `start planning "<unformed-plan>"`
- Standard task execution: `begin task <task-id> in <plan-key>`
- One-shot execution: `begin one-shot in <plan-key>`
- Task review: `begin review <task-id>`, `resume review <task-id>`
- Ad-hoc review: `begin review ad-hoc`, `resume review ad-hoc`

## Plan key resolution

Use `<plan-key>` directly for both standard and one-shot execution.

Resolve files exactly as:

- Required task list: `tasks/tasks-plan-<plan-key>.md`
- Optional PRD: `tasks/prd-<plan-key>.md`
- Optional TDD: `tasks/tdd-<plan-key>.md`

## Temporary execution files

- Per-sub-task plan doc: `tasks/tmp/plan-task-<task-id>.md`
- Task review log: `tasks/tmp/review-task-<task-id>.md`
- Ad-hoc review log: `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`

## Mode rules

### Standard mode

- Requires `<task-id>` and `<plan-key>`.
- If `tasks/tasks-plan-<plan-key>.md` is missing, stop and ask for clarification.
- Pause for user confirmation between sub-tasks.

### One-shot mode

- Requires `<plan-key>`.
- If `tasks/tasks-plan-<plan-key>.md` is missing, stop and ask for clarification.
- Start at first unchecked sub-task, continue in file order.
- No pauses between sub-tasks.
- Run finalization once after all sub-tasks complete.

## Legacy syntax

Do not accept legacy `prd-key`/`prd-id` trigger wording. Ask the user to use `plan-key` commands.
