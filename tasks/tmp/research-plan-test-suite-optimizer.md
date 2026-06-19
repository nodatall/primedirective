# Deep Research Memo: Test Suite Optimizer

web research status: completed
current date used: 2026-06-18
timezone: America/Los_Angeles

## Project Context Snapshot

- Product or workflow: Prime Directive skill authoring for a new `$test-suite-optimizer` skill.
- Repo stack: Codex plugin source repo with Markdown skills, Python contract validator, shell installers, GitHub Actions validation, and a nested `apps/board` Node/Vitest/Playwright app used by this repo.
- Known local validation: `python3 scripts/validate-skill-contracts.py`, `git diff --check`, `./scripts/install-codex-plugin.sh`.
- Relevant local versions: `apps/board/package.json` uses `@playwright/test ^1.59.1`, Vitest `latest`, Vite `latest`, React `latest`; repo-level Python versions are not pinned.
- Highest-priority quality attributes: maintainability, confidence preservation, low-noise measurement, flake safety, CI feedback speed, and safe cross-stack defaults.
- Privacy notes: external searches used public runner names, docs, and generic behavior. No private repo contents, secrets, customer data, or unpublished identifiers were sent.

## Draft-Linked Research Agenda

| question_id | draft link | research bucket | question | possible plan impact |
| --- | --- | --- | --- | --- |
| RQ1 | Step 2, baseline and timing evidence | testing, verification, observability | What timing signals should the skill require before claiming a test-suite speed win? | Add native slow-test/report discovery and before/after timing gates. |
| RQ2 | Step 2, parallelism and flake safeguards | performance, concurrency, failure handling | When are parallelism, sharding, shared fixtures, and runner pools safe versus likely to create flakes? | Add isolation proof, repeat-run, and collection-consistency gates. |
| RQ3 | Step 2, confidence preservation evidence | testing, coverage, anti-cheat | What proof should prevent fake wins such as skipped tests, weakened assertions, or coverage erosion? | Add test-count, skip/focus scan, coverage-threshold, and assertion-weakening anti-cheat checks. |
| RQ4 | Step 3, CI and public contract | CI, rollout, artifact handling | How should CI caching, artifacts, and test reports fit without making the skill provider-specific? | Add CI timing/artifact candidates and make broad CI/provider changes gated. |

## Evidence Ledger

| source_id | source_type | source_family | url | publication_date | last_updated_date | accessed_date | version_or_scope | supported_claims | counts_toward_external_primary_minimum | current_enough_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | official docs | pytest | https://docs.pytest.org/en/stable/how-to/usage.html | unknown | 2026-06-13 | 2026-06-18 | stable pytest usage | Pytest exposes native slow-test duration reporting, useful for baseline and ranking. | yes | Stable docs updated days before this pass. |
| S2 | official docs | pytest | https://docs.pytest.org/en/stable/explanation/flaky.html | unknown | 2026-06-13 | 2026-06-18 | stable pytest flake guidance | Flaky tests are linked to uncontrolled system state, ordering, and parallelism-sensitive behavior. | yes | Stable docs updated days before this pass. |
| S3 | official docs | pytest-xdist | https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html | unknown | 2025-05-26 | 2026-06-18 | stable xdist | Parallel distribution has collection/order limitations; test order and amount must be consistent. | yes | Current stable xdist docs; directly relevant to parallelism safety. |
| S4 | official docs | Jest | https://jestjs.io/docs/cli | unknown | unknown | 2026-06-18 | Jest CLI options | Jest exposes max worker, run-in-band, shard, and open-handle diagnostics; debug flags can materially affect runtime. | yes | Current versioned docs site, direct owner of behavior. |
| S5 | official docs | Jest | https://jestjs.io/docs/configuration | unknown | unknown | 2026-06-18 | Jest configuration | Jest owns coverage thresholds and slow-test thresholds that can be used as anti-cheat and ranking inputs. | yes | Current versioned docs site, direct owner of behavior. |
| S6 | official docs | Vitest | https://vitest.dev/guide/improving-performance | unknown | unknown | 2026-06-18 | current Vitest performance guide | Vitest performance tuning includes isolation, pool, sharding, concurrency, and transform/cache decisions. | yes | Current official docs for a local repo test runner. |
| S7 | official docs | Vitest | https://vitest.dev/config/ | unknown | unknown | 2026-06-18 | current Vitest config | Vitest has config-level isolation/pool/sequencing controls that can trade speed against isolation. | yes | Current official docs for local repo runner. |
| S8 | official docs | Playwright | https://playwright.dev/docs/test-parallel | unknown | 2026-06-17 | 2026-06-18 | Playwright Test | Playwright supports workers, full parallel mode, and serial mode; worker count and serial grouping affect runtime and isolation. | yes | Official docs updated one day before this pass. |
| S9 | official docs | Playwright | https://playwright.dev/docs/best-practices | unknown | 2026-06-17 | 2026-06-18 | Playwright Test | Playwright recommends web-first assertions, test isolation, parallelism, and sharding as best practices. | yes | Official docs updated one day before this pass. |
| S10 | official docs | Playwright | https://playwright.dev/docs/test-sharding | unknown | 2026-06-17 | 2026-06-18 | Playwright Test | Sharded runs need report merge handling; shard evidence should not replace a coherent final report. | yes | Official docs updated one day before this pass. |
| S11 | official docs | GitHub Actions | https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows | unknown | unknown | 2026-06-18 | GitHub Actions dependency cache | Cache key and restore-key behavior matter for safe CI speed work; cache misses/hits are evidence inputs. | yes | Current official CI docs for common provider. |
| S12 | official docs | GitHub Actions | https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts | unknown | unknown | 2026-06-18 | GitHub Actions artifacts | CI timing/report artifacts can preserve evidence across runs. | yes | Current official CI docs for common provider. |
| S13 | official docs | Gradle | https://docs.gradle.org/current/userguide/performance.html | unknown | 2026-05-12 | 2026-06-18 | current Gradle | Gradle performance guidance includes parallel execution, build cache, and test execution optimization. | yes | Current official docs, updated in 2026. |
| S14 | official docs | Maven Surefire | https://maven.apache.org/surefire/maven-surefire-plugin/examples/fork-options-and-parallel-execution.html | unknown | 2026-06-05 | 2026-06-18 | Maven Surefire | JVM test speed knobs include forking, reuse, and parallel execution; these are configuration-sensitive. | yes | Current plugin docs updated in June 2026. |
| S15 | official docs | coverage.py | https://coverage.readthedocs.io/en/7.9.1/config.html | unknown | unknown | 2026-06-18 | coverage.py 7.9.1 | Coverage thresholds such as `fail_under` and branch options are anti-cheat inputs. | yes | Versioned current docs. |
| S16 | official docs | coverage.py | https://coverage.readthedocs.io/en/7.9.1/branch.html | unknown | unknown | 2026-06-18 | coverage.py 7.9.1 | Branch coverage is stronger confidence evidence than line coverage alone when available. | yes | Versioned current docs. |
| S17 | official docs | Istanbul/nyc | https://github.com/istanbuljs/nyc | unknown | unknown | 2026-06-18 | current nyc README | JavaScript coverage tooling can enforce per-file and global thresholds. | yes | Primary project README for nyc behavior. |
| S18 | operator practice | Google Testing Blog | https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html | 2017-04 | unknown | 2026-06-18 | large-scale test flake practice | Ignoring flaky tests can hide production bugs; flake fixes should target root cause, not suppression. | no | Older but high-authority operator evidence; still about stable test-system behavior. |
| S19 | operator practice | Google Testing Blog | https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html | 2015-04 | unknown | 2026-06-18 | test pyramid operator guidance | Overusing E2E tends to increase runtime and flakes; moving coverage down can help when behavior remains covered. | no | Older but widely cited operator practice; used as heuristic, not tool-specific rule. |
| S20 | operator practice | Google Testing Blog | https://testing.googleblog.com/2020/08/code-coverage-best-practices.html | 2020-08 | unknown | 2026-06-18 | coverage practice | Coverage is useful for gaps and risk discussion; raw percentage alone is not a quality guarantee. | no | Current enough for coverage practice and used as anti-cheat framing. |
| S21 | operator practice | Martin Fowler | https://martinfowler.com/articles/nonDeterminism.html | 2011 | unknown | 2026-06-18 | nondeterministic test practice | Quarantine can reduce damage, but non-deterministic tests must be fixed; isolation and async waits are common causes. | no | Older but canonical operator guidance; corroborates current flake sources. |

external primary sources count: 17
operator practice sources count: 4
source_family_count: 12

## Improvement Backlog Tested

- Add a reusable goal-state and ledger contract like `$page-speed-optimizer`.
- Require native timing signals before ranking candidates.
- Treat parallelism and sharding as gated candidates, not default fixes.
- Track test-count, skipped/focused tests, and coverage threshold changes as anti-cheat checks.
- Include CI cache/report/artifact surfaces without locking the skill to GitHub Actions.
- Avoid a universal timing script because runner-native data is more reliable and stack-specific.

## Findings By Bucket

### Testing, Verification, And Observability

| finding_id | research_question_id | disposition | recommendation | recommendation_level | support_type | source_ids | execution_plan_sections_changed | disposition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | RQ1 | adopted | The skill should inventory native timing/report surfaces before inventing probes: pytest durations, Jest slow-test/open-handle options, Vitest reports, Playwright reports, CI job timing, JUnit/JSON/coverage artifacts when present. | adopt now | sourced + synthesis | S1, S4, S5, S6, S8, S10, S12 | Step 2 | Gives the skill evidence without binding it to one runner. |
| F2 | RQ3 | adopted | Confidence-preservation should check test count, skipped/focused tests, assertion weakening, coverage thresholds, branch coverage when available, and deleted/rewritten E2E coverage. | adopt now | sourced + synthesis | S5, S15, S16, S17, S20 | Step 2 | Prevents fake speed wins. |
| F3 | RQ4 | adopted | CI artifacts and cache hit/miss evidence should be in scope, but broad CI/provider changes should be gated when they affect cost, security, or org policy. | adopt now | sourced + inference | S11, S12 | Step 2, Step 3 | CI speed is real suite speed, but provider policy can be external. |

### Performance, Concurrency, And Failure Handling

| finding_id | research_question_id | disposition | recommendation | recommendation_level | support_type | source_ids | execution_plan_sections_changed | disposition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F4 | RQ2 | adopted | Parallelism, sharding, pooled workers, shared fixtures, DB reset changes, and service reuse must require isolation proof and at least one repeat or focused flake check when timing/order changed. | adopt now | sourced + synthesis | S2, S3, S6, S7, S8, S9, S10, S18, S21 | Step 2 | Multiple source families show speed knobs can expose or create ordering/state issues. |
| F5 | RQ2 | adopted | The skill should distinguish runner debug flags from representative speed measurements; flags like serial mode, open-handle detection, or low worker count can diagnose but should not prove optimized runtime unless intentionally configured. | adopt now | sourced + synthesis | S4, S8, S13, S14 | Step 2 | Avoids false timing claims from debug-only commands. |

### Architecture, Scope, And Workflow Shape

| finding_id | research_question_id | disposition | recommendation | recommendation_level | support_type | source_ids | execution_plan_sections_changed | disposition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F6 | RQ3 | adopted | Moving behavior out of slow E2E/browser tests into cheaper tests is valid only when the behavior remains covered through unit, integration, contract, or smoke checks that exercise the right boundary. | adopt now | operator practice + local judgment | S9, S19, S20 | Step 2 | Keeps speed work from hollowing out user-path protection. |
| F7 | RQ1 | rejected | Add one universal cross-runner timing script to the skill. | avoid | synthesis | S1, S4, S6, S8, S13, S14 | none | Too brittle across ecosystems; use runner-native reports and add probes only when native timing is missing. |
| F8 | RQ3 | rejected | Require 100% coverage or a universal coverage floor. | avoid | operator practice + source-backed judgment | S15, S16, S17, S20 | none | Raw coverage percentage can be gamed and is not the same as confidence. Preserve existing thresholds and explain meaningful gaps instead. |

## Adopt-Now Guidance

- Discover the runner and CI surfaces first: commands, configs, reports, coverage tools, CI jobs, caches, artifact paths, test categories, services, DB setup, and env needs.
- Measure current wall-clock and slowest candidates before patching.
- Rank by user feedback value: total CI time, local fast-loop time, slowest files, setup/teardown cost, flake pain, and maintainer burden.
- Prefer runner-native evidence. Add repo-local probes only when native timing or report data is missing.
- Treat parallelism/sharding/reused setup as candidates that need isolation proof.
- Preserve confidence with checks for skipped/focused tests, changed assertions, deleted coverage, threshold changes, branch/line coverage, and test-count movement.
- When moving coverage from E2E to cheaper tests, name the behavior that remains covered and the boundary it still exercises.

## Watchlist Or Avoid

- Watch: CI provider-specific optimizations. They can be useful, but a global skill should record generic rules and gate provider/cost/security decisions.
- Watch: test impact analysis and changed-test selection. Useful in mature repos, but risky as a first optimization unless there is already reliable dependency mapping.
- Avoid: deleting slow tests because they are slow.
- Avoid: adding blanket sleeps, retries, or quarantines as a speed or flake fix.
- Avoid: lowering coverage thresholds or switching off branch coverage to make a speed run pass.
- Avoid: treating one noisy faster run as proof.

## Load-Bearing Falsification Pass

| claim_id | claim | why_load_bearing | current_support_source_ids | strongest_counterevidence_or_gap | falsification_searches_or_sources | outcome | artifact_or_conclusion_change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | Parallelism should be a gated candidate, not an automatic fix. | Would change the skill from conservative to aggressive. | S2, S3, S6, S7, S8, S9, S10, S18, S21 | Counterpoint: runner docs promote parallelism and sharding as best practice. | Follow-up across Playwright, Vitest, pytest-xdist, Gradle, Maven docs. | survived | Plan adds isolation and flake gates instead of banning parallelism. |
| C2 | Confidence-preservation proof must include more than coverage percentage. | Would decide whether the skill can accept moving or deleting tests. | S15, S16, S17, S20 | Coverage tools support thresholds, so a threshold-only gate might seem enough. | Follow-up on coverage.py, nyc, Google coverage practice. | survived | Plan requires threshold preservation plus test-count/skip/assertion behavior checks. |
| C3 | A global skill should not own one universal timing script. | Would affect skill resources and maintenance cost. | S1, S4, S6, S8, S13, S14 | A script could normalize evidence across repos. | Follow-up on native runner timing and report surfaces. | survived | Plan keeps no script by default; implementation may add a reference schema only. |
| C4 | CI cache/artifact work belongs in scope but can be gated. | Would decide whether this is only local test optimization. | S11, S12 | CI cache changes may be outside a repo or policy-owned. | Follow-up on GitHub cache/artifact docs and local workflow. | survived | Plan includes CI surfaces but gates broad provider/cost/security changes. |

## Finding-to-Artifact Delta

| finding_id | research_question_id | bucket | disposition | recommendation | recommendation_level | support_type | source_ids | prd_tdd_sections_changed | execution_plan_sections_changed | task_plan_inputs_created | disposition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | RQ1 | testing/observability | adopted | Inventory native timing/report surfaces before probes. | adopt now | sourced + synthesis | S1,S4,S5,S6,S8,S10,S12 | not applicable | Step 2 | implementation checklist input | Improves evidence quality. |
| F2 | RQ3 | anti-cheat | adopted | Track test count, skips/focuses, assertions, coverage thresholds, and branch coverage. | adopt now | sourced + synthesis | S5,S15,S16,S17,S20 | not applicable | Step 2 | implementation checklist input | Prevents fake speed wins. |
| F3 | RQ4 | CI/artifacts | adopted | Include CI timing, cache, and artifact surfaces with approval gates for broad provider changes. | adopt now | sourced + inference | S11,S12 | not applicable | Step 2, Step 3 | implementation checklist input | Captures real feedback-loop cost. |
| F4 | RQ2 | concurrency/failure | adopted | Gate parallelism/sharding/service reuse on isolation and flake proof. | adopt now | sourced + synthesis | S2,S3,S6,S7,S8,S9,S10,S18,S21 | not applicable | Step 2 | implementation checklist input | Avoids introducing nondeterminism. |
| F5 | RQ2 | measurement | adopted | Separate diagnostic/debug timing from representative timing. | adopt now | sourced + synthesis | S4,S8,S13,S14 | not applicable | Step 2 | implementation checklist input | Prevents bad before/after claims. |
| F6 | RQ3 | test architecture | adopted | Allow E2E reduction only when the behavior remains covered at the right level. | adopt now | operator practice + judgment | S9,S19,S20 | not applicable | Step 2 | implementation checklist input | Preserves useful behavior coverage. |
| F7 | RQ1 | tooling | rejected | Universal timing script. | avoid | synthesis | S1,S4,S6,S8,S13,S14 | not applicable | none | none | Native tools vary too much. |
| F8 | RQ3 | coverage | rejected | Universal 100% coverage or arbitrary threshold. | avoid | operator practice + source-backed judgment | S15,S16,S17,S20 | not applicable | none | none | Easy to game and not plan-specific. |

## Risks And Unknowns

- The skill will be cross-stack by design, so its reference should define evidence shape and safety gates rather than runner-specific command recipes for every ecosystem.
- Some repos lack coverage or CI timing. In those cases, the skill should measure what exists and recommend adding evidence only when it is low-noise and useful.
- Test impact analysis, smart changed-test selection, and remote execution are powerful but should be watchlist topics unless a repo already has dependency mapping or mature CI support.

## Decision Checklist For Implementation

- Keep `SKILL.md` concise and put ledger/state details in `references/optimization-loop.md`.
- Make the default public contract no-mode like `$backend-optimizer` and `$page-speed-optimizer`.
- Add goal-state fields for baseline command, representative command, coverage command, test-count source, flake check, active candidate, and evidence paths.
- Add ledger fields for candidate type, runner, command, baseline duration, after duration, confidence evidence, isolation risk, disposition, and next action.
- Include scope routing to `$repo-sweep`, `$backend-optimizer`, `$page-speed-optimizer`, and `$bootstrap-repo-rules`.
- Validate README and contract ownership mirror behavior after adding the skill.

## Deep Research Completion Stamp

research_started_at: 2026-06-18T16:24:00-0700
research_completed_at: 2026-06-18T16:45:00-0700
elapsed_minutes: 21
duration_expectation_met: yes
under_20_minutes_explanation: not applicable
external_primary_sources_count: 17
operator_practice_sources_count: 4
source_family_count: 12
research_questions_answered: 4
buckets_reviewed: 5
follow_up_passes_completed: 3
load_bearing_claims_checked: 4
falsification_follow_up_passes_completed: 3
conclusions_changed_by_falsification: 0
adopted_findings_count: 6
rejected_or_deferred_findings_count: 2
prd_tdd_sections_changed: not applicable
execution_plan_sections_changed: Step 1, Step 2
task_plan_inputs_created: 6
evidence_bar_met: yes
