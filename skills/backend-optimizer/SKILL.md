---
name: backend-optimizer
description: Optimize backend and database performance through report-first audits or bounded `/goal` fix loops. Use when the user asks to speed up backend routes, perform database query sweeps, inspect schema/index health, reduce backend runtime work, or improve connection/lock/migration/observability hygiene. Normal use has no mode flags.
---

# Backend Optimizer Skill

Improve backend and database performance with measured evidence. This skill is narrower than `$repo-sweep`: it focuses on backend performance candidates, not broad security, architecture redesign, maintainability, frontend, or whole-repo production audit work.

## Activation

Invoke explicitly with `$backend-optimizer`.

Invoke inside a Codex goal when the user wants the bounded measured fix loop:

```text
/goal $backend-optimizer
```

Do not add or require public mode flags. A bare invocation is enough; the skill decides what to inspect from backend routes, jobs, queries, schema, migrations, runtime behavior, configuration, and evidence.

## References

Load `skills/backend-optimizer/references/optimization-loop.md` before substantive work. It owns the goal-run state document, candidate ledger, backend/database inventory, safety gates, measurement rules, and stop conditions.

Also load these when they materially affect the run:

- `skills/shared/references/analysis/verification-pivot.md` when current evidence cannot separate plausible bottlenecks.
- `skills/shared/references/reasoning-budget.md` for planning, loop, worker, and verification reasoning tiers.
- `skills/shared/references/architecture/architecture-guidance.md` when a proposed change would alter module or data-access boundaries, or when `docs/ARCHITECTURE.md` exists.

## Invocation Behavior

Bare `$backend-optimizer` is report-first:

- inventory and rank candidates
- collect measurement evidence when practical
- recommend safe fixes
- stop before code, schema, config, migration, or deployment changes unless the user explicitly approves fixes

`/goal $backend-optimizer` is the bounded measured fix loop:

- create or update the goal-run state document and candidate ledger
- inventory and rank candidates
- fix only safe candidates with before/after evidence
- update the state document and ledger after each meaningful checkpoint or candidate disposition
- resweep until every high-impact candidate is improved, rejected with evidence, or gated behind a clear decision
- do not mark the goal complete while the goal-run state document is missing, stale, or inconsistent with the ledger
- do not mark the goal complete after one query, index, route, job, or config win while high-impact backend/database candidates remain unclassified

## Scope

In scope:

- application-visible database queries
- ORM and SQL call sites
- indexes, constraints, table growth risks, and performance-relevant schema health
- backend request, job, worker, CLI, and service runtime work
- connection pooling, timeouts, locks, migrations, slow-query visibility, and observability gaps

Out of scope:

- frontend rendering and browser performance
- broad repo review, security review, dependency audit, and general maintainability cleanup
- single-route deep dives as a special mode
- large schema or backend redesign as an auto-fix lane

Route out-of-scope work:

- Use `$repo-sweep` for broad repository audit, production readiness, security/config/API-surface review, or larger redesign findings.
- Use `$create-architecture` or normal planning workflows for table splits, ownership changes, denormalized read models, partitioning strategy, or other major boundary changes.

## Safety Rules

- Use realistic data, staging, a clone, or safe local fixtures before claiming a database performance win.
- Do not run destructive database commands, production migrations, large backfills, or high-risk index builds without explicit approval and target verification.
- Do not change product-visible behavior, public API shape, billing/security policy, data-retention semantics, or schema meaning without human approval.
- Treat a missing realistic benchmark, missing credentials, or unsafe database target as a blocker or gated candidate, not as permission to guess.
- Prefer the smallest measured fix. Reject speculative indexes, cache layers, and rewrites when evidence does not show they affect a high-impact candidate.

## Workflow

1. Establish baseline and safety.
   - Inspect git status and preserve unrelated changes.
   - Identify backend entrypoints, database technology, ORM/query layer, migrations, env loading, test commands, and safe database targets.
   - Record missing env, credentials, services, or realistic data before attempting measurements.
   - For `/goal`, create or update `tasks/tmp/backend-optimizer-goal-state.md` and `tasks/tmp/backend-optimizer-ledger.jsonl`.
2. Inventory candidates.
   - Map queries, backend hot paths, runtime work, schema/index health, migrations, and ops hygiene items.
   - Complete the query-surface inventory before declaring query candidates exhausted. Include every discovered SQL, ORM, query-builder, transaction, RPC/view/function, route, worker, job, script, and migration-backed query surface.
   - Complete the schema-health inventory before declaring schema candidates exhausted. Include discovered tables, indexes, constraints, relationships, migrations, retention/growth paths, and schema assumptions made by app code.
   - Prefer runtime evidence such as logs, traces, query stats, benchmarks, route timings, or `EXPLAIN` output when available.
3. Rank by impact.
   - Prioritize total time, mean or p95 latency, call frequency, user-facing importance, table size, sequential scans, round trips, lock risk, write cost, and operational blast radius.
4. Report or fix.
   - Bare `$backend-optimizer`: report the ranked candidates and stop before changes unless fixes were explicitly approved.
   - `/goal $backend-optimizer`: fix safe high-impact candidates one at a time, verify, update the state document and ledger, and resweep.
5. Verify.
   - Capture before/after evidence for each accepted optimization.
   - Run focused regression checks and any migration or schema checks affected by the fix.
6. Close out.
   - State why the loop stopped.
   - List improved candidates, rejected candidates, gated decisions, validation, and residual risks.
   - State whether the result is `backend optimization complete` or a narrower result such as `safe local pass complete`.
   - For `/goal`, include the goal state path, ledger path, wall-clock elapsed time, inventory coverage, and stop-condition status.

## Output

For report-first runs, lead with ranked findings:

- candidate
- evidence
- impact
- safe fix path
- risk or gate
- recommended next action

For `/goal` runs, include:

- rounds completed, wall-clock elapsed time, and stop reason
- goal state path and ledger path
- inventory coverage across queries, schema, runtime paths, migrations/config, and ops hygiene
- candidates improved
- candidates rejected with evidence
- human-decision gates
- validation commands and outcomes
- residual risks and resume point when incomplete
