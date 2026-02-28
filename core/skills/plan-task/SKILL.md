---
name: plan-task
description: Use when the user starts planning with `start planning "<unformed-plan>"` and needs conversational task planning that produces `tasks/tasks-plan-<plan-key>.md`, with optional PRD/TDD escalation only for explicit request or confirmed major complexity.
---

# Plan Task Skill

Execute planning only. Do not write implementation code.

## Trigger

Accept only:

- `start planning "<unformed-plan>"`

## Required references

Load these files before running:

- `skills/shared/references/planning/socratic-planning.md`
- `skills/shared/references/planning/generate-tasks.md`
- `skills/shared/references/planning/create-prd.md`
- `skills/shared/references/planning/create-tdd.md`
- `skills/shared/references/planning/improve-plan.md`
- `skills/shared/references/execution/task-file-contract.md`

## Workflow

1. Run planning preflight from `socratic-planning.md`.
2. Run conversational Socratic loop (one question per turn): intent -> example -> acceptance.
3. Run major-complexity detection from `socratic-planning.md`.
4. If complexity is high, ask one confirmation question before generating optional PRD/TDD.
5. Generate `tasks/tasks-plan-<plan-key>.md` using `generate-tasks.md`.
6. If PRD/TDD exist, optionally run `improve-plan.md` once.
7. Stop and wait for implementation trigger.

## UI behavior

Prefer structured dialog questions when client supports them. Fallback to plain-text one-question turns when not supported.

## Hard gate

After planning is complete, wait for one of these implementation triggers:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`

Do not start coding from planning flow.
