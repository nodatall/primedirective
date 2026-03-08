---
name: review-chain
description: Use when the user requests explicit review via `begin review` (ad-hoc default) or `begin review <task-id>`, and run the full A-H review protocol with required review logs and gates.
---

# Review Chain Skill

Run explicit branch review workflows.

## Triggers

Accept:

- `begin review`
- `begin review <task-id>`

## Required references

Load these files before running:

- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/execution/task-file-contract.md`

## Workflow

1. Keep current branch (do not create/rename/switch branch during review).
2. Create the correct review log file when missing, otherwise append a new review round to the existing file.
3. For task-scoped review, use PRD + TDD + tasks-plan as scope context when those artifacts exist.
4. Execute prompts A-H sequentially, one prompt at a time.
5. Treat Prompt G as required only when the change is deploy-bound or materially affects operations, infrastructure, migrations, security posture, or runtime observability. Otherwise record it as not applicable with a reason.
6. Record findings, fixes, and test evidence for each prompt.
7. Enforce completion gates, including unresolved TODO checks.
8. Provide summary and delete review log only after all review checks pass.

## Scope

- Task mode review: review all branch changes vs `origin/main`, including working-tree edits, against PRD + TDD + tasks-plan context.
- Ad-hoc review: same branch-wide scope, without task-artifact requirements unless explicitly requested.
