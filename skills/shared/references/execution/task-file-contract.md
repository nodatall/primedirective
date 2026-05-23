# Task File Contract

Legacy PRD/TDD/tasks-plan artifact, plan-key, temp-file, archive-file, and refinement-entry contract.

See `skills/shared/references/contract-ownership.md` for the broader contract ownership model. This file owns legacy artifact path compatibility and refinement gates; it does not own the detailed workflow behavior of `$deliver`, `$plan-refine`, deep research, Pro analysis, review, or finalization.

## Accepted Activations

- Plan refinement: `$plan-refine` with optional `plan-key=<plan-key>`
- Task review: `$review-chain` with a specific task ID
- Ad-hoc review: `$review-chain` without a task ID
- Legacy artifact conversion: `$deliver` or `$plan-to-goal` may use a PRD/TDD/tasks-plan set as source material.

## Owner References

- `$plan-refine` behavior, challenger schema, severity gate, and stop discipline: `skills/plan-refine/SKILL.md`
- Finalization baseline and terminal gate: `skills/shared/references/execution/finalization-gate.md`
- Review topology and final review behavior: `skills/shared/references/review/review-protocol.md`
- Deep research details: `skills/shared/references/planning/deep-research.md`
- Pro analysis details: `skills/shared/references/analysis/pro-browser-analysis.md`

## Modifier Ownership

- `--deep-research` is valid where the invoking skill explicitly supports it; detailed behavior is owned by `skills/shared/references/planning/deep-research.md`.
- `--pro-analysis` is valid with `$first-principles-mode`, `$deliver`, and `$repo-sweep`; detailed behavior is owned by `skills/shared/references/analysis/pro-browser-analysis.md`.

## Plan Key Resolution

Resolve `<plan-key>` in this order for plan refinement and legacy artifact conversion:

1. If the activation includes an explicit `plan-key=<plan-key>`, use it.
2. Otherwise inspect `tasks/` for complete planning sets:
   - `tasks/prd-<plan-key>.md`
   - `tasks/tdd-<plan-key>.md`
   - `tasks/tasks-plan-<plan-key>.md`
3. If exactly one `<plan-key>` has all three files, infer that key and continue.
4. If no complete planning set exists, stop immediately and tell the user the legacy PRD/TDD/tasks-plan set is incomplete.
5. If more than one complete planning set exists, stop and ask for an explicit `plan-key=<plan-key>`.

Resolve files exactly as:

- Required PRD: `tasks/prd-<plan-key>.md`
- Required TDD: `tasks/tdd-<plan-key>.md`
- Required task list: `tasks/tasks-plan-<plan-key>.md`

## Temporary Workflow Files

- Planning research memo: `tasks/tmp/research-plan-<plan-key>.md`
- Pro analysis synthesis memo: `tasks/tmp/pro-analysis-<plan-key>.md`
- Plan refinement log: `tasks/tmp/plan-refine-<plan-key>.md`
- Finalization dirty-state baseline: `tasks/tmp/finalization-baseline-<plan-key>.status`
- Task review log: `tasks/tmp/review-task-<task-id>.md`
- Ad-hoc review log: `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`

## Archive Workflow Files

- Final archive directory: `tasks/archive/<yyyy-mm-dd>-<plan-key>/`

Use the local current date in ISO format (`YYYY-MM-DD`) when creating the archive directory.

By default, refinement and review temporary files are deleted after successful completion unless the matching preservation flag is active. Owner-specific retention rules live with the workflow owner listed above.

## Legacy Artifact Gate

Legacy PRD/TDD/tasks-plan refinement or conversion requires all three planning artifacts:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

If any required planning artifact is missing, stop immediately, do not code from the partial set, and instruct the user to either provide the full legacy artifact set or use `$deliver` for a new readable execution plan.

Before using a refined legacy set as execution source material, confirm the refinement log includes:

- the `Refinement Completion Stamp`
- `plan_refine_complete: yes`
- `ready_for_execution: yes`
- at least one fresh reviewer round recorded by the stamp
- a reviewer stop gate showing no unresolved blocker/material findings

If any of those are missing, stop before implementation. A short risk checklist or ad-hoc note is not a valid refinement handoff.

## Mode Entry Summary

### Plan refinement mode

- Requires a complete planning artifact set.
- `plan-key=<plan-key>` may be explicit or inferred through the resolution rules above.
- Edits only the PRD, TDD, tasks-plan, and refinement log.
- Uses `skills/plan-refine/SKILL.md` for challenger/reviewer behavior, severity rules, stop discipline, and cleanup.
- Successful parent handoff requires the refinement log completion stamp defined by `skills/plan-refine/SKILL.md`.

### Conversion mode

- `plan-key=<plan-key>` may be explicit or inferred through the resolution rules above.
- Treats the PRD/TDD/tasks-plan set as source material for `$deliver` or `$plan-to-goal`.
- Does not execute from `tasks/tasks-plan-<plan-key>.md` directly.
- Writes any new execution scope into `tasks/execution-plan-<plan-key>.md` or `tasks/goal-plan-<plan-key>.md`.

## Legacy Syntax

Do not depend on legacy `start planning`, `begin task`, `begin one-shot`, or `begin review` command phrases.
Do not accept legacy `prd-key`/`prd-id` wording. Use explicit skill activation plus `plan-key` or `task-id` context instead.
