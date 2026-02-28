# Rule: Generating an Optional Technical Design Document (TDD)

## Goal

Generate a technical design doc when explicitly requested or when major complexity escalation is accepted.

TDD is optional in default planning mode.

## When to run

Run this only if one is true:

1. User explicitly asks for TDD.
2. Major complexity detection triggered and user confirmed PRD/TDD generation.

## Input

- `<plan-key>`
- `tasks/prd-<plan-key>.md` if present
- planning/task context from `tasks/tasks-plan-<plan-key>.md`

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tdd-<plan-key>.md`

## TDD structure

1. Overview and scope alignment
2. Architecture and component boundaries
3. Data model/storage changes
4. Interfaces/contracts
5. Technical requirements (`TDR-*`)
6. Command contract
7. Failure modes and rollback
8. Observability and monitoring
9. Test strategy
10. Rollout plan/runbook
11. Open technical questions

## Rules

1. Do not start implementation while creating TDD.
2. Keep TDD aligned with PRD when PRD exists.
3. Use stable `TDR-*` IDs.
4. Include executable command contract with expected outcomes.
5. TDD generation is optional and must not block task-plan generation when not requested.

## Build gate reminder

Implementation starts only from:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`
