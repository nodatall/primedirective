---
name: review-plan
description: Review an active `$deliver` execution plan with a mandatory first-principles adversarial council loop before implementation. Defaults to applying safe plan-only fixes, supports `--approval-gate` for read-only proposed fixes, and writes `tasks/tmp/review-plan-<plan-key>.md`.
---

# Review Plan Skill

Review active `$deliver` execution plans only. Do not edit implementation code, do not run implementation steps, and do not start `$deliver` implementation. This skill must never edit implementation code and must not start implementation.

## Activation

Invoke explicitly with `$review-plan`, or with approval language such as `apply the review-plan fixes` after a `$review-plan --approval-gate` run has written proposed fixes for the active plan.

Activation examples:

- `$review-plan`
- `$review-plan plan-key=<plan-key>`
- `$review-plan --approval-gate plan-key=<plan-key>`
- `$review-plan using tasks/execution-plan-<plan-key>.md`
- `apply the review-plan fixes`
- `approved, apply the proposed review-plan changes`

Required artifact:

- `tasks/execution-plan-<plan-key>.md`

Supported modifiers:

- `plan-key=<plan-key>` when more than one active execution plan exists
- `--approval-gate`

Supports `--approval-gate` for a read-only proposed-fixes gate.

Defaults:

- `--max-rounds=8` internally. There is no public max-round modifier.
- Without `--approval-gate`, apply safe plan-only fixes for reviewer-confirmed `blocker` and `material` findings.
- Safe plan auto-fix is the default when a reviewer-confirmed blocker/material issue can be fixed without changing product scope, implementation code, or user-owned decisions.

Round limit:

- `8` is the hard maximum round count.

Fixed stop rule:

- Stop when a fresh reviewer round finds no `blocker` or `material` issues.
- Stop successfully only when a fresh reviewer round finds no `blocker` or `material` issues.
- Stop unsuccessfully when a required user decision, unsafe fix, missing artifact, missing reviewer, max-round limit, or churn condition prevents reaching a clean reviewer round.

## Required References

Load these files before running:

- `skills/deliver/SKILL.md`
- `skills/plan-refine/SKILL.md`
- `skills/first-principles-mode/SKILL.md`
- `skills/first-principles-mode/references/analysis-rubric.md`
- `skills/shared/references/reasoning-budget.md`
- `skills/shared/references/analysis/verification-pivot.md`

Use those references for detailed Deliver plan shape, bounded refinement discipline, first-principles council behavior, and reasoning-budget expectations. Do not copy their full workflows into the review log.

## Scope Boundaries

This skill may create or update only:

- `tasks/execution-plan-<plan-key>.md`, except in `--approval-gate`
- `tasks/tmp/review-plan-<plan-key>.md`

This skill must never edit:

- implementation source code
- tests
- migrations
- generated build outputs
- README or shared contract references
- `$deliver`, `$plan-refine`, or `$first-principles-mode` skill files
- archived completed plans, except for read-only evidence

If the user combines `$review-plan` with an implementation request, complete the review-plan workflow and stop. Tell the user to approve implementation separately through the normal `$deliver` flow after the plan review is complete.

## Plan Resolution

Resolve the plan in this order:

- Use an explicit user-provided path such as `tasks/execution-plan-<plan-key>.md` when present.
- Use `plan-key=<plan-key>` when provided.
- Use the visible, attached, referenced, or current-thread `$deliver` execution plan when one is active.
- Active execution plans are files matching `tasks/execution-plan-*.md`.
- Ignore `tasks/archive/**`.
- If exactly one active execution plan exists, infer its `plan-key`.
- If more than one active execution plan exists, stop and ask for `plan-key=<plan-key>`.
- If no active execution plan exists, stop and suggest `$deliver` to create one.
- If the selected execution plan is missing, stop and report the missing path.

Inspect `git status --short` before editing:

- Continue when the working tree is clean.
- Continue when unrelated dirty files exist, but do not touch them.
- If unrelated dirty files overlap the execution plan or review log path, stop and ask before editing.

## Workflow

1. Resolve the active `tasks/execution-plan-<plan-key>.md`.
2. Create or refresh `tasks/tmp/review-plan-<plan-key>.md`.
   - Keep the log concise but auditable.
   - Record invocation mode, resolved plan path, git dirty-state summary, and references loaded.
   - If the user is approving proposed fixes from a prior `--approval-gate` run, load the existing review log first, verify it targets the same execution plan, verify the current plan has not materially changed since the proposals, then apply still-valid proposed fixes or rerun the review against the current plan.
3. Confirm the plan is a Deliver execution plan.
   - It should carry the Deliver implementation instruction or clearly be the active readable `$deliver` execution plan.
   - If it is a draft discussion plan, stop and ask the user to refine it through `$deliver` first.
   - If it is a legacy PRD/TDD/tasks-plan artifact or a goal plan, stop and route to the owning skill instead of converting it here.
4. Set the effective max round count to `8`.
5. For each round from 1 through 8:
   - Start from the current execution plan and current review log.
   - Spawn one fresh read-only reviewer subagent for the round.
   - If a fresh reviewer cannot be spawned, stop immediately; this workflow requires a fresh reviewer for every round.
   - Request the strongest appropriate reasoning tier for plan review, following `reasoning-budget.md`.
   - Send the reviewer the execution plan, plan key, round number, this skill, and the required references.
   - Require the reviewer to run a first-principles adversarial council internally before producing findings.
   - Treat the council as an internal adversarial conversation, not a user-visible transcript.
   - Use 3-5 independent lanes before synthesis, selected from the first-principles-mode pattern: mechanism/root-cause analyst, skeptic/adversary, systems/architecture analyst, operator/pragmatist, and contrarian/reframe analyst.
   - Include a smaller-delta challenge and a skeptic/falsifier check in the council synthesis when they apply, so the plan is tested for simpler safe scope and unsupported hostile findings are rejected with evidence.
   - Run two rebuttal rounds by default.
   - The second rebuttal round may be abbreviated only when the first rebuttal proves the plan is clean and continuing would only repeat the same evidence.
   - Run a third rebuttal round only when the second rebuttal surfaces a new blocker, a new evidence need, or a genuinely different framing.
   - Preserve serious minority risks that survived rebuttal even when the final disposition is residual risk or proposed follow-up.
   - Do not expose a debate transcript. Require a compact council audit summary with lanes used, rebuttal rounds run, issues that survived rebuttal, and the key falsifier or verification need.
   - Ask the reviewer to judge whether the plan is ready for implementation, not whether it is more verbose.
   - Do not ask the reviewer to edit files, apply fixes, or continue into another round.
   - Keep each reviewer round isolated. Do not reuse a reviewer across rounds.
6. Require structured reviewer findings before any plan edit:
   - `id`
   - `severity`: `blocker`, `material`, or `minor`
   - `disposition`: `safe_auto_fix`, `needs_user_decision`, `unsafe_to_auto_fix`, `residual_risk`, or `no_action`
   - `plan_reference`
   - `issue`
   - `why_it_matters`
   - `best_fix`
   - `change_required`: `yes` or `no`
7. Classify severity locally:
   - `blocker` prevents honest implementation from starting.
   - `material` changes scope, sequencing, technical direction, verification, rollout, safety, acceptance criteria, or implementer clarity.
   - `minor` is wording, formatting, local clarity, or polish that does not change execution risk.
8. In default mode, apply only safe plan-only fixes.
   - Safe fixes may clarify ambiguous checkboxes, split oversized steps, restore omitted source scope, reorder dependency flow, add missing verification obligations, add missing rollout or rollback notes, remove contradictions, or tighten acceptance criteria.
   - Safe fixes must stay inside `tasks/execution-plan-<plan-key>.md` and must not invent exact APIs, schemas, routes, helper names, tests, migrations, file paths, or implementation details unless already supported by the plan or repo evidence.
   - Do not remove scope just because it is hard.
   - Do not weaken Deliver closeout obligations, validation expectations, final review, archive movement, or user approval rules.
   - Do not apply findings with `needs_user_decision`, `unsafe_to_auto_fix`, `residual_risk`, or `no_action`.
   - Stop before editing when any `blocker` or `material` finding requires a user decision or is unsafe to auto-fix.
   - Apply `minor` fixes only when needed to keep the plan coherent after a blocker/material fix.
9. In `--approval-gate` mode, stay read-only with respect to the execution plan.
   - Do not edit `tasks/execution-plan-<plan-key>.md`.
   - Write proposed fixes to `tasks/tmp/review-plan-<plan-key>.md`.
   - For each `blocker` or `material` finding, include the proposed replacement text, insertion point, or deletion in a form the user can review.
   - Stop after the first reviewer round that finds any `blocker` or `material` issue, because no plan edit has occurred and later rounds would not be reviewing a changed plan.
   - Ask the user to approve the proposed fixes or request changes. When the user approves, apply still-valid proposed fixes or rerun against the current plan before editing.
   - If the first reviewer round finds no `blocker` or `material` issues, write a successful completion stamp.
10. After default-mode edits, append round results and changed plan sections to the review log, then start a new fresh reviewer round.
11. Stop successfully only after a post-edit fresh reviewer round finds no `blocker` or `material` issues.
12. Stop for churn when a round repeats the same finding without a stronger fix, reverses a prior fix without new evidence, or produces only local wording edits after the previous round already satisfied the fixed stop rule.
13. If 8 rounds are reached while `blocker` or `material` findings remain, stop and report that the plan is not ready for implementation.
14. End every run by appending the Review Plan Completion Stamp below to `tasks/tmp/review-plan-<plan-key>.md`.
15. Before returning control, print a compact Review Plan Findings Summary.

## Retention And Cleanup

Keep `tasks/tmp/review-plan-<plan-key>.md` while any of these are true:

- the run stopped with unresolved blocker or material findings
- `--approval-gate` wrote proposed fixes that have not been applied or rejected
- the user requested preserved review artifacts
- downstream `$deliver` implementation has not reached final closeout yet and the log is needed as review evidence

After successful downstream `$deliver` final review and finalization, delete the completed review-plan log unless the user requested preservation or the log records unresolved risk. `$deliver` owns the final cleanup step once implementation starts.

## Reviewer Standard

The reviewer must pressure-test the plan against the active `$deliver` contract and the first-principles-mode council standard.

The review must cover:

- whether the plan states the actual user goal and implementation boundary
- whether the current checklist preserves the requested scope instead of silently shrinking it
- whether the work is sliced in dependency order
- whether any checkbox is too vague for an implementer to start without guessing
- whether acceptance criteria, validation, rollback, migration, frontend evidence, security, or operational checks are missing where relevant
- whether any item smuggles implementation work into planning without enough evidence
- whether any exact API, schema, route, helper, file, command, or test path is invented beyond available evidence
- whether `--fast`, Pro analysis, final review, archive movement, commit, and finalization expectations from `$deliver` are preserved when relevant
- whether the plan should be delegated to `$plan-to-goal`, `$plan-refine`, `$repo-sweep`, or another owning skill instead of being implemented as a normal Deliver plan
- whether user approval, credentials, destructive changes, data-loss risk, billing, security, schema/API decisions, or product scope choices require an explicit human decision before implementation
- whether a materially simpler or safer plan would satisfy the same user goal
- whether current evidence is too weak to separate competing approaches, requiring the verification pivot before implementation
- whether any hostile-prior concern was falsified and should be recorded as `no_action` rather than turned into a forced plan change

## Review Log

Write `tasks/tmp/review-plan-<plan-key>.md` with stable sections:

- `# Review Plan: <plan-key>`
- `## Invocation`
- `## Plan Inputs`
- `## Round <n>`
- `### Council Audit`
- `### Reviewer Findings`
- `### Applied Fixes` or `### Proposed Fixes`
- `### Stop Decision`
- `## Review Plan Completion Stamp`

The log is a workflow artifact, not a second plan. Keep it focused on issues, fixes, and stop evidence.

## Review Plan Completion Stamp

Every run must end the review log with this stamp. Downstream implementation must treat the stamp as a plan-review gate; a short risk note without this stamp is not a completed `$review-plan` run.

Required stamp fields:

- `review_plan_complete`: `yes` only when the review loop completed successfully.
- `plan_key`: the resolved plan key.
- `plan_path`: `tasks/execution-plan-<plan-key>.md`.
- `approval_gate`: `yes` or `no`.
- `rounds_run`: integer, at least `1` for any completed review attempt.
- `fresh_reviewer_rounds`: integer, at least `1` for a successful run.
- `fresh_council_rounds`: integer count of fresh reviewer rounds where the internal council completed.
- `council_lanes_run`: comma-separated lane names or `not_reached`.
- `rebuttal_rounds_run`: integer or `not_reached`.
- `all_objections_dispositioned`: `yes`, `no`, or `not_applicable`.
- `stop_reason`: one of `clean_reviewer_round`, `approval_gate_proposed_fixes`, `max_rounds_unresolved_material`, `unresolved_user_decision`, `unsafe_to_auto_fix`, `missing_required_artifact`, `missing_required_reviewer`, `churn`, or `wrong_plan_type`.
- `reviewer_stop_gate`: `no_unresolved_blocker_or_material`, `unresolved_blocker_or_material`, or `not_reached`.
- `safe_auto_fixes_applied`: integer count.
- `proposed_fixes_written`: integer count.
- `execution_plan_edited`: `yes` or `no`.
- `implementation_started`: must be `no`.
- `ready_for_deliver_implementation`: `yes` only when `review_plan_complete: yes`, `reviewer_stop_gate: no_unresolved_blocker_or_material`, `fresh_reviewer_rounds >= 1`, and `implementation_started: no`.
- `ready_for_implementation`: same value as `ready_for_deliver_implementation`; keep both fields so downstream gates can check either wording.

Successful default-mode stamp template:

```text
## Review Plan Completion Stamp

review_plan_complete: yes
plan_key: <plan-key>
plan_path: tasks/execution-plan-<plan-key>.md
approval_gate: no
rounds_run: <n>
fresh_reviewer_rounds: <n>
fresh_council_rounds: <n>
council_lanes_run: <lanes>
rebuttal_rounds_run: <n>
all_objections_dispositioned: yes
stop_reason: clean_reviewer_round
reviewer_stop_gate: no_unresolved_blocker_or_material
safe_auto_fixes_applied: <n>
proposed_fixes_written: 0
execution_plan_edited: yes|no
implementation_started: no
ready_for_deliver_implementation: yes
ready_for_implementation: yes
```

Successful `--approval-gate` clean stamp template:

```text
## Review Plan Completion Stamp

review_plan_complete: yes
plan_key: <plan-key>
plan_path: tasks/execution-plan-<plan-key>.md
approval_gate: yes
rounds_run: 1
fresh_reviewer_rounds: 1
fresh_council_rounds: 1
council_lanes_run: <lanes>
rebuttal_rounds_run: <n>
all_objections_dispositioned: yes|not_applicable
stop_reason: clean_reviewer_round
reviewer_stop_gate: no_unresolved_blocker_or_material
safe_auto_fixes_applied: 0
proposed_fixes_written: 0
execution_plan_edited: no
implementation_started: no
ready_for_deliver_implementation: yes
ready_for_implementation: yes
```

`--approval-gate` proposed-fixes stamp template:

```text
## Review Plan Completion Stamp

review_plan_complete: no
plan_key: <plan-key>
plan_path: tasks/execution-plan-<plan-key>.md
approval_gate: yes
rounds_run: 1
fresh_reviewer_rounds: 1
fresh_council_rounds: 1
council_lanes_run: <lanes>
rebuttal_rounds_run: <n>
all_objections_dispositioned: yes
stop_reason: approval_gate_proposed_fixes
reviewer_stop_gate: unresolved_blocker_or_material
safe_auto_fixes_applied: 0
proposed_fixes_written: <n>
execution_plan_edited: no
implementation_started: no
ready_for_deliver_implementation: no
ready_for_implementation: no
```

## Output Contract

Final response must include:

- resolved `plan-key`
- rounds run
- stop reason
- whether `--approval-gate` was active
- files changed
- safe plan fixes applied
- proposed fixes written, when any
- unresolved blockers, material issues, user decisions, or residual risk
- completion stamp status, including `review_plan_complete`, `ready_for_deliver_implementation`, `ready_for_implementation`, `rounds_run`, and `fresh_reviewer_rounds`
- explicit confirmation that implementation code was not edited and implementation was not started

Keep the final answer compact. Do not paste the full review log unless the user asks for it.
