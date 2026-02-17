---
description:
globs:
alwaysApply: false
---
# Rule: Generating a Task List from a PRD

## Goal

To guide an AI assistant in creating a detailed, step-by-step task list in Markdown format based on an existing Product Requirements Document (PRD). The task list should guide a developer through implementation.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tasks-[prd-file-name].md` (e.g., `tasks-prd-user-profile-editing.md`)

## Process

1.  **Receive PRD Reference:** The user points the AI to a specific PRD file
2.  **Analyze PRD:** The AI reads and analyzes the functional requirements, user stories, and other sections of the specified PRD.
3.  **Build Requirement Coverage Map (Required):** Extract all functional requirement IDs (`FR-*`) and acceptance criteria into a mapping table. Every generated sub-task must point to one or more requirement IDs.
4.  **Risk-First Ordering Pass (Required):** Prioritize parent tasks so high-risk / high-uncertainty / high-impact work is scheduled earlier.
5.  **Phase 1: Generate Parent Tasks:** Based on the PRD analysis, create the file and generate the main, high-level tasks required to implement the feature. Use your judgement on how many high-level tasks to use. It's likely to be about 5. Present these tasks to the user in the specified format (without sub-tasks yet). Inform the user: "I have generated the high-level tasks based on the PRD. Ready to generate the sub-tasks? Respond with 'Go' to proceed."
6.  **Wait for Confirmation:** Pause and wait for the user to respond with "Go".
7.  **Phase 2: Generate Sub-Tasks:** Once the user confirms, break down each parent task into smaller, actionable sub-tasks necessary to complete the parent task. Ensure sub-tasks logically follow from the parent task and cover the implementation details implied by the PRD.
8.  **Sub-Task Specificity Rule (Required):** Every sub-task must include:
    - `covers:` one or more requirement IDs (`FR-*`)
    - `output:` concrete artifact(s) to produce (files, endpoint, migration, test, doc)
    - `verify:` command(s) or checks used to validate behavior
    - `done_when:` clear completion condition
9.  **Identify Relevant Files:** Based on the tasks and PRD, identify potential files that will need to be created or modified. List these under the `Relevant Files` section, including corresponding test files if applicable.
10. **Generate Final Output:** Combine the parent tasks, sub-tasks, relevant files, and notes into the final Markdown structure.
11. **Save Task List:** Save the generated document in the `/tasks/` directory with the filename `tasks-[prd-file-name].md`, where `[prd-file-name]` matches the base name of the input PRD file (e.g., if the input was `prd-user-profile-editing.md`, the output is `tasks-prd-user-profile-editing.md`).
12. **Run Plan Improvement Pass (Required):** After both `prd-*.md` and `tasks-prd-*.md` exist, run the review/improvement workflow in `rules/improve-plan.md` and update the PRD/task files accordingly.

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
    - covers: FR-1
    - output: `path/to/file.ts`, `path/to/file.test.ts`
    - verify: `npm test -- path/to/file.test.ts`
    - done_when: [specific observable condition]
  - [ ] 1.2 [Sub-task description 1.2]
    - covers: FR-2, FR-3
    - output: [concrete artifact]
    - verify: [command/check]
    - done_when: [specific observable condition]
- [ ] 2.0 Parent Task Title
  - [ ] 2.1 [Sub-task description 2.1]
    - covers: FR-4
    - output: [concrete artifact]
    - verify: [command/check]
    - done_when: [specific observable condition]
- [ ] 3.0 Parent Task Title (may not require sub-tasks if purely structural or configuration)
```
