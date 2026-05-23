---
name: repo-sweep
description: Run a full-repository sweep that always starts with a first-principles no-edit audit, then the full review chain, and pauses for approval before fixes. Invoke inside `/goal $repo-sweep` for a repair/resweep goal. Supports `--pro-analysis`, `--swarm`, `--dep-scan`, and `--preserve-review-artifacts`; `--swarm` includes nitpick-depth maintainability review by default.
---

# Repo Sweep Skill

Run a full-repository sweep that separates first-principles detection from repair. The sweep should start from a broad mechanism-level understanding of the repository, expose production risks even when the repo "works" locally, cover the same review components and gates as the normal review chain, present a structured repo-wide report, and only then ask whether fixes should begin.

## Activation

Invoke explicitly with `$repo-sweep`.

Invoke inside a Codex goal when the user wants the bounded repair/resweep loop:

```text
/goal $repo-sweep
```

If the user asks for a repo-sweep loop, repeated fixing, or "keep going until clean" outside a goal, prepare or give the exact `/goal $repo-sweep` command instead of using a `--loop` modifier.

Supported modifiers:

- `--pro-analysis`
- `--swarm`
- `--dep-scan`
- `--preserve-review-artifacts`

## References

Load references by path, not all up front:

- Always load `skills/shared/references/review/review-protocol.md`, `skills/shared/references/review/review-calibration.md`, `skills/shared/references/review/finding-disposition.md`, `skills/shared/references/architecture/architecture-guidance.md`, `skills/first-principles-mode/references/analysis-rubric.md`, and `skills/shared/references/reasoning-budget.md`.
- `skills/shared/references/review/swarm-lanes.md` and `skills/repo-sweep/references/nitpick-depth.md` when `--swarm` is present
- `skills/shared/references/review/dep-audit-checklist.md` when `--dep-scan` is present
- `skills/shared/references/analysis/pro-browser-analysis.md` when `--pro-analysis` is present
- `skills/repo-sweep/references/high-risk-checks.md` for API, config, security, destructive-path, and runtime-probe checks
- `skills/repo-sweep/references/go-live-readiness.md` for deployable service readiness
- `skills/repo-sweep/references/report-format.md` before emitting the repo-wide report
- `skills/repo-sweep/references/goal-mode.md` when invoked inside `/goal $repo-sweep`

## Scope

- Treat the whole checked-out repository as the review and repair scope.
- Use code, config, CI definitions, and runtime behavior as ground truth.
- Use docs or specs only as secondary evidence when they clarify intent or reveal contradictions.
- Detect before repairing.
- Always run a first-principles no-edit pre-pass before normal review-chain prompts or fixes.
- Prefer verified findings over plausible theory.
- Do not edit files before the repo-wide report and explicit user approval to proceed with fixes.
- Inside `/goal $repo-sweep`, the goal invocation is approval for a bounded repair/resweep loop on verified, fixable findings after the Round 1 report is recorded. Still stop for changes that require a human product, security, schema, billing, customer-visible UX, or public API decision.
- With `--pro-analysis`, use ChatGPT Pro browser analysis as a Round 1 audit-thesis input through the shared Pro browser reference. Do not run Pro in every resweep round unless a future modifier explicitly says so.
- With `--swarm`, run the optional read-only specialized lanes from `swarm-lanes.md` plus the nitpick-depth maintainability checks from `nitpick-depth.md` as discovery input before the report. The main agent still verifies, deduplicates, classifies, and owns the final findings.
- With `--dep-scan`, run the dependency and supply-chain audit from `dep-audit-checklist.md`. If required scanners are unavailable, report the unavailable checks as residual risk instead of silently skipping them.
- Include all normal review-chain components. For repo sweep, force a comprehensive review pass rather than a shortened provider-specific subset.

## Workflow

1. Establish the baseline.
   - Detect repo structure, frameworks, languages, package managers, monorepo layout, and tooling.
   - Read `docs/ARCHITECTURE.md` when it exists and use it as the repo's boundary contract.
   - Read the actual verification sources: manifests, task runners, CI workflows, test configs, lint/typecheck/build scripts, docker files, and migration tooling.
   - Inspect recent churn and file-size hotspots before judging the repo: use git history and line counts to identify the largest files, most frequently changed files, and any overlap between the two. Treat that overlap as an audit-prioritization signal, not as proof of debt.
   - Identify maintainability hotspots: godfiles, duplicated local patterns, unclear module boundaries, shallow pass-through modules, adapter seams with only one real adapter, brittle abstractions, hard-to-test paths, missing runnable feedback loops, and places where a future agent would have to infer behavior from scattered or stale clues.
   - For suspected shallow modules, use the deletion test from `architecture-guidance.md`: would deleting the module remove complexity, or would the same complexity spread across callers?
   - Use `architecture-guidance.md` to compare the repo against `docs/ARCHITECTURE.md` when it exists, flagging stale docs, missing modules, forbidden dependency edges, undocumented entrypoints, expired deviations, and shared-code drift.
   - When `docs/ARCHITECTURE.md` is missing, still report generic architecture smells when evidence supports them, but label those findings as inferred rather than contract drift.
   - Do not report technical debt from size, churn, or style alone. A debt finding needs exact files or lines, a concrete maintenance cost, user or engineering impact, and a credible fix path.
   - Check `git status`, note whether the tree is dirty, and do not revert unrelated changes.
   - Identify missing env vars, broken assumptions, and install blockers.
2. Run a first-principles no-edit pre-pass.
   - Follow `reasoning-budget.md`: the first-principles audit and review/resweep subagents use the strongest appropriate reasoning tier, fix workers use strong reasoning, and mechanical verification/cleanup uses medium or standard reasoning.
   - Use `analysis-rubric.md` as the working rubric every time, not as an optional modifier.
   - Start wide before drilling into local issues: read enough of the repository to understand product intent, entrypoints, trust boundaries, data flow, runtime surfaces, operational wiring, and deploy assumptions.
   - Infer the repo's real risk shape from code and configuration rather than accepting docs, green tests, or the user's initial framing as sufficient.
   - Build materially different candidate risk explanations when more than one is plausible, such as auth-boundary weakness, configuration drift, untested integration behavior, operational fragility, or overbroad abstraction.
   - Look for evidence that would disconfirm the leading risk story before settling on it.
   - Keep the standalone first-principles skill's read-only posture, but do not stop after this pre-pass. In repo sweep, continue into the no-edit audit and review-chain evidence collection, then stop before fixes at the normal approval gate.
   - Carry one concise audit thesis into the repo-wide report so the findings are organized around mechanism, not only around file-local defects.
   - With `--pro-analysis`, run local repo reconnaissance, select context, drive the visible ChatGPT Pro browser pass, and synthesize the Pro result into the audit thesis before continuing to the no-edit audit.
   - Treat the Pro result as external reviewer input, not as source of truth. Verify or qualify Pro claims against local files, commands, probes, and tests.
   - If `--pro-analysis` is active inside `/goal $repo-sweep`, use Pro only in Round 1 by default. Subsequent resweeps use fresh local review subagents unless the user explicitly asks for another Pro pass.
   - If `--swarm` is present, use the swarm lanes and nitpick-depth checks as additional candidate-risk generators, not as final authority. Merge their output through the finding disposition rules before reporting or fixing.
3. Run a no-edit security, config, and API-surface audit.
   - Use `skills/repo-sweep/references/high-risk-checks.md`.
   - Do not edit code in this step.
   - Inventory public surfaces before touching build or test failures.
   - Treat "works locally" as insufficient evidence.
4. Perform mandatory high-risk checks with evidence.
   - Use `skills/repo-sweep/references/high-risk-checks.md`.
   - Cover public state-changing endpoints, CORS, secrets/config, dev/mock defaults, env validation, destructive data paths, public admin/debug/internal endpoints, and concrete evidence capture.
   - When `--dep-scan` is present, run `skills/shared/references/review/dep-audit-checklist.md` after the baseline inventory and before the report.
5. Run a go-live readiness pass for deployable web/API services.
   - Use `skills/repo-sweep/references/go-live-readiness.md`.
   - Apply it when the repo exposes deployable services or integrations.
   - Mark irrelevant items `not applicable` with a short reason.
6. Require runtime probing where applicable.
   - Use the runtime-probing rules in `skills/repo-sweep/references/high-risk-checks.md`.
7. Run the normal review chain components as part of the no-edit review phase.
   - Use the prompts from `review-protocol.md` as required review components for the repo sweep.
   - For repo sweep, force the comprehensive `full-chain` coverage: Prompt A through Prompt I, one prompt at a time.
   - `full-chain` is mandatory for repo sweep even when normal Codex task reviews would select the shorter Codex prompt profile.
   - With `--swarm`, ensure Prompt C, Prompt D, Prompt E, Prompt F, and Prompt I run even if the rest of the review work is delegated to swarm lanes. Run Prompt G and Prompt H when their normal applicability rules are met.
   - Treat Prompt G and Prompt H with the same applicability rules as the normal review chain, but record them explicitly as executed or `not applicable`.
   - Record findings, repair authorization, and test or probe evidence for each prompt. During the pre-fix no-edit phase, the fix field must be `none during no-edit phase`.
   - Enforce the normal review-chain completion gates during reporting: do not mark the review phase complete while material verified findings are still hidden, unclassified, or hand-waved.
   - During this pre-fix review phase, use the prompts to deepen evidence collection and categorization, not to edit files.
8. Emit the repo-wide report before repairs.
   - Use `skills/repo-sweep/references/report-format.md`.
   - Open with the `Audit Thesis`.
   - Report verified findings before repairs.
   - With `--swarm`, include a compact nitpick-depth summary: hotspots inspected, hotspots intentionally not inspected, accepted maintainability/test-quality/product-surface findings, and rejected false positives under `Looks Bad But Fine`.
9. Stop on a hard user gate after the report unless invoked inside `/goal $repo-sweep`.
   - After presenting the report, explicitly ask whether the user wants fixes to proceed.
   - Do not patch files, change config, or "fix while reviewing" until the user answers yes.
   - If the user declines or does not answer, stop after the report.
   - Inside `/goal $repo-sweep`, record the Round 1 report in the goal state and continue because the goal invocation is the approval to proceed with the bounded sweep/fix/resweep loop.
10. After approval, run everything that defines repo health.
   - Run every relevant install, lint, format check, typecheck, test, build, migration, and security command defined by the repo or CI.
   - Treat any failing verification command as top priority.
11. Work in a fix-first stabilization loop.
   - Reproduce the failure.
   - Find the root cause from code.
   - Apply the smallest correct fix.
   - Re-run the affected command or flow.
   - Continue until green or blocked.
12. Sweep for high-value issues beyond verification.
   - Trace the top 5-10 core user or system journeys through entrypoint, handler, business logic, DB or side effects, and response or error handling.
   - Check actual routes, pages, jobs, integrations, schema, migrations, auth, validation, error handling, observability, and deployability.
   - Fix weak links when the remediation is clear and low-risk.
13. Run a dedicated final production-readiness and security pass after fixes.
   - Always run this pass after stabilization, regardless of model or prompt profile.
   - Re-run the relevant normal review-chain components needed to validate the repaired state, including Prompt H and Prompt I, plus Prompt G when frontend work was touched.
   - Re-check configuration externalization, rollback or migration safety, dependency and security hygiene, logging and monitoring visibility, performance-sensitive paths, and operational failure handling.
   - Re-run the applicable go-live readiness checks for deployable services and update any fixed findings or residual risks.
   - Re-confirm the high-risk API-surface findings against the post-fix state so repaired systems are not accidentally re-opened by later changes.
14. Stop only on a real blocker.
   - Ask the user only when the correct fix would change product behavior, auth rules, schema semantics, billing logic, customer-visible UX intent, or public API behavior in a non-obvious way.

## Goal Mode

`/goal $repo-sweep` turns repo sweep into a sweep/fix/resweep workflow. Use `skills/repo-sweep/references/goal-mode.md` for the detailed goal-state rules, round shape, stop conditions, and final output.

## Artifact behavior

- By default, keep working notes minimal and do not leave behind sweep artifacts.
- If `--preserve-review-artifacts` is present, keep a concise working log under `tasks/tmp/` when that directory exists and is already part of repo workflow. Otherwise preserve notes only when explicitly requested.

## Output

Keep output compact and action-oriented.

While working:

- give short progress updates
- say what you are running, what failed, and whether you are still in review mode or have started the approved fix phase
- explicitly say when the first-principles pre-pass is complete and what risk thesis is driving the rest of the audit
- when `--swarm` is active, explicitly say that nitpick depth is included and which maintainability/code-quality hotspots are being inspected
- after the no-edit audit and review-chain passes, emit the structured repo-wide report before repairs begin
- after the report, stop and ask a direct yes-or-no question about whether to proceed with fixes

Use `skills/repo-sweep/references/report-format.md` for before-fix report order, after-fix report order, success criteria, and backend/API hard-stop conditions.
