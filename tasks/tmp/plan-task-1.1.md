# Sub-task Contract: 1.1

plan_key: plan-refine-challenger-lane
task_id: 1.1

## Goal

Define the internal `$plan-refine` challenger role, applicable-round cadence, no-edit rule, and reasoning/subagent requirements in `skills/plan-refine/SKILL.md`.

## In Scope

- `skills/plan-refine/SKILL.md` only.
- Add challenger lane ownership and cadence language.
- Keep public `$plan-refine` invocation and modifiers unchanged.
- Preserve fresh read-only subagent requirements and strongest reasoning guidance.

## Out Of Scope

- Challenge brief schema and dispositions beyond what is needed to make cadence/role coherent; task 1.2 owns the detailed schema.
- Shared contract and `$plan-and-execute` mirror updates; task 2.0 owns those.
- New helper/function names or machine-readable schema.

## Surfaces

- `skills/plan-refine/SKILL.md`

## Acceptance Checks

- The doc says `$plan-refine` uses an internal challenger lane in applicable rounds.
- The challenger is fresh, read-only, and does not edit files.
- The cadence is explicit: `round == 1 OR previous_reviewer_round_had_blocker_or_material`.
- Challenger objections alone do not trigger another round.
- The reviewer remains the severity/stop gate.

## Reference Patterns

- Existing `$plan-refine` reviewer subagent language in `skills/plan-refine/SKILL.md`.
- Existing reasoning tier guidance in `skills/shared/references/reasoning-budget.md`.

## Test First Plan

Failing-test-first is not practical because this is a markdown skill-contract change with no executable parser. Pre-change inspection already showed no challenger lane in `skills/plan-refine/SKILL.md`.

## Verify

```bash
rg -n "challenger|round == 1|previous_reviewer_round_had_blocker_or_material|no_material_challenges_found" skills/plan-refine/SKILL.md
```
