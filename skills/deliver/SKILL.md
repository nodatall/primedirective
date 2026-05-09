---
name: deliver
description: Create or load one plain-language execution plan, refine it until no material backlog issues remain, ask the user to approve the readable plan, then execute it one item at a time with focused validation, useful commits, plan updates, and final review. Use when invoked with `$deliver`, or when the user wants lightweight planned execution without PRD/TDD/tasks-plan artifacts.
---

# Deliver Skill

Run lightweight planned execution from one readable plan document.

This skill is a separate workflow from `$plan-work`, `$plan-and-execute`, and `$execute-task`. Do not generate PRD, TDD, or full tasks-plan artifacts unless the user explicitly switches workflows.

Load these references before starting:

- `skills/shared/references/plain-language.md`
- `skills/shared/references/reasoning-budget.md`
- `skills/shared/references/analysis/verification-pivot.md`
- `skills/shared/references/review/review-protocol.md` before the final review

## Activation

Invoke explicitly with `$deliver`.

Examples:

- `$deliver` with a thread plan above it.
- `$deliver` followed by a rough checklist, bug list, repo review, research output, or product idea.
- `$deliver using tasks/execution-plan-startup-fixes.md` when a readable execution plan already exists.

## Artifacts

Use these files:

- Durable plan: `tasks/execution-plan-<plan-key>.md`
- Optional active-step note: `tasks/tmp/active-step-<plan-key>-<step>.md`
- Completed plan archive: `tasks/archive/<yyyy-mm-dd>-<plan-key>/execution-plan-<plan-key>.md`

The durable plan is for the user to read and edit. Keep it low-friction. Do not turn it into an audit log.

## Plan Format

Prefer this shape:

```md
# <Plan Name>

Goal: <one sentence>

Please review this before I start.
Tell me what is wrong, missing, or out of order.

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
- Do not add `Status`, `Result`, or `Commit` lines by default.
- Keep validation evidence and commit details in the final handoff or git history unless the evidence changes the plan.

## Workflow

1. Establish source material.
   - Use the current thread, pasted source, rough checklist, existing execution plan, repo review, research output, or user-provided plan path.
   - Inspect the target repo enough to avoid inventing a plan that ignores obvious local constraints.
   - Inspect `git status --short` before edits and do not overwrite unrelated changes.
2. Prepare the branch before writing plan or implementation files.
   - If currently on a non-base branch, stay on that branch.
   - If currently on `main`, `master`, or the resolved local base branch, create a new feature branch before writing the execution plan.
   - Name the branch from the plan key when obvious, such as `deliver/<plan-key>`, unless the repo's branch naming convention suggests a better local pattern.
   - If detached `HEAD`, stop and ask.
   - If unrelated or dangerous overlapping changes exist, stop and ask before carrying them onto the new branch.
3. Create or load the plain-language plan.
   - If no plan exists, write `tasks/execution-plan-<plan-key>.md`.
   - Preserve every concrete source item unless it is a duplicate, contradiction, or user-approved removal.
   - Phrase steps as user-readable outcomes or actions, not implementation jargon.
   - Keep future items readable rather than fully specified.
4. Refine the plan before user review.
   - Run at least one refinement round.
   - Continue while material backlog issues remain.
   - If a refinement round finds material issues or changes the plan, run another refinement round after those edits.
   - Stop only after a full post-edit refinement round finds no material backlog issues.
   - Stop after 8 rounds even if issues remain.
   - Use a fresh reviewer subagent when available; otherwise perform the reviewer pass in the main agent and record that no fresh reviewer was available.
   - The reviewer checks for missing source items, vague checkboxes, bad order, duplicate work, oversized steps, hidden dependencies, contradictions, and unclear next step.
   - Edit only the execution plan during refinement.
   - Do not create a refinement notes file or separate refinement markdown artifact.
   - If 8 rounds end with unresolved material issues, stop and show the exact blocker instead of starting implementation.
5. Ask for user review once.
   - Show the final readable plan or summarize it with the file path.
   - Ask: `Please review this before I start. Tell me what is wrong, missing, or out of order.`
   - Do not begin implementation until the user approves or corrects the plan.
   - If the user corrects the plan, update it and rerun refinement only if the correction introduces material backlog risk.
6. Execute one item at a time.
   - Choose the next unchecked item in plan order unless new evidence makes a different next item clearly better; update the plan first when order changes.
   - Create a tiny active-step note only when it helps execution. Keep it private and disposable.
   - Identify repo-local implementation and validation patterns before editing.
   - Use worker agents when useful and available for a bounded item; the orchestrator owns integration, validation, plan updates, and commits.
   - For tiny or tightly coupled items, implement in the main agent.
7. Verify each useful step.
   - Run the narrow check that proves the current item.
   - For UI, layout, styling, or rendered-content changes, inspect the affected UI when practical and capture visual evidence.
   - If a check fails, classify the failure layer before patching again.
   - If another patch would be a guess, use the verification pivot: add the smallest useful log, deterministic test, replay, or temporary probe under `/codex-scripts/`.
8. Commit useful completed work.
   - Commit each completed useful item or coherent group of tightly coupled items.
   - Do not commit unrelated user changes.
   - If a step produces no useful code/docs change, update the plan or handoff with the reason instead of creating an empty commit.
9. Update the plan after each item.
   - Check off completed items.
   - Split, reorder, add, remove, or clarify items when implementation evidence changes the right path.
   - Keep the plan readable. Do not add detailed logs, commit SHAs, or validation transcripts unless they are needed to understand the next step.
10. Continue until done or blocked.
   - Keep moving through unchecked items after each commit.
   - Stop only for a required user decision, a missing environment/service/credential, an unsafe/destructive action needing approval, an unresolved material plan contradiction, or a verification blocker.
11. Run final review before declaring completion.
   - Use a fresh final reviewer when available.
   - Review the diff against the execution plan, plan updates, and relevant validation evidence.
   - Fix in-scope material findings, rerun relevant checks, and update the plan before the final handoff.
12. Archive the execution plan after final review is complete.
   - Move `tasks/execution-plan-<plan-key>.md` to `tasks/archive/<yyyy-mm-dd>-<plan-key>/execution-plan-<plan-key>.md`.
   - Archive only after final review findings are dispositioned and any required remediation has been verified.
   - Leave the archived plan readable; do not rewrite it into an audit log during archive.
   - Remove disposable active-step temp files unless they are still needed to explain an unresolved blocker.

## Output

For the initial review gate:

- link the plan file
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
