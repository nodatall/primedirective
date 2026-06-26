---
name: deliver
description: Manual `$deliver` workflow for readable execution plans, optional deep research, optional Pro analysis, user review, and approved implementation. `--fast` skips only the initial plan-review pause. Supports `--deep-research`, `--pro-analysis`, and `--fast`.
---

# Deliver Skill

Run lightweight planned execution from one readable Markdown plan document. The normal path is plan -> optional deep research -> optional Pro analysis -> refine -> user reviews the `.md` file -> approve -> implement. Fast mode skips only the initial user plan-review pause after refinement; it does not skip the written plan, research, Pro analysis, refinement, validation, final review, archive, commit, or finalization. Use draft mode only for explicit discussion/update requests.

This skill replaces the retired PRD/TDD/tasks-plan execution stack for new work. Do not generate PRD, TDD, or full tasks-plan artifacts for new `$deliver` plans.

Load references by path, not all up front:

- Always load `skills/shared/references/plain-language.md`, `skills/shared/references/reasoning-budget.md`, and `skills/shared/references/analysis/verification-pivot.md`.
- `skills/shared/references/architecture/architecture-guidance.md` when implementation work is boundary-affecting or `docs/ARCHITECTURE.md` exists
- `skills/plan-to-goal/SKILL.md` when the source is goal-shaped
- `skills/review-plan/SKILL.md` when the user asks for an adversarial plan review before implementation
- `skills/shared/references/planning/deep-research.md` when `--deep-research` is present
- `skills/shared/references/analysis/pro-browser-analysis.md` when `--pro-analysis` is present
- `skills/shared/references/review/review-protocol.md` before the final review
- `skills/shared/references/execution/finalization-gate.md` before any terminal handoff
- `skills/deliver/references/plan-format.md` when drafting or refining the plan
- `skills/deliver/references/worker-packet.md` before assigning a worker packet

## Activation

Invoke explicitly with `$deliver`, `$deliver refine`, `$deliver plan`, legacy `$deliver discuss`, or plain-language deliver requests such as `deliver`, `refine it`, `implement deliver`, `deliver this`, `start deliver`, or `continue deliver`.

Supported modifiers:

- `--deep-research`
- `--pro-analysis`
- `--fast`

Use one self-identifying document flow:

- `$deliver` creates or resumes a readable execution plan at `tasks/execution-plan-<plan-key>.md`, embeds the Deliver implementation instruction near the top, runs `--deep-research` immediately when present, runs `--pro-analysis` immediately when present, runs refinement immediately, then stops and asks the user to review the Markdown file before approving implementation unless `--fast` is present.
- `$deliver --fast` creates or resumes the same readable execution plan, runs the same research/Pro/refinement gates, treats the refined plan as approved scope, and continues directly to step 7 without the initial user plan-review pause.
- `$deliver refine`, `$deliver plan`, `refine it`, `turn this into a deliver plan`, or equivalent keeps the same checklist file, replaces any draft instruction with the Deliver implementation instruction, runs `--deep-research` immediately when present, runs `--pro-analysis` immediately when present, runs refinement, then stops and asks the user to review the Markdown file before approving implementation unless `--fast` is present.
- `$deliver discuss` is a legacy alias for the draft-update behavior. Do not prefer it or introduce it as a separate workflow.
- When the user later says `implement`, `implement the doc`, `implement this plan`, `go ahead`, or equivalent while the visible, attached, referenced, or active document is a Deliver execution plan, load this skill, load that exact plan, treat it as the approved scope, and start implementation at step 7. Continue through focused validation, final review, archive movement, commit, and the finalization gate before the final handoff.

Examples:

- `$deliver` with a thread plan above it.
- `$deliver discuss` when the user explicitly wants to talk through the work and keep a plain current draft as the conversation changes.
- `$deliver refine` or `$deliver plan` when the current draft is ready to tighten into a reviewable execution plan.
- `$deliver --pro-analysis` when a lightweight readable plan should immediately get ChatGPT Pro pressure before refinement and user review of the Markdown file.
- `$deliver --deep-research` when a readable execution plan needs a web-backed operator/current-practice research pass before refinement and user review of the Markdown file.
- `$deliver --deep-research --pro-analysis` when the research pass should complete first, adopted findings should be applied to the readable execution plan, and then ChatGPT Pro should pressure-test the researched plan before refinement.
- `$deliver --fast` when the user wants the plan written and refined but does not want to pause for manual review before implementation starts.
- `$deliver --pro-analysis --fast` when the Pro pass should run, adopted findings should be applied, refinement should finish, and implementation should start without the initial user plan-review pause.
- `$deliver --deep-research --pro-analysis --fast` when the deep research pass and Pro pass should both run before refinement and implementation should start without the initial user plan-review pause.
- `$deliver` followed by a rough checklist, bug list, repo review, research output, or product idea.
- `turn this into a deliver plan` after a `$deliver discuss` conversation has produced a draft checklist plan.
- `implement deliver` after a long planning discussion or after the user has reviewed a deliver-style checklist.
- `implement the doc` when the opened or referenced doc contains the Deliver implementation instruction.
- `$deliver using tasks/execution-plan-startup-fixes.md` when a readable execution plan already exists.

After `$deliver discuss` has created or loaded a draft execution plan in the thread, the draft workflow stays active until the user asks to refine it, cancels it, or explicitly switches workflows. Later planning messages update `tasks/execution-plan-<plan-key>.md` when they materially change the current plan. If the user says `refine it`, `turn this into a deliver plan`, `make the plan`, `$deliver`, `$deliver refine`, `$deliver plan`, or equivalent, keep the same checklist file, replace the draft instruction with the Deliver implementation instruction, run `--deep-research` immediately when present, run `--pro-analysis` immediately when present, refine it, and stop for the user to review the Markdown file before implementation unless `--fast` is present.

After `$deliver` has created or loaded an execution plan in the thread, the workflow stays active until final handoff, explicit cancellation, or an explicit workflow switch. Later user messages such as `implement`, `implement deliver`, `go ahead`, `start`, `continue`, `finish it`, `do it`, or `ship it` are approval/resume signals for the active `$deliver` plan even when `$deliver` is not repeated. Re-open the active `tasks/execution-plan-<plan-key>.md`, apply any correction, and resume this workflow instead of treating the message as generic implementation.

When a plan document contains the Deliver implementation instruction, that document is enough to route implementation back through this skill. Do not require the user to say `$deliver execute <plan-path>`. If the user asks to implement the document, load the document, scan every checkbox, and run the closeout path in this file. If the document is not already named `tasks/execution-plan-<plan-key>.md`, first import it into that canonical filename unless doing so would change scope.

## Artifacts

Use these files:

- Draft plan and durable plan: `tasks/execution-plan-<plan-key>.md`
- Optional frontend mockup: `tasks/ui-mockup-<plan-key>.html`
- Durable goal plan: `tasks/goal-plan-<plan-key>.md`
- Optional active-step note: `tasks/tmp/active-step-<plan-key>-<step>.md`
- Completed plan archive: `tasks/archive/<yyyy-mm-dd>-<plan-key>/execution-plan-<plan-key>.md`

The draft plan is for discussion. Keep it as plain as possible: short full sentences, concrete words, and only the structure needed to make the current plan easy to read. It is not approved implementation scope until it has been refined, carries the Deliver implementation instruction, and the user approves implementation.

The durable plan is for the user to read and edit. Keep it low-friction. Do not turn it into an audit log.

Use `tasks/goal-plan-<plan-key>.md` only through `$plan-to-goal`. A goal plan is a reviewable source-of-truth context file with an embedded copy-pasteable `Start Prompt` for `/goal`. It is not a normal execution checklist and should not be archived by the `$deliver` finalization gate unless the user explicitly converts it into a normal execution plan.

Non-canonical plan-like files such as `tasks/tasks-plan-<plan-key>.md`, `tasks/*-spec.md`, pasted checklists, and review notes are source material only for `$deliver`. Do not implement directly against them. If the user invokes deliver from one of those artifacts, import or convert the in-scope checklist into `tasks/execution-plan-<plan-key>.md` before implementation, then use that execution plan for unchecked-item scans, final review scope, archive movement, and finalization.

## Architecture Awareness

For boundary-affecting implementation work, compose `skills/shared/references/architecture/architecture-guidance.md`. If `docs/ARCHITECTURE.md` exists, read it before planning or coding and follow its module responsibilities, allowed dependencies, composition roots, shared-code rules, and testing boundaries. If the repo is non-trivial and the architecture doc is missing, create or update it with `$create-architecture` before making the boundary change unless the user asked for a small local fix inside one existing boundary. When intentionally changing a boundary, update `docs/ARCHITECTURE.md` in the same run.

## Plan Format

Use `skills/deliver/references/plan-format.md` for the full draft and refined execution-plan templates.

Draft plan rules:

- The draft plan is for discussion. Keep it as plain as possible.
- Every draft plan must include `Draft instruction:`.
- Every draft plan must include: `When asked to keep discussing or update this doc, load the `$deliver` skill and update this file as the current draft plan.`
- Every draft plan must include: `When asked to refine this, turn this into a deliver plan, or make the plan, load the `$deliver` skill, keep this same checklist file, replace this instruction with the Deliver implementation instruction, refine the plan, and ask for review before implementation.`
- Every draft plan must include: `Please review this before I refine it.`
- Use phases plus checkboxes from the start, even while the plan is still rough.
- Keep draft checkboxes concrete enough to discuss, but do not pretend every implementation detail is final.
- Do not add PRD, TDD, task-plan, status-log, audit-log, readiness, or topical section headers such as `The Problem`, `Current Best Plan`, `Decisions So Far`, or `Still Unclear`.
- Treat user removals as edits to the current plan, not as content to preserve. Delete removed items from the checklist and adjust the remaining items.
- Do not turn removed scope into repeated `do not...` reminders. If a rejected or out-of-scope idea must be retained to avoid reintroducing it, keep one concise decision note or checkbox and phrase the active plan positively.
- Write open questions as checkboxes, prefixed with `Open question:` when useful, so they are easy to resolve or remove during discussion.
- Do not refine, execute, or commit implementation work from the draft plan.

Refined execution-plan rules:

- Use phases plus checkboxes.
- Allow one level of checkboxes under a phase.
- Avoid checkboxes inside checkboxes.
- Add `Context`, phase `Goal`, or `Decision notes` only when they reduce confusion.
- Keep `Context` short. Use it for current-state facts, constraints, and settled decisions, not plan justification.
- Convert any supporting rationale into concrete decisions, constraints, or checks.
- Omit plan-justifying prose. The plan should say what to do, what is true now, and what must be checked, not argue that the approach is good.
- Add `Done when` only when the checkbox text is too vague to define completion.
- Every normal execution plan must include `Deliver implementation instruction:`.
- Include the exact Deliver implementation instruction near the top of every normal execution plan.
- In `--fast` mode, omit the normal initial review request and include a short `Fast mode note:` that says the initial plan-review pause was skipped by `--fast`.
- Do not add `Status`, `Result`, or `Commit` lines by default.
- Keep validation evidence and commit details in the final handoff or git history unless the evidence changes the plan.

Frontend plan mockup rules:

- When a `$deliver` plan touches a frontend component, rendered content, layout, styling, or an interaction flow, create a simple standalone HTML/CSS mockup at `tasks/ui-mockup-<plan-key>.html` before asking the user to approve the plan.
- Read `docs/DESIGN.md` first when it exists, and make the mockup reflect the current product style and expected changed state. The mockup is a visual intent artifact, not production source code.
- Keep the mockup lightweight: static HTML and CSS are enough unless a small inline script is needed to show an expected interaction state.
- Link the mockup from the execution plan with a short `Visual mockup:` note so the user can open it while reviewing the plan.
- If the expected visual result cannot be inferred without a product/design decision, add an `Open question:` checkbox instead of inventing the UI and stop before implementation.

## Goal Plan Delegation

Before drafting a normal execution plan, check whether the source is goal-shaped:

- The plan cannot honestly name the remaining implementation steps until after the next validation result.
- The work is inspect -> patch -> validate -> inspect again until confidence or a blocker.
- The success condition is proving a path works, exhausting a search space, improving coverage until recoverable options are exhausted, or diagnosing why repeated attempts still fail.
- The plan has a fixed holdout artifact, benchmark, comparator, baseline, ceiling, or target metric that should guide iterative work.

Even when the source sounds like an evidence loop, do not choose goal mode unless the agent can run multiple useful validation loops inside the goal. If the decisive evidence depends on a slow, paid, approval-gated, nightly, or externally scheduled run, write a normal execution plan that prepares the harness, cheap checks, smoke run, and human-approved decision run instead.

If the source is goal-shaped, use `$plan-to-goal` instead of writing a normal `$deliver` checklist. `$plan-to-goal` owns the `tasks/goal-plan-<plan-key>.md` format, embedded `Start Prompt`, target/baseline rules, state-recording guidance, and no-early-stop wording.

After `$plan-to-goal` writes the goal plan, stop for user review. Do not start normal `$deliver` implementation unless the user rejects goal mode or asks to convert it into an execution plan.

## Pro Analysis

When `--deep-research` is present, compose `skills/shared/references/planning/deep-research.md` after the readable execution plan exists and before any Pro analysis or refinement. Do not make the user approve an unresearched draft before the research pass.

Rules:

- Run local reconnaissance first and use the execution plan plus relevant repo context to frame current-state research.
- Write the working memo to `tasks/tmp/research-plan-<plan-key>.md`.
- Use live web research and the evidence bar from `skills/shared/references/planning/deep-research.md`.
- Reduce adopted findings into execution-plan changes before Pro analysis or refinement.
- Print a short `Deep Research Summary` before Pro analysis or refinement.
- Do not start Pro analysis, refinement, user review, or implementation if the research memo is missing, lacks the Deep Research Completion Stamp, leaves material adopted findings unapplied or undispositioned, or does not end with `evidence_bar_met: yes`.
- A short partial research pass is not a completed research gate and should not become a terminal user handoff. If the evidence bar is unmet only because the pass is incomplete, keep researching and repairing the memo until the gate passes. Stop only for a real blocker such as unavailable web access, unsafe context exposure, a required user decision, or the user explicitly dropping `--deep-research`.

When `--pro-analysis` is present, compose `skills/shared/references/analysis/pro-browser-analysis.md` after the readable execution plan exists and before the refinement loop. Do not make the user approve an unrefined draft before the Pro pass.

Rules:

- Run local reconnaissance first and use the plan plus relevant repo context to choose a Pro context bundle.
- Use the Chrome-backed visible ChatGPT browser-driver workflow from `skills/shared/references/analysis/pro-browser-analysis.md`, not the in-app Browser/standalone Playwright surface or a private browser profile.
- Write the synthesis memo to `tasks/tmp/pro-analysis-<plan-key>.md`.
- Reduce the Pro answer into a findings ledger with local verification/disposition for each material finding.
- Apply adopted findings directly into `tasks/execution-plan-<plan-key>.md` before refinement.
- Print a short `Pro Findings Summary` before refinement and user review.
- Do not start refinement, user review, or implementation if the Pro memo is missing, lacks browser evidence for a real Pro browser run, leaves material findings undispositioned, leaves adopted findings unapplied, or does not end with `pro_synthesis_complete: yes`.
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
   - If it is goal-shaped, load `skills/plan-to-goal/SKILL.md`, write `tasks/goal-plan-<plan-key>.md`, and stop after the goal-plan draft and `Start Prompt` are produced.
   - Do not execute a goal plan as a normal `$deliver` checklist.
   - If the user approves and explicitly asks to start the goal from this thread, start the goal using the prompt when goal mode is available; otherwise provide the exact `/goal` prompt from the file.
   - If the user says not to use goal mode, convert the source into a normal execution plan and continue with step 4.
3.5. Create or update the draft checklist plan only when the request is explicitly plan discussion.
   - Do not use this step for bare `$deliver`, `$deliver --deep-research`, `$deliver --pro-analysis`, `$deliver --fast`, `$deliver plan`, `$deliver refine`, `deliver this`, or equivalent requests; those continue to step 4 and run research/Pro/refinement in the same command.
   - Use `tasks/execution-plan-<plan-key>.md`.
   - If an older `tasks/planning-discussion-<plan-key>.md` exists and no matching execution plan exists, import its current in-scope content into `tasks/execution-plan-<plan-key>.md` and continue with the execution-plan file.
   - Keep the doc plain, current, and checklist-shaped, not fully specified.
   - Embed the draft instruction near the top so the document routes future discussion or refinement back through `$deliver`.
   - Record the plan so far as phases and unchecked checkboxes, including decisions, current constraints, likely work items, and open questions only when useful.
   - Shape broad work into high-level implementation slices in dependency order. Put contracts, types, validators, data shape, and other lower-level foundations before the concrete features, UI, integration, or polish that depend on them.
   - Record rejected ideas only when they are still useful to prevent accidental reintroduction.
   - When the user removes scope, delete or compress the old plan text instead of preserving it as negative instructions.
   - After updating the doc, stop with a short pointer to the file and continue the discussion. Do not run refinement and do not execute.
   - If the user asks to refine the draft into a deliver plan, keep the same `tasks/execution-plan-<plan-key>.md`, replace the draft instruction with the Deliver implementation instruction, and continue with step 4.25 when `--deep-research` is present, step 4.5 when `--pro-analysis` is present, or step 5 otherwise.
4. Create or load the plain-language plan.
   - If no plan exists, write `tasks/execution-plan-<plan-key>.md`.
   - Use the refined execution-plan format with the Deliver implementation instruction, not the draft instruction, unless step 3.5 explicitly selected draft discussion mode.
   - If the approved source is an older `tasks/planning-discussion-<plan-key>.md`, import its current in-scope plan, decisions, unresolved questions that still affect execution, and likely work items into `tasks/execution-plan-<plan-key>.md`.
   - Do not carry rejected or removed scope into execution-plan work items. Include rejected ideas only as concise decision notes when they are necessary to prevent accidental reintroduction.
   - If the latest approved source is a non-canonical plan-like file such as `tasks/tasks-plan-<plan-key>.md`, `tasks/*-spec.md`, a pasted checklist, or review notes, treat it as source material and convert the in-scope work into `tasks/execution-plan-<plan-key>.md` before implementation starts.
   - Do not continue into implementation with only a `tasks-plan`, spec, or notes file as the scope artifact.
   - If the user asked to implement a non-canonical plan-like document, import the in-scope content into `tasks/execution-plan-<plan-key>.md`, then continue as an implementation request unless the import exposed a scope contradiction.
   - Preserve every concrete source item unless it is a duplicate, contradiction, or user-approved removal.
   - Phrase steps as user-readable outcomes or actions, not implementation jargon.
   - Keep future items readable rather than fully specified.
   - Keep the main plan high level. Detailed files, tests, commands, and done conditions belong in the active-step packet when execution reaches that slice.
   - If the plan is frontend-facing, create or update `tasks/ui-mockup-<plan-key>.html` and link it from the execution plan before step 5.
4.25. If `--deep-research` is present, run deep research before Pro analysis or refinement.
   - Load `skills/shared/references/planning/deep-research.md`.
   - Use `tasks/execution-plan-<plan-key>.md` plus selected repo context as the research input.
   - Write and verify `tasks/tmp/research-plan-<plan-key>.md`.
   - Apply adopted research findings into the execution plan before step 4.5 or step 5.
   - Hard-stop before Pro analysis or refinement if the Deep Research Completion Stamp is incomplete or `evidence_bar_met: yes` is missing.
   - Do not hand that incomplete state back as completed planning. Continue the research pass unless there is a real blocker or the user explicitly drops `--deep-research`.
4.5. If `--pro-analysis` is present, run Pro analysis before refinement.
   - Load `skills/shared/references/analysis/pro-browser-analysis.md`.
   - Use `tasks/execution-plan-<plan-key>.md` plus selected repo context as the Pro input. If `--deep-research` is also present, include `tasks/tmp/research-plan-<plan-key>.md` in the Pro context bundle after the research gate is satisfied.
   - Write and verify `tasks/tmp/pro-analysis-<plan-key>.md`.
   - Apply adopted Pro findings into the execution plan before step 5.
   - Hard-stop before refinement if the Pro synthesis gate is incomplete.
5. Refine the plan before user review or fast-mode implementation.
   - Run at least one refinement round.
   - Continue while material backlog issues remain.
   - If a refinement round finds material issues or changes the plan, run another refinement round after those edits.
   - Stop only after a full post-edit refinement round finds no material backlog issues.
   - Stop after 8 rounds even if issues remain.
   - Use a fresh reviewer subagent by default when subagents are available.
   - Do not mention whether a subagent was or was not used in the user-facing review request unless it creates a real blocker or residual risk.
   - The reviewer checks for missing source items, vague checkboxes, bad order, duplicate work, oversized steps, hidden dependencies, contradictions, and unclear next step.
   - The reviewer also checks that the plan is sliced in dependency order without turning the main plan into a per-file implementation script.
   - Edit only the execution plan during refinement.
   - Do not create a refinement notes file or separate refinement markdown artifact.
   - If 8 rounds end with unresolved material issues, stop and show the exact blocker instead of starting implementation.
6. Stop for user review of the Markdown plan file unless `--fast` is present.
   - Do not launch a review app or external viewer.
   - Normal mode: link `tasks/execution-plan-<plan-key>.md` and ask the user to review the Markdown file.
   - Normal mode: ask the user to say `implement the doc` when it looks right, or tell you what is wrong, missing, or out of order.
   - `--fast` mode: do not ask for initial plan review. Treat the refined execution plan as approved scope and continue directly to step 7 after checking the fast-mode stop conditions below.
   - `--fast` mode must still stop for destructive or data-loss actions, missing credentials/env/service access, material scope ambiguity, billing/security/schema/API/product decisions, goal-plan delegation, incomplete `--deep-research`, incomplete `--pro-analysis`, unresolved material refinement issues, or any blocker that would make immediate implementation unsafe or dishonest.
   - If the user corrects the plan, update the same Markdown file and rerun refinement only if the correction introduces material backlog risk.
   - If this plan came from a draft Deliver plan, stop here even if the user asked to `deliver this`. In-place refinement only prepares the execution plan; implementation still requires a separate approval such as `implement the doc` unless the current refinement request includes `--fast`.
   - Normal mode: do not begin implementation until the user approves or corrects the plan.
   - If the user asks to review, pressure-test, or adversarially improve the plan before implementation, route that request through `$review-plan` and return here only after the review leaves the plan ready for approval.
   - Plan discussion does not clear `$deliver` activation. If the user approves after back-and-forth plan review, continue to step 7 for the active execution plan.
7. Execute one item at a time.
   - `implement the doc` or `--fast` mode starts here after loading the canonical execution plan and confirming the branch/finalization baseline from earlier steps is available or recapturing it if needed.
   - Choose the next unchecked item in plan order unless new evidence makes a different next item clearly better; update the plan first when order changes.
   - Create a tiny active-step note only when it helps execution. Keep it private and disposable.
   - Identify repo-local implementation and validation patterns before editing.
   - For each non-trivial implementation item, create an active-step packet.
   - Assign one worker agent by default when worker agents are available.
   - Do not run implementation workers in parallel. Parallelism is allowed only for read-only discovery or review lanes, such as `$repo-sweep --swarm`, or for a future workflow that explicitly isolates implementation workers with worktrees or equivalent disjoint checkouts.
   - Do not let the orchestrator absorb implementation by default. The orchestrator owns next-step selection, worker packet creation, integration, validation judgment, plan updates, and commits.
   - Give each worker a compact active-step packet, not the whole planning history.
   - When worker agents are unavailable, the orchestrator implements directly.
   - Do not mention whether worker agents were or were not used unless it creates a real blocker or residual risk.
8. Verify each useful step.
   - Run the narrow check that proves the current item.
   - For UI, layout, styling, or rendered-content changes, inspect the affected UI when practical and capture visual evidence.
   - If a check fails, classify the failure layer before patching again.
   - If another patch would be a guess, use the verification pivot: add the smallest useful log, deterministic test, replay, or temporary probe under `/agent-scratch/`.
9. Commit useful completed work.
   - Commit each completed useful item or coherent group of tightly coupled items.
   - Do not commit unrelated user changes.
   - If a step produces no useful code/docs change, update the plan or handoff with the reason instead of creating an empty commit.
10. Update the plan after each item.
   - Check off completed items.
   - Split, reorder, add, remove, or clarify items when implementation evidence changes the right path.
   - Write findings back into the plan only when they change a later slice, clarify a future decision, or prevent likely rework.
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
   - If `tasks/ui-mockup-<plan-key>.html` exists, move it to the same archive directory as `ui-mockup-<plan-key>.html` so the execution-plan link remains reviewable.
   - Archive only after final review findings are dispositioned and any required remediation has been verified.
   - Leave the archived plan readable; do not rewrite it into an audit log during archive.
   - Remove disposable active-step temp files unless they are still needed to explain an unresolved blocker.
   - Remove `tasks/tmp/review-plan-<plan-key>.md` when it records a completed `$review-plan` pass with no unresolved risk, unless the user requested preserved review artifacts.
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

For `--fast` mode:

- mention that the initial plan-review pause was skipped
- name the plan file before implementation starts when useful, but do not stop for review
- continue into step 7 unless a fast-mode stop condition applies

For the final handoff:

- name the archived plan file
- summarize completed items
- list commits created when relevant
- list validation commands or flows run
- mention final review result
- name any skipped checks, blockers, or residual risk

Do not claim the plan is complete until all in-scope checkboxes are done or explicitly deferred by the user, focused validation has run, and final review is complete.

## Worker Packet

Use worker agents by default for non-trivial implementation items when worker agents are available. Use `skills/deliver/references/worker-packet.md` for the full worker-packet template. Pass one bounded item with only the context needed to implement it correctly.

Do not run implementation workers in parallel. Parallelism is allowed only for read-only discovery or review lanes, such as `$repo-sweep --swarm`, or for a future workflow that explicitly isolates implementation workers with worktrees or equivalent disjoint checkouts.

The orchestrator keeps ownership of the full plan, next-step selection, worker packet creation, worker integration, final validation judgment, checkbox updates, commits, and plan changes. It should not hand a worker the whole backlog or ask the worker to choose the next item.
