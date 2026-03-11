# Rule: Deep Research for Planning

## Goal

Run a focused pre-draft research pass when the planning trigger includes `--deep-research`.

This pass exists to strengthen the technical design before PRD, TDD, and tasks-plan are generated. It should reduce avoidable implementation mistakes, missing rollout work, and weak verification strategy.

This mode is not satisfied by a token burst of a few searches. Treat `--deep-research` as a substantial research pass with a real evidence bar before planning artifacts may be drafted.

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
3. Write a short research agenda first:
   - the main technical questions to answer
   - the highest-risk unknowns
   - which research buckets apply to this plan
4. Create a temporary working memo at `tasks/tmp/research-plan-<plan-key>.md` while the research pass is in progress.
5. Research in multiple passes, not one search burst:
   - first pass: official docs and primary references for the core stack or provider
   - second pass: operational constraints, failure modes, limits, rollout, and verification guidance
   - third pass: any plan-specific edge areas uncovered by the first two passes
6. Prefer primary sources for technical claims:
   - official documentation
   - vendor documentation
   - standards or specifications
   - primary technical references
7. Use live web research when available and relevant.
8. If live web research is unavailable, fall back to repo context and prior technical knowledge, and state that limitation explicitly.
9. Keep the effort bounded to a deep pass, targeting roughly 20-30 minutes of research effort, and do not treat the pass as complete until the completion checks below are met.
10. If research would materially change product behavior, external scope, or business intent, stop and ask one targeted follow-up question before finalizing artifacts.

## Minimum evidence bar

Before deep research may be considered complete, gather and record:

- at least 5 substantive source reviews, with primary sources making up the majority whenever available
- at least 3 distinct research questions answered for this plan
- at least 4 applicable buckets reviewed from the default scope, unless the plan is genuinely too narrow for that many
- at least 2 rounds of follow-up research after the initial source pass
- explicit notes on at least 3 design-impacting findings, not just links

If the plan is narrow enough that one of these minimums is not reasonable, state why in the memo instead of silently doing less work.

## Research buckets

Cover all applicable buckets below, not just the easiest one:

- core technical approach and architecture patterns
- APIs, interfaces, schemas, storage, or SDK constraints
- limits, quotas, performance, concurrency, or cost constraints
- migration, rollout, rollback, backfill, or recovery behavior
- security, privacy, secrets, auth, or operational readiness
- testing, verification, observability, and failure handling

## Working memo contract

The temporary research memo must contain:

- research agenda
- sources reviewed
- findings by bucket
- design decisions or defaults changed by research
- risks or unknowns that remain
- explicit note when a bucket was not applicable

Do not start PRD, TDD, or tasks-plan drafting until this memo is substantively complete.

## Research output

Capture these outcomes:

- a short research summary
- concrete recommendations adopted into the plan
- alternatives considered and rejected when they materially affect the design
- risks, constraints, or follow-up validation uncovered by research
- source links or citations supporting the adopted recommendations

Default behavior:

- inline the findings into the TDD and improve-plan pass
- delete the standalone research memo after planning completes

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
5. The working memo meets the minimum evidence bar or explicitly explains why a lower bar was appropriate for this plan.
6. PRD, TDD, and tasks-plan drafting has not started before the research memo was completed.
