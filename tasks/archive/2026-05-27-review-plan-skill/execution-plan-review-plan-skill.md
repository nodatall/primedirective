# Review Plan Skill

Goal: Add `$review-plan` as the default way to adversarially improve a `$deliver` execution plan before implementation.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- `$deliver` already creates and refines one readable execution plan.
- `$plan-refine` already has the strong challenger/reviewer loop, but it only applies to legacy PRD/TDD/tasks-plan artifacts.
- `$first-principles-mode` already owns the adversarial council idea, but it is read-only and does not patch a plan.
- The new skill should bridge that gap for `tasks/execution-plan-<plan-key>.md`.
- Default behavior should patch the plan automatically. A flag should make proposed plan changes approval-gated.
- This repo currently has pre-existing dirty workflow files. The implementation must inspect and preserve those edits instead of overwriting them.

## Steps

### 1. Protect Current Work

Goal: Make sure implementation works with the current dirty branch instead of overwriting unrelated edits.

- [x] Re-read `git status --short` before implementation edits.
- [x] Inspect the existing diff for every file the new skill may touch, especially `README.md`, `scripts/validate-skill-contracts.py`, `skills/deliver/SKILL.md`, `skills/deliver/references/plan-format.md`, and shared workflow references.
- [x] Classify which hunks are pre-existing work and which hunks belong to `$review-plan`.
- [x] Patch only against the current dirty content.
- [x] Do not stage, commit, or rewrite unrelated pre-existing edits unless they become explicit in-scope `$review-plan` changes.

### 2. Define The Public Contract

Goal: Make the new workflow easy to invoke and hard to confuse with `$plan-refine`.

- [x] Add a new public `$review-plan` skill for active `$deliver` execution plans.
- [x] Make first-principles review mandatory for `$review-plan`.
- [x] Make the adversarial council an internal conversation between agents or lanes, not a question flow for the user.
- [x] Make auto-fixing the default: apply safe blocker/material plan fixes directly to the active execution plan.
- [x] Add `--approval-gate` for report-before-edit mode.
- [x] Define `--approval-gate` precisely: run the same council and reviewer loop read-only, write proposed blocker/material plan edits to `tasks/tmp/review-plan-<plan-key>.md`, stop before editing the execution plan, and resume only after explicit approval by applying still-valid proposed fixes or rerunning against the current plan.
- [x] Add a bounded loop with the same practical cap as `$plan-refine`: stop when a fresh reviewer round finds no blocker/material issues, or after 8 rounds.
- [x] Keep `$review-plan` planning-only. It must never edit implementation code or start implementation.

### 3. Build The Skill Surface

Goal: Give agents a concrete workflow to load and follow.

- [x] Create `skills/review-plan/SKILL.md`.
- [x] Create `skills/review-plan/agents/openai.yaml`.
- [x] Reuse the existing first-principles council and `$plan-refine` challenger/reviewer ideas without copying stale legacy PRD/TDD wording.
- [x] Define how `$review-plan` finds the active execution plan, including explicit paths and the current `$deliver` thread state.
- [x] Define council lanes that attack the plan from different angles, such as thesis, hidden assumptions, verification, scope/order, operations, and simpler alternatives.
- [x] Load `skills/first-principles-mode/SKILL.md` and `skills/first-principles-mode/references/analysis-rubric.md` for the council standard.
- [x] Require 3-5 independent council lanes, two rebuttal rounds by default, and a third rebuttal only when the second round reveals a new blocker, evidence need, or genuinely different framing.
- [x] Preserve serious minority risks from the council even when the final plan edit chooses a different path.
- [x] Define the adjudication rule: council pressure is advisory, one fresh reviewer owns severity and stop gating, and the orchestrator applies accepted fixes.
- [x] Define `tasks/tmp/review-plan-<plan-key>.md` as the review log path.
- [x] Define required completion-stamp fields such as `review_plan_complete`, `plan_key`, `mode`, `rounds_run`, `fresh_council_rounds`, `fresh_reviewer_rounds`, `reviewer_stop_gate`, `all_objections_dispositioned`, `plan_changed`, and `ready_for_implementation`.
- [x] Define retention rules: clean up the review log after successful final `$deliver` closeout unless preservation or unresolved blockers require keeping it.

### 4. Wire Public Documentation And Contracts

Goal: Make the new skill discoverable and keep contract mirrors in sync.

- [x] Add `$review-plan` to the README skill table.
- [x] Add a short README section that explains when to use `$review-plan` versus `$deliver`, `$plan-refine`, and `$first-principles-mode`.
- [x] Add `$review-plan` to `skills/shared/references/contract-ownership.md`.
- [x] Update `scripts/validate-skill-contracts.py` so the public skill metadata and key `$review-plan` guarantees are checked.
- [x] Keep the existing `$plan-refine` contract intact for legacy PRD/TDD/tasks-plan artifacts.

### 5. Connect It To Deliver Flow

Goal: Make the normal user path smooth without changing `$deliver` into a review workflow.

- [x] Update `$deliver` documentation only where needed to mention `$review-plan` as an optional pre-implementation second-opinion pass.
- [x] Preserve the current `$deliver` sequence: plan, optional Pro analysis, normal refinement, user review, then implementation approval.
- [x] Ensure `implement the doc` still routes through `$deliver`, not `$review-plan`.
- [x] Ensure `$review-plan` leaves the active execution plan ready for the user to say `implement the doc`.

### 6. Validate And Refresh Local Install

Goal: Prove the workflow contract is current in the repo and installed Codex skill surface.

- [x] Run `python3 scripts/validate-skill-contracts.py`.
- [x] Run `git diff --check`.
- [x] Run `./scripts/install-codex-plugin.sh`.
- [x] Inspect `git diff` to confirm only intended workflow files and the execution-plan archive/closeout files changed.
- [x] Run or simulate default `$review-plan` against a disposable sample execution plan with a known material issue and confirm only the plan changes.
- [x] Run or simulate `$review-plan --approval-gate` against a disposable sample execution plan and confirm the execution plan is unchanged while proposed fixes are logged.
- [x] Check active-plan resolution for an explicit path, one active `$deliver` plan, and ambiguous multiple-plan cases.
- [x] Confirm validation catches implementation-code edits or implementation-start behavior inside `$review-plan`.
