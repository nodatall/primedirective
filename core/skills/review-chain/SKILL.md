---
name: review-chain
description: Use when the user requests explicit review via `begin review` (ad-hoc default) or `begin review <task-id>`, and run the full A-E review protocol with required review logs and gates.
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
3. Execute prompts A-E sequentially, one prompt at a time.
4. Record findings, fixes, and test evidence for each prompt.
5. Enforce completion gates, including unresolved TODO checks.
6. Provide summary and delete review log only after all review checks pass.

## Scope

- Task mode review: review all branch changes vs `origin/main`, including working-tree edits.
- Ad-hoc review: same branch-wide scope, without PRD/TDD checklist requirements unless explicitly requested.
