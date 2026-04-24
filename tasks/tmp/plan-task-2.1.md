# Sub-task Contract: 2.1

plan_key: plan-refine-challenger-lane
task_id: 2.1

## Goal

Update `skills/shared/references/execution/task-file-contract.md` with composition-relevant challenger behavior and refinement outcome semantics.

## In Scope

- `skills/shared/references/execution/task-file-contract.md` only.
- Mirror composition-relevant behavior from `$plan-refine`:
  - challenger cadence
  - fresh read-only challenger/reviewer requirements
  - reviewer-owned severity/stop rule
  - challenge disposition logging
  - hard-stop vs recoverable outcomes
  - refinement-log retention through `$plan-and-execute` final review/finalization
- Avoid duplicating full challenge brief schema.

## Out Of Scope

- Detailed challenge brief field list; source of truth remains `skills/plan-refine/SKILL.md`.
- `$plan-and-execute` wording update; task 2.2 owns that.

## Surfaces

- `skills/shared/references/execution/task-file-contract.md`

## Acceptance Checks

- Shared contract says challenger runs when `round == 1 OR previous_reviewer_round_had_blocker_or_material`.
- Shared contract says challenger and reviewer are fresh/read-only when required.
- Shared contract says reviewer owns severity and stop rule.
- Shared contract says every challenge ID must have reviewer disposition before clean stop.
- Shared contract says unresolved reviewer blocker/material findings at max rounds are hard stops.
- Shared contract says only recoverable churn with no unresolved reviewer blocker/material findings may continue under `$plan-and-execute`.
- Shared contract says `$plan-and-execute --refine-plan` retains the refinement log through final full-branch review and finalization.

## Reference Patterns

- Existing Plan-and-execute refinement modifier section.
- Existing Plan refinement mode section.
- Existing temporary workflow file retention section.

## Test First Plan

Failing-test-first is not practical for markdown skill-contract behavior. Pre-change inspection showed no challenger terms in `task-file-contract.md`.

## Verify

```bash
rg -n "challenger|hard-stop|recoverable|unresolved reviewer blocker|plan-refine-<plan-key>" skills/shared/references/execution/task-file-contract.md
```
