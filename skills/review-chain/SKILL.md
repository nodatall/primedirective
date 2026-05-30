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
- `skills/shared/references/review/finding-disposition.md`
- `skills/shared/references/architecture/architecture-guidance.md` when `docs/ARCHITECTURE.md` exists or the review touches boundary-affecting changes
- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/reasoning-budget.md`

## Workflow

1. Keep current branch (do not create/rename/switch branch during review).
2. Create the correct review log file when missing, otherwise append a new review round to the existing file.
3. For task-scoped review, use PRD + TDD + tasks-plan as scope context when those artifacts exist.
4. Select the active prompt profile from `review-protocol.md`, then execute its prompts sequentially, one prompt at a time.
   - Follow `reasoning-budget.md`: explicit review runs should use the strongest appropriate reasoning tier for the selected model family or budget.
   - Include the bounded adversarial-prior checks from `review-protocol.md` during Prompt A, and do not force findings when the hostile prior is falsified by evidence.
5. When `docs/ARCHITECTURE.md` exists or the diff is boundary-affecting, compose `architecture-guidance.md` and compare the change against the architecture doc. Flag stale docs, missing modules, forbidden dependency edges, undocumented entrypoints, expired deviations, and shared-code drift.
6. Treat Prompt G as required only for frontend-facing work or changes that affect rendered content, interaction flows, layout, styling, or responsive behavior. Otherwise record it as not applicable with a reason.
7. Treat Prompt H as required when the change is deploy-bound, materially affects operations, infrastructure, migrations, security posture, or runtime observability, or touches agents, private data, secrets, untrusted input, or outbound actions/tools. Otherwise record it as not applicable with a reason.
8. Record findings, disposition, and test evidence for each prompt, comparing the change against the task contract when `tasks/tmp/plan-task-<task-id>.md` exists, including acceptance checks, the recorded test-first plan, `test_first_evidence`, local reference patterns, and any trust-boundary notes.
9. Enforce completion gates, including unresolved TODO checks.
10. Provide summary and delete review log only after all review checks pass, unless `--preserve-review-artifacts` was supplied.

Default behavior is report-first. Do not patch files from standalone `$review-chain` unless the user explicitly asked for fixes in the same request. If fixes are requested, the main agent applies them after the review findings are recorded; the review subagent remains detect-only.

## Scope

- Task mode review: review all branch changes vs `origin/main`, including working-tree edits, against PRD + TDD + tasks-plan context.
- Ad-hoc review: same branch-wide scope, without task-artifact requirements unless explicitly requested.

## Output

Follow `review-protocol.md` for review logs, prompt completion, and cleanup.

Final review output must lead with findings. For each material finding, use the shared finding shape from `finding-disposition.md`: severity, execution gate, disposition, confidence, scope, evidence, impact, fix path, and owner. If there are no findings, say that clearly and list any residual test, visual, deployment, or review-scope gaps.

After findings, keep the summary brief: prompts run, Prompt G/H applicability, fixes made during review, validation commands run, remaining accepted risks or blockers, and whether review artifacts were deleted or preserved.
