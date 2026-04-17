# Rule: Generating the Technical Design Document (TDD)

## Goal

Generate a required TDD that preserves and normalizes the technical and implementation-facing substance of the planning input.

TDD is always required for planned work.

## When to run

Run this for every completed planning flow after PRD structure is locked. When `--deep-research` is active, generate the initial TDD before the research pass, then revise it with the adopted research-backed technical recommendations before tasks-plan finalization.

## Input

- `<plan-key>`
- `tasks/prd-<plan-key>.md`
- source plan or source prompt
- locked decisions from Socratic refinement
- deep-research findings when `--deep-research` is active and available during finalization
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
- Existing repo validation/tooling inventory and gaps

Do not collapse concrete interface, schema, migration, or verification detail into generic prose.
When the plan involves agents, secrets, untrusted input, or outbound actions, make those constraints explicit in the existing `System Boundaries / Source of Truth`, `Failure Modes / Recovery / Rollback`, and `Operational Readiness` sections rather than inventing standalone security-only headings.

## Rules

1. Do not start implementation while creating TDD.
2. Keep TDD aligned with PRD scope and acceptance criteria.
3. Use stable `TDR-*` IDs for meaningful technical obligations.
4. Preserve interface examples and type-shape examples when they matter to implementation.
   - Preserve exact technical detail when it comes from source material or repo inspection.
   - Do not invent exact APIs, schemas, classes, algorithms, routes, file names, or helper boundaries to fill gaps.
   - Mark plausible but unproven technical direction as an assumption or defer it to the `$execute-task` per-sub-task contract.
5. Convert unresolved ambiguity into explicit defaults before finalizing.
6. Do not include an `Open technical questions` section.
7. Ensure verification strategy is concrete enough to drive task `verify` steps later.
8. In `Current Technical Diagnosis`, record the repo's current validation surface and notable gaps: lint, format, typecheck, test, build, CI, and git hooks, as applicable to the stack.
9. In `Verification and Test Strategy`, name the concrete repo commands or workflows expected to enforce the work. If those commands do not exist yet, say so explicitly and describe the bootstrap that must land first.
10. Treat local git-hook integration as optional and stack-specific, not a required outcome. If the repo already has another hook mechanism or CI is the right enforcement path, design around that instead of forcing a new hook layer in.
11. When missing validation tooling is in scope, describe the config files, scripts, CI wiring, and developer workflow impact needed to make those checks real.
12. Keep the section order stable so the plain-language summary is the first substantive section a human or agent reads.
13. Do not omit sections. If a section is truly not relevant, fill it with one explicit, concise note rather than leaving it out.
14. If `--deep-research` is active, TDD is the primary home for research-backed technical recommendations and rationale.
15. When `--deep-research` is active, treat the first TDD draft as a staging artifact for research review, then update it with the adopted findings before tasks-plan generation.
16. When repo-local implementations or tests already provide a good pattern, name them in the relevant design sections so execution can follow an existing local convention.
17. When the plan breaks into executable slices, make clear which slices are expected to use a failing-test-first red/green loop and where a test-first exception is likely because the work is not practically testable first.
18. When the plan touches agents, secrets, untrusted input, or outbound actions, enrich `System Boundaries / Source of Truth`, `Failure Modes / Recovery / Rollback`, and `Operational Readiness` with the concrete trust and approval constraints that execution and review must enforce.
19. Do not add standalone `Security Trust Boundaries` or `Agent Safety Constraints` sections; enrich the existing section set only when those concerns are relevant.

## Build gate reminder

Implementation starts only from:

- explicit `$execute-task` activation with a specific `<task-id>` and optional `<plan-key>` when it can be inferred from `/tasks/`
- explicit `$execute-task --one-shot` activation with optional `<plan-key>` when it can be inferred from `/tasks/`
