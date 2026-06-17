# Backend Optimizer Loop

Use this reference for `$backend-optimizer` runs.

## Candidate Ledger

Keep one row per candidate in goal state or, when the repo has `tasks/tmp/`, in:

```text
tasks/tmp/backend-optimizer-<mode>-ledger.jsonl
```

Each row should be JSONL with these fields when known:

```json
{
  "id": "short-stable-id",
  "mode": "query-sweep|schema-health|runtime|ops-hygiene",
  "candidate": "what may be slow or risky",
  "surface": "route, job, query, table, migration, or config path",
  "evidence": "baseline measurement or static evidence",
  "impact": "why this matters",
  "proposed_fix": "smallest useful change",
  "experiment": "measurement or check to run",
  "result": "before/after or rejection evidence",
  "disposition": "improved|already acceptable|not worth cost|unsafe without approval|blocked by missing realistic data|requires product/schema decision|failed experiment",
  "validation": "commands, plans, logs, screenshots, or artifacts",
  "next_action": "resume point or none"
}
```

Update the ledger or goal state after every candidate is classified, fixed, rejected, or gated. After interruption or context compaction, resume from the first high-impact row whose disposition still requires action.

## Dispositions

- `improved`: accepted fix has before/after evidence and required regression checks passed.
- `already acceptable`: baseline evidence shows the candidate is not a meaningful bottleneck.
- `not worth cost`: improvement is too small, index/write/storage cost is too high, or complexity outweighs gain.
- `unsafe without approval`: action could affect production data, schema meaning, product behavior, API contracts, security, billing, or deployment safety.
- `blocked by missing realistic data`: current environment cannot produce credible measurements.
- `requires product/schema decision`: the right fix changes product semantics, ownership, table shape, retention, or migration strategy.
- `failed experiment`: a plausible low-risk experiment did not improve the measured bottleneck.

## Shared Stop Condition

Stop only when every high-impact candidate is one of:

- improved and verified
- already acceptable
- not worth cost with evidence
- unsafe without approval
- blocked by missing realistic data
- requires product/schema decision
- failed experiment with evidence

Do not stop only because one phase is complete, one benchmark improved, or one obvious candidate was fixed.

## Query Sweep

Inventory:

- SQL files, ORM calls, query builders, RPC functions, views, stored procedures, route handlers, workers, jobs, scripts, and migrations that define read or write paths.
- Runtime query evidence when available: slow query logs, APM traces, `pg_stat_statements`, database dashboards, request logs, or benchmark output.

Rank:

- total execution time
- mean or p95 latency
- call count
- user-facing route importance
- table size and growth rate
- sequential scans on large tables
- rows removed by filters
- nested-loop or sort costs
- repeated round trips and N+1 patterns
- RLS or policy overhead where applicable

Experiment safely:

- Capture a baseline plan or timing first.
- Use representative parameters.
- Prefer staging, clone, local fixture, or safe read-only analysis.
- Test query rewrites, batching, projection narrowing, pagination changes, and candidate indexes.
- For indexes, consider duplicate indexes, write cost, storage cost, lock behavior, online/concurrent build support, and migration rollback.

Accept only measured wins.

## Schema Health

Review tables and schema only for performance or reliability impact.

Check:

- primary keys and foreign keys
- indexes on join/filter columns and foreign-key sides
- duplicate, overlapping, unused, or too-wide indexes
- missing constraints that the app assumes
- nullable columns that encode too many states
- JSON or text blobs that create proven query/index pain
- tables with unbounded growth and no retention, partitioning, or archival story
- high-churn tables with write-heavy index cost
- migrations that can lock large tables or fail on existing data

Safe auto-fix examples:

- low-risk missing indexes proven by plans and realistic data
- constraints only when existing data is verified compatible and semantics are already enforced by code
- migration comments or guards that reduce accidental unsafe execution

Gate larger changes:

- table splits
- denormalized read models
- partitioning strategy
- ownership changes
- retention semantics
- backfills or destructive data changes

## Runtime

Inspect backend work outside the database:

- serial awaits that can safely run in parallel
- repeated expensive initialization
- synchronous or blocking I/O in request paths
- unnecessary repeated network calls
- excessive response payloads
- expensive serialization or transformation
- avoidable overfetching
- missing cache for stable data
- background work blocking request response
- unbounded fan-out, retry storms, or missing timeouts

Measure:

- route timing
- job runtime
- local benchmark
- fixture replay
- logs around the suspected bottleneck
- profiler or trace when available

Accept only changes that preserve behavior and have before/after evidence.

## Ops Hygiene

Review operational performance and safety:

- connection pooling and connection limits
- idle and statement timeouts
- transaction length
- lock risk and migration lock behavior
- vacuum/analyze or bloat signals
- slow-query monitoring
- health checks and readiness checks
- logging, metrics, and alerts for backend/database latency
- retry and idempotency behavior
- migration dry-run or rollback evidence

Prefer small observability and safety fixes. Gate deployment, pool sizing, timeout, and migration changes when the correct value depends on production traffic, hosting limits, or operator policy.

## Measurement Rules

- A passing test is not a performance measurement unless it records the relevant timing, plan, or resource signal.
- A local microbenchmark is useful only when it exercises the actual bottleneck or isolates a proven hot function.
- Static code reading can rank candidates, but it cannot prove a speedup.
- If two plausible causes fit the evidence, use the verification pivot and add the smallest probe that separates them.
- Record both positive and negative experiments so the loop does not repeat failed ideas.
