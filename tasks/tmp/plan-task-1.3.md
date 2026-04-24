# Sub-task Contract: 1.3

plan_key: plan-refine-challenger-lane
task_id: 1.3

## Goal

Preserve research/Pro-backed decisions in the challenger lane and update `$plan-refine` final output/log rules for challenger-sourced fixes or accepted residual challenge risks.

## In Scope

- `skills/plan-refine/SKILL.md` only.
- Challenger receives same research/Pro context as reviewer and must handle those decisions carefully.
- Final output contract includes challenger-sourced material fixes or residual accepted challenge risks when any exist.
- `$plan-and-execute --refine-plan` keeps the refinement log through final full-branch review and finalization before cleanup unless preservation is active.

## Out Of Scope

- Shared contract mirror updates.
- `$plan-and-execute` wording updates.
- New public flags.

## Surfaces

- `skills/plan-refine/SKILL.md`

## Acceptance Checks

- Challenger context includes loaded research memo/digest and Pro memo/digest.
- Challenger can contest research/Pro-backed decisions only by naming conflict, stale evidence, over-scope, missing carry-forward, or unsafe assumption with artifact/research basis.
- Final output contract includes challenger-sourced material fixes or accepted residual challenge risks when any exist.
- Cleanup rule distinguishes standalone `$plan-refine` from `$plan-and-execute --refine-plan` log retention through final full-branch review/finalization.

## Reference Patterns

- Existing research/Pro preservation rules in `skills/plan-refine/SKILL.md`.
- Existing task-file contract wording for retention through composed workflows.

## Test First Plan

Failing-test-first is not practical for markdown skill-contract behavior. Pre-change inspection showed no output contract line for challenger-sourced residual risks and no `$plan-and-execute` retention rule in `$plan-refine`.

## Verify

```bash
rg -n "research-backed|Pro-backed|challenger-sourced|residual.*challenge|final full-branch review|finalization|plan-refine-<plan-key>" skills/plan-refine/SKILL.md
```
