# Rule: Review and Improve Task Plan

## Goal

Improve `tasks/tasks-plan-<plan-key>.md` before implementation.

If optional PRD/TDD docs exist, use them as extra context; do not require them.

## Review priorities

1. Task clarity and sequencing
2. Coverage of acceptance criteria
3. Failure-path handling in tasks and verification commands
4. Risk-first ordering and rollback awareness
5. Removal of over-engineering and ambiguity

## Rules

1. Keep edits proportional to real risk.
2. Prefer concrete, executable steps over abstract wording.
3. Ensure every sub-task has `output`, `verify`, and `done_when`.
4. If material ambiguity remains, ask one clear question.

## Output expectations

- Task plan is decision-complete enough to implement without guessing.
- Optional PRD/TDD alignment issues are called out and resolved when those docs exist.

## Execution Trigger Gate (Hard Stop)

After improvements are complete:

- Stop and wait for explicit execution trigger.
- Do not start implementation from planning review.

Accepted build triggers:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`
