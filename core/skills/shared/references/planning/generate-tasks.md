# Rule: Generating a Task Plan

## Goal

Generate one implementation-ready task plan file:

- `tasks/tasks-plan-<plan-key>.md`

Do not require PRD/TDD by default.

## Inputs

Required:

- Planning conversation outcomes (intent, example, acceptance)
- Locked decisions and assumptions

Optional (if available):

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tasks-plan-<plan-key>.md`

## Required structure

```markdown
See `skills/shared/references/execution/task-management.md` for task workflow and review guidelines.

## Goal
- [1-3 lines]

## Acceptance Criteria
- [3-7 concrete bullets]

## Decisions
- [final choices that steer implementation]

## Assumptions
- [unresolved items with chosen defaults]

## Out of Scope
- [optional]

## Relevant Files
- `path/to/file.ts` - Why this file matters.
- `path/to/file.test.ts` - Tests for the file.

## Tasks
- [ ] 1.0 Parent task title
  - [ ] 1.1 Sub-task description
    - output: `path/to/file.ts`
    - verify: `npm test -- path/to/file.test.ts`
    - done_when: [observable pass condition]
```

## Process

1. Confirm `<plan-key>` is known.
2. Synthesize core behavior from planning answers.
3. Incorporate optional PRD/TDD context when present.
4. Order work risk-first.
5. Generate parent tasks and actionable sub-tasks.
6. Ensure each sub-task has `output`, `verify`, and `done_when`.
7. Save `tasks/tasks-plan-<plan-key>.md`.
8. Stop and wait for build trigger.

## Hard stop

Do not start coding after generating the task plan. Build starts only from:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`
