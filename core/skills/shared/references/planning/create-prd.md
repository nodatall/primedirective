# Rule: Generating the Product Requirements Document (PRD)

## Goal

Generate a required PRD that preserves and normalizes the product-facing substance of the planning input.

PRD is always required for planned work.

## When to run

Run this for every completed planning flow before TDD/task generation is finalized.

## Input

- `<plan-key>`
- source plan or source prompt
- locked decisions from Socratic refinement
- finalized plain-language summary

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `prd-<plan-key>.md`

## Required PRD structure

1. Title
2. Plain-Language Summary
3. Target User / Audience
4. Problem Statement
5. Current-State / Product Diagnosis
6. Product Goal
7. Success Criteria
8. Explicit Non-Goals
9. User Stories or Primary User Outcomes
10. Functional Requirements (`FR-*`)
11. Acceptance Criteria
12. Product Rules / UX Rules / Content Rules
13. Constraints and Defaults
14. Success Metrics / Guardrails

## Plain-Language Summary rules

- Must be understandable to a 12-year-old.
- Keep it concrete and plain.
- Use it to sanity-check that the document still matches the actual intent.
- Preserve the same core meaning as the Socratic plain-language summary.

## Mapping rules

If the source plan contains sections like these, preserve them in PRD under the closest matching headings:

- Target user / audience cues
- Problem framing or user pain
- Current-State Diagnosis
- Product Goal
- Success Criteria
- Explicit Non-Goals
- Frontend Page Spec
- Missing Data Rules
- User-facing behavior rules
- Acceptance Criteria

Do not drop product-facing detail just because the source heading name differs from the PRD heading name.

## Rules

1. Do not start implementation while creating PRD.
2. Keep PRD product-focused (`what` and `why`), but preserve detailed product constraints when they matter.
3. Use stable `FR-*` IDs for meaningful product requirements.
4. Map acceptance criteria back to the relevant `FR-*` requirements.
5. Convert unresolved ambiguity into explicit defaults before finalizing.
6. Do not include an `Open questions` section.
7. If source-plan content appears both product and technical, keep product intent in PRD and let TDD carry the technical realization.
8. Keep the section order stable so the plain-language summary is the first substantive section a human or agent reads.
9. Do not omit sections. If a section is truly not relevant, fill it with one explicit, concise note rather than leaving it out.

## Build gate reminder

Implementation starts only from:

- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]`
