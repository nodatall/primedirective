# Deliver Plan Format

Read this before drafting or refining a `$deliver` plan.

## Draft Plan

Use this shape:

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

Keep the draft easy to change and fast to read:

- Use short, concrete sentences. Define any necessary jargon.
- Use phases and checkboxes from the start, but do not pretend every detail is settled.
- Use `Open question:` checkboxes only when useful.
- Keep only the work the user currently wants. Delete removed scope. If a rejected idea must remain to prevent its return, keep one short, positive decision note.
- Avoid PRD, TDD, task-plan, status-log, audit-log, readiness, and essay headings such as `The Problem`, `Current Best Plan`, `Decisions So Far`, or `Still Unclear`.
- Keep the exact draft instruction near the top.
- Update the same `tasks/execution-plan-<plan-key>.md` when discussion changes the plan.
- Do not refine, implement, or commit from the draft.

When the user asks to refine it, keep the same file and replace the draft instruction with the exact implementation instruction below.

## Refined Execution Plan

Use this shape:

```md
# <Plan Name>

Goal: <one sentence>

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## Context

- <Only include current-state facts, constraints, or settled decisions that help implementation.>

Visual mockup: <relative link to `ui-mockup-<plan-key>.html` when this plan is frontend-facing.>

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

Keep the refined plan executable and easy to review:

- Use phases and one checkbox level. Do not nest checkboxes.
- Add `Context`, a phase `Goal`, or `Decision notes` only when it reduces confusion.
- Keep `Context` to current facts, constraints, and settled decisions. Do not use it to justify the plan.
- Turn useful rationale into a decision, constraint, or check. Remove plan-justifying prose.
- Do not put planning work inside a refined execution plan. Record the chosen contract, shape, policy, acceptance criteria, and any remaining explicit `Open question:` before implementation.
- Do not disguise missing decisions as work items such as `Define...`, `Decide...`, `Determine...`, `Plan...`, `Figure out...`, or `Clarify...` unless the deliverable is itself a planning artifact.
- If a decision would change implementation, write it as an `Open question:` checkbox and stop for review. Otherwise record the settled decision and make the checkbox implement it.
- Implementation-changing open questions block implementation. List them in the review handoff and say they must be resolved or explicitly deferred.
- Add `Done when` only when the checkbox is otherwise too vague.
- Keep the exact `Deliver implementation instruction:` near the top.
- Do not add `Status`, `Result`, or `Commit` lines by default.
- Keep validation transcripts and commit details in the final handoff or git history unless they change later work.

Normal mode uses the review request shown above. The user reviews the Markdown file directly; do not open a separate review app.

For `--fast`, remove the two review-request lines and add:

`Fast mode note: Initial plan-review pause skipped by --fast; continue into implementation after refinement unless a fast-mode stop condition applies.`

## Frontend Mockup

For frontend components, rendered content, layout, styling, or interaction flows:

- Read `docs/DESIGN.md` when it exists.
- Before asking for approval, create `tasks/ui-mockup-<plan-key>.html` as a small standalone HTML/CSS mockup that matches the current product style. Use a small inline script only when an interaction state needs it.
- Link it with `Visual mockup: [ui-mockup-<plan-key>.html](ui-mockup-<plan-key>.html)`.
- Treat it as visual intent, not production code or a replacement for browser verification after implementation.
- If it exposes an unresolved design or product decision, add an `Open question:` checkbox and stop before implementation.
