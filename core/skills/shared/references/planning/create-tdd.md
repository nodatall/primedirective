# Rule: Generating the Technical Design Document (TDD)

## Goal

Generate a required TDD that preserves and normalizes the technical and implementation-facing substance of the planning input.

TDD is always required for planned work.

## When to run

Run this for every completed planning flow after PRD structure is locked and before tasks-plan finalization.

## Input

- `<plan-key>`
- `tasks/prd-<plan-key>.md`
- source plan or source prompt
- locked decisions from Socratic refinement
- deep-research findings when `--deep-research` is active
- finalized three-paragraph plain-language summary from the summary checkpoint

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tdd-<plan-key>.md`

## Required TDD structure

1. Title
2. Plain-Language Summary
3. Technical Summary
4. Scope Alignment to PRD
5. Current Technical Diagnosis
6. Architecture / Approach
7. System Boundaries / Source of Truth
8. Dependencies
9. Route / API / Public Interface Changes
10. Data Model / Schema / Storage Changes
11. Technical Requirements (`TDR-*`)
12. Ingestion / Backfill / Migration / Rollout Plan
13. Failure Modes / Recovery / Rollback
14. Operational Readiness
15. Verification and Test Strategy

## Plain-Language Summary rules

- Must be understandable to a 12-year-old.
- Explain the technical approach in concrete, plain language.
- Preserve the same core meaning as the Socratic plain-language summary.
- Use it to sanity-check that the design still matches the product intent.
- Keep the same three-paragraph structure unless a paragraph is genuinely empty after normalization.

## Mapping rules

If the source plan contains sections like these, preserve them in TDD under the closest matching headings:

- System boundaries or source-of-truth statements
- Dependencies on services, jobs, sources, flags, secrets, or rollout order
- Route and API Changes
- Public Interface / Type Changes
- Program Signal Schema Changes
- Data Source Plan
- Implementation Plan
- External Source Validation
- Migration, backfill, rollout, or rollback detail
- Test Cases and Scenarios with technical verification content

Do not collapse concrete interface, schema, migration, or verification detail into generic prose.

## Rules

1. Do not start implementation while creating TDD.
2. Keep TDD aligned with PRD scope and acceptance criteria.
3. Use stable `TDR-*` IDs for meaningful technical obligations.
4. Preserve interface examples and type-shape examples when they matter to implementation.
5. Convert unresolved ambiguity into explicit defaults before finalizing.
6. Do not include an `Open technical questions` section.
7. Ensure verification strategy is concrete enough to drive task `verify` steps later.
8. Keep the section order stable so the plain-language summary is the first substantive section a human or agent reads.
9. Do not omit sections. If a section is truly not relevant, fill it with one explicit, concise note rather than leaving it out.
10. If `--deep-research` is active, TDD is the primary home for research-backed technical recommendations and rationale.

## Build gate reminder

Implementation starts only from:

- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]`
