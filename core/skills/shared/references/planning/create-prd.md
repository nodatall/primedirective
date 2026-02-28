# Rule: Generating an Optional Product Requirements Document (PRD)

## Goal

Generate a product-only PRD when explicitly requested or when major complexity escalation is accepted.

PRD is optional in default planning mode.

## When to run

Run this only if one is true:

1. User explicitly asks for PRD.
2. Major complexity detection triggered and user confirmed PRD/TDD generation.

## Input

- `<plan-key>`
- Planning context from `tasks/tasks-plan-<plan-key>.md` or active planning conversation.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `prd-<plan-key>.md`

## PRD structure

1. Overview
2. Goals
3. User stories
4. Functional requirements (`FR-*`)
5. Acceptance criteria mapped to each `FR-*`
6. Non-goals
7. Constraints
8. Success metrics
9. Open questions (if any)
10. Handoff to TDD

## Rules

1. Do not start implementation while creating PRD.
2. Keep PRD product-focused (`what/why`), not deep implementation.
3. If PRD conflicts with locked planning decisions, reconcile before finalizing.
4. PRD generation is optional and must not block task-plan generation when not requested.

## Build gate reminder

Implementation starts only from:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`
