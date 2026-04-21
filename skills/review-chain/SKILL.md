---
name: review-chain
description: Run explicit branch reviews with optional task scoping. Supports ad-hoc full-branch review, task-scoped review, and `--preserve-review-artifacts`.
---

# Review Chain Skill

Run explicit branch review workflows.

## Activation

Invoke explicitly with `$review-chain`.

Request modes:

- ad-hoc review: no task ID provided, review the full branch
- task-scoped review: user provides a specific `<task-id>`

Supported modifier:

- `--preserve-review-artifacts`

## Required references

Load these files before running:

- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/review/review-calibration.md`
- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/reasoning-budget.md`

## Workflow

1. Keep current branch (do not create/rename/switch branch during review).
2. Create the correct review log file when missing, otherwise append a new review round to the existing file.
3. For task-scoped review, use PRD + TDD + tasks-plan as scope context when those artifacts exist.
4. Select the active prompt profile from `review-protocol.md`, then execute its prompts sequentially, one prompt at a time.
   - Follow `reasoning-budget.md`: explicit review runs should use the strongest appropriate reasoning tier for the selected model family or budget.
5. Treat Prompt G as required only for frontend-facing work or changes that affect rendered content, interaction flows, layout, styling, or responsive behavior. Otherwise record it as not applicable with a reason.
6. Treat Prompt H as required when the change is deploy-bound, materially affects operations, infrastructure, migrations, security posture, or runtime observability, or touches agents, private data, secrets, untrusted input, or outbound actions/tools. Otherwise record it as not applicable with a reason.
7. Record findings, fixes, and test evidence for each prompt, comparing the change against the task contract when `tasks/tmp/plan-task-<task-id>.md` exists, including acceptance checks, the recorded test-first plan, local reference patterns, and any trust-boundary notes.
8. Enforce completion gates, including unresolved TODO checks.
9. Provide summary and delete review log only after all review checks pass, unless `--preserve-review-artifacts` was supplied.

## Scope

- Task mode review: review all branch changes vs `origin/main`, including working-tree edits, against PRD + TDD + tasks-plan context.
- Ad-hoc review: same branch-wide scope, without task-artifact requirements unless explicitly requested.
