---
name: plan-refine
description: Run a bounded iterative refinement loop over existing Prime Directive planning artifacts (`prd`, `tdd`, and `tasks-plan`) using one fresh reviewer subagent per critique round. Use when the user asks to improve, pressure-test, critique, iterate, loop on, or first-principles-review a plan before execution; supports `plan-key=KEY`, `--max-rounds=N`, and `--preserve-refine-artifacts`.
---

# Plan Refine Skill

Run planning refinement only. Do not write implementation code.

## Activation

Invoke explicitly with `$plan-refine`.

Activation examples:

- `$plan-refine`
- `$plan-refine --max-rounds=8`
- `$plan-refine --preserve-refine-artifacts plan-key=<plan-key>`

Required planning artifact set:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

Supported modifiers:

- `plan-key=<plan-key>` when more than one complete planning set exists
- `--max-rounds=<n>`
- `--preserve-refine-artifacts`

Defaults:

- `--max-rounds=8`

Round limit:

- `8` is the hard maximum round count.
- If the user requests more than 8 rounds, cap the run at 8 rounds and mention the cap in the final response.

Fixed stop rule:

- Stop when a fresh reviewer round finds no `blocker` or `material` issues.

## Required References

Load these files before running:

- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/planning/improve-plan.md`
- `skills/first-principles-mode/SKILL.md`
- `skills/first-principles-mode/references/analysis-rubric.md`

## Workflow

1. Resolve the planning artifact set from `plan-key=<plan-key>` or the inference rules in `task-file-contract.md`.
   - If exactly one complete PRD/TDD/tasks-plan set exists under `tasks/`, bare `$plan-refine` must infer that `plan-key` and continue.
   - If multiple complete planning sets exist, stop and ask for `plan-key=<plan-key>`.
2. Stop immediately if any required artifact is missing. Tell the user to complete `$plan-work` first.
3. Stay on the current branch. Do not create, switch, rename, commit, or push branches.
4. Inspect `git status --short`.
   - Continue when the working tree is clean.
   - Continue when only the current plan artifacts are dirty.
   - If unrelated dirty files exist, report that they are unrelated and ignore them unless they prevent reading or editing the planning artifacts.
5. Create a temporary refinement log at `tasks/tmp/plan-refine-<plan-key>.md`.
6. Treat invocation of `$plan-refine` as an explicit request to delegate every critique round to a fresh reviewer subagent.
   - Spawn one fresh read-only reviewer subagent per round.
   - The reviewer subagent must not edit files.
   - The main agent owns orchestration, artifact edits, audit checks, refinement-log updates, and final user summary.
   - If fresh reviewer subagents cannot be spawned, stop immediately and tell the user this workflow requires subagents.
7. For each round from 1 through `--max-rounds`:
   - Start from the current PRD, TDD, and tasks-plan.
   - Send the reviewer subagent the current PRD, TDD, tasks-plan, plan key, round number, and this skill's critique standard.
   - Ask the reviewer subagent to run a fresh first-principles critique using the analysis rubric plus the audit checks in `improve-plan.md`.
   - Do not ask the reviewer to apply fixes, rewrite artifacts, or continue into another round.
   - Keep each reviewer round isolated. Do not reuse the same reviewer subagent for later rounds.
   - Produce structured findings before editing:
     - `id`
     - `severity`: `blocker`, `material`, or `minor`
     - `artifact`: `prd`, `tdd`, `tasks-plan`, or `cross-artifact`
     - `issue`
     - `why_it_matters`
     - `best_fix`
     - `change_required`: `yes` or `no`
   - Treat `blocker` as an issue that prevents execution.
   - Treat `material` as an issue that changes behavior, technical direction, sequencing, verification, rollout, safety, or implementer clarity.
   - Treat `minor` as wording, formatting, local clarity, or polish that does not change execution risk.
   - Apply fixes for all `blocker` and `material` findings.
   - Apply `minor` fixes only when the edit is necessary to keep the artifacts coherent after material changes.
   - Update only PRD, TDD, tasks-plan, and the refinement log.
   - Do not invent exact APIs, schemas, classes, routes, file names, helper names, or test paths unless the source plan or repo inspection already supports them.
   - Preserve useful source-plan substance. Do not remove scope just because it is hard.
   - Re-run the required audit checks from `improve-plan.md` after edits.
   - Append the round findings, fixes, and stop decision to `tasks/tmp/plan-refine-<plan-key>.md`.
8. Stop early when a fresh reviewer round finds no `blocker` or `material` issues.
9. Stop early and report churn when a round repeats the same finding without a stronger fix, reverses a prior fix without new evidence, or only produces local wording edits after the previous round already satisfied the fixed stop rule.
10. If the requested `--max-rounds` is greater than 8, set the effective round cap to 8 and record that cap in the refinement log.
11. If the effective max round count is reached while `blocker` or `material` findings remain, stop and report that the plan is not ready for execution.
    - Keep the refinement log even without `--preserve-refine-artifacts`.
    - Include the last round's remaining blocker/material findings in the final response.
    - Say this max-round stop is evidence for improving `$plan-refine` from the concrete example.
12. Delete `tasks/tmp/plan-refine-<plan-key>.md` after a successful run unless `--preserve-refine-artifacts` is active. Keep it when the run stops with unresolved blockers, material findings, max rounds, or churn.

## Critique Standard

Each round must ask whether the artifact set is more executable, not whether it is more verbose.

The critique must cover:

- whether the PRD still states the real user/problem goal and success guardrails
- whether the TDD names the right source of truth, dependencies, failure modes, rollout needs, and verification obligations
- whether the tasks-plan is sequenced so implementation can start without guessing
- whether task outputs and verification steps are concrete enough
- whether every meaningful product requirement has an `FR-*` ID
- whether every meaningful technical obligation has a `TDR-*` ID
- whether every task maps back to relevant `FR-*` and `TDR-*` IDs
- whether unsupported low-level implementation detail should be removed, softened, or deferred to `$execute-task`
- whether any acceptance criterion lacks test or verification coverage
- whether migration, backfill, rollback, security, operational, or frontend evidence requirements are missing where relevant
- whether the current plan is over-engineered relative to the actual problem
- whether the current plan is under-specified in ways that would cause implementation drift

## Stop Discipline

Do not use "the model says it is good enough" as the stop condition.

Stop only from an explicit reason:

- no remaining `blocker` or `material` findings from a fresh reviewer subagent
- max rounds reached
- unresolved blocker needs user input
- repeated or contradictory churn
- missing required artifacts

Do not continue rounds just to spend the requested budget when the fixed stop rule has already passed.

## Output Contract

Final response must include:

- resolved `plan-key`
- number of rounds run
- stop reason
- effective max round cap, only when the user requested more than 8 rounds or the run stopped because max rounds were reached
- files changed
- material issues fixed
- unresolved issues or accepted residual risk
- whether the plan is ready for `$execute-task`
- preserved artifact path when `--preserve-refine-artifacts` is active or when the run stopped before success

Keep the final answer compact. Do not paste the full refinement log unless the user asks for it.
