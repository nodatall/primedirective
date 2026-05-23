# Deliver Plan Format

Use this reference when drafting or refining a `$deliver` execution plan.

## Draft Plan

For a draft plan, use this checklist shape from the start:

```md
# <Plan Name>

This is a draft Deliver plan.
It is not approved for implementation yet.

Draft instruction:
When asked to keep discussing or update this doc, load the `$deliver` skill and update this file as the current draft plan.
When asked to refine this, turn this into a deliver plan, or make the plan, load the `$deliver` skill, keep this same checklist file, replace this instruction with the Deliver implementation instruction, refine the plan, and ask for review before implementation.

Please review this before I refine it.
Tell me what is wrong, missing, or out of order.

## Steps

### 1. <Plain-language phase>

- [ ] <Likely work item, phrased positively.>
- [ ] <Another current plan item.>
- [ ] Open question: <Question, risk, or missing fact, only when useful.>

### 2. <Next phase>

- [ ] <Likely work item.>
```

Draft plan rules:

- Write for fast human reading.
- Use short full sentences and concrete words.
- Avoid implementation jargon unless it is the clearest word; define it in plain language when needed.
- Use phases plus checkboxes from the start, even while the plan is still rough.
- Keep draft checkboxes concrete enough to discuss, but do not pretend every implementation detail is final.
- Do not add PRD, TDD, task-plan, status-log, audit-log, readiness, or topical section headers such as `The Problem`, `Current Best Plan`, `Decisions So Far`, or `Still Unclear`.
- Update the doc after meaningful discussion changes the current plan, a decision is made, an option is rejected, or a blocker becomes clear.
- Treat user removals as edits to the current plan, not as content to preserve. Delete removed items from the checklist and adjust the remaining items.
- Do not turn removed scope into repeated `do not...` reminders. If a rejected or out-of-scope idea must be retained to avoid reintroducing it, keep one concise decision note or checkbox and phrase the active plan positively.
- Keep the draft checkboxes focused only on what the user currently wants to do.
- Write open questions as checkboxes, prefixed with `Open question:` when useful, so they are easy to resolve or remove during discussion.
- Keep the draft instruction near the top until the user asks to refine the draft.
- Do not refine, execute, or commit implementation work from the draft plan.
- When refining, keep this same `tasks/execution-plan-<plan-key>.md` file, replace the draft instruction with the Deliver implementation instruction, and tighten the checklist before implementation can start.

## Refined Execution Plan

For a refined execution plan, prefer this shape:

```md
# <Plan Name>

Goal: <one sentence>

Please review this in Roughdraft before I start.
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
- Ask for review with `Please review this in Roughdraft before I start.` before the plan is opened in Roughdraft.
- Do not add `Status`, `Result`, or `Commit` lines by default.
- Keep validation evidence and commit details in the final handoff or git history unless the evidence changes the plan.
