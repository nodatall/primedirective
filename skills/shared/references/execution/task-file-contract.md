# Task File Contract

Canonical activation, plan-key, artifact-path, temp-file, archive-file, and execution-entry contract for planning, execution, refinement, and review skills.

See `skills/shared/references/contract-ownership.md` for the broader contract ownership model. This file owns path and entry gates; it does not own the detailed workflow behavior of `$plan-work`, `$plan-refine`, `$execute-task`, deep research, Pro analysis, review, or finalization.

## Accepted Activations

- Planning: `$plan-work`
- Plan and execute: `$plan-and-execute`
- Plan refinement: `$plan-refine` with optional `plan-key=<plan-key>`
- Standard task execution: `$execute-task` with a specific `task-id=<task-id>` and optional `plan-key=<plan-key>`
- One-shot execution: `$execute-task --one-shot` with optional `plan-key=<plan-key>`
- Task review: `$review-chain` with a specific task ID
- Ad-hoc review: `$review-chain` without a task ID

## Owner References

- `$plan-work` behavior: `skills/plan-work/SKILL.md`
- `$plan-refine` behavior, challenger schema, severity gate, and stop discipline: `skills/plan-refine/SKILL.md`
- `$execute-task` activation behavior: `skills/execute-task/SKILL.md`
- One-shot worker cadence, task-list lifecycle, temp sub-task contract shape, and cleanup phase: `skills/shared/references/execution/task-management.md`
- Finalization baseline and terminal gate: `skills/shared/references/execution/finalization-gate.md`
- Review topology and final review behavior: `skills/shared/references/review/review-protocol.md`
- Deep research details: `skills/shared/references/planning/deep-research.md`
- Pro analysis details: `skills/shared/references/analysis/pro-oracle-escalation.md`

## Execution Branch Modifier

`--stay-on-current-branch` is valid only with `$execute-task`, in standard or one-shot mode.

When present:

- Keep the current non-base branch instead of creating/switching to a new branch from `origin/main`.
- Do not create, switch, or rename branches during kickoff.
- Do not use this mode on `main`, `master`, a resolved local base branch, or detached `HEAD`; stop and ask if that is the current state.
- If the current branch already has an open PR, do not stop solely because the PR title/scope differs from the current plan. Continue locally, do not push or update that PR by default when the parent `$plan-and-execute` existing-branch exception applies, and surface the mismatch in the final handoff.
- Do not skip execution gates, review rounds, commits, final rebase, push, or PR creation, except for the `$plan-and-execute` existing non-base branch no-PR terminal behavior documented in the review protocol.

## Modifier Ownership

- `--check-harness-drift` is valid with `$execute-task` and `$plan-and-execute`; detailed behavior is owned by `skills/shared/references/harness-drift.md`.
- `--refine-plan` is valid with `$plan-and-execute`; detailed behavior is owned by `skills/plan-refine/SKILL.md`.
- `--deep-research` is valid with `$plan-work` and `$plan-and-execute`; detailed behavior is owned by `skills/shared/references/planning/deep-research.md`.
- `--pro-analysis` is valid with `$first-principles-mode`, `$plan-and-execute`, and `$repo-sweep`; detailed behavior is owned by `skills/shared/references/analysis/pro-oracle-escalation.md`.

## Plan Key Resolution

Resolve `<plan-key>` in this order for plan refinement, standard execution, and one-shot execution:

1. If the activation includes an explicit `plan-key=<plan-key>`, use it.
2. Otherwise inspect `tasks/` for complete planning sets:
   - `tasks/prd-<plan-key>.md`
   - `tasks/tdd-<plan-key>.md`
   - `tasks/tasks-plan-<plan-key>.md`
3. If exactly one `<plan-key>` has all three files, infer that key and continue.
4. If no complete planning set exists, stop immediately and tell the user planning is incomplete.
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
- Per-sub-task plan doc: `tasks/tmp/plan-task-<task-id>.md`
- Task review log: `tasks/tmp/review-task-<task-id>.md`
- One-shot final review log: `tasks/tmp/review-task-final-<plan-key>.md`
- Ad-hoc review log: `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`

## Archive Workflow Files

- Final archive directory: `tasks/archive/<yyyy-mm-dd>-<plan-key>/`

Use the local current date in ISO format (`YYYY-MM-DD`) when creating the archive directory.

By default, planning, refinement, and review temporary files are deleted after successful completion unless the matching preservation flag is active. Owner-specific retention rules live with the workflow owner listed above.

## Execution Artifact Gate

Execution requires all three planning artifacts:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

If any required planning artifact is missing, stop immediately, do not code, and instruct the user to complete planning first.

When `$plan-and-execute --refine-plan` is active, execution also requires a valid `tasks/tmp/plan-refine-<plan-key>.md` handoff from `skills/plan-refine/SKILL.md`.

Before coding, confirm the refinement log includes:

- the `Refinement Completion Stamp`
- `plan_refine_complete: yes`
- `ready_for_execution: yes`
- at least one fresh reviewer round recorded by the stamp
- a reviewer stop gate showing no unresolved blocker/material findings

If any of those are missing, stop before implementation. A short risk checklist or ad-hoc note is not a valid refinement handoff.

## Mode Entry Summary

### Standard mode

- Requires `task-id=<task-id>`.
- `plan-key=<plan-key>` may be explicit or inferred through the resolution rules above.
- Executes the requested sub-task.
- Pauses for user confirmation between sub-tasks.
- Uses the task-management, review-protocol, and finalization owners for detailed behavior.

### Plan refinement mode

- Requires a complete planning artifact set.
- `plan-key=<plan-key>` may be explicit or inferred through the resolution rules above.
- Edits only the PRD, TDD, tasks-plan, and refinement log.
- Uses `skills/plan-refine/SKILL.md` for challenger/reviewer behavior, severity rules, stop discipline, and cleanup.
- Successful parent handoff requires the refinement log completion stamp defined by `skills/plan-refine/SKILL.md`.

### One-shot mode

- Requires `--one-shot`.
- `plan-key=<plan-key>` may be explicit or inferred through the resolution rules above.
- Starts at the first unchecked sub-task and continues in file order until no unchecked sub-tasks remain.
- Uses `skills/shared/references/execution/task-management.md` for worker cadence, task contract shape, checklist updates, and cleanup.
- Uses `skills/shared/references/review/review-protocol.md` for the final full-branch review.
- Existing non-base branch mode and `--stay-on-current-branch` skip branch creation only, and the `$plan-and-execute` existing non-base branch exception skips default PR creation only. Neither path skips commits, checklist completion, final review, archiving, validation, final status checks, or baseline comparison.

## Legacy Syntax

Do not depend on legacy `start planning`, `begin task`, `begin one-shot`, or `begin review` command phrases.
Do not accept legacy `prd-key`/`prd-id` wording. Use explicit skill activation plus `plan-key` or `task-id` context instead.
