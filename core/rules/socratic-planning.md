---
description:
globs:
alwaysApply: false
---
# Rule: Socratic Planning System (Repo-Agnostic, Standalone Handoff)

## Goal

Run a mandatory decision-clarification workflow before PRD/TDD/task generation so implementation can start without guessing.

This is a **process gate**

## Start Trigger

Accepted command:

`start planning for <feature-name>`

Optional payload:

- `goal: ...`
- `constraints: ...`
- `must-have: ...`
- `out-of-scope: ...`

## Output Files

Store generated planning artifacts in `/tasks/`:

- `socratic-<feature>.md`
- `decision-log-<feature>.md`
- `prd-<feature>.md`
- `tdd-<feature>.md`
- `tasks-prd-<feature>.md`

## Phase 1: Socratic Rounds (Mandatory)

Run micro-rounds with **1-3 high-impact questions per round**.

Each round must include:

- Questions asked
- User answers
- Locked decisions
- Remaining unknowns
- Plain-language recap (short)

Persist round history in `socratic-<feature>.md` using this schema:

- `round`
- `questions`
- `answers`
- `locked_decisions`
- `remaining_unknowns`
- `plain_recap`

Maintain `decision-log-<feature>.md` with this schema:

- `id`
- `decision`
- `reason`
- `alternatives`
- `impact`

### Required Socratic Sequence (in order)

1. Problem clarity: exact user problem being solved.
2. Success clarity: measurable done outcomes.
3. Scope clarity: in-scope vs out-of-scope.
4. Constraint clarity: legal/compliance/ops boundaries.
5. Data clarity: required data, quality expectations, ownership.
6. Execution clarity: command paths, runtime behavior, dependencies.
7. Failure clarity: what can fail, detection, recovery, rollback.
8. Rollout clarity: release shape, monitoring, operator workflow.
9. Plain-language readiness: 12-year-old summary + checklist.

## Gate to Move Forward

PRD/TDD generation is allowed only when all are true:

- No unresolved high-impact unknowns remain.
- Core behavior decisions are explicit.
- Execution path is concrete enough to implement without guessing.
- User accepts the plain-language summary + checklist.

If any gate fails, continue Socratic rounds.

## Non-Technical Approval Layer (Mandatory)

Before implementation handoff, present:

- 3 short paragraphs understandable by a 12-year-old.
- 5 yes/no checklist items.

If any checklist item is `No`, return to Socratic rounds. Do not proceed to implementation handoff.

## Phase 2: PRD Generation Handoff

After Phase 1 gate passes, generate `prd-<feature>.md` using `rules/create-prd.md`.

PRD remains product truth (`what/why`) and must not include deep implementation details.

## Phase 3: TDD Generation Handoff

After PRD approval, generate `tdd-<feature>.md` using `rules/create-tdd.md`.

TDD is execution truth (`how`) and must include:

- Architecture and component boundaries
- Data model/storage changes
- Interfaces/contracts (API/CLI/events)
- Command contract (exact run commands + expected outcomes)
- Failure modes and rollback
- Observability/monitoring
- Test strategy (unit/integration/e2e)
- Rollout plan and operational runbook

Use stable technical requirement IDs in TDD: `TDR-*`.

## Phase 4: Task Generation Handoff

Generate tasks only after both `prd-<feature>.md` and `tdd-<feature>.md` exist and are reconciled.

Use `rules/generate-tasks.md`, which must enforce:

- PRD coverage map (`FR-*`)
- TDD coverage map (`TDR-*`)
- Stop on PRD/TDD conflicts until reconciled
- Sub-task metadata: `covers_prd`, `covers_tdd`, `verify`, `done_when`

Execution cleanup/archive behavior belongs to `rules/task-management.md` and `AGENTS.md` finalization flow, not Socratic planning.

## Process Validation Scenarios

- PRD exists but TDD missing:
  - Expected: do not generate tasks.
- PRD and TDD disagree on behavior:
  - Expected: stop and reconcile first.
- Task missing `covers_tdd` or `verify`:
  - Expected: task list is incomplete.
- Socratic rounds skipped:
  - Expected: do not proceed to PRD/TDD generation.
- Plain-language checklist not approved:
  - Expected: return to Socratic rounds, no implementation handoff.

## Assumptions and Defaults

- This process is human-enforced, not lint/CI-enforced.
- PRD is product truth (`what/why`), TDD is execution truth (`how`).
- Task generation always requires both PRD + TDD.
- Unknowns must be resolved through micro-round questions, not hidden as assumptions.
- Optimize for low cognitive load for approvers and high clarity for implementers.
