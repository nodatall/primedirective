# Sub-task Contract: 1.2

plan_key: plan-refine-challenger-lane
task_id: 1.2

## Goal

Add challenge brief schema, valid empty-brief behavior, reviewer normal-audit-first handoff, challenge ID dispositions, and direct-edit prohibition to `skills/plan-refine/SKILL.md`.

## In Scope

- `skills/plan-refine/SKILL.md` only.
- Define required challenge brief fields.
- Define allowed challenge dispositions.
- Require reviewer to run normal audit before challenge adjudication.
- Require `challenge_id` disposition completeness before edits or clean stop.
- Prohibit main agent from directly applying challenger-derived changes without reviewer promotion.

## Out Of Scope

- Shared contract mirror updates.
- `$plan-and-execute` wording.
- Public invocation changes.

## Surfaces

- `skills/plan-refine/SKILL.md`

## Acceptance Checks

- Challenger brief fields include `challenge_id`, `pressure_type`, `artifact_refs`, `hidden_assumption_or_failure_mode`, `how_it_could_break_execution`, `evidence_or_gap`, `counter_plan_pressure`, `suggested_reviewer_test`, and `requires_user_decision_candidate`.
- Empty challenger brief is valid with `no_material_challenges_found`.
- Reviewer runs normal audit first, then challenge adjudication.
- Allowed dispositions include `promoted_to_finding`, `already_covered`, `non_material`, `rejected`, `superseded`, and `deferred_with_owner`.
- `deferred_with_owner` has an owner/carry-forward location and cannot hide blocker-grade issues.
- Main agent applies challenger-derived fixes only after reviewer promotion to blocker/material, except minor coherence edits after accepted blocker/material fixes.

## Reference Patterns

- Structured finding fields in `skills/plan-refine/SKILL.md`.
- Pro finding disposition language in `skills/shared/references/analysis/pro-oracle-escalation.md`.
- Research/Pro preservation language already in `$plan-refine`.

## Test First Plan

Failing-test-first is not practical for markdown skill-contract behavior. Pre-change inspection showed the schema and disposition rules were absent.

## Verify

```bash
rg -n "challenge_id|deferred_with_owner|promoted_to_finding|normal.*audit|reviewer owns severity" skills/plan-refine/SKILL.md
```
