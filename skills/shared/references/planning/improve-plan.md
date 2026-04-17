# Rule: Review and Improve the Normalized Plan

## Goal

Run a senior-engineering improvement pass after PRD, TDD, and tasks-plan are generated and before implementation starts.

Required planning artifacts:

- source plan or planning transcript
- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`
- `tasks/tmp/research-plan-<plan-key>.md` when `--deep-research --preserve-planning-artifacts` is used

This pass exists to strengthen the plan and to prove that normalization did not drop anything important.

## Core engineering principles

All improvements must align with these principles:

- Prefer clarity, explicitness, and maintainability over cleverness.
- Avoid under-engineering (fragile or ambiguous plans).
- Avoid over-engineering (premature abstraction or unnecessary indirection).
- Reduce meaningful duplication without abstracting too early.
- Handle edge cases conservatively where risk exists.
- Keep recommendations proportional to real impact.
- Preserve useful source-plan detail rather than compressing it away.

When multiple solutions are valid:

- Choose the simplest option that fully solves the problem.
- Favor lower cognitive load for implementers.
- Prefer predictable behavior over speculative flexibility.

## Review and improve in this order

### 1. Source-plan preservation review

Evaluate and improve:

- Whether the locked `Goal`, `Context`, `Constraints`, and `Done when` intake survived normalization.
- Whether any meaningful source-plan section was dropped.
- Whether product-facing sections landed in PRD.
- Whether technical sections landed in TDD.
- Whether execution sequencing and verification landed in tasks-plan.
- Whether any normalized heading weakened important specificity.

If any meaningful source content is missing, restore it before continuing.

### 2. PRD quality review

Evaluate and improve:

- Target user and problem statement clarity.
- Goal, success-criteria, and acceptance alignment.
- Completeness of non-goals, product rules, UX rules, and constraints.
- Usefulness of success metrics or guardrails.
- Quality and stability of `FR-*` requirements.
- Whether the PRD plain-language summary is clear enough for non-technical review.
- Whether the standalone three-paragraph summary checkpoint happened as a separate text-only turn before artifact generation started.

### 3. TDD quality review

Evaluate and improve:

- Scope alignment to PRD.
- Architecture clarity and interface boundaries.
- Clarity of system boundaries and source-of-truth ownership.
- Explicit dependencies that affect sequencing or integration behavior.
- Completeness of route/API/schema/storage changes.
- Quality and stability of `TDR-*` obligations.
- Presence of migration, rollout, backfill, rollback, and failure-mode detail when relevant.
- Presence of operational readiness detail when production behavior changes.
- Whether the TDD plain-language summary is clear enough for non-technical review.
- Whether the checkpoint summary meaning survived into both PRD and TDD without drift.
- Whether deep-research findings were reflected in the technical design when `--deep-research` was used.

### 4. Task-plan quality review

Evaluate and improve:

- Sequencing and dependency order.
- Actionability of each task and sub-task.
- Traceability from tasks to `FR-*` and `TDR-*`.
- Elimination of vague steps.
- Missing failure-path or cleanup work.
- Whether `output`, `verify`, and `done_when` are concrete enough for implementation.
- Whether each sub-task is narrow enough to support a pre-coding contract and a meaningful review pass without bundling unrelated work together.
- For frontend-facing work, whether tasks name the affected screens, states, and flows instead of leaving design intent implicit.

### 5. Premature specificity review

Evaluate and improve:

- Whether PRD or TDD invented exact APIs, schemas, classes, algorithms, routes, file names, helper boundaries, or test locations without support from source material or repo inspection.
- Whether task-plan `output` fields name precise files only when they are known or strongly supported.
- Whether unsupported technical specifics should be moved into assumptions, softened into high-level constraints, or deferred to `tasks/tmp/plan-task-<task-id>.md` during `$execute-task`.
- Whether the plan remains precise about behavior, constraints, source-of-truth decisions, and verification expectations after unsupported low-level detail is removed.

### 6. Verification coverage review

Evaluate and improve:

- Coverage of PRD acceptance criteria by TDD verification strategy.
- Coverage of TDD verification obligations by task `verify` steps.
- Regression protection for risky areas.
- Missing edge-case or negative-path checks.
- Gaps in migration/backfill/rollback validation.
- For frontend-facing work, whether browser-based verification covers the changed states, responsive breakpoints, and obvious visual regressions.

### 7. Research integration review

Evaluate and improve when `--deep-research` was used:

- Whether the deep-research pass actually met the evidence bar rather than stopping after a few searches.
- Whether the deep-research memo used live web research and included the required web-status section.
- Whether the deep-research memo captured the exact current date and used plan-specific stack and constraint framing rather than a generic research prompt.
- Whether the deep-research memo included at least 5 substantive external primary web sources.
- Whether substantive external sources included freshness metadata and were current enough for the claims they supported.
- Whether the deep-research pass reviewed the initial PRD/TDD drafts rather than researching in the abstract.
- Whether the selected design reflects the strongest research-backed recommendation.
- Whether the best ideas from the research memo were pulled back into PRD/TDD before tasks-plan generation.
- Whether source-backed risks, rollout work, or verification gaps were carried into TDD and tasks-plan.
- Whether the research stayed within `Tech + Delivery` scope unless the plan clearly required more.
- Whether PRD changed only where research affected product-facing constraints or defaults.
- Whether findings were clearly separated into adopt-now guidance, emerging trends, and avoid guidance where relevant.
- Whether the research produced a plan-specific checklist or implementation guidance section rather than only a raw source dump.
- Whether any cited sources were merely decorative rather than materially supporting the selected design.

## Required audit checks

The improved plan must explicitly satisfy all of these:

1. Nothing important from the source plan was dropped.
2. The locked `Goal`, `Context`, `Constraints`, and `Done when` intake remains explicit after normalization.
3. PRD and TDD boundaries are correct.
4. Every meaningful product requirement has an `FR-*` ID.
5. Every meaningful technical obligation has a `TDR-*` ID.
6. Every task or sub-task maps back to relevant `FR-*` and `TDR-*` IDs.
7. Test strategy covers the stated acceptance criteria.
8. Migration/backfill/rollback detail exists when relevant.
9. No final artifact contains `Open questions` or `Open technical questions`.
10. Plain-language summaries remain clear and faithful to the full plan.
11. PRD includes clear user/problem framing and success guardrails.
12. TDD makes dependencies, source of truth, and operational readiness explicit enough to guide execution and debugging.
13. Any `--deep-research` pass includes live web research, the external-source minimum, the required memo sections, and PRD/TDD revisions before tasks-plan generation.
14. Any `--deep-research` pass is explicitly date-anchored, source-freshness-aware, and scoped to the actual stack and constraints.
15. Any `--deep-research` pass leaves behind plan-specific checklist or implementation guidance in the memo before cleanup or preservation.
16. The user saw a separate three-paragraph plain-language checkpoint as a text-only turn before artifact drafting started.
17. Unsupported low-level implementation details were removed, softened, or explicitly deferred to the execution-time sub-task contract.

## For every issue identified

You must:

1. State the issue clearly.
2. Explain why it matters.
3. Consider multiple fixes internally.
4. Choose one best fix.
5. Explain why that fix is best.
6. Update the PRD, TDD, or tasks-plan accordingly.

Do not dump option menus on the user unless business intent is ambiguous.

If a `--deep-research` pass fails the mandatory web-backed evidence bar, or if PRD/TDD were not revised from the adopted findings before tasks-plan generation, do not improve around the gap. Treat the planning pass as incomplete and require the research step to be redone before execution begins.

## Escalation policy (rare)

Ask a clarifying question only when one is true:

- Product behavior would materially change.
- Business intent is ambiguous.
- Scope/contract changes would affect external stakeholders.

When escalation is required:

- Ask one clear business-language question.
- Avoid technical tradeoff detail unless requested.

## Output expectations

The improved plan must be:

- structured, detailed, and implementation-ready
- faithful to the source plan's substance
- explicit about assumptions and failure paths
- free of obvious over-engineering
- clear enough that coding can begin without guessing

## Execution trigger gate (hard stop)

After plan improvements are complete:

- Stop and wait for explicit execution trigger.
- Do not start implementation from planning review.

Accepted execution activations:

- `$execute-task` with a specific `<task-id>` and optional `<plan-key>` when it can be inferred from `/tasks/`
- `$execute-task --one-shot` with optional `<plan-key>` when it can be inferred from `/tasks/`
