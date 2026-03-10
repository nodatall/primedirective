# Task File Contract

Canonical path and trigger contract for planning, build, and review skills.

## Accepted triggers

- Planning: `start planning "<unformed-plan>"`
- Standard task execution: `begin task <task-id> in <plan-key>`
- One-shot execution: `begin one-shot in <plan-key>`
- Task review: `begin review <task-id>`
- Ad-hoc review (default): `begin review`

## Plan key resolution

Use `<plan-key>` directly for both standard and one-shot execution.

Resolve files exactly as:

- Required PRD: `tasks/prd-<plan-key>.md`
- Required TDD: `tasks/tdd-<plan-key>.md`
- Required task list: `tasks/tasks-plan-<plan-key>.md`

## Temporary execution files

- Per-sub-task plan doc: `tasks/tmp/plan-task-<task-id>.md`
- Task review log: `tasks/tmp/review-task-<task-id>.md`
- One-shot final review log: `tasks/tmp/review-task-final-<plan-key>.md`
- Ad-hoc review log: `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`

## Execution artifact gate

Execution requires all three planning artifacts.

If any one of these is missing:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

Then:

- stop immediately
- do not code
- do not auto-generate missing planning docs
- instruct the user to complete planning first

## Mode rules

### Standard mode

- Requires `<task-id>` and `<plan-key>`.
- Executes the requested task/sub-task in the main agent.
- Pause for user confirmation between sub-tasks.

### One-shot mode

- Requires `<plan-key>`.
- Start at first unchecked sub-task and continue in file order.
- Continue until there are no unchecked sub-tasks left anywhere in the file; do not stop at parent-task or section boundaries.
- Use one worker subagent per sub-task.
- Worker context must include:
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
  - the exact sub-task block being implemented
- Main agent owns task-list updates, review, commits, integration checks, and finalization.
- No pauses between sub-tasks.
- Run finalization once after all sub-tasks complete.

## Legacy syntax

Do not accept legacy `prd-key`/`prd-id` trigger wording. Ask the user to use `plan-key` commands.
