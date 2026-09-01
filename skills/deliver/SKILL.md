---
name: deliver
description: Plan and complete repo work from one readable Markdown execution plan. Supports normal review, draft discussion, `--deep-research`, `--pro-analysis`, and `--fast`; fast skips only the first plan-review pause.
---

# Deliver

Use one readable Markdown plan to guide work from planning through final handoff.

The normal order is: plan -> optional deep research -> optional Pro analysis -> refine -> user review and approval -> implement -> validate -> final review -> archive -> commit -> finalize -> handoff. `--fast` skips only the first plan-review pause. It does not skip any other part of this order.

New Deliver work does not use the retired PRD, TDD, or full tasks-plan stack.

## Load The Right References

Always load:

- `skills/shared/references/plain-language.md`
- `skills/shared/references/reasoning-budget.md`
- `skills/shared/references/analysis/verification-pivot.md`

Load these before the named decision or action:

- `skills/deliver/references/plan-format.md` before drafting or refining a plan
- `skills/plan-to-goal/SKILL.md` before choosing goal mode for work that may need an adaptive evidence loop
- `skills/review-plan/SKILL.md` when the user asks for adversarial plan review
- `skills/shared/references/planning/deep-research.md` when `--deep-research` is present
- `skills/shared/references/analysis/pro-browser-analysis.md` when `--pro-analysis` is present
- `skills/shared/references/architecture/architecture-guidance.md` before planning or implementing boundary-affecting work, or when `docs/ARCHITECTURE.md` exists; follow its `$create-architecture` gate
- `skills/shared/references/review/finding-disposition.md` before implementation may add or change tests
- `skills/deliver/references/worker-packet.md` before assigning a worker
- `skills/shared/references/review/finding-disposition.md`, `skills/shared/references/review/review-protocol.md`, and `skills/deliver/references/rereview-scope-record.md` before final review
- `skills/shared/references/execution/finalization-gate.md` before any terminal handoff

The shared references own their detailed rules. Apply their Deliver-only `test_disposition` and final-review `rereview_scope` rules only to Deliver. Do not copy their rubrics here or apply them to other review workflows.

## Commands And Modes

Use Deliver for `$deliver`, `$deliver refine`, `$deliver plan`, legacy `$deliver discuss`, and plain-language deliver requests such as `deliver`, `refine it`, `implement deliver`, `deliver this`, `start deliver`, or `continue deliver`.

Supported modifiers:

- `--deep-research`
- `--pro-analysis`
- `--fast`

The modes are:

- **Normal:** `$deliver`, `$deliver refine`, `$deliver plan`, or an equivalent request creates or reuses `tasks/execution-plan-<plan-key>.md`. Run requested research, Pro analysis, and refinement in the same command. Then ask the user to review the Markdown plan before implementation.
- **Fast:** `$deliver --fast` follows the same path, treats the refined plan as approved scope, and starts implementation without the first plan-review pause.
- **Draft discussion:** Use this only when the user explicitly asks to discuss or keep updating a draft. `$deliver discuss` is a legacy alias for this behavior; do not prefer it or present it as a separate workflow.

`$deliver --deep-research` and `$deliver --pro-analysis` use the normal mode with their named gate. Their modifiers may be combined with each other and with `--fast`.

When both optional modifiers are present, finish and apply deep research before Pro analysis. Finish and apply Pro analysis before refinement.

An active Deliver workflow stays active until final handoff, cancellation, or an explicit workflow switch. Later messages such as `implement`, `implement deliver`, `implement the doc`, `implement this plan`, `go ahead`, `start`, `continue`, `finish it`, `do it`, or `ship it` approve or resume the active plan even when `$deliver` is not repeated. Reopen the exact plan, apply any correction, and continue this workflow.

A document with `Deliver implementation instruction:` routes back to Deliver. The user does not need `$deliver execute <plan-path>`. If the document is not already `tasks/execution-plan-<plan-key>.md`, import its in-scope content into that path without changing scope before implementation.

For a fixed, approved execution plan or fixed remediation packet, resume at implementation without refining again. Packet approval authorizes only its fixed repairs.

Its review replaces Deliver's initial full review only when `skills/shared/references/review/review-protocol.md` accepts its fail-closed attestation. The evidence must prove the active workflow, unchanged base commit/tree/diff, complete full-branch profile, fresh reviewer, final quality audit, findings, repair authorization, and fixed stop boundary. Otherwise run the normal fresh full review.

Return to refinement only after a material plan change or when implementation evidence exposes a blocking contradiction.

## Files

- Execution plan: `tasks/execution-plan-<plan-key>.md`
- Optional frontend mockup: `tasks/ui-mockup-<plan-key>.html`
- Goal plan: `tasks/goal-plan-<plan-key>.md`
- Optional active-step note: `tasks/tmp/active-step-<plan-key>-<step>.md`
- Deep-research memo: `tasks/tmp/research-plan-<plan-key>.md`
- Pro-analysis memo: `tasks/tmp/pro-analysis-<plan-key>.md`
- Final-review log: `tasks/tmp/review-deliver-final-<plan-key>.md`
- Repair-scope record: `tasks/tmp/review-deliver-final-<plan-key>.rereview.json`
- Archive: `tasks/archive/<yyyy-mm-dd>-<plan-key>/execution-plan-<plan-key>.md`

## Workflow

### 1. Check The Repo And Branch

Use the current thread, pasted material, rough checklist, existing plan, review, research, or user-named path as source material. Inspect enough of the repo to honor obvious local constraints.

Run `git status --short` before edits. Preserve unrelated changes. Stop if unrelated or dangerous changes overlap this work.

- Stay on a non-base branch.
- On `main`, `master`, or the resolved local base branch, create a feature branch before writing a plan or implementation file. Prefer `deliver/<plan-key>` when local conventions do not suggest a better name.
- On detached `HEAD`, stop and ask.
- Do not carry overlapping unrelated or dangerous changes onto a new branch without asking.

After the branch decision and before writing a plan, goal plan, or implementation change, capture the baseline required by `skills/shared/references/execution/finalization-gate.md`.

### 2. Choose The Plan Type

Route through `$plan-to-goal` when the next implementation step depends on the result of a repeatable inspect -> patch -> validate loop with a meaningful target, comparator, or success signal. Its contract lives in `skills/plan-to-goal/SKILL.md`.

Do not use goal mode when the decisive run is slow, paid, approval-gated, nightly, externally scheduled, or otherwise cannot support several useful loops now. Write a normal execution plan that prepares cheap checks and the human-approved decision run.

Goal mode creates `tasks/goal-plan-<plan-key>.md` with `Goal`, `Done When`, `Not Done Yet If`, and its absolute-path `/goal` `Start Prompt`. Stop after the goal plan and `Start Prompt`. Do not execute it as a normal Deliver checklist. Start the goal in this thread only when the user explicitly asks and goal mode is available.

### 3. Create Or Update The Plan

Follow `skills/deliver/references/plan-format.md`.

For explicit draft discussion, update the same `tasks/execution-plan-<plan-key>.md` as the conversation changes. If only `tasks/planning-discussion-<plan-key>.md` exists, import its current in-scope content first. Stop after each useful draft update with a short link to the file. Do not refine, implement, or commit from the draft. When the user asks to refine it, keep the same file and replace the draft instruction with the exact Deliver implementation instruction.

For normal planning, create or reuse the canonical execution plan and include `Deliver implementation instruction:` near the top. Treat `tasks/tasks-plan-<plan-key>.md`, `tasks/*-spec.md`, pasted checklists, and review notes as source material only. Preserve their concrete in-scope items unless they are duplicates, contradictions, or user-approved removals. Never implement from a tasks-plan, spec, or notes file. A named existing plan such as `tasks/execution-plan-startup-fixes.md` follows the same rule.

Keep the main plan high-level and readable. Detailed files, commands, tests, done conditions, and worker context belong in the active-step packet when that item starts.

### 4. Run Optional Gates

With `--deep-research`, use `skills/shared/references/planning/deep-research.md`. Run local reconnaissance, write `tasks/tmp/research-plan-<plan-key>.md`, apply adopted findings to the execution plan, and print a short `Deep Research Summary`.

Do not continue to Pro analysis, refinement, review, or implementation until the memo has its exact Deep Research Completion Stamp. All material findings must be applied or dispositioned, and the memo must end with `evidence_bar_met: yes`. Keep repairing an incomplete pass. Stop only for unavailable web access, unsafe context exposure, a required user decision, or when the user explicitly drops `--deep-research`.

With `--pro-analysis`, use `skills/shared/references/analysis/pro-browser-analysis.md`. Write `tasks/tmp/pro-analysis-<plan-key>.md`, verify and disposition the findings, apply adopted findings to the plan, and print a short `Pro Findings Summary`. A degraded or incomplete pass is diagnostic only. Do not refine, review, or implement until the required browser evidence and synthesis fields are complete and the memo ends with `pro_synthesis_complete: yes`, unless the user explicitly drops `--pro-analysis`.

### 5. Refine And Get Approval

Run at least one refinement round. Use a fresh reviewer subagent by default when subagents are available. The reviewer checks missing scope, vague items, order, duplicates, oversized work, hidden dependencies, contradictions, unclear next steps, and meta-planning placeholders. Keep the plan in dependency order without turning it into a per-file script.

When a round finds a material issue or changes the plan, edit only the plan and run a full post-edit round. Do not create a separate refinement artifact. Stop when a round finds no material backlog issue or after 8 rounds. At the limit, show the exact unresolved blocker and do not implement.

Normal mode: link `tasks/execution-plan-<plan-key>.md` and ask the user to review it directly. Ask them to say `implement the doc` when it is right or explain what is wrong, missing, or out of order. Do not launch a review app or external viewer. A draft that was just refined still needs this separate approval unless the request includes `--fast`.

If the user asks for an adversarial plan review, route it through `$review-plan`. It may improve only the plan and must return here without starting implementation.

In `--fast` mode, mention that the first review pause was skipped and continue to implementation. Still stop for:

- destructive or data-loss actions
- missing credentials, environment, or service access
- material scope ambiguity
- billing, security, schema, API, or product decisions
- unresolved implementation-changing `Open question:` checkboxes
- goal-plan delegation
- incomplete optional gates or unresolved refinement issues
- anything that would make immediate implementation unsafe or dishonest

### 6. Implement The Whole Plan

Start only from the canonical approved execution plan. Choose the next unchecked item in file order unless evidence makes another order clearly better; update the plan before changing order.

Before editing, identify repo-local implementation and validation patterns. Use a private active-step note only when helpful. For each non-trivial item, create the packet from `skills/deliver/references/worker-packet.md` and assign one worker by default when workers are available. Never run implementation workers in parallel. Only read-only discovery or review lanes, such as `$repo-sweep --swarm`, may run in parallel. The orchestrator implements directly only when workers are unavailable. Do not mention whether reviewers or workers were used unless it creates a real blocker or residual risk.

Before keeping a new or changed test as permanent coverage, use `skills/shared/references/review/finding-disposition.md`. Record `test_disposition: permanent | table_case | probe_only | no_test` and a concise evidence-backed rationale. A disposable or historical fixture without a permanent-test path uses `probe_only`; do not invent a permanent test harness. Every implementation change still needs verification.

After each useful item:

1. Run the narrow check that proves it.
2. Commit the useful item or a tightly coupled group. Do not include unrelated user changes or create an empty commit.
3. Check off the item and update later plan items only when evidence changes the right path. Keep the plan readable and omit routine transcripts and commit SHAs.
4. After every useful commit or plan update, reopen the whole plan and start the next unchecked item.

Execution scope is the entire unchecked remainder of `tasks/execution-plan-<plan-key>.md`, not one phase. Do not send a recap or handoff while in-scope items remain. A completed phase, passing check, or useful commit is not a stopping point. After the final checkbox, continue directly through final review, authorized repairs, archive, closeout commit, and finalization.

After implementation starts, stop only for a required user decision, a missing environment/service/credential, an unsafe or destructive action needing approval, an unresolved material plan contradiction, or a verification blocker. Missing closeout work is not a blocker.

### 7. Verify Each Change

- Run the narrow check that proves the current item.
- For a parser or validator repair, test accepted-looking inputs against the downstream consumer grammar. When relevant to shell numeric state, include empty, non-digit, leading-zero or base-sensitive, and bounded-length inputs.
- For an approved cross-process lifecycle repair, verify synchronous completion after any intermediate readiness signal, concurrent waiters, the active owner or lock, failed or stale owner recovery, and default-versus-foreground behavior. A synchronous caller must not return while protected work or its live owner or lock remains active. Do not expand the approved contract to satisfy the check.
- For UI, layout, styling, or rendered-content changes, inspect the real affected UI when practical and capture visual evidence.
- After a failed check, classify the failure layer before patching again. If another patch would be a guess, use `skills/shared/references/analysis/verification-pivot.md` and put the smallest useful log, deterministic test, replay, or temporary probe under `/agent-scratch/`.

### 8. Run Final Review

Follow `skills/shared/references/review/review-protocol.md` and `skills/shared/references/review/finding-disposition.md`. Use the execution plan as scope. Write the log to `tasks/tmp/review-deliver-final-<plan-key>.md` unless the repo has another temp convention, and keep it through finalization.

Run one initial fresh full-branch review with a fresh final reviewer when available. Do not add a second full review as ceremony. Fix authorized, verified, in-scope findings, rerun the affected checks, and update the plan.

Before any repair rereview, follow `skills/deliver/references/rereview-scope-record.md`. For fixed-packet repairs, record every action before the first post-repair review. Run its plan-phase check before rereview and its complete-phase check after recording the rounds. Do not copy its validator into the target repo or target diff. The validator-derived action scope and grouped widest scope are authoritative. Do not complete review, archive, or finalize unless the required check passes.

Skip final review only when a real blocker prevents it. Stop with the blocker and do not claim completion.

### 9. Archive And Finalize

After final-review findings are dispositioned and required repairs are verified:

1. Move `tasks/execution-plan-<plan-key>.md` to `tasks/archive/<yyyy-mm-dd>-<plan-key>/execution-plan-<plan-key>.md`.
2. If `tasks/ui-mockup-<plan-key>.html` exists, move it into the same directory as `ui-mockup-<plan-key>.html` so its relative link still works.
3. Leave the archived plan readable. Do not turn it into an audit log.
4. Remove disposable active-step files unless a blocker still needs them. Remove `tasks/tmp/review-plan-<plan-key>.md` after a completed `$review-plan` with no unresolved risk unless the user requested preserved artifacts.
5. Commit the archive move and every final-review, checklist, cleanup, implementation, or validation edit before handoff.

Do not archive `tasks/goal-plan-<plan-key>.md` unless the user explicitly converts it into a normal execution plan.

Run the `$deliver` readable-plan path in `skills/shared/references/execution/finalization-gate.md` immediately before the final handoff. Search the entire live or archived plan for unchecked items. Continue when any in-scope item remains unless a real blocker prevents it. Commit any new closeout work.

## Handoffs

At the normal plan-review gate, link the plan, say whether refinement finished, list unresolved implementation-changing `Open question:` items, and ask the user to correct anything wrong, missing, or out of order. If Deliver chose a goal plan, say so.

In `--fast` mode, say the first plan-review pause was skipped. Stop and list any implementation-changing `Open question:` instead of starting work. Otherwise continue without a review handoff.

Write the final handoff only from evidence that passed finalization. Include the archived plan, completed work, relevant commits and validation, final-review result and material findings, skipped checks, blockers, residual risk, branch or PR state, and final working-tree status.

Do not claim completion until every in-scope checkbox is done or the user explicitly deferred it, focused validation ran, and final review completed.
