---
name: plan-and-execute
description: Convert the current thread plan into PRD, TDD, and tasks-plan artifacts, optionally prepare, deepen, or refine the plan, then execute it one-shot through final review and cleanup. Defaults to current-branch execution on feature branches and branch-plus-PR execution from main. Supports `--prepare-plan`, `--deep-research`, `--pro-analysis`, `--refine-plan`, `--check-harness-drift`, and `--preserve-artifacts`.
---

# Plan And Execute Skill

Turn the plan already discussed in the current thread into normal planning artifacts, then execute it end to end.

## Activation

Invoke explicitly with `$plan-and-execute`.

Supported modifiers:

- `--deep-research`
- `--pro-analysis`
- `--prepare-plan`
- `--refine-plan`
- `--check-harness-drift`
- `--preserve-artifacts`

## Required references

Load these files before running:

- `skills/shared/references/contract-ownership.md`
- `skills/plan-work/SKILL.md`
- `skills/plan-refine/SKILL.md`
- `skills/shared/references/architecture/architecture-guidance.md` when planning or execution is boundary-affecting or `docs/ARCHITECTURE.md` exists
- `skills/plan-to-goal/SKILL.md` when generated or refined artifacts are goal-shaped
- `skills/execute-task/SKILL.md`
- `skills/shared/references/planning/deep-research.md` when `--deep-research` is present
- `skills/shared/references/analysis/pro-browser-analysis.md` when `--pro-analysis` is present
- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/execution/task-management.md`
- `skills/shared/references/execution/finalization-gate.md`
- `skills/shared/references/reasoning-budget.md`
- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/review/review-calibration.md`
- `skills/shared/references/harness-drift.md`
- `skills/shared/references/plain-language.md` when `--prepare-plan` is present

## Workflow

1. Treat the current conversation above the trigger as the source plan.
   - Follow `reasoning-budget.md` for every phase and subagent: strongest appropriate reasoning for planning/refinement/deep-research/final review, strong reasoning for implementation workers, and medium/standard reasoning for mechanical chores.
2. If `--prepare-plan` is present, run a short collaborative plan-prep pass before branch state, artifact generation, or execution mechanics:
   - use plain language from `skills/shared/references/plain-language.md` for the whole prep pass: the first restatement, every question, every recommendation, and the prepared-plan summary
   - first, restate the full current plan from the thread in plain English before asking any questions
   - include goal, scope, major work slices, order, hard constraints, validation evidence, and any assumptions that would matter during execution
   - ask the user whether the restated plan is right enough to continue
   - if the user confirms, treat that restatement plus the earlier thread as the locked source plan and continue with the normal workflow
   - if the user says the restatement is wrong, thin, or missing something, stay focused on making the plan look right, not on PR, branch, commit, reviewer, or finalization details
   - ask at most five user-facing questions total after the first restatement, one per turn
   - ask only high-value, non-obvious questions whose answer would change scope, sequencing, risk, verification, rollout, data contracts, or ownership
   - do not ask questions the repo can answer through quick inspection
   - include a recommended default with each question
   - after the last useful question, or sooner when the plan is clear, give a concise plain-English prepared-plan summary and ask the user to confirm before continuing
   - after confirmation, treat that summary plus the earlier thread as the locked source plan and continue with the normal workflow
3. Inspect branch state before creating artifacts.
   - If currently on a non-base branch, stay on that branch.
   - An existing open PR for that non-base branch is not a kickoff blocker, even when its title/scope differs from the new plan. Treat it as branch context: do not create, update, or push a PR by default on the existing-branch path, and mention any visible open-PR scope mismatch in the final handoff.
   - If currently on `main`, `master`, or the resolved local base branch, fetch `origin/main`, verify local main and `origin/main` do not diverge, then create a new feature branch from `origin/main`.
   - If detached `HEAD`, stop and ask.
   - If the worktree has unrelated or dangerous overlapping changes, stop and ask.
   - Capture the finalization baseline from `finalization-gate.md` after branch-state decisions and before generating PRD/TDD/tasks-plan artifacts.
4. Generate planning artifacts using `$plan-work --from-thread --direct` behavior, adding `--deep-research` when that modifier is present:
   - no Socratic question loop
   - no summary checkpoint gate
   - ask only for a true blocker where the core objective is missing, contradictory, or unsafe to infer
   - write assumptions into the artifacts instead of stopping for low-impact clarification
   - before drafting PRD/TDD, identify the latest user-approved source plan in the thread; if it conflicts with earlier assistant summaries, the latest user-approved plan wins
   - when the source plan says "full plan", "everything", "all at once", "not a tiny slice", "whole roadmap", or equivalent, treat each concrete source-plan item as in scope and as an acceptance obligation, not as optional roadmap context
   - if the run cannot safely execute every concrete source-plan item, stop before task generation and ask for scope reduction or `--prepare-plan`; do not silently convert the work into a first slice, foundation pass, interface, stub, diagnostic, or follow-up list
   - with `--deep-research`, compose the owner contract in `skills/shared/references/planning/deep-research.md` through `$plan-work`; print the required short Deep Research Summary before task generation or execution
   - with `--pro-analysis`, compose the owner contract in `skills/shared/references/analysis/pro-browser-analysis.md`; print the required short Pro findings summary before refinement or execution
   - when both `--deep-research` and `--pro-analysis` are active, use the order and gates owned by `pro-browser-analysis.md`
	   - Pro analysis, deep research, and refinement may add safety gates or sequencing, but they must not narrow an explicit full-plan source into partial completion unless that narrowing is recorded as a blocker needing user decision before execution
	   - before boundary-affecting planning or execution, compose `architecture-guidance.md`; if `docs/ARCHITECTURE.md` exists, read it and incorporate its boundary contract, and if the repo is non-trivial but the doc is missing, create or update it with `$create-architecture` unless the source plan is only a small local fix inside one existing boundary
5. Require all three artifacts before execution:
   - `tasks/prd-<plan-key>.md`
   - `tasks/tdd-<plan-key>.md`
   - `tasks/tasks-plan-<plan-key>.md`
6. If `--refine-plan` is present, run the `$plan-refine plan-key=<plan-key>` improvement loop before execution:
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
7. Before one-shot execution, check whether the generated or refined artifacts are goal-shaped:
   - Load `skills/plan-to-goal/SKILL.md` only when the plan cannot honestly name the remaining implementation steps until after the next validation result, the plan is an inspect -> patch -> validate loop, or the work should optimize against a measurable baseline, benchmark, comparator, ceiling, or target.
   - Do not convert the plan into a goal when the decisive evidence depends on a slow, paid, approval-gated, nightly, or externally scheduled run that the agent cannot repeat several times before the next operator decision. Keep that as a normal tasks plan with cheap checks, smoke coverage, and decision-run readiness.
   - If the plan is goal-shaped, use `$plan-to-goal plan-key=<plan-key>` semantics to write `tasks/goal-plan-<plan-key>.md`, then stop for user review with the goal-plan path.
   - Do not continue into `$execute-task --one-shot` after creating a goal plan.
   - Do not add this preflight to `$execute-task`; `$plan-and-execute` owns this combined planning-to-execution fork.
8. Execute the generated or refined plan in one-shot mode:
   - if the skill started on a non-base branch, use current-branch execution and do not open a PR by default
   - if the skill created a branch from main/base, use normal branch execution and open a PR at the end
   - use compact worker packets, focused validation per sub-task, no per-sub-task review chains, and one final full-branch review
	   - when implementation and focused validation are complete, continue directly into final broad validation, final full-branch review, review remediation, cleanup/archive, commit, and the finalization gate; do not hand off a validated-but-unreviewed or dirty branch as incomplete workflow state
	   - when intentionally changing a boundary, update `docs/ARCHITECTURE.md` in the same run
   - after the last implementation validation passes, treat any user-facing implementation recap as blocked until the post-implementation closeout evidence exists: final full-branch review log complete, all in-scope review findings dispositioned and fixed or explicitly accepted, task checklist complete, PRD/TDD/tasks-plan archived unless preservation is requested, new run-created changes committed, final status compared against the baseline, and finalization gate passed
   - if the next message you are about to send would list "What changed" or "Validation" before that evidence exists, do not send it; run the missing closeout step instead
9. If `--check-harness-drift` is present, keep generated planning artifacts, sub-task contracts, review logs, and relevant temp files available until the compact harness drift report is generated. Include the actual compact report inline in the final handoff under a visible `Harness Drift Check` heading with a one-line verdict; do not satisfy this by only mentioning an archived report path. Then continue normal cleanup unless `--preserve-artifacts` is present.
10. Archive PRD, TDD, and tasks-plan under `tasks/archive/<yyyy-mm-dd>-<plan-key>/` after completion and after any requested harness drift report has been generated.
11. If `--preserve-artifacts` is present, keep temp planning, refinement, and review artifacts and list them in the final handoff.
12. Run the hard finalization gate from `finalization-gate.md` before any terminal handoff. The existing non-base branch path skips default PR creation only; it does not skip commits, checklist completion, final review, archiving, validation, final status checks, or baseline comparison.
13. Treat any final response shaped like "implemented X, validation passed, changed files are Y" before final review, review remediation, archive, commit, baseline comparison, and finalization as an invalid terminal handoff. Continue into those closeout steps instead unless a real blocker prevents them.

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

The terminal handoff must name the final review result, final commit or explicit existing-branch commit status, archive/preservation result, final validation result, and working-tree status. A handoff that only names implementation changes and tests is incomplete.

## Relationship to underlying skills

This skill is a thin orchestrator. Do not duplicate planning, goal drafting, or execution logic. Use `$plan-work --from-thread --direct` semantics for artifact generation, `$plan-to-goal` semantics for the goal-shaped fork before execution, and `$execute-task --one-shot` semantics for implementation, with this skill's branch and PR defaults taking precedence.

See `skills/shared/references/contract-ownership.md` for the contract ownership model. This skill owns only the combined workflow order and branch/PR defaults unique to `$plan-and-execute`.
