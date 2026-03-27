# Rule: Generating the Task Plan

## Goal

Generate one implementation-ready task plan file from finalized PRD and TDD:

- `tasks/tasks-plan-<plan-key>.md`

Tasks-plan is always required, but it is no longer the sole planning artifact.

## Inputs

Required:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- locked planning decisions and defaults
- deep-research findings when `--deep-research` is active, already applied to finalized PRD/TDD

Tasks must be generated from finalized PRD and TDD, not directly from the raw source plan.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tasks-plan-<plan-key>.md`

## Required structure

```markdown
See `skills/shared/references/execution/task-management.md` for execution workflow and review guidelines.

# <Plan Title>

## Scope Summary
- Short summary of what this plan covers.
- Call out the highest-risk implementation concerns.

## Relevant Files
- `path/to/file.ts` - Why this file matters.
- `path/to/file.test.ts` - Tests for the file.

## Task Ordering Notes
- Sequencing assumptions and dependency notes.
- Any required migration/backfill/rollout order.

## Tasks
- [ ] 1.0 Parent task title
  - covers_prd: `FR-001`, `FR-002`
  - covers_tdd: `TDR-001`
  - [ ] 1.1 Sub-task description
    - covers_prd: `FR-001`
    - covers_tdd: `TDR-001`
    - output: `path/to/file.ts`
    - verify: `npm test -- path/to/file.test.ts`
    - done_when: Observable pass condition
```

## Generation rules

1. Confirm `<plan-key>` is known.
2. Confirm PRD and TDD are both finalized first. If `--deep-research` is active, confirm they were revised after the research pass before continuing.
3. Derive task sequencing from finalized PRD and TDD obligations.
4. Order work risk-first and dependency-aware.
5. Preserve meaningful implementation detail from the source plan by expressing it as actionable tasks.
6. Ensure every meaningful `FR-*` and `TDR-*` is covered by at least one task or sub-task.
7. Ensure every sub-task has `covers_prd`, `covers_tdd`, `output`, `verify`, and `done_when`.
8. Make every sub-task small enough that implementation and review can agree on a concrete contract before coding starts.
9. For frontend-facing sub-tasks, make `verify` and `done_when` describe the actual screens, states, interactions, and visible quality bar to be checked in the browser. Avoid generic wording such as `UI looks good`.
10. Sequence frontend work so shared layout/theming primitives land before high-polish states, unless the risk profile clearly favors a spike first.
11. Save `tasks/tasks-plan-<plan-key>.md`.
12. Stop and wait for build trigger.
13. If `--deep-research` is active, fold research-discovered rollout, migration, verification, and cleanup work into the task ordering and sub-task details.

## Coverage rule

No requirement from PRD or TDD may disappear during task generation.

If something is intentionally omitted from tasks, it must already be explicitly marked as out of scope, deferred, or non-goal in PRD/TDD before task generation.

## Hard stop

Do not start coding after generating the task plan. Build starts only from:

- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]`
