# Deliver Plan Format

Read this before drafting or refining a `$deliver` plan.

## Refined Execution Plan

Apply `skills/shared/references/plain-language.md`, the same writing rules used by `$plain-language`, to the entire plan. The Plain-Language Review below is required before the plan is ready for approval or `--fast` implementation.

Default to the shortest sufficient plan: one sentence for the goal, only necessary decisions or constraints, and a few steps with clear outcomes and checks. Use this shape; omit optional sections that add no necessary information:

```md
# <Plan Name>

Goal: <one sentence>

## Steps

### 1. <Plain-language phase>

- [ ] <work item>
- [ ] <work item>

### 2. <Next phase>

- [ ] <work item and its success check>

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.
```

Keep the refined plan executable and easy to review:

- Use phases and one checkbox level. Do not nest checkboxes.
- Keep only the work the user currently wants. Delete removed scope. If a rejected idea must remain to prevent its return, keep one short, positive decision note.
- Add `Context`, a phase `Goal`, or `Decision notes` only when it reduces confusion.
- Use a short descriptive section for essential selection rules or constraints when that is clearer than `Context`. Link the frontend mockup when required below.
- Keep `Context` to current facts, constraints, and settled decisions. Do not use it to justify the plan.
- Turn useful rationale into a decision, constraint, or check. Remove plan-justifying prose.
- Do not put planning work inside a refined execution plan. Record the chosen contract, shape, policy, acceptance criteria, and any remaining explicit `Open question:` before implementation.
- Do not disguise missing decisions as work items such as `Define...`, `Decide...`, `Determine...`, `Plan...`, `Figure out...`, or `Clarify...` unless the deliverable is itself a planning artifact.
- If a decision would change implementation, write it as an `Open question:` checkbox and stop for review. Otherwise record the settled decision and make the checkbox implement it.
- Implementation-changing open questions block implementation. List them in the review handoff and say they must be resolved or explicitly deferred.
- Add `Done when` only when the checkbox is otherwise too vague.
- Put the exact `Deliver implementation instruction:` and its sentence at the very bottom of the document.
- Keep the review request in the chat handoff, not in the plan. Do not add "Please review this before I start" or "Tell me what is wrong, missing, or out of order" to the file.
- Do not add checkboxes for routine Deliver refinement, final review, archive movement, commits, or finalization. The footer and skill already require them; retain task-specific validation and delivery requirements.
- Do not add `Status`, `Result`, or `Commit` lines by default.
- Keep validation transcripts and commit details in the final handoff or git history unless they change later work.

The user reviews the Markdown file directly; do not open a separate review app. For `--fast`, mention the skipped initial review pause in chat; do not add mode boilerplate to the file.

## Linked Implementation Notes

When research, investigation, or an earlier plan contains useful implementation details, preserve them before shortening the plan. Create `tasks/implementation-notes-<plan-key>.md` and link it near the goal with `Implementation notes: [implementation-notes-<plan-key>.md](implementation-notes-<plan-key>.md)`. Reuse and link an existing authoritative guide when it already preserves the details; do not create a duplicate. No companion is needed when there are no useful technical findings to retain.

- Save the relevant API requests, field mappings, calculations, repo findings, pitfalls, and validation examples already established. Keep source links, the date checked, and whether each finding was documented, locally verified, or still needs a live check. Do not rely only on chat history, temporary memos, or attachments for details needed later.
- The execution plan controls scope. Keep essential decisions, output locations, limits, acceptance criteria, stop conditions, and implementation-changing open questions visible there. Notes explain how to implement that scope; they must not add hidden work or turn an unresolved decision into a settled requirement.
- Keep notes focused on useful findings. Delete filler and duplication rather than moving them into another file. Do not invent implementation detail just to fill a companion.
- On resume, read the linked notes before repeating discovery. Recheck findings when their age, uncertainty, or conflicting evidence makes that necessary. If required local notes are missing, recover them from available sources or report the missing reference before relying on them.

## Plain-Language Review

Read the whole plan from the user's perspective before passing refinement:

- Run a cut pass on every draft and refinement, including additions from research or review. Preserve useful researched implementation details in linked notes before removing them from the plan. Delete repetition, optional features the user did not request, rationale that changes no decision, and speculative implementation detail that can wait for the worker packet. Keep a plan sentence only when removing it would change approved scope, a necessary decision or constraint, execution order, or proof of success. Delete filler rather than relocating it.
- The goal and steps must explain what will change, what each step accomplishes, and how success will be checked without requiring the user to decode implementation terminology. Apply the shared plain-language rules to headings, context, decision notes, and checkboxes alike.
- Give each checkbox one understandable outcome. Split items that bundle separate outcomes; avoid replacing a dense paragraph with a long list of unexplained technical labels.
- Keep scope, settled decisions, exact limits, acceptance criteria, stop conditions, and implementation-changing `Open question:` items visible in plain words. Simplifying must not delete, weaken, or postpone them.
- Do not add a technical appendix by default. Keep technical detail in the main plan only when needed to approve the work or preserve a requirement that cannot be stated briefly. Use the linked implementation notes for researched mechanics and carry the relevant sections into the worker packet during implementation. Do not invent a specification, exhaustive edge-case list, or file-by-file script during planning.
- Keep each requirement in one place; use short references where later steps depend on it. Supporting detail should add implementation mechanics, not repeat the main plan.
- Check that linked implementation notes retain useful source findings, resolve from the plan, and agree with its scope. Review additions to the notes alongside plan changes; a short plan must not hide lost research or new requirements.
- Flag unnecessary length, unexplained necessary terms, paragraphs that mix many decisions, and steps whose purpose is unclear as material readability issues. Rewrite the affected text and reread the whole plan. Cosmetic preferences alone do not require another round.

Scale length to necessary scope, not a fixed word count. When the user asks for a specific reduction, meet it without dropping required content; surface a conflict if both cannot be satisfied.

Do not add a readability report, score, or completion stamp to the plan. The revised plan itself must pass this review.

## Frontend Mockup

For frontend components, rendered content, layout, styling, or interaction flows:

- Read `docs/DESIGN.md` when it exists.
- Before asking for approval, create `tasks/ui-mockup-<plan-key>.html` as a small standalone HTML/CSS mockup that matches the current product style. Use a small inline script only when an interaction state needs it.
- Link it with `Visual mockup: [ui-mockup-<plan-key>.html](ui-mockup-<plan-key>.html)`.
- Treat it as visual intent, not production code or a replacement for browser verification after implementation.
- If it exposes an unresolved design or product decision, add an `Open question:` checkbox and stop before implementation.
