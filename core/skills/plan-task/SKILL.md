---
name: plan-task
description: Use when the user starts planning with `start planning "<plan-from-llm>" [--deep-research] [--preserve-planning-artifacts]` and needs rich-plan intake, optional deep research, targeted Socratic refinement, and normalization into required `prd`, `tdd`, and `tasks-plan` artifacts.
---

# Plan Task Skill

Execute planning only. Do not write implementation code.

## Trigger

Accept only:

- `start planning "<plan-from-llm>" [--deep-research] [--preserve-planning-artifacts]`

The quoted input may be a sparse idea or a fully fleshed-out Codex/Claude plan. Treat rich source plans as the default case.

## Required references

Load these files before running:

- `skills/shared/references/planning/socratic-planning.md`
- `skills/shared/references/planning/deep-research.md`
- `skills/shared/references/planning/create-prd.md`
- `skills/shared/references/planning/create-tdd.md`
- `skills/shared/references/planning/generate-tasks.md`
- `skills/shared/references/planning/improve-plan.md`
- `skills/shared/references/execution/task-file-contract.md`

## Workflow

1. Run planning preflight from `socratic-planning.md`.
2. Intake the source material, classify it as rich source plan or sparse source prompt, and normalize it into `Goal`, `Context`, `Constraints`, and `Done when`.
3. Run the Socratic refinement loop:
   - one question per turn
   - plain language
   - gap-check, contradiction-check, and assumption-check only
   - for non-trivial rich plans touching infrastructure, deployment, scheduling, source-of-truth, or operations, ask at least one targeted challenge question before document generation
   - close gaps in `Goal`, `Context`, `Constraints`, and `Done when` before document generation
   - produce a final plain-language summary that a 12-year-old could follow
4. If `--deep-research` is present, run `deep-research.md` after decisions are locked and before artifact generation.
5. Generate `tasks/prd-<plan-key>.md` using `create-prd.md`.
6. Generate `tasks/tdd-<plan-key>.md` using `create-tdd.md`.
7. Generate `tasks/tasks-plan-<plan-key>.md` using `generate-tasks.md`.
8. Run `improve-plan.md` once against the source plan plus all generated artifacts, plus the research memo when preserved.
9. Stop and wait for implementation trigger.

## Planning rules

- Always produce all three planning artifacts.
- Do not use lean-mode branching. Simpler work produces shorter docs naturally.
- Do not leave `Open questions` or `Open technical questions` in final artifacts.
- Preserve substantive source-plan sections; normalize them without dropping content.
- With `--deep-research`, research defaults to `Tech + Delivery`: technical design, migration/rollout/rollback, security/ops, and verification strategy.
- With `--deep-research`, do not begin PRD/TDD/tasks drafting until the research memo and completion checks from `deep-research.md` are complete.
- `--deep-research` should influence TDD and tasks-plan first; update PRD only when product constraints or defaults materially change.
- With `--preserve-planning-artifacts`, keep `tasks/tmp/research-plan-<plan-key>.md` and mention it in the final planning summary.
- Restore traceability from tasks to `FR-*` and `TDR-*` IDs.

## UI behavior

Prefer structured dialog questions when client supports them. Fallback to plain-text one-question turns when not supported.

## Hard gate

After planning is complete, wait for one of these implementation triggers:

- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]`

Do not start coding from planning flow.
