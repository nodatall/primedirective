---
name: plan-and-execute
description: Convert the current thread plan into PRD, TDD, and tasks-plan artifacts, optionally deepen or refine the plan, then execute it one-shot through final review and cleanup. Defaults to current-branch execution on feature branches and branch-plus-PR execution from main. Supports `--deep-research`, `--refine-plan`, `--check-harness-drift`, and `--preserve-artifacts`.
---

# Plan And Execute Skill

Turn the plan already discussed in the current thread into normal planning artifacts, then execute it end to end.

## Activation

Invoke explicitly with `$plan-and-execute`.

Supported modifiers:

- `--deep-research`
- `--refine-plan`
- `--check-harness-drift`
- `--preserve-artifacts`

## Required references

Load these files before running:

- `skills/plan-work/SKILL.md`
- `skills/plan-refine/SKILL.md`
- `skills/execute-task/SKILL.md`
- `skills/shared/references/planning/deep-research.md` when `--deep-research` is present
- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/execution/task-management.md`
- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/review/review-calibration.md`
- `skills/shared/references/harness-drift.md`

## Workflow

1. Treat the current conversation above the trigger as the source plan.
2. Inspect branch state before creating artifacts.
   - If currently on a non-base branch, stay on that branch.
   - If currently on `main`, `master`, or the resolved local base branch, fetch `origin/main`, verify local main and `origin/main` do not diverge, then create a new feature branch from `origin/main`.
   - If detached `HEAD`, stop and ask.
   - If the worktree has unrelated or dangerous overlapping changes, stop and ask.
3. Generate planning artifacts using `$plan-work --from-thread --direct` behavior, adding `--deep-research` when that modifier is present:
   - no Socratic question loop
   - no summary checkpoint gate
   - ask only for a true blocker where the core objective is missing, contradictory, or unsafe to infer
   - write assumptions into the artifacts instead of stopping for low-impact clarification
   - with `--deep-research`, run the normal `plan-work` research pass after initial PRD/TDD drafting and before tasks-plan generation, then adopt findings into PRD, TDD, and task sequencing before execution
   - with `--deep-research`, do not add a user-facing revised-summary checkpoint or any extra approval pause before execution; keep going unless live web research is unavailable or the research exposes a true blocker that is unsafe, contradictory, or impossible to default
4. Require all three artifacts before execution:
   - `tasks/prd-<plan-key>.md`
   - `tasks/tdd-<plan-key>.md`
   - `tasks/tasks-plan-<plan-key>.md`
5. If `--refine-plan` is present, run the `$plan-refine plan-key=<plan-key>` improvement loop before execution:
   - use the generated plan key explicitly
   - use `$plan-refine`'s normal default round cap, fresh reviewer rounds, and artifact-editing rules
   - keep the refinement log when `--preserve-artifacts` is present; otherwise use normal `$plan-refine` cleanup behavior
   - apply fixes for blocker and material findings in the PRD, TDD, and tasks-plan before execution
   - if the loop reaches max rounds or churn, choose the safest concrete artifact fix available, record the accepted assumption or residual risk, and continue
   - ask the user only when the remaining issue is unsafe, impossible to infer, or would change external scope in a way the artifacts cannot safely default
   - continue into execution with the refined artifacts
6. Execute the generated or refined plan in one-shot mode:
   - if the skill started on a non-base branch, use current-branch execution and do not open a PR by default
   - if the skill created a branch from main/base, use normal branch execution and open a PR at the end
   - use compact worker packets, focused validation per sub-task, no per-sub-task review chains, and one final full-branch review
7. If `--check-harness-drift` is present, keep generated planning artifacts, sub-task contracts, review logs, and relevant temp files available until the compact harness drift report is generated. Include the actual compact report inline in the final handoff under a visible `Harness Drift Check` heading with a one-line verdict; do not satisfy this by only mentioning an archived report path. Then continue normal cleanup unless `--preserve-artifacts` is present.
8. Archive PRD, TDD, and tasks-plan under `tasks/archive/<yyyy-mm-dd>-<plan-key>/` after completion and after any requested harness drift report has been generated.
9. If `--preserve-artifacts` is present, keep temp planning, refinement, and review artifacts and list them in the final handoff.

## Branch and PR rules

- Existing non-base branch start: complete the branch locally and do not open a PR by default.
- Main/base branch start: create a feature branch, push it, and open a PR.
- Detached `HEAD`: stop and ask.
- Diverged local main versus `origin/main` before branch creation: stop and ask.

## Terminal condition

Do not stop after artifact generation. The run is terminal only when:

- all planned work is implemented, validated, final-reviewed, cleaned up, and handed off, or
- a real blocker prevents safe continuation and the exact required user action is stated.

## Relationship to underlying skills

This skill is a thin orchestrator. Do not duplicate planning or execution logic. Use `$plan-work --from-thread --direct` semantics for artifact generation and `$execute-task --one-shot` semantics for implementation, with this skill's branch and PR defaults taking precedence.
