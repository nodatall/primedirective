# Rule: Review and Improve the Normalized Plan

## Goal

Run a senior-engineering improvement pass after PRD, TDD, and tasks-plan are generated and before implementation starts.

Required planning artifacts:

- source plan or planning transcript
- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

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

### 4. Task-plan quality review

Evaluate and improve:

- Sequencing and dependency order.
- Actionability of each task and sub-task.
- Traceability from tasks to `FR-*` and `TDR-*`.
- Elimination of vague steps.
- Missing failure-path or cleanup work.
- Whether `output`, `verify`, and `done_when` are concrete enough for implementation.

### 5. Verification coverage review

Evaluate and improve:

- Coverage of PRD acceptance criteria by TDD verification strategy.
- Coverage of TDD verification obligations by task `verify` steps.
- Regression protection for risky areas.
- Missing edge-case or negative-path checks.
- Gaps in migration/backfill/rollback validation.

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

## For every issue identified

You must:

1. State the issue clearly.
2. Explain why it matters.
3. Consider multiple fixes internally.
4. Choose one best fix.
5. Explain why that fix is best.
6. Update the PRD, TDD, or tasks-plan accordingly.

Do not dump option menus on the user unless business intent is ambiguous.

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

Accepted build triggers:

- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]`
