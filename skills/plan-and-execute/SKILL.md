---
name: plan-and-execute
description: Convert the current thread plan into PRD, TDD, and tasks-plan artifacts, optionally deepen or refine the plan, then execute it one-shot through final review and cleanup. Defaults to current-branch execution on feature branches and branch-plus-PR execution from main. Supports `--deep-research`, `--pro-analysis`, `--refine-plan`, `--check-harness-drift`, and `--preserve-artifacts`.
---

# Plan And Execute Skill

Turn the plan already discussed in the current thread into normal planning artifacts, then execute it end to end.

## Activation

Invoke explicitly with `$plan-and-execute`.

Supported modifiers:

- `--deep-research`
- `--pro-analysis`
- `--refine-plan`
- `--check-harness-drift`
- `--preserve-artifacts`

## Required references

Load these files before running:

- `skills/shared/references/contract-ownership.md`
- `skills/plan-work/SKILL.md`
- `skills/plan-refine/SKILL.md`
- `skills/execute-task/SKILL.md`
- `skills/shared/references/planning/deep-research.md` when `--deep-research` is present
- `skills/shared/references/analysis/pro-oracle-escalation.md` when `--pro-analysis` is present
- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/execution/task-management.md`
- `skills/shared/references/execution/finalization-gate.md`
- `skills/shared/references/reasoning-budget.md`
- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/review/review-calibration.md`
- `skills/shared/references/harness-drift.md`

## Workflow

1. Treat the current conversation above the trigger as the source plan.
   - Follow `reasoning-budget.md` for every phase and subagent: strongest appropriate reasoning for planning/refinement/deep-research/final review, strong reasoning for implementation workers, and medium/standard reasoning for mechanical chores.
2. Inspect branch state before creating artifacts.
   - If currently on a non-base branch, stay on that branch.
   - An existing open PR for that non-base branch is not a kickoff blocker, even when its title/scope differs from the new plan. Treat it as branch context: do not create, update, or push a PR by default on the existing-branch path, and mention any visible open-PR scope mismatch in the final handoff.
   - If currently on `main`, `master`, or the resolved local base branch, fetch `origin/main`, verify local main and `origin/main` do not diverge, then create a new feature branch from `origin/main`.
   - If detached `HEAD`, stop and ask.
   - If the worktree has unrelated or dangerous overlapping changes, stop and ask.
   - Capture the finalization baseline from `finalization-gate.md` after branch-state decisions and before generating PRD/TDD/tasks-plan artifacts.
3. Generate planning artifacts using `$plan-work --from-thread --direct` behavior, adding `--deep-research` when that modifier is present:
   - no Socratic question loop
   - no summary checkpoint gate
   - ask only for a true blocker where the core objective is missing, contradictory, or unsafe to infer
   - write assumptions into the artifacts instead of stopping for low-impact clarification
   - with `--deep-research`, compose the owner contract in `skills/shared/references/planning/deep-research.md` through `$plan-work`; print the required short Deep Research Summary before task generation or execution
   - with `--pro-analysis`, compose the owner contract in `skills/shared/references/analysis/pro-oracle-escalation.md`; print the required short Pro findings summary before refinement or execution
   - when both `--deep-research` and `--pro-analysis` are active, use the order and gates owned by `pro-oracle-escalation.md`
4. Require all three artifacts before execution:
   - `tasks/prd-<plan-key>.md`
   - `tasks/tdd-<plan-key>.md`
   - `tasks/tasks-plan-<plan-key>.md`
5. If `--refine-plan` is present, run the `$plan-refine plan-key=<plan-key>` improvement loop before execution:
   - use the generated plan key explicitly
   - use `$plan-refine`'s normal default round cap, internal challenger lane, fresh read-only challenger/reviewer requirements, reviewer-owned severity gate, and artifact-editing rules
   - apply fixes for reviewer blocker and material findings in the PRD, TDD, and tasks-plan before execution
   - hard-stop execution when `$plan-refine` fails because required refinement gates fail, required fresh subagents are unavailable, challenge dispositions are incomplete, unsafe blockers remain, or max rounds end with unresolved reviewer blocker/material findings
   - treat churn as recoverable only when no unresolved reviewer blocker/material findings remain and the refinement log records the safest concrete artifact fix, accepted assumption, or accepted residual risk
   - ask the user only when the remaining issue is unsafe, impossible to infer, or would change external scope in a way the artifacts cannot safely default
   - after `$plan-refine` returns, audit `tasks/tmp/plan-refine-<plan-key>.md` before any implementation edit
   - hard-stop when the refinement log is missing, lacks a `Refinement Completion Stamp`, lacks round evidence from at least one fresh reviewer subagent, or looks like a hand-written risk note rather than a real `$plan-refine` run
   - continue into execution only when the stamp says `plan_refine_complete: yes`, `ready_for_execution: yes`, `fresh_reviewer_rounds` is at least `1`, and `reviewer_stop_gate: no_unresolved_blocker_or_material`
   - print the short `Refinement Findings Summary` before execution; do not paste the full refinement log unless the user asks
   - keep the refinement log available through execution, final full-branch review, and finalization; delete it during final cleanup only after finalization succeeds unless `--preserve-artifacts` is present
6. Execute the generated or refined plan in one-shot mode:
   - if the skill started on a non-base branch, use current-branch execution and do not open a PR by default
   - if the skill created a branch from main/base, use normal branch execution and open a PR at the end
   - use compact worker packets, focused validation per sub-task, no per-sub-task review chains, and one final full-branch review
7. If `--check-harness-drift` is present, keep generated planning artifacts, sub-task contracts, review logs, and relevant temp files available until the compact harness drift report is generated. Include the actual compact report inline in the final handoff under a visible `Harness Drift Check` heading with a one-line verdict; do not satisfy this by only mentioning an archived report path. Then continue normal cleanup unless `--preserve-artifacts` is present.
8. Archive PRD, TDD, and tasks-plan under `tasks/archive/<yyyy-mm-dd>-<plan-key>/` after completion and after any requested harness drift report has been generated.
9. If `--preserve-artifacts` is present, keep temp planning, refinement, and review artifacts and list them in the final handoff.
10. Run the hard finalization gate from `finalization-gate.md` before any terminal handoff. The existing non-base branch path skips default PR creation only; it does not skip commits, checklist completion, final review, archiving, validation, final status checks, or baseline comparison.

## Branch and PR rules

- Existing non-base branch start: complete the branch locally and do not open a PR by default.
- Existing non-base branch start with an already-open PR: still complete locally on the current branch; do not stop solely because the PR title/scope differs. Do not push or mutate that PR by default. Surface the mismatch in the final handoff as follow-up context.
- Main/base branch start: create a feature branch, push it, and open a PR.
- Detached `HEAD`: stop and ask.
- Diverged local main versus `origin/main` before branch creation: stop and ask.

## Terminal condition

Do not stop after artifact generation. The run is terminal only when:

- all planned work is implemented, validated, final-reviewed, cleaned up, committed, archived, passed through the finalization gate, and handed off, or
- a real blocker prevents safe continuation and the exact required user action is stated.

## Relationship to underlying skills

This skill is a thin orchestrator. Do not duplicate planning or execution logic. Use `$plan-work --from-thread --direct` semantics for artifact generation and `$execute-task --one-shot` semantics for implementation, with this skill's branch and PR defaults taking precedence.

See `skills/shared/references/contract-ownership.md` for the contract ownership model. This skill owns only the combined workflow order and branch/PR defaults unique to `$plan-and-execute`.
