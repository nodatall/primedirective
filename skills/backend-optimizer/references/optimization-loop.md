# Backend Optimizer Loop

Use this reference for `$backend-optimizer` runs.

This skill has no public mode flags. A user should be able to invoke `/goal $backend-optimizer` without adding a custom prompt. Apply the backend/database inventory, goal state, candidate ledger, measurement rules, safety gates, and completion gate automatically.

## Goal-Run State

For `/goal $backend-optimizer`, maintain a readable state document at:

```text
tasks/tmp/backend-optimizer-goal-state.md
```

Create it at the start of the goal run. Update it after every meaningful checkpoint, after every candidate disposition, before context compaction or interruption handoff when possible, and before final closeout.

The state document should contain:

- `started_at`: local timestamp with timezone when known
- `last_checkpoint_at`: local timestamp with timezone when known
- `elapsed_wall_clock`: current elapsed wall-clock time for the run
- `user_budget`: time, token, or scope budget if the user provided one; otherwise `none provided`
- `current_phase`: discovering, measuring, patching, validating, resweeping, blocked, or complete
- `last_completed_step`: concrete completed step or `none yet`
- `active_step`: current work or `none`
- `next_exact_action`: the next command, route, query, table, trace, file, or decision to inspect
- `primary_verifier`: the strongest check or evidence bundle for this backend
- `supporting_checks`: non-decisive checks that catch regressions or safety issues
- `inventory_coverage`: queries, schema, runtime paths, migrations/config, and ops hygiene
- `active_candidate`: current ledger candidate id or `none`
- `ledger_path`: path to the JSONL ledger
- `evidence_paths`: reports, query plans, traces, benchmarks, logs, or fixtures
- `stop_condition_status`: incomplete, success, blocked, interrupted, or unsafe without approval
- `blockers`: exact blocker and required user/external action, or `none`
- `protected_boundaries`: behavior, policy, data, schema, config, or files that must not change

Use this shape unless the repo has a stronger local convention:

```md
# Backend Optimizer Goal State

started_at: <timestamp>
last_checkpoint_at: <timestamp>
elapsed_wall_clock: <duration>
user_budget: <time/token/scope budget or none provided>

## Current State

- current_phase: <discovering|measuring|patching|validating|resweeping|blocked|complete>
- last_completed_step: <step or none yet>
- active_step: <step or none>
- next_exact_action: <command, route, query, table, trace, file, or decision>
- stop_condition_status: <incomplete|success|blocked|interrupted|unsafe without approval>

## Verification

- primary_verifier: <strongest check or evidence bundle for this backend>
- supporting_checks: <regression, migration, load, benchmark, trace, or safety checks>
- last_validation: <command, artifact, or observable result>

## Inventory Coverage

- queries: <covered/pending/gated>
- schema: <covered/pending/gated>
- runtime_paths: <covered/pending/gated>
- migrations_config: <covered/pending/gated>
- ops_hygiene: <covered/pending/gated>

## Active Candidate

- active_candidate: <ledger id or none>
- ledger_path: tasks/tmp/backend-optimizer-ledger.jsonl
- evidence_paths: <reports, query plans, traces, benchmarks, logs, fixtures, or none yet>

## Boundaries And Blockers

- protected_boundaries: <behavior, policy, data, schema, config, or files that must not change>
- blockers: <none or exact blocker and required user/external action>
```

Do not mark a `/goal` run complete if this state document is missing, stale, or inconsistent with the ledger.

## Candidate Ledger

Keep one row per candidate in:

```text
tasks/tmp/backend-optimizer-ledger.jsonl
```

Each row should be JSONL with these fields when known:

```json
{
  "id": "short-stable-id",
  "candidate": "what may be slow or risky",
  "surface": "query|schema|runtime|migration|config|ops-hygiene|regression-check",
  "route_or_job": "route, job, worker, script, CLI, or none",
  "query_or_table": "query shape, table, view, function, or none",
  "environment": "prod-like-local|staging|clone|fixture|static-review|unknown",
  "coverage_status": "inventoried|measured|static-reviewed|fixed|gated|rejected",
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

The ledger is also the inventory receipt. Every high-impact backend/database surface discovered during the run must have a row or be covered by a row with a clear scope, even when it is fast, already indexed, static-reviewed only, or gated by missing safe database access.

Query rows should cover every app-visible query surface discovered during the run. Schema rows should cover every performance- or reliability-relevant table, index, constraint, relationship, migration, growth path, and app-assumed schema invariant discovered during the run.

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

Do not decide that the high-impact set is exhausted until the backend/database inventory is exhausted. A safe local fix plus a few gated remote candidates is a partial pass, not a completed backend optimization, unless every discovered high-impact query, schema, runtime, migration/config, and ops-hygiene surface has a ledger disposition.

The final answer must distinguish `backend optimization complete` from narrower outcomes such as `safe local pass complete`, `query inventory complete`, `schema inventory complete`, or `blocked before realistic measurement`.

## Backend Inventory

Discover the full backend performance surface before fixing obvious candidates:

- database query surfaces
- schema/index/constraint and migration surfaces
- backend request, job, worker, CLI, and service runtime paths
- connection, timeout, lock, observability, and deployment hygiene surfaces

Rank all discovered high-impact candidates together. It is acceptable to inspect a narrow area first when evidence points there, but do not report the overall goal complete while another high-impact surface remains unclassified.

## Query Surfaces

Inventory:

- SQL files, ORM calls, query builders, transactions, RPC functions, views, stored procedures, route handlers, workers, jobs, scripts, and migrations that define read or write paths.
- Runtime query evidence when available: slow query logs, APM traces, `pg_stat_statements`, database dashboards, request logs, or benchmark output.

Inventory rules:

- Search static source and migrations before fixing. Do not stop after the first measured bottleneck.
- Record every discovered app-visible query surface in the ledger with `coverage_status`.
- Map each query surface to the table, filter columns, join columns, order columns, limit/pagination shape, and caller when knowable.
- Compare each query shape against schema indexes, unique constraints, foreign keys, and migrations.
- When no safe database target is available, still do static query/schema/index matching and fixture-based or synthetic measurement where reasonable.
- Treat missing safe Postgres, MySQL, SQLite, or hosted database access as a gate for measurement, not as a reason to skip inventory.

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

Completion gate:

- Every app-visible query surface has a ledger row.
- Every ledger row has one of the allowed dispositions.
- Every measured optimization has before/after evidence.
- Every unmeasured query candidate has static schema/index evidence or an explicit blocked/gated reason.
- Gated candidates do not complete the goal by themselves. Continue through all ungated query surfaces before stopping.
- The final answer must distinguish `query inventory complete` from `safe local pass complete` when any database or query family could not be measured.

## Schema Health

Review tables and schema only for performance or reliability impact.

Inventory:

- schema files, migrations, ORM models, generated schema metadata, database clients, table definitions, indexes, constraints, triggers, views, functions, retention jobs, cleanup jobs, and app code that assumes schema invariants
- runtime schema evidence when available: table sizes, index sizes, index usage, slow plans, lock history, migration history, bloat/vacuum stats, constraint violations, or dashboard output

Inventory rules:

- Search static schema, migrations, models, and database call sites before fixing. Do not stop after the first missing index or unsafe migration.
- Record every discovered performance- or reliability-relevant schema surface in the ledger with `coverage_status`.
- Map each table to primary keys, foreign keys, unique constraints, important nullable columns, growth/retention story, high-churn writes, and query shapes that filter, join, order, or aggregate on it.
- Map each index to the query shapes or constraints it serves, and flag duplicates, overlaps, unused indexes, overly wide indexes, and write-amplification risk.
- Compare code-assumed invariants against actual database constraints, nullability, uniqueness, defaults, and migration order.
- When no safe database target is available, still do static schema/query/index matching and mark measurement-only questions as gated.
- Treat missing safe Postgres, MySQL, SQLite, or hosted database access as a gate for measurement, not as a reason to skip inventory.

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

Rank:

- table size and growth rate
- frequency and importance of queries touching the table
- sequential scans, sort/hash costs, and rows removed by filters
- constraint absence that can create bad data or expensive defensive code
- write amplification from existing or proposed indexes
- migration lock duration, rollback safety, and existing-data compatibility
- cleanup, archival, or retention gaps that will make current queries degrade

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

Completion gate:

- Every discovered performance- or reliability-relevant schema surface has a ledger row or an explicitly scoped ledger row that covers it.
- Every ledger row has one of the allowed dispositions.
- Every accepted schema or index change has before/after evidence and migration/regression validation.
- Every unmeasured schema candidate has static schema/query evidence or an explicit blocked/gated reason.
- Larger redesign candidates are gated and routed out; they do not justify ending the sweep early while safe schema-health candidates remain.
- The final answer must distinguish `schema inventory complete` from `safe local pass complete` when any database, table family, or schema evidence source could not be measured.

## Runtime Work

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
