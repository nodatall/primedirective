# Sub-task Contract: 2.2

plan_key: plan-refine-challenger-lane
task_id: 2.2

## Goal

Update `skills/plan-and-execute/SKILL.md` thin wording so `--refine-plan` references normal `$plan-refine` behavior, including the internal challenger lane, reviewer-owned severity gate, hard-stop outcomes, recoverable churn, and refinement-log availability through final review/finalization.

## In Scope

- `skills/plan-and-execute/SKILL.md` only.
- Keep `$plan-and-execute` as a thin orchestrator.
- Do not duplicate full challenger schema.
- Replace reviewer-only phrasing with normal `$plan-refine` behavior.
- Split hard-stop refinement outcomes from recoverable churn.
- Retain refinement log through final full-branch review/finalization.

## Out Of Scope

- Shared contract updates.
- `$plan-refine` source workflow updates.
- README invocation changes.

## Surfaces

- `skills/plan-and-execute/SKILL.md`

## Acceptance Checks

- The `--refine-plan` step references internal challenger lane and reviewer-owned severity gate.
- It explicitly hard-stops on failed required refinement gates, unavailable subagents, incomplete challenge dispositions, unsafe blockers, or unresolved blocker/material findings at max rounds.
- It continues only after clean refinement success or recoverable churn with no unresolved reviewer blocker/material findings.
- It keeps refinement log available through final full-branch review and finalization.

## Reference Patterns

- Existing thin orchestrator wording in `skills/plan-and-execute/SKILL.md`.
- Composition-relevant behavior in `skills/shared/references/execution/task-file-contract.md`.

## Test First Plan

Failing-test-first is not practical for markdown skill-contract behavior. Pre-change inspection showed the file referred only to fresh reviewer rounds and did not mention challenger/hard-stop semantics.

## Verify

```bash
rg -n "challenger|reviewer-owned|hard-stop|recoverable|unresolved reviewer blocker|refinement log" skills/plan-and-execute/SKILL.md
```
