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
- direct source interpretation and assumptions when `--direct` is active
- deep-research findings when `--deep-research` is active and available during finalization
- finalized three-paragraph plain-language summary from the summary checkpoint, or direct source interpretation and assumptions when `--direct` is active

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
- When `--direct` is active, preserve the same core meaning as the direct source interpretation.
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
- Core domain entities, stable identifiers, normalization rules, or shared vocabulary
- Lifecycle states, status transitions, retry/reconciliation behavior, or scheduling rules
- Typed error, blocker, timeout, approval, or recovery categories
- Config fields, defaults, environment indirection, reload behavior, or runtime preflight rules
- Safety invariants, trust boundaries, destructive-action limits, and secret-handling constraints
- Reference algorithms, pseudocode, or step-by-step runtime flows

Do not collapse concrete interface, schema, migration, or verification detail into generic prose.
When the plan involves agents, secrets, untrusted input, or outbound actions, make those constraints explicit in the existing `System Boundaries / Source of Truth`, `Failure Modes / Recovery / Rollback`, and `Operational Readiness` sections rather than inventing standalone security-only headings.

## Contract detail rules

`$plan-work` is normally used for serious, non-trivial work. Default to a spec-like technical contract in the TDD whenever the work has runtime behavior, integration behavior, persistence, orchestration, APIs, jobs, schedulers, agents, external tools, configuration, state transitions, concurrency, retries, reconciliation, cleanup, permissions, secrets, destructive actions, or security-sensitive behavior.

Do not create a large standalone spec section by default. Fold contract detail into the existing TDD headings:

- Put domain entities, stable identifiers, vocabulary, and normalization rules in `Architecture / Approach`, `System Boundaries / Source of Truth`, `Route / API / Public Interface Changes`, or `Data Model / Schema / Storage Changes`.
- Put ownership of mutable state, allowed writers, lifecycle states, transition triggers, concurrency rules, idempotency, and reconciliation in `System Boundaries / Source of Truth`, `Architecture / Approach`, or `Failure Modes / Recovery / Rollback`.
- Put config fields, defaults, env-var resolution, dynamic reload behavior, startup checks, and runtime preflight validation in `Dependencies`, `Operational Readiness`, or the relevant interface/config section.
- Put typed error classes, blocker reason codes, timeout handling, retry/backoff behavior, recovery paths, rollback behavior, and operator intervention points in `Failure Modes / Recovery / Rollback`.
- Put trust boundaries, approval/sandbox posture, filesystem/path invariants, secret handling, and destructive-action guardrails in `System Boundaries / Source of Truth`, `Operational Readiness`, and `Failure Modes / Recovery / Rollback`.
- Put reference algorithms or pseudocode only when prose would leave a multi-step runtime flow ambiguous; keep them compact and language-agnostic.
- Put conformance-style deterministic tests, extension/optional-feature tests, and real-integration smoke checks in `Verification and Test Strategy`.

If a contract detail category truly does not apply, compress it to one explicit sentence in the closest existing section instead of adding ceremonial headings.

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
16. When `--deep-research` is active, preserve compact durable research-backed rationale inside the relevant existing sections rather than adding a standalone research section. For each adopted technical recommendation that affects implementation, include:
   - the decision being adopted
   - why it matters to the plan
   - the supporting source IDs or links from the research memo
   - the affected `TDR-*` obligations
17. When `--deep-research` is active and the temporary memo will be cleaned up later, make the TDD durable enough that execution and review can still understand the adopted decision, source basis, implementation impact, and affected `TDR-*` without reopening the full memo.
18. When repo-local implementations or tests already provide a good pattern, name them in the relevant design sections so execution can follow an existing local convention.
19. When the plan breaks into executable slices, make clear which slices are expected to use a failing-test-first red/green loop and where a test-first exception is likely because the work is not practically testable first.
20. When the plan touches agents, secrets, untrusted input, or outbound actions, enrich `System Boundaries / Source of Truth`, `Failure Modes / Recovery / Rollback`, and `Operational Readiness` with the concrete trust and approval constraints that execution and review must enforce.
21. Do not add standalone `Security Trust Boundaries` or `Agent Safety Constraints` sections; enrich the existing section set only when those concerns are relevant.
22. When `--direct` is active, record concise assumptions in the relevant existing sections and defer unsupported exact implementation choices to `$execute-task` sub-task contracts.
23. If the source plan contains a full implementation checklist, map each checklist item to a concrete technical requirement, explicit non-goal, or user-approved deferral. A technical design may sequence the work, but it may not redefine a requested shipped capability as a placeholder, interface, diagnostic, or later roadmap item.
24. Before finalizing the TDD, perform a contract completeness check: every important entity, state, transition, config/default, invariant, failure class, recovery path, and verification profile that affects implementation must either be documented in the TDD, explicitly marked not applicable, or deferred with a reason to the `$execute-task` sub-task contract.
25. Prefer normative wording for true implementation obligations (`must`, `must not`, `required`) and softer wording for recommendations or implementation choices (`should`, `may`, `implementation-defined`). Do not use normative wording for guesses that lack source-plan or repo evidence.

## Build gate reminder

Implementation starts only from:

- explicit `$execute-task` activation with a specific `<task-id>` and optional `<plan-key>` when it can be inferred from `/tasks/`
- explicit `$execute-task --one-shot` activation with optional `<plan-key>` when it can be inferred from `/tasks/`
