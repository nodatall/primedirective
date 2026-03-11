# Rule: Deep Research for Planning

## Goal

Run a focused pre-draft research pass when the planning trigger includes `--deep-research`.

This pass exists to strengthen the technical design before PRD, TDD, and tasks-plan are generated. It should reduce avoidable implementation mistakes, missing rollout work, and weak verification strategy.

## Accepted trigger suffixes

- `--deep-research`
- `--preserve-planning-artifacts`

Planning trigger form:

- `start planning "<plan-from-llm>" [--deep-research] [--preserve-planning-artifacts]`

## When to run

Run this only after Socratic refinement has locked:

- `Goal`
- `Context`
- `Constraints`
- `Done when`

Run it before generating:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

## Default research scope

Deep research defaults to `Tech + Delivery`, not broad product discovery.

Cover these areas when relevant:

- technical design and architecture patterns
- route, API, interface, schema, and storage best practices
- migration, backfill, rollout, rollback, and recovery concerns
- security, operational readiness, and dependency concerns
- verification strategy, edge cases, and regression protection

Do not expand into broad market research or product discovery unless the source plan clearly depends on it.

## Research process

1. Start from the locked planning decisions, not from a blank prompt.
2. Identify the highest-risk technical and delivery questions that could change implementation quality or sequencing.
3. Prefer primary sources for technical claims:
   - official documentation
   - vendor documentation
   - standards or specifications
   - primary technical references
4. Use live web research when available and relevant.
5. If live web research is unavailable, fall back to repo context and prior technical knowledge, and state that limitation explicitly.
6. Keep the effort bounded to a deep pass, targeting roughly 30 minutes of research effort.
7. If research would materially change product behavior, external scope, or business intent, stop and ask one targeted follow-up question before finalizing artifacts.

## Research output

Capture these outcomes:

- a short research summary
- concrete recommendations adopted into the plan
- alternatives considered and rejected when they materially affect the design
- risks, constraints, or follow-up validation uncovered by research
- source links or citations supporting the adopted recommendations

Default behavior:

- inline the findings into the TDD and improve-plan pass
- do not keep a standalone research artifact after planning completes

Preservation behavior:

- if `--preserve-planning-artifacts` is present, keep `tasks/tmp/research-plan-<plan-key>.md`
- mention the preserved artifact path in the final planning summary

## Document boundary rules

- PRD: update only when research changes product-facing constraints, defaults, guardrails, or acceptance behavior
- TDD: absorb the detailed technical recommendations and rationale
- tasks-plan: add any new rollout, migration, verification, cleanup, or sequencing work discovered by research

## Completion checks

Before continuing to document generation:

1. The research has answered the most important technical and delivery questions for this plan.
2. The selected approach is supported by cited sources or explicitly labeled as an internal default when sources are unavailable.
3. Any new risks or sequencing requirements are ready to be reflected in TDD and tasks-plan.
4. The research did not silently widen scope into broad product discovery.
