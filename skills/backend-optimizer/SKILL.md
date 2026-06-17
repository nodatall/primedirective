---
name: backend-optimizer
description: Optimize backend and database performance through report-first audits or bounded `/goal` fix loops. Use when the user asks to speed up backend routes, perform exhaustive database query sweeps, inspect schema/index health, reduce backend runtime work, or improve connection/lock/migration/observability hygiene. Supports `--query-sweep`, `--schema-health`, `--runtime`, and `--ops-hygiene`.
---

# Backend Optimizer Skill

Improve backend and database performance with measured evidence. This skill is narrower than `$repo-sweep`: it focuses on backend performance candidates, not broad security, architecture redesign, maintainability, frontend, or whole-repo production audit work.

## Activation

Invoke explicitly with `$backend-optimizer`.

Invoke inside a Codex goal when the user wants the bounded measured fix loop:

```text
/goal $backend-optimizer
```

Supported modifiers:

- `--query-sweep`
- `--schema-health`
- `--runtime`
- `--ops-hygiene`

If no mode is supplied, choose the smallest mode set that matches the user's request. For broad "make the backend faster" requests, start with `--query-sweep` and `--runtime`; add `--schema-health` or `--ops-hygiene` only when evidence points there.

Mode flags are complete instructions. Do not require the user to paste extra scope, safety, inventory, ledger, or stop-condition text after an invocation such as:

```text
/goal $backend-optimizer --schema-health
```

When a mode flag is present, load the optimization-loop reference and apply that mode's full checklist and completion gate automatically.

## References

Load `skills/backend-optimizer/references/optimization-loop.md` before substantive work. It owns the candidate ledger shape, mode checklists, safety gates, measurement rules, and stop conditions.

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

- inventory and rank candidates
- fix only safe candidates with before/after evidence
- update the candidate ledger or goal state after each candidate
- resweep until every high-impact candidate is improved, rejected with evidence, or gated behind a clear decision
- when a mode flag is present, use the reference's mode contract without asking the user for extra boilerplate
- for `--query-sweep`, do not mark the goal complete until the ledger covers every discovered app-visible query surface, not just the first safe bottleneck fixed
- for `--schema-health`, do not mark the goal complete until schema-health inventory covers discovered tables, indexes, constraints, relationships, migrations, and growth risks with ledger dispositions

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
2. Inventory candidates.
   - Map queries, backend hot paths, runtime work, schema/index health, or ops hygiene items according to the selected mode.
   - For `--query-sweep`, complete the query-surface inventory before declaring the candidate set exhausted. Include every discovered SQL, ORM, query-builder, transaction, RPC/view/function, route, worker, job, script, and migration-backed query surface.
   - For `--schema-health`, complete the schema-health inventory before declaring the candidate set exhausted. Include discovered tables, indexes, constraints, relationships, migrations, retention/growth paths, and schema assumptions made by app code.
   - Prefer runtime evidence such as logs, traces, query stats, benchmarks, route timings, or `EXPLAIN` output when available.
3. Rank by impact.
   - Prioritize total time, mean or p95 latency, call frequency, user-facing importance, table size, sequential scans, round trips, lock risk, write cost, and operational blast radius.
4. Report or fix.
   - Bare `$backend-optimizer`: report the ranked candidates and stop before changes unless fixes were explicitly approved.
   - `/goal $backend-optimizer`: fix safe high-impact candidates one at a time, verify, update the ledger, and resweep.
5. Verify.
   - Capture before/after evidence for each accepted optimization.
   - Run focused regression checks and any migration or schema checks affected by the fix.
6. Close out.
   - State why the loop stopped.
   - List improved candidates, rejected candidates, gated decisions, validation, and residual risks.
   - For `--query-sweep`, state the inventory coverage and do not call the sweep complete unless every app-visible query surface has a ledger disposition.
   - For `--schema-health`, state the schema inventory coverage and do not call the sweep complete unless every performance- or reliability-relevant schema surface has a ledger disposition.

## Output

For report-first runs, lead with ranked findings:

- candidate
- evidence
- impact
- safe fix path
- risk or gate
- recommended next action

For `/goal` runs, include:

- rounds completed and stop reason
- inventory coverage, especially for `--query-sweep` and `--schema-health`
- candidates improved
- candidates rejected with evidence
- human-decision gates
- validation commands and outcomes
- ledger or resume-state location
