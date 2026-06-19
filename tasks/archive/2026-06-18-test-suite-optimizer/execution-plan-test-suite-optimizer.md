# Test Suite Optimizer Skill

Goal: Add a Prime Directive `$test-suite-optimizer` skill for measured test-suite speed work that preserves or improves validation confidence.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The skill should optimize the test harness itself: suite runtime, slow tests, setup cost, flake risk, and CI feedback time.
- The skill should not be a generic "make tests pass" skill, a coverage-increase skill, or a permission slip to skip slow tests.
- Bare `$test-suite-optimizer` should be report-first.
- `/goal $test-suite-optimizer` should be a bounded measured fix loop that records baseline timing, candidate dispositions, before/after evidence, coverage checks, and resume state.
- The closest local patterns are `$backend-optimizer` and `$page-speed-optimizer`: a small public `SKILL.md`, one detailed `references/optimization-loop.md`, `agents/openai.yaml`, README mirror, and contract validation.
- Deep research adopted these additions: native timing/report discovery before custom probes, isolation gates before parallelism or service reuse, explicit anti-cheat checks for skipped/focused tests and coverage/assertion erosion, and CI cache/artifact evidence as an optimization surface with policy gates.
- Pro analysis adopted these plan tightenings: exact report-first versus goal-mode permissions, representative versus diagnostic timing definitions, noise/minimum-claim rules, required goal-state and ledger fields, baseline-relative anti-cheat wording, E2E relocation mapping, and explicit human approval gates for risky test/CI changes.

## Steps

### 1. Research and tighten the skill contract

- [x] Run the requested web-backed deep research pass against this plan and record the working memo at `tasks/tmp/research-plan-test-suite-optimizer.md`.
- [x] Apply adopted deep-research findings to this execution plan before Pro analysis.
- [x] Run the requested ChatGPT Pro analysis pass against the researched plan and record the synthesis memo at `tasks/tmp/pro-analysis-test-suite-optimizer.md`.
- [x] Apply adopted Pro findings to this execution plan before refinement.
- [x] Refine this plan until the checklist is ordered, concrete, and free of material gaps.

### 2. Add the new skill

- [x] Create `skills/test-suite-optimizer/` with `SKILL.md`, `references/optimization-loop.md`, and `agents/openai.yaml`.
- [x] Inspect existing optimizer skill patterns before writing files: `skills/backend-optimizer/SKILL.md`, `skills/backend-optimizer/references/optimization-loop.md`, `skills/page-speed-optimizer/SKILL.md`, `skills/page-speed-optimizer/references/optimization-loop.md`, README routing, `skills/shared/references/contract-ownership.md`, and `scripts/validate-skill-contracts.py`.
- [x] Define `$test-suite-optimizer` as report-first: discover test commands and timing sources, measure the suite, rank safe speed candidates, recommend fixes, and stop before code, test files, snapshots, config, CI, package files, coverage thresholds, retries, timeouts, or test-selection changes unless the user approves fixes.
- [x] Define `/goal $test-suite-optimizer` as the bounded measured fix loop: baseline, inventory, rank, fix one safe candidate, verify, update state and ledger, resweep, and stop only when high-impact candidates are improved, rejected with evidence, or gated behind a clear decision.
- [x] Define the required run artifacts for goal mode: `tasks/tmp/test-suite-optimizer-goal-state.md` and `tasks/tmp/test-suite-optimizer-ledger.jsonl`.
- [x] Define required goal-state fields: scope, user goal, repo root, representative command, diagnostic commands, coverage command, CI jobs, baseline timing, timing source, test-count source, coverage/threshold source, known flakes, active candidate, gate status, last verification, evidence paths, human decisions, stop condition, and resume instructions.
- [x] Define required ledger fields: candidate id, candidate type, runner, affected surface, hypothesis, baseline command, baseline duration, after duration, delta, timing source, test count before/after, skip/focus scan result, coverage threshold or summary result, branch coverage status when available, isolation risk, flake/repeat check, CI evidence, disposition, rationale, files changed, artifact paths, and next action.
- [x] Require a test-surface inventory before fixes: commands, runner configs, CI jobs, coverage tools, reports, test categories, services, database setup, browser setup, caches, artifacts, env needs, and known flakes.
- [x] Prefer runner-native timing and report data before custom probes, including slow-test reports, JUnit/JSON/blob reports, coverage summaries, CI job timing, cache hit/miss data, and artifact paths when available.
- [x] Define representative timing evidence separately from diagnostic timing: a suite-speed claim needs the same representative command before and after unless the candidate intentionally changes the normal command; isolated micro-runs can explain causes but cannot prove the suite is faster by themselves.
- [x] Require timing evidence to record command, environment notes, timing source, raw duration, cache state, test count, and local-versus-CI source before claiming a suite-speed win.
- [x] Add a noise rule: prefer repeated runs or median timing when practical; label one-run evidence provisional; do not claim tiny wins unless the relative improvement, wall-clock improvement, or CI trend evidence is meaningful.
- [x] Require baseline-relative confidence-preservation evidence: no new or expanded skips/focuses, no unexplained test-count drop, no deleted coverage without replacement mapping, no lowered thresholds, no disabled branch coverage, and no assertion weakening.
- [x] Require flake and isolation safeguards before changing timers, waits, shared fixtures, database resets, service startup, runner pools, sharding, or parallelism.
- [x] Require collection consistency, order/isolation review, and at least one focused repeat or flake check before accepting changes to workers, sharding, pools, DB reset behavior, shared fixtures, browser startup, timers, waits, retries, or service reuse.
- [x] Allow moving behavior out of slow E2E or browser tests only with an E2E relocation map: old behavior covered, new boundary covering it, remaining smoke/E2E protection, and verification command.
- [x] Include CI cache, dependency install, artifact, and report-merge candidates while gating provider, cost, secret, or organization-policy changes for human approval.
- [x] Add a candidate taxonomy in `references/optimization-loop.md`: measurement/reporting, runner config, setup/teardown, fixture reuse, database reset, browser startup, CI cache, artifact/report merge, sharding, parallelism, flake reduction, and E2E boundary movement.
- [x] Add acceptable versus unacceptable claim examples, a low-value-work filter, and artifact hygiene notes in the reference file.
- [x] Define scope boundaries against failing-test repair, broad product rewrites, generic repo cleanup, app/runtime performance, page speed, unrelated coverage drives, arbitrary coverage floors, dependency upgrades without timing evidence, blanket retries/quarantines, deleting slow tests, mature-only test-impact selection, and CI-provider changes that need human approval.

### 3. Wire the public contract

- [x] Add `$test-suite-optimizer` to the README quick reference table.
- [x] Add a short README detail section explaining when to use it instead of `$repo-sweep`, `$backend-optimizer`, `$page-speed-optimizer`, `$bootstrap-repo-rules`, or normal failing-test/debug work.
- [x] Add a contract ownership row for `$test-suite-optimizer`, matching the optimizer-skill pattern unless implementation proves the validator does not need a new owned contract row.
- [x] Keep detailed loop behavior in the skill reference instead of duplicating it in README.

### 4. Validate and review

- [x] Run `python3 /Users/fromdarkness/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/test-suite-optimizer`.
- [x] Run `python3 scripts/validate-skill-contracts.py`.
- [x] Run `git diff --check`.
- [x] Run `./scripts/install-codex-plugin.sh`.
- [x] Run a final branch review against this plan and fix material findings before closeout.
