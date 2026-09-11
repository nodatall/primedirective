# Deliver Plan Format

Read this before drafting or refining a `$deliver` plan.

## Refined Execution Plan

Apply `skills/shared/references/plain-language.md`, the same writing rules used by `$plain-language`, to the entire plan. The Plain-Language Review below is required before the plan is ready for approval or `--fast` implementation.

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
- Keep only the work the user currently wants. Delete removed scope. If a rejected idea must remain to prevent its return, keep one short, positive decision note.
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

## Plain-Language Review

Read the whole plan from the user's perspective before passing refinement:

- The goal and steps must explain what will change, what each step accomplishes, and how success will be checked without requiring the user to decode implementation terminology. Apply the shared plain-language rules to headings, context, decision notes, and checkboxes alike.
- Give each checkbox one understandable outcome. Split items that bundle separate outcomes; avoid replacing a dense paragraph with a long list of unexplained technical labels.
- Keep scope, settled decisions, exact limits, acceptance criteria, stop conditions, and implementation-changing `Open question:` items visible in plain words. Simplifying must not delete, weaken, or postpone them.
- Keep file-by-file instructions, commands, algorithms, and detailed test cases out of the main review path unless the user needs them to make a decision. Preserve already-settled technical detail in existing linked supporting material or a clearly labeled technical appendix after the steps, then carry it into the active-step packet when implementation starts. The main plan must remain understandable without opening that detail.
- Keep each requirement in one place; use short references where later steps depend on it. Supporting detail should add implementation mechanics, not repeat the main plan.
- Flag unexplained necessary terms, paragraphs that mix many decisions, and steps whose purpose is unclear as material readability issues. Rewrite the affected text and reread the whole plan. Cosmetic preferences alone do not require another round.

Do not add a readability report, score, or completion stamp to the plan. The revised plan itself must pass this review.

## Frontend Mockup

For frontend components, rendered content, layout, styling, or interaction flows:

- Read `docs/DESIGN.md` when it exists.
- Before asking for approval, create `tasks/ui-mockup-<plan-key>.html` as a small standalone HTML/CSS mockup that matches the current product style. Use a small inline script only when an interaction state needs it.
- Link it with `Visual mockup: [ui-mockup-<plan-key>.html](ui-mockup-<plan-key>.html)`.
- Treat it as visual intent, not production code or a replacement for browser verification after implementation.
- If it exposes an unresolved design or product decision, add an `Open question:` checkbox and stop before implementation.
