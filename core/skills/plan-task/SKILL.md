---
name: plan-task
description: Use when the user starts planning with `start planning "<unformed-plan>"` and needs rich-plan intake, targeted Socratic refinement, and normalization into required `prd`, `tdd`, and `tasks-plan` artifacts.
---

# Plan Task Skill

Execute planning only. Do not write implementation code.

## Trigger

Accept only:

- `start planning "<unformed-plan>"`

The quoted input may be a sparse idea or a fully fleshed-out Codex/Claude plan. Treat rich source plans as the default case.

## Required references

Load these files before running:

- `skills/shared/references/planning/socratic-planning.md`
- `skills/shared/references/planning/create-prd.md`
- `skills/shared/references/planning/create-tdd.md`
- `skills/shared/references/planning/generate-tasks.md`
- `skills/shared/references/planning/improve-plan.md`
- `skills/shared/references/execution/task-file-contract.md`

## Workflow

1. Run planning preflight from `socratic-planning.md`.
2. Intake the source material and classify it as rich source plan or sparse source prompt.
3. Run the Socratic refinement loop:
   - one question per turn
   - plain language
   - gap-check, contradiction-check, and assumption-check only
   - produce a final plain-language summary that a 12-year-old could follow
4. Generate `tasks/prd-<plan-key>.md` using `create-prd.md`.
5. Generate `tasks/tdd-<plan-key>.md` using `create-tdd.md`.
6. Generate `tasks/tasks-plan-<plan-key>.md` using `generate-tasks.md`.
7. Run `improve-plan.md` once against the source plan plus all generated artifacts.
8. Stop and wait for implementation trigger.

## Planning rules

- Always produce all three planning artifacts.
- Do not use lean-mode branching. Simpler work produces shorter docs naturally.
- Do not leave `Open questions` or `Open technical questions` in final artifacts.
- Preserve substantive source-plan sections; normalize them without dropping content.
- Restore traceability from tasks to `FR-*` and `TDR-*` IDs.

## UI behavior

Prefer structured dialog questions when client supports them. Fallback to plain-text one-question turns when not supported.

## Hard gate

After planning is complete, wait for one of these implementation triggers:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`

Do not start coding from planning flow.
