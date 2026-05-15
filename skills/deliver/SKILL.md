---
name: deliver
description: Create or load one plain-language execution plan, or create a goal-plan prompt when the source is really an evidence loop, then refine it, ask the user to approve the readable plan, and execute normal plans one item at a time with focused validation, useful commits, plan updates, and final review. Supports `--pro-analysis` for ChatGPT Pro browser escalation before refinement. Use when invoked with `$deliver`, plain `deliver` phrases, or when the user asks to implement a Deliver execution plan doc.
---

# Deliver Skill

Run lightweight planned execution from one readable plan document, or create one readable goal-plan prompt when the request is better handled by Codex goal mode.

This skill is a separate workflow from `$plan-work`, `$plan-and-execute`, and `$execute-task`. Do not generate PRD, TDD, or full tasks-plan artifacts unless the user explicitly switches workflows.

Load these references before starting:

- `skills/shared/references/plain-language.md`
- `skills/plan-to-goal/SKILL.md` when the source is goal-shaped
- `skills/shared/references/analysis/pro-oracle-escalation.md` when `--pro-analysis` is present
- `skills/shared/references/reasoning-budget.md`
- `skills/shared/references/analysis/verification-pivot.md`
- `skills/shared/references/review/review-protocol.md` before the final review
- `skills/shared/references/execution/finalization-gate.md` before any terminal handoff

## Activation

Invoke explicitly with `$deliver`, `$deliver plan`, or plain-language deliver requests such as `deliver`, `implement deliver`, `deliver this`, `start deliver`, or `continue deliver`.

Supported modifiers:

- `--pro-analysis`

After long planning conversations, prefer a self-identifying document flow:

- `$deliver plan` creates or refines `tasks/execution-plan-<plan-key>.md`, embeds the Deliver implementation instruction in the plan, then stops for review.
- When the user later says `implement`, `implement the doc`, `implement this plan`, `go ahead`, or equivalent while the visible, attached, referenced, or active document is a Deliver execution plan, load this skill, load that exact plan, treat it as the approved scope, and start implementation at step 7. Continue through focused validation, final review, archive movement, commit, and the finalization gate before the final handoff.

Examples:

- `$deliver` with a thread plan above it.
- `$deliver plan` with a thread plan above it.
- `$deliver --pro-analysis` when a lightweight readable plan should get ChatGPT Pro pressure before refinement and user review.
- `$deliver` followed by a rough checklist, bug list, repo review, research output, or product idea.
- `implement deliver` after a long planning discussion or after the user has reviewed a deliver-style checklist.
- `implement the doc` when the opened or referenced doc contains the Deliver implementation instruction.
- `$deliver using tasks/execution-plan-startup-fixes.md` when a readable execution plan already exists.

After `$deliver` has created or loaded an execution plan in the thread, the workflow stays active until final handoff, explicit cancellation, or an explicit workflow switch. Later user messages such as `implement`, `implement deliver`, `go ahead`, `start`, `continue`, `finish it`, `do it`, or `ship it` are approval/resume signals for the active `$deliver` plan even when `$deliver` is not repeated. Re-open the active `tasks/execution-plan-<plan-key>.md`, apply any correction, and resume this workflow instead of treating the message as generic implementation.

When a plan document contains the Deliver implementation instruction, that document is enough to route implementation back through this skill. Do not require the user to say `$deliver execute <plan-path>`. If the user asks to implement the document, load the document, scan every checkbox, and run the closeout path in this file. If the document is not already named `tasks/execution-plan-<plan-key>.md`, first import it into that canonical filename unless doing so would change scope.

## Artifacts

Use these files:

- Durable plan: `tasks/execution-plan-<plan-key>.md`
- Durable goal plan: `tasks/goal-plan-<plan-key>.md`
- Optional active-step note: `tasks/tmp/active-step-<plan-key>-<step>.md`
- Completed plan archive: `tasks/archive/<yyyy-mm-dd>-<plan-key>/execution-plan-<plan-key>.md`

The durable plan is for the user to read and edit. Keep it low-friction. Do not turn it into an audit log.

Use `tasks/goal-plan-<plan-key>.md` only through `$plan-to-goal`. A goal plan is a paste-ready `/goal` prompt plus enough readable context to review the loop before it starts. It is not a normal execution checklist and should not be archived by the `$deliver` finalization gate unless the user explicitly converts it into a normal execution plan.

Non-canonical plan-like files such as `tasks/tasks-plan-<plan-key>.md`, `tasks/*-spec.md`, pasted checklists, and review notes are source material only for `$deliver`. Do not implement directly against them. If the user invokes deliver from one of those artifacts, import or convert the in-scope checklist into `tasks/execution-plan-<plan-key>.md` before implementation, then use that execution plan for unchecked-item scans, final review scope, archive movement, and finalization.

## Plan Format

Prefer this shape:

```md
# <Plan Name>

Goal: <one sentence>

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- <Only include when useful.>

## Steps

### 1. <Plain-language phase>

Goal: <Only if useful.>

Decision notes:
- <Only include when useful.>

- [ ] <work item>
- [ ] <work item>
- [ ] <work item>

### 2. <Next phase>

- [ ] <work item>
```

Rules:

- Use phases plus checkboxes.
- Allow one level of checkboxes under a phase.
- Avoid checkboxes inside checkboxes.
- Add `What We Know`, phase `Goal`, or `Decision notes` only when they reduce confusion.
- Add `Done when` only when the checkbox text is too vague to define completion.
- Include the exact Deliver implementation instruction near the top of every normal execution plan.
- Do not add `Status`, `Result`, or `Commit` lines by default.
- Keep validation evidence and commit details in the final handoff or git history unless the evidence changes the plan.

## Goal Plan Delegation

Before drafting a normal execution plan, check whether the source is goal-shaped:

- The plan cannot honestly name the remaining implementation steps until after the next validation result.
- The work is inspect -> patch -> validate -> inspect again until confidence or a blocker.
- The success condition is proving a path works, exhausting a search space, improving coverage until recoverable options are exhausted, or diagnosing why repeated attempts still fail.
- The plan has a fixed holdout artifact, benchmark, comparator, baseline, ceiling, or target metric that should guide iterative work.

Even when the source sounds like an evidence loop, do not choose goal mode unless the agent can run multiple useful validation loops inside the goal. If the decisive evidence depends on a slow, paid, approval-gated, nightly, or externally scheduled run, write a normal execution plan that prepares the harness, cheap checks, smoke run, and human-approved decision run instead.

If the source is goal-shaped, use `$plan-to-goal` instead of writing a normal `$deliver` checklist. `$plan-to-goal` owns the `tasks/goal-plan-<plan-key>.md` format, compact `/goal` prompt, target/baseline rules, state-recording guidance, and review wording.

After `$plan-to-goal` writes the goal plan, stop for user review. Do not start normal `$deliver` implementation unless the user rejects goal mode or asks to convert it into an execution plan.

## Pro Analysis

When `--pro-analysis` is present, compose `skills/shared/references/analysis/pro-oracle-escalation.md` after the normal execution plan exists and before the refinement loop.

Rules:

- Run local reconnaissance first and use the plan plus relevant repo context to choose a Pro context bundle.
- Use the Prime Directive wrapper, not raw Oracle commands.
- Write the synthesis memo to `tasks/tmp/pro-analysis-<plan-key>.md`.
- Reduce the Pro answer into a findings ledger with local verification/disposition for each material finding.
- Apply adopted findings directly into `tasks/execution-plan-<plan-key>.md` before refinement.
- Print a short `Pro Findings Summary` before refinement and user review.
- Do not start refinement, user review, or implementation if the Pro memo is missing, lacks Oracle invocation evidence for a real extended-thinking run, leaves material findings undispositioned, leaves adopted findings unapplied, or does not end with `pro_synthesis_complete: yes`.
- A degraded Pro fallback may be recorded for diagnostics, but it is not a completed `--pro-analysis` pass and must block normal `$deliver --pro-analysis` progress until resolved or the user explicitly drops the modifier.

## Workflow

1. Establish source material.
   - Use the current thread, pasted source, rough checklist, existing execution plan, repo review, research output, or user-provided plan path.
   - Inspect the target repo enough to avoid inventing a plan that ignores obvious local constraints.
   - Inspect `git status --short` before edits and do not overwrite unrelated changes.
2. Prepare the branch before writing plan or implementation files.
   - If currently on a non-base branch, stay on that branch.
   - If currently on `main`, `master`, or the resolved local base branch, create a new feature branch before writing the execution plan or goal plan.
   - Name the branch from the plan key when obvious, such as `deliver/<plan-key>`, unless the repo's branch naming convention suggests a better local pattern.
   - If detached `HEAD`, stop and ask.
   - If unrelated or dangerous overlapping changes exist, stop and ask before carrying them onto the new branch.
   - Capture the finalization baseline from `skills/shared/references/execution/finalization-gate.md` after branch-state decisions and before writing the execution plan, goal plan, or implementation changes.
3. Classify whether this is a normal execution plan or a goal plan.
   - Before drafting a normal execution plan, run the Goal Plan Delegation check.
   - If it is goal-shaped, load `skills/plan-to-goal/SKILL.md`, write `tasks/goal-plan-<plan-key>.md`, and stop after the `$plan-to-goal` review request.
   - Do not execute a goal plan as a normal `$deliver` checklist.
   - If the user approves and explicitly asks to start the goal from this thread, start the goal using the prompt when goal mode is available; otherwise provide the exact `/goal` prompt from the file.
   - If the user says not to use goal mode, convert the source into a normal execution plan and continue with step 4.
4. Create or load the plain-language plan.
   - If no plan exists, write `tasks/execution-plan-<plan-key>.md`.
   - If the latest approved source is a non-canonical plan-like file such as `tasks/tasks-plan-<plan-key>.md`, `tasks/*-spec.md`, a pasted checklist, or review notes, treat it as source material and convert the in-scope work into `tasks/execution-plan-<plan-key>.md` before implementation starts.
   - Do not continue into implementation with only a `tasks-plan`, spec, or notes file as the scope artifact.
   - If the user asked to implement a non-canonical plan-like document, import the in-scope content into `tasks/execution-plan-<plan-key>.md`, then continue as an implementation request unless the import exposed a scope contradiction.
   - Preserve every concrete source item unless it is a duplicate, contradiction, or user-approved removal.
   - Phrase steps as user-readable outcomes or actions, not implementation jargon.
   - Keep future items readable rather than fully specified.
4.5. If `--pro-analysis` is present, run Pro analysis before refinement.
   - Load `skills/shared/references/analysis/pro-oracle-escalation.md`.
   - Use `tasks/execution-plan-<plan-key>.md` plus selected repo context as the Pro input.
   - Write and verify `tasks/tmp/pro-analysis-<plan-key>.md`.
   - Apply adopted Pro findings into the execution plan before step 5.
   - Hard-stop before refinement if the Pro synthesis gate is incomplete.
5. Refine the plan before user review.
   - Run at least one refinement round.
   - Continue while material backlog issues remain.
   - If a refinement round finds material issues or changes the plan, run another refinement round after those edits.
   - Stop only after a full post-edit refinement round finds no material backlog issues.
   - Stop after 8 rounds even if issues remain.
   - Use a fresh reviewer subagent by default when subagents are available.
   - Do not mention whether a subagent was or was not used in the user-facing review request unless it creates a real blocker or residual risk.
   - The reviewer checks for missing source items, vague checkboxes, bad order, duplicate work, oversized steps, hidden dependencies, contradictions, and unclear next step.
   - Edit only the execution plan during refinement.
   - Do not create a refinement notes file or separate refinement markdown artifact.
   - If 8 rounds end with unresolved material issues, stop and show the exact blocker instead of starting implementation.
6. Ask for user review once.
   - Show the final readable plan or summarize it with the file path.
   - Ask: `Please review this before I start. Tell me what is wrong, missing, or out of order.`
   - Tell the user they can say `implement the doc` when it looks right.
   - Do not begin implementation until the user approves or corrects the plan.
   - If the user corrects the plan, update it and rerun refinement only if the correction introduces material backlog risk.
   - Plan discussion does not clear `$deliver` activation. If the user approves after back-and-forth plan review, continue to step 7 for the active execution plan.
7. Execute one item at a time.
   - `implement the doc` starts here after loading the canonical execution plan and confirming the branch/finalization baseline from earlier steps is available or recapturing it if needed.
   - Choose the next unchecked item in plan order unless new evidence makes a different next item clearly better; update the plan first when order changes.
   - Create a tiny active-step note only when it helps execution. Keep it private and disposable.
   - Identify repo-local implementation and validation patterns before editing.
   - For each non-trivial implementation item, create an active-step packet.
   - Assign one worker agent by default when worker agents are available.
   - Do not let the orchestrator absorb implementation by default. The orchestrator owns next-step selection, worker packet creation, integration, validation judgment, plan updates, and commits.
   - Give each worker a compact active-step packet, not the whole planning history.
   - When worker agents are unavailable, the orchestrator implements directly.
   - Do not mention whether worker agents were or were not used unless it creates a real blocker or residual risk.
8. Verify each useful step.
   - Run the narrow check that proves the current item.
   - For UI, layout, styling, or rendered-content changes, inspect the affected UI when practical and capture visual evidence.
   - If a check fails, classify the failure layer before patching again.
   - If another patch would be a guess, use the verification pivot: add the smallest useful log, deterministic test, replay, or temporary probe under `/codex-scripts/`.
9. Commit useful completed work.
   - Commit each completed useful item or coherent group of tightly coupled items.
   - Do not commit unrelated user changes.
   - If a step produces no useful code/docs change, update the plan or handoff with the reason instead of creating an empty commit.
10. Update the plan after each item.
   - Check off completed items.
   - Split, reorder, add, remove, or clarify items when implementation evidence changes the right path.
   - Keep the plan readable. Do not add detailed logs, commit SHAs, or validation transcripts unless they are needed to understand the next step.
11. Continue until done or blocked.
   - If the current turn starts from a generic approval or resume message while an active unarchived `$deliver` execution plan exists, re-open that plan and scan the entire unchecked remainder before doing or reporting anything else.
   - If the current turn starts with `implement deliver` or another deliver resume phrase and the only available scope artifact is non-canonical, first convert it into `tasks/execution-plan-<plan-key>.md`; do not treat the absence of a canonical execution plan as permission to skip final review, archive movement, or the finalization gate.
   - Keep moving through unchecked items after each commit.
   - Execution scope is the entire unchecked remainder of `tasks/execution-plan-<plan-key>.md`, not the current phase, section, or next coherent slice.
   - After every useful commit or plan update, immediately re-open the execution plan, scan the whole file for the next unchecked checkbox in file order, and start it when one exists.
   - Do not stop after completing a phase such as `1. ...` or at any section boundary while unchecked checkboxes remain later in the file.
   - After implementation starts, do not send a user-facing recap, handoff, or "please review" message while unchecked in-scope items remain.
   - If the next message would summarize completed work before all in-scope checkboxes are done or explicitly deferred, do not send it; reopen the plan, identify the next unchecked item, and continue.
   - A completed phase, passing focused check, or useful commit is not a stopping point when later unchecked items remain.
   - After the last checkbox is checked, implementation is still not terminal. Continue directly into final review, review remediation, archive movement, commit of any closeout changes, and the finalization gate.
   - A user-visible "What changed" plus "Validation" recap before final review, archive, commit, and finalization is an invalid terminal handoff. Suppress it and keep executing closeout unless a real blocker prevents the next closeout action.
   - Stop only for a required user decision, a missing environment/service/credential, an unsafe/destructive action needing approval, an unresolved material plan contradiction, or a verification blocker.
12. Run final review before declaring completion.
   - Use the final full-branch review path from `review-protocol.md`.
   - Use the execution plan as the scope artifact instead of PRD/TDD/tasks-plan.
   - Write the final review log to `tasks/tmp/review-deliver-final-<plan-key>.md` unless a repo-local convention requires a different temp path.
   - Use a fresh final reviewer when available.
   - Review the diff against the execution plan, plan updates, and relevant validation evidence.
   - Fix in-scope material findings, rerun relevant checks, and update the plan before the final handoff.
   - Skipping final review is allowed only when a real blocker prevents it; in that case, stop with the blocker and do not claim completion.
13. Archive the execution plan after final review is complete.
   - Move `tasks/execution-plan-<plan-key>.md` to `tasks/archive/<yyyy-mm-dd>-<plan-key>/execution-plan-<plan-key>.md`.
   - Archive only after final review findings are dispositioned and any required remediation has been verified.
   - Leave the archived plan readable; do not rewrite it into an audit log during archive.
   - Remove disposable active-step temp files unless they are still needed to explain an unresolved blocker.
   - Commit the archive move and any final review, checklist, cleanup, implementation, or validation edits before the final handoff.
14. Run the finalization gate before the final handoff.
   - Use the `$deliver` / readable execution-plan path in `skills/shared/references/execution/finalization-gate.md`.
   - The unchecked-checkbox search must inspect the entire execution plan or archived execution plan, not only the last phase worked.
   - If any unchecked in-scope checkbox remains, continue execution instead of handing off unless one of the real blockers from step 11 prevents progress.
   - If final review, archive movement, checklist updates, implementation edits, validation edits, or cleanup created uncommitted changes, commit them before handing off.

## Output

For the initial review gate:

- link the plan file
- if `$deliver` chose a goal plan, say that it is a goal plan
- say refinement completed or name unresolved issues
- ask the user to correct anything wrong, missing, or out of order

For the final handoff:

- name the archived plan file
- summarize completed items
- list commits created when relevant
- list validation commands or flows run
- mention final review result
- name any skipped checks, blockers, or residual risk

Do not claim the plan is complete until all in-scope checkboxes are done or explicitly deferred by the user, focused validation has run, and final review is complete.

## Worker Packet

Use worker agents by default for non-trivial implementation items when worker agents are available. Pass one bounded item with only the context needed to implement it correctly:

```md
# Active Step Packet

Plan: tasks/execution-plan-<plan-key>.md
Step: <exact phase and checkbox text>

Goal:
<one sentence from the plan when useful>

Do:
<the one checkbox/item this worker owns>

Done when:
<include only when the checkbox text is not enough>

Relevant context:
- <only useful What We Know or Decision notes for this step>
- <important constraints from the approved plan>

Repo context:
- Current branch:
- Relevant files or surfaces to inspect first:
- Existing local pattern to follow:
- Unrelated dirty files to avoid:

Validation:
- Focused command or flow to run:
- UI/app inspection needed: yes/no

Rules:
- Do not edit outside this step unless required and reported.
- Do not mark other plan items done.
- Do not commit.
- Return changed files, validation run, result, and blockers.
```

The orchestrator keeps ownership of the full plan, next-step selection, worker packet creation, worker integration, final validation judgment, checkbox updates, commits, and plan changes. It should not hand a worker the whole backlog or ask the worker to choose the next item.
