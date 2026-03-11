---
name: review-chain
description: Use when the user requests explicit review via `begin review [--preserve-review-artifacts]` (ad-hoc default) or `begin review <task-id> [--preserve-review-artifacts]`, and run the full A-I review protocol with required review logs and gates.
---

# Review Chain Skill

Run explicit branch review workflows.

## Triggers

Accept:

- `begin review [--preserve-review-artifacts]`
- `begin review <task-id> [--preserve-review-artifacts]`

## Required references

Load these files before running:

- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/execution/task-file-contract.md`

## Workflow

1. Keep current branch (do not create/rename/switch branch during review).
2. Create the correct review log file when missing, otherwise append a new review round to the existing file.
3. For task-scoped review, use PRD + TDD + tasks-plan as scope context when those artifacts exist.
4. Execute prompts A-I sequentially, one prompt at a time.
5. Treat Prompt G as required only for frontend-facing work or changes that affect rendered content, interaction flows, layout, styling, or responsive behavior. Otherwise record it as not applicable with a reason.
6. Treat Prompt H as required only when the change is deploy-bound or materially affects operations, infrastructure, migrations, security posture, or runtime observability. Otherwise record it as not applicable with a reason.
7. Record findings, fixes, and test evidence for each prompt.
8. Enforce completion gates, including unresolved TODO checks.
9. Provide summary and delete review log only after all review checks pass, unless `--preserve-review-artifacts` was supplied.

## Scope

- Task mode review: review all branch changes vs `origin/main`, including working-tree edits, against PRD + TDD + tasks-plan context.
- Ad-hoc review: same branch-wide scope, without task-artifact requirements unless explicitly requested.
