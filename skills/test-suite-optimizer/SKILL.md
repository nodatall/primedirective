---
name: test-suite-optimizer
description: Optimize test-suite runtime and CI feedback speed through report-first audits or bounded `/goal` fix loops. Use when the user asks to speed up tests, reduce slow or flaky test feedback, profile unit/integration/e2e test runtime, improve setup or teardown cost, optimize runner or CI test execution, or reduce test harness noise while preserving validation confidence. Normal use has no mode flags.
---

# Test Suite Optimizer Skill

Improve test-suite and CI feedback speed with measured evidence. This skill is narrower than `$repo-sweep`: it focuses on validation speed, harness cost, slow tests, flakes that slow feedback, runner setup, and CI execution surfaces, not broad repo audit work or generic failing-test repair.

## Activation

Invoke explicitly with `$test-suite-optimizer`.

Invoke inside a Codex goal when the user wants the bounded measured fix loop:

```text
/goal $test-suite-optimizer
```

Do not add or require public mode flags. A bare invocation is enough; the skill decides what to inspect from test commands, runner configs, CI jobs, coverage tools, reports, fixtures, services, and evidence.

## References

Load `skills/test-suite-optimizer/references/optimization-loop.md` before substantive work. It owns the goal-run state document, candidate ledger, test-surface inventory, measurement rules, anti-cheat checks, safety gates, and stop conditions.

Also load these when they materially affect the run:

- `skills/shared/references/analysis/verification-pivot.md` when current evidence cannot separate plausible slowdowns or flake causes.
- `skills/shared/references/reasoning-budget.md` for planning, loop, worker, and verification reasoning tiers.
- `skills/shared/references/architecture/architecture-guidance.md` when a proposed test or CI change would alter module, service, or boundary ownership, or when `docs/ARCHITECTURE.md` exists.

## Invocation Behavior

Bare `$test-suite-optimizer` is report-first:

- discover test commands, runner configs, timing sources, coverage tools, and CI jobs
- inventory test categories, slow surfaces, setup/teardown cost, services, fixtures, caches, artifacts, and known flakes
- collect runner-native timing, report, coverage, CI timing, cache, or artifact evidence when practical
- rank safe speed candidates and recommend fixes
- stop before code, test files, snapshots, configs, CI files, package files, coverage thresholds, retries, timeouts, or test-selection changes unless the user explicitly approves fixes

`/goal $test-suite-optimizer` is the bounded measured fix loop:

- create or update the goal-run state document and candidate ledger
- establish a representative baseline, then inventory and rank candidates before fixing
- fix only safe high-impact candidates with before/after evidence
- update the state document and ledger after each meaningful checkpoint or candidate disposition
- resweep until every high-impact candidate is improved, rejected with evidence, or gated behind a clear decision
- do not mark the goal complete while the goal-run state document is missing, stale, or inconsistent with the ledger
- do not mark the goal complete after one faster test, one config tweak, or one CI cache win while high-impact test, harness, flake, or CI feedback candidates remain unclassified

## Scope

In scope:

- unit, integration, browser, e2e, snapshot, contract, and smoke test runtime
- test runner configuration, sharding, parallelism, worker pools, process startup, collection time, and report generation
- setup and teardown cost, fixture construction, service startup, database resets, browser startup, and shared test infrastructure
- slow tests, slow files, noisy or flaky tests that create repeat work, and deterministic wait/timer issues
- coverage command cost, coverage report generation, and coverage threshold checks when they affect feedback speed
- CI job timing, dependency install caches, test artifacts, report merging, job split shape, and validation pipeline feedback time
- test-impact selection or dependency mapping only when the repo already has mature support for it

Out of scope:

- generic failing-test debugging or application bug fixing
- broad repository audit, security review, dependency audit, or production-readiness review
- backend runtime performance, database query optimization, page speed, or product-surface performance
- unrelated coverage drives, arbitrary coverage floors, or using optimization work to create a blanket 100% coverage target
- deleting, skipping, focusing, quarantining, retrying, or weakening tests to make the suite appear faster
- broad dependency upgrades, CI provider migrations, paid remote-cache adoption, secret changes, or required-check policy changes as automatic fixes

Route out-of-scope work:

- Use normal debugging or `$bootstrap-repo-rules` when the repo lacks a basic validation surface or tests currently fail for functional reasons.
- Use `$backend-optimizer` for backend/database runtime or query performance.
- Use `$page-speed-optimizer` for browser-perceived application speed.
- Use `$repo-sweep` for broad repository audit, production readiness, security/config/API-surface review, or larger redesign findings.

## Safety Rules

- Preserve validation confidence. Do not delete tests, remove assertions, weaken snapshots, lower coverage thresholds, disable branch coverage, or add/expand skips, focuses, quarantines, retries, or blanket timeouts as a speed win.
- Require baseline-relative evidence before accepting a speed claim: no unexplained test-count drop, no new focused/skipped tests, no deleted behavior without replacement coverage, and no assertion erosion.
- Treat flaky or noisy tests as candidates for deterministic fixes, isolation fixes, or gated decisions; do not hide them behind broad retries or larger sleeps.
- Prove collection consistency, order/isolation safety, and at least one focused repeat or flake check before changing workers, sharding, pools, database reset behavior, shared fixtures, browser startup, timers, waits, retries, or service reuse.
- Gate CI provider changes, paid services, remote caches, secret or env changes, required-check policy, org-level CI policy, and broad dependency upgrades for human approval.
- Treat missing representative runtime, missing CI access, missing services, or missing credentials as a blocker or gated candidate, not as permission to invent a win.

## Workflow

1. Establish baseline and safety.
   - Inspect git status and preserve unrelated changes.
   - Identify package manager, test commands, runner configs, coverage commands, CI jobs, reports, env needs, services, database/browser setup, and known flakes.
   - Separate representative suite timing from diagnostic timing.
   - For `/goal`, create or update `tasks/tmp/test-suite-optimizer-goal-state.md` and `tasks/tmp/test-suite-optimizer-ledger.jsonl`.
2. Inventory candidates.
   - Map test categories, slow files, slow tests, setup/teardown, fixture construction, collection time, services, DB resets, browser startup, runner config, coverage/report generation, CI cache/artifact/report-merge surfaces, and known flakes.
   - Prefer runner-native timing and report data before custom probes.
   - Record every high-impact surface in the ledger, even when it is already acceptable, static-reviewed only, or gated.
3. Rank by feedback impact.
   - Prioritize total local feedback time, CI wall-clock time, slowest files, setup cost, repeat failure cost, flake frequency, user/system importance, maintenance burden, implementation risk, and confidence risk.
4. Report or fix.
   - Bare `$test-suite-optimizer`: report ranked candidates and stop before changes unless fixes were explicitly approved.
   - `/goal $test-suite-optimizer`: fix safe high-impact candidates one at a time, verify, update state and ledger, and resweep.
5. Verify.
   - Capture before/after evidence for each accepted optimization.
   - Use the same representative command before and after unless the candidate intentionally changes the normal command.
   - Run focused regression checks plus skip/focus scans, test-count comparisons, coverage or threshold checks, and flake/isolation checks appropriate to the changed surface.
6. Close out.
   - State why the loop stopped.
   - List improved candidates, rejected candidates, gated decisions, validation, and residual risks.
   - State whether the result is `test-suite optimization complete` or a narrower result such as `safe local pass complete`, `report-only pass complete`, or `blocked before representative measurement`.
   - For `/goal`, include the goal state path, ledger path, wall-clock elapsed time, inventory coverage, and stop-condition status.

## Output

For report-first runs, lead with ranked findings:

- candidate
- runner, command, CI job, or affected surface
- evidence
- impact
- safe fix path
- risk or gate
- recommended next action

For `/goal` runs, include:

- rounds completed, wall-clock elapsed time, and stop reason
- goal state path and ledger path
- inventory coverage across commands, runner configs, test categories, setup/teardown, services, coverage/reporting, CI jobs, caches, artifacts, and flakes
- candidates improved
- candidates rejected with evidence
- human-decision gates
- validation commands, timing reports, coverage summaries, CI evidence, and artifact paths
- residual risks and resume point when incomplete
