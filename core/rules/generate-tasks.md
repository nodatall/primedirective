---
description:
globs:
alwaysApply: false
---
# Rule: Generating a Task List from PRD + TDD

## Goal

Generate a detailed, implementation-ready task list by combining:

- product intent from `prd-<feature>.md`
- execution design from `tdd-<feature>.md`

The task list is complete only when both PRD and TDD coverage are explicit.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tasks-prd-<feature>.md`

## Process

1. **Receive Inputs:** Read both `tasks/prd-<feature>.md` and `tasks/tdd-<feature>.md`.
2. **Readiness Gate (Required):** Stop if either file is missing.
3. **TDD Source Gate (Required):** Confirm TDD was generated through `rules/create-tdd.md` expectations (includes `TDR-*`, command contract, failure/rollback, observability, and test strategy).
4. **Build PRD Coverage Map (Required):** Extract all `FR-*` requirements and acceptance criteria.
5. **Build TDD Coverage Map (Required):** Extract all `TDR-*` requirements and technical constraints.
6. **Conflict Gate (Required):** If PRD and TDD disagree on behavior or scope, stop and reconcile before generating tasks.
7. **Risk-First Ordering Pass (Required):** Order parent tasks to execute highest risk/impact items first.
8. **Generate Parent Tasks and Sub-Tasks in One Pass (Required):** Produce high-level parent tasks and immediately expand them into actionable sub-tasks that jointly satisfy PRD and TDD.
9. **Optional Review Checkpoint:** Only pause after parent tasks if the user explicitly asks for a review checkpoint.
10. **Sub-Task Metadata Rule (Required):** Every sub-task must include:
    - `covers_prd:` one or more `FR-*`
    - `covers_tdd:` one or more `TDR-*`
    - `output:` concrete artifact(s)
    - `verify:` exact commands/checks
    - `done_when:` observable pass condition
11. **Identify Relevant Files:** Include files implied by both PRD scope and TDD scope (including tests, runbooks, migration files, interfaces/contracts docs where applicable).
12. **Generate Final Output:** Combine parent tasks, sub-tasks, relevant files, and notes in the required format.
13. **Save Task List:** Write `tasks/tasks-prd-<feature>.md`.
14. **Run Plan Improvement Pass (Required):** After `prd-*.md`, `tdd-*.md`, and `tasks-prd-*.md` exist, run `rules/improve-plan.md` and update the plan artifacts.
15. **Completion Cleanup Gate (Required):** When the final task is checked off during execution, move `tasks-prd-<feature>.md`, `prd-<feature>.md`, and `tdd-<feature>.md` to `tasks/archive/<feature>/` before final PR handoff.
16. **Execution Trigger Gate (Required):** After planning artifacts are ready, stop and wait. Do not start implementation unless the user explicitly sends `begin task <task-id> in <prd-key>` or `begin one-shot in <prd-id>`.

## Output Format

The generated task list _must_ follow this structure:

```markdown
See `rules/task-management.md` for task workflow and review guidelines.

## Relevant Files

- `path/to/potential/file1.ts` - Brief description of why this file is relevant (e.g., Contains the main component for this feature).
- `path/to/file1.test.ts` - Unit tests for `file1.ts`.
- `path/to/another/file.tsx` - Brief description (e.g., API route handler for data submission).
- `path/to/another/file.test.tsx` - Unit tests for `another/file.tsx`.
- `lib/utils/helpers.ts` - Brief description (e.g., Utility functions needed for calculations).
- `lib/utils/helpers.test.ts` - Unit tests for `helpers.ts`.

### Notes
- Unit tests should typically be placed alongside the code files they are testing (e.g., `MyComponent.tsx` and `MyComponent.test.tsx` in the same directory).
- Use `npx jest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by the Jest configuration.

## Tasks

- [ ] 1.0 Parent Task Title
  - [ ] 1.1 [Sub-task description 1.1]
    - covers_prd: FR-1
    - covers_tdd: TDR-1
    - output: `path/to/file.ts`, `path/to/file.test.ts`
    - verify: `npm test -- path/to/file.test.ts`
    - done_when: [specific observable condition]
  - [ ] 1.2 [Sub-task description 1.2]
    - covers_prd: FR-2, FR-3
    - covers_tdd: TDR-2
    - output: [concrete artifact]
    - verify: [command/check]
    - done_when: [specific observable condition]
- [ ] 2.0 Parent Task Title
  - [ ] 2.1 [Sub-task description 2.1]
    - covers_prd: FR-4
    - covers_tdd: TDR-3
    - output: [concrete artifact]
    - verify: [command/check]
    - done_when: [specific observable condition]
- [ ] 3.0 Parent Task Title (may not require sub-tasks if purely structural or configuration)
```
