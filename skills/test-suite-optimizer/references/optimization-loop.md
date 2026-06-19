# Test Suite Optimizer Loop

Use this reference for `$test-suite-optimizer` runs.

This skill has no public mode flags. A user should be able to invoke `/goal $test-suite-optimizer` without adding a custom prompt. Apply the test-surface inventory, goal state, candidate ledger, measurement rules, anti-cheat checks, safety gates, and completion gate automatically.

## Goal-Run State

For `/goal $test-suite-optimizer`, maintain a readable state document at:

```text
tasks/tmp/test-suite-optimizer-goal-state.md
```

Create it at the start of the goal run. Update it after every meaningful checkpoint, after every candidate disposition, before context compaction or interruption handoff when possible, and before final closeout.

The state document should contain:

- `started_at`: local timestamp with timezone when known
- `last_checkpoint_at`: local timestamp with timezone when known
- `elapsed_wall_clock`: current elapsed wall-clock time for the run
- `user_budget`: time, token, or scope budget if the user provided one; otherwise `none provided`
- `scope`: requested repo, path, command family, package, test type, or CI lane
- `user_goal`: the user's requested speed or feedback objective
- `repo_root`: absolute or repo-relative checkout root
- `representative_command`: the normal command used to prove suite speed before and after
- `diagnostic_commands`: isolated commands, micro-runs, reporters, or probes used only to explain causes
- `coverage_command`: coverage or threshold command, or `none discovered`
- `ci_jobs`: relevant CI jobs, required checks, cache keys, artifact/report jobs, or `none discovered`
- `baseline_timing`: raw baseline duration and unit
- `timing_source`: runner report, shell timing, CI job timing, trace, JUnit/JSON/blob report, or other source
- `test_count_source`: runner output, report file, CI summary, or other source for collected/executed tests
- `coverage_threshold_source`: coverage config, summary, branch coverage report, or `none discovered`
- `known_flakes`: known flaky tests, noisy surfaces, retry patterns, or `none discovered`
- `current_phase`: discovering, measuring, patching, validating, resweeping, blocked, or complete
- `last_completed_step`: concrete completed step or `none yet`
- `active_step`: current work or `none`
- `next_exact_action`: the next command, report, config, file, CI job, or decision to inspect
- `active_candidate`: current ledger candidate id or `none`
- `gate_status`: no gate, awaiting approval, missing representative runtime, missing CI access, missing service/env, unsafe without approval, or blocked
- `last_verification`: command, artifact, or observable result from the latest verification
- `evidence_paths`: reports, logs, timing artifacts, coverage summaries, CI URLs, screenshots, videos, or none
- `human_decisions`: approvals, rejected risky changes, scoped boundaries, or `none yet`
- `stop_condition`: incomplete, success, blocked, interrupted, or unsafe without approval
- `resume_instructions`: exact next action and why, or `none`
- `ledger_path`: path to the JSONL ledger

Use this shape unless the repo has a stronger local convention:

```md
# Test Suite Optimizer Goal State

started_at: <timestamp>
last_checkpoint_at: <timestamp>
elapsed_wall_clock: <duration>
user_budget: <time/token/scope budget or none provided>

## Run Scope

- scope: <repo, path, command family, package, test type, or CI lane>
- user_goal: <requested speed or feedback objective>
- repo_root: <repo root>

## Timing Baseline

- representative_command: <normal command proving suite speed>
- diagnostic_commands: <isolated commands or probes>
- baseline_timing: <raw duration and unit>
- timing_source: <runner report, shell timing, CI job timing, report file, or trace>
- test_count_source: <runner output, report file, CI summary, or unknown>

## Validation Confidence

- coverage_command: <coverage or threshold command, or none discovered>
- coverage_threshold_source: <coverage config, summary, branch coverage report, or none discovered>
- known_flakes: <known flakes or none discovered>
- last_verification: <command, artifact, or observable result>

## CI And Artifacts

- ci_jobs: <jobs, required checks, cache keys, artifacts, report merge jobs, or none discovered>
- evidence_paths: <reports, logs, timing artifacts, coverage summaries, CI URLs, screenshots, videos, or none>

## Current State

- current_phase: <discovering|measuring|patching|validating|resweeping|blocked|complete>
- last_completed_step: <step or none yet>
- active_step: <step or none>
- next_exact_action: <command, report, config, file, CI job, or decision>
- active_candidate: <ledger id or none>
- gate_status: <no gate|awaiting approval|missing representative runtime|missing CI access|missing service/env|unsafe without approval|blocked>
- stop_condition: <incomplete|success|blocked|interrupted|unsafe without approval>

## Decisions And Resume

- human_decisions: <approvals, rejected risky changes, scoped boundaries, or none yet>
- ledger_path: tasks/tmp/test-suite-optimizer-ledger.jsonl
- resume_instructions: <exact next action and why, or none>
```

Do not mark a `/goal` run complete if this state document is missing, stale, or inconsistent with the ledger.

## Candidate Ledger

Keep one row per candidate in:

```text
tasks/tmp/test-suite-optimizer-ledger.jsonl
```

Each row should be JSONL with these fields when known:

```json
{
  "id": "short-stable-id",
  "candidate": "what may slow or destabilize feedback",
  "candidate_type": "measurement-reporting|runner-config|setup-teardown|fixture-reuse|database-reset|browser-startup|ci-cache|artifact-report-merge|sharding|parallelism|flake-reduction|e2e-boundary-movement|regression-check",
  "runner": "jest|vitest|pytest|mocha|xcodebuild|playwright|cypress|go test|cargo test|ci|unknown",
  "affected_surface": "command, test file, fixture, service, DB reset, browser setup, coverage, CI job, cache, artifact, or report",
  "hypothesis": "why this candidate may matter",
  "baseline_command": "representative or diagnostic command",
  "baseline_duration": "raw duration and unit",
  "after_duration": "raw duration and unit, or none",
  "delta": "absolute and relative change, or none",
  "timing_source": "runner report, shell timing, CI job timing, report file, trace, or other source",
  "test_count_before": "count and source, or unknown",
  "test_count_after": "count and source, or none",
  "skip_focus_scan_result": "no new skips/focuses|changed with explanation|not checked",
  "coverage_threshold_or_summary_result": "unchanged/pass|changed with approval|not applicable|not checked",
  "branch_coverage_status": "unchanged|not available|changed with approval|not checked",
  "isolation_risk": "none|low|medium|high|unknown",
  "flake_repeat_check": "repeat command/result, known flake evidence, or not checked",
  "ci_evidence": "CI job timing, cache hit/miss, artifact/report path, URL, or none",
  "disposition": "improved|already acceptable|not worth cost|unsafe without approval|blocked by missing representative runtime|blocked by missing CI access|blocked by missing service/env|requires test policy decision|requires CI policy decision|failed experiment|diagnostic-only",
  "rationale": "why this disposition is correct",
  "files_changed": "files changed, or none",
  "artifact_paths": "reports, logs, timing outputs, coverage summaries, traces, screenshots, videos, or none",
  "next_action": "resume point or none"
}
```

Update the ledger or goal state after every candidate is classified, fixed, rejected, or gated. After interruption or context compaction, resume from the first high-impact row whose disposition still requires action.

The ledger is also the inventory receipt. Every high-impact test, command, runner config, setup/teardown cost, service, database reset, browser startup, coverage/reporting cost, CI cache/artifact/report-merge surface, or known flake discovered during the run must have a row or be covered by a row with a clear scope.

## Candidate Taxonomy

Use these candidate types unless the repo has a clearer local taxonomy:

- `measurement-reporting`: timing reports, slow-test reporters, JUnit/JSON/blob reports, coverage summaries, CI timing summaries, and artifact paths.
- `runner-config`: collection behavior, transforms, environment startup, worker settings, watch/default command split, reporter cost, and config loading.
- `setup-teardown`: expensive global setup, per-test setup, cleanup, service boot, fixture lifecycle, and teardown waits.
- `fixture-reuse`: repeated expensive fixture construction that can be narrowed or shared without leaking state.
- `database-reset`: migrations, truncation, transactions, seeded data, snapshots, containers, and per-test DB cleanup.
- `browser-startup`: browser launch, context/page creation, auth state, fixture reuse, network mocking, and video/trace/screenshot policy.
- `ci-cache`: dependency installs, build caches, test caches, browser binary caches, and cache key correctness.
- `artifact-report-merge`: test report generation, coverage merge, screenshot/video/trace artifacts, upload/download cost, and report parsing.
- `sharding`: runner-native sharding or CI matrix splits with stable test counts and deterministic report merge.
- `parallelism`: worker/pool/process concurrency with order/isolation and resource-limit checks.
- `flake-reduction`: deterministic waits, isolation fixes, fixed clocks, service readiness checks, and removing timing races.
- `e2e-boundary-movement`: moving behavior out of slow e2e/browser coverage only with a replacement coverage map.
- `regression-check`: low-noise budget or guard that protects an accepted speed improvement.

## Dispositions

- `improved`: accepted fix has before/after representative evidence and required confidence checks passed.
- `already acceptable`: baseline evidence shows the candidate is not a meaningful feedback bottleneck.
- `not worth cost`: improvement is too small, too noisy, or complexity and confidence risk outweigh the gain.
- `unsafe without approval`: action could reduce validation confidence, affect product behavior, change CI policy, change secrets/env, add cost, or alter required checks.
- `blocked by missing representative runtime`: current environment cannot run the normal command needed to prove a suite-speed claim.
- `blocked by missing CI access`: CI timing, required-check, cache, or artifact evidence is needed and unavailable.
- `blocked by missing service/env`: required service, credentials, seeded data, browser, database, or external dependency is unavailable.
- `requires test policy decision`: the right fix changes test boundaries, coverage expectations, snapshot policy, or validation ownership.
- `requires CI policy decision`: the right fix changes provider, cost, secrets, required checks, org policy, or remote cache strategy.
- `failed experiment`: a plausible low-risk experiment did not improve the measured bottleneck or failed confidence checks.
- `diagnostic-only`: evidence helped explain a cause but did not prove suite speed improved.

## Shared Stop Condition

Stop only when every high-impact candidate is one of:

- improved and verified
- already acceptable
- not worth cost with evidence
- unsafe without approval
- blocked by missing representative runtime
- blocked by missing CI access
- blocked by missing service/env
- requires test policy decision
- requires CI policy decision
- failed experiment with evidence
- diagnostic-only with a linked representative candidate still dispositioned

Do not stop only because one slow test got faster, one file was split, one reporter changed, one CI cache hit improved, or one obvious flake was fixed.

Do not decide that the high-impact set is exhausted until the test-surface inventory is exhausted. A safe local fix plus unmeasured CI candidates is a partial pass, not a completed test-suite optimization, unless every discovered high-impact test, runner, setup, flake, coverage, and CI feedback surface has a ledger disposition.

The final answer must distinguish `test-suite optimization complete` from narrower outcomes such as `safe local pass complete`, `report-only pass complete`, `CI-gated pass complete`, or `blocked before representative measurement`.

## Test-Surface Inventory

Discover the validation surface before fixing obvious candidates:

- package manager and test scripts
- runner configs and runner versions
- representative local commands and diagnostic commands
- coverage commands, coverage thresholds, branch coverage settings, report merge steps, and coverage artifacts
- CI jobs, required checks, matrices, cache keys, artifacts, test report upload/download, and job dependencies
- test categories: unit, integration, e2e/browser, snapshot, contract, smoke, type-level, lint-like, or custom harnesses
- slowest tests, slowest files, setup/teardown hotspots, collection cost, transform/build cost, and reporter cost
- services, databases, containers, browser setup, external dependencies, env vars, credentials, seeded data, and auth state
- known flaky tests, retry patterns, fixed sleeps, broad timeouts, quarantine/skip/focus patterns, and order-dependent tests

Inventory rules:

- Search static scripts, configs, CI files, and reports before patching.
- Prefer native timing/report data before writing custom probes: slow-test reports, JUnit, JSON, blob reports, coverage summaries, CI job timing, cache hit/miss data, and artifact paths.
- Record representative commands separately from diagnostic commands.
- Record missing services, credentials, browser binaries, seeded data, CI access, or reports as gates, not as reasons to skip inventory.
- For `/goal`, add a ledger row or scoped ledger row for every high-impact surface discovered.

## Measurement Rules

- A passing test run is not a speed measurement unless it records the relevant duration, command, timing source, test count, and environment notes.
- A suite-speed claim needs the same representative command before and after unless the candidate intentionally changes the normal command.
- Isolated micro-runs, single-file runs, `--grep`, focused tests, and profiler probes can explain causes but cannot prove the whole suite is faster by themselves.
- Record command, env notes, timing source, raw duration, cache state, test count, and local-versus-CI source before claiming a speed win.
- Prefer repeated runs or median timing when practical. Label one-run evidence provisional.
- Do not claim tiny wins unless the relative improvement, wall-clock improvement, or CI trend evidence is meaningful for the repo's feedback loop.
- Use CI timing for CI feedback claims when available; local timing can guide a CI hypothesis but does not prove CI wall-clock improvement by itself.
- Static code reading can rank candidates, but it cannot prove a speedup.
- If two plausible causes fit the evidence, use the verification pivot and add the smallest probe that separates them.
- Record positive and negative experiments so the loop does not repeat failed ideas.

## Anti-Cheat Rules

Do not count any of these as success:

- adding or expanding skips, focuses, quarantines, broad retries, or blanket timeouts
- deleting slow tests or snapshots instead of replacing the same behavior with mapped coverage
- lowering coverage thresholds, disabling branch coverage, or removing coverage report surfaces
- weakening assertions, snapshots, mocks, schema checks, accessibility checks, or behavior checks
- accepting an unexplained test-count drop between before and after runs
- measuring only a narrowed diagnostic command and claiming the representative suite got faster
- accepting parallelism, sharding, fixture reuse, shared services, DB reset changes, or browser reuse without collection consistency and isolation checks
- hiding flakes behind retries instead of fixing determinism, isolation, or readiness
- using a CI cache hit that depends on incorrect keys, stale artifacts, missing lockfiles, or unchecked dependency state
- improving a single known slow surface while leaving discovered high-impact surfaces unclassified

## Flake And Isolation Safeguards

Before changing timers, waits, shared fixtures, database resets, service startup, runner pools, sharding, or parallelism:

- inspect collection consistency and test count before/after
- review order and isolation assumptions for the affected tests
- run at least one focused repeat or flake check when practical
- verify no new skip/focus/quarantine/retry pattern was introduced without explicit approval
- verify coverage thresholds and branch coverage behavior remain intact when applicable
- record local resource limits such as CPU, RAM, ports, DB connections, browser processes, and CI worker limits

Deterministic flake fixes are valid speed work when they reduce repeated runs or CI reruns. Blanket sleeps, larger global timeouts, broad retries, or quarantines are not valid speed fixes unless the user explicitly chooses a temporary policy gate and the final output labels the risk.

## E2E Boundary Movement

Moving behavior out of slow e2e or browser tests is allowed only with an E2E relocation map:

- old behavior covered
- new boundary covering it, such as unit, integration, contract, component, or service test
- remaining smoke or e2e protection
- verification command
- confidence tradeoff and owner decision when the boundary changes meaningfully

Do not treat deleting an e2e test as an optimization unless the same behavior remains covered and the map is recorded in the ledger.

## Safe Fix Examples

Safe fixes can include:

- replacing fixed sleeps with deterministic readiness, event, network, or DOM waits
- narrowing expensive fixtures while preserving isolation
- reusing immutable fixtures, auth state, build output, or browser context only when isolation is verified
- reducing repeated service or database setup where tests do not require fresh global state
- using runner-native slow-test reporting, sharding, or parallelism after collection and isolation checks pass
- correcting CI dependency cache keys, browser binary caches, or build caches when lockfiles and invalidation are sound
- splitting commands or CI jobs when feedback improves and report/coverage merge remains correct
- reducing artifact upload cost by changing retention or scope only when debugging and compliance needs remain covered
- moving slow behavior down the test pyramid with an E2E relocation map
- adding a low-noise regression guard for a measured speed improvement

Accept only measured wins or clearly verified confidence-preserving harness improvements.

## Unacceptable Claim Examples

Reject or gate claims like these:

- "The suite is faster because `test.only`/focused selection ran quickly."
- "The slow test was removed, so runtime improved."
- "Retries fixed the flake."
- "Coverage is faster because coverage thresholds are lower."
- "One file is faster, so CI is faster."
- "Local dev mode timing improved, so the required CI check is faster."
- "The cache hit once, so the cache strategy is correct."
- "Parallel workers passed once, so order isolation is safe."

## Low-Value Filter

Avoid optimization work when:

- expected savings are below timing noise or irrelevant to the user's feedback loop
- the fix adds complexity or flake risk greater than the measured gain
- the command is rarely run and CI/user feedback time is dominated elsewhere
- a candidate needs broad dependency upgrades or provider changes without strong evidence
- a custom timing harness would cost more to maintain than the native report it replaces

Prefer recommending no action with evidence over creating fragile speed machinery.

## Human-Decision Gates

Gate these instead of auto-fixing:

- deleting tests, lowering assertions, or changing validation ownership
- lowering coverage thresholds, disabling branch coverage, or changing coverage policy
- changing required CI checks, branch protection, provider, org policy, or paid services
- adding remote cache services or changing secrets/env distribution
- broad dependency upgrades or runner migrations
- introducing test-impact selection, dependency maps, or affected-test-only lanes when the repo does not already support them maturely
- moving behavior out of e2e/browser coverage when the replacement boundary changes product confidence
- changing retry/quarantine policy as a temporary operational tradeoff

## Artifact Hygiene

- Put disposable probes, reports, and one-off timing outputs in `/agent-scratch/` unless the repo has a better temp convention.
- Keep durable `/goal` state in `tasks/tmp/test-suite-optimizer-goal-state.md` and durable candidate rows in `tasks/tmp/test-suite-optimizer-ledger.jsonl`.
- Link report files, raw timing logs, coverage summaries, CI URLs, screenshots, videos, traces, and cache evidence from the ledger instead of pasting large blobs into chat.
- If timing artifacts are too noisy or environment-specific to keep, summarize the exact command, timestamp, raw duration, and reason they were discarded.

## Closeout Requirements

For report-first runs, lead with ranked findings and the evidence behind each finding.

For `/goal` runs, final output must include:

- goal state path and ledger path
- started time, end time, and elapsed wall-clock time
- inventory coverage
- representative baseline and final timing, or why representative timing was unavailable
- diagnostic timing used and how it was bounded
- candidates improved
- candidates rejected with evidence
- human-decision gates
- skip/focus scan result
- test-count before/after evidence
- coverage threshold or summary result
- branch coverage status when available
- flake/repeat or isolation evidence for risky harness changes
- CI timing, cache, artifact, or report evidence when CI feedback was in scope
- residual risks and next action when incomplete
