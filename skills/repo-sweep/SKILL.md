---
name: repo-sweep
description: Run a full-repository sweep that always starts with a first-principles no-edit audit, then the full review chain, and pauses for approval before fixes unless `--loop` is present. Supports `--pro-analysis`, `--loop`, and `--preserve-review-artifacts`.
---

# Repo Sweep Skill

Run a full-repository sweep that separates first-principles detection from repair. The sweep should start from a broad mechanism-level understanding of the repository, expose production risks even when the repo "works" locally, cover the same review components and gates as the normal review chain, present a structured repo-wide report, and only then ask whether fixes should begin.

## Activation

Invoke explicitly with `$repo-sweep`.

Supported modifiers:

- `--loop`
- `--pro-analysis`
- `--preserve-review-artifacts`

## Required references

Load these files before running:

- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/review/review-calibration.md`
- `skills/first-principles-mode/references/analysis-rubric.md`
- `skills/shared/references/reasoning-budget.md`
- `skills/shared/references/analysis/pro-oracle-escalation.md` when `--pro-analysis` is present

## Scope

- Treat the whole checked-out repository as the review and repair scope.
- Use code, config, CI definitions, and runtime behavior as ground truth.
- Use docs or specs only as secondary evidence when they clarify intent or reveal contradictions.
- Detect before repairing.
- Always run a first-principles no-edit pre-pass before normal review-chain prompts or fixes.
- Prefer verified findings over plausible theory.
- Do not edit files before the repo-wide report and explicit user approval to proceed with fixes, unless `--loop` is present.
- With `--loop`, the user has pre-approved the repair loop for verified, fixable findings. Still stop for changes that require a human product, security, schema, billing, customer-visible UX, or public API decision.
- With `--pro-analysis`, use ChatGPT Pro browser escalation as a Round 1 audit-thesis input through the shared Pro escalation reference. Do not run Oracle in every loop round unless a future modifier explicitly says so.
- Include all normal review-chain components. For repo sweep, force a comprehensive review pass rather than a shortened provider-specific subset.

## Workflow

1. Establish the baseline.
   - Detect repo structure, frameworks, languages, package managers, monorepo layout, and tooling.
   - Read the actual verification sources: manifests, task runners, CI workflows, test configs, lint/typecheck/build scripts, docker files, and migration tooling.
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
   - With `--pro-analysis`, run local repo reconnaissance, select context, dry-run the file bundle, run Oracle Pro, and synthesize the Pro result into the audit thesis before continuing to the no-edit audit.
   - Treat the Pro result as external reviewer input, not as source of truth. Verify or qualify Pro claims against local files, commands, probes, and tests.
   - If `--pro-analysis` and `--loop` are both present, use Pro only in Round 1 by default. Subsequent resweeps use fresh local review subagents unless the user explicitly asks for another Pro pass.
3. Run a no-edit security, config, and API-surface audit.
   - Do not edit code in this step.
   - Inventory entrypoints, routes, jobs, background workers, config defaults, auth boundaries, CORS policy, secret sources, and public state-changing endpoints before touching build or test failures.
   - For backend or API repos, identify the concrete runtime entrypoints such as `main.py`, `server.js`, framework boot files, compose services, or dev scripts that expose the public surface.
   - Treat "works locally" as insufficient evidence. Look for "works, but unsafe in production" risks before stabilization work begins.
4. Perform mandatory high-risk checks with evidence.
   - Public `POST`/`PUT`/`PATCH`/`DELETE` endpoints: probe for missing auth, weak authz, missing CSRF protection when relevant, and absent rate limiting.
   - CORS: probe with arbitrary hostile origins and verify the real response headers, credential behavior, and origin matching rules.
   - Secrets and config: scan for committed credentials, hardcoded secrets, unsafe defaults, and insecure fallbacks.
   - Dev or mock behavior: verify debug, bootstrap, seed, admin, bypass, and mock flags default off for a fresh deployment.
   - Env validation: verify required env vars fail closed rather than silently degrading to insecure or mock behavior.
   - Destructive data paths: search scripts, tests, migrations, seed/reset/bootstrap jobs, and helper CLIs for `DROP`, `TRUNCATE`, broad `DELETE`, `CASCADE`, reset/recreate commands, and production-like connection strings. Verify they prefer isolated test env vars, positively identify disposable targets before mutating data, and refuse to run against production, shared dev, or ambiguous databases unless the user explicitly approved the exact operation.
   - Public admin, debug, or internal endpoints: verify they are absent, disabled, or properly authenticated.
   - For each check, capture concrete evidence from code, config, logs, command output, or runtime probes. Do not mark a check complete from code reading alone when the behavior can be executed safely. Do not execute destructive paths as proof unless the target is disposable and the command scope is explicit.
5. Run a go-live readiness pass for deployable web/API services.
   - Apply this pass when the repo exposes a production web app, API, worker, upload flow, websocket/realtime feature, background job, database-backed service, or third-party integration. For local-only CLIs, libraries, prototypes, and non-deployable tools, mark the irrelevant items `not applicable` with a short reason.
   - Check load and capacity evidence: load/stress test command, known traffic limit, rate-limit behavior, and the highest-risk bottleneck if no load test exists.
   - Check horizontal scale assumptions: server-memory sessions, in-memory queues, in-memory rate limits, websocket state, local disk state, and whether multiple app instances would preserve behavior.
   - Check file uploads and static assets: uploads should not depend on ephemeral app-server disk for durable storage, and large/static assets should have an object-storage/CDN path when traffic volume warrants it.
   - Check background work: email sending, webhooks, image/video processing, AI calls, report generation, and other slow tasks should not block latency-sensitive API routes unless the synchronous behavior is explicitly acceptable.
   - Check queue and worker behavior where background tasks exist: retry policy, dead-letter/failure visibility, idempotency, and whether one slow task can block unrelated work.
   - Check database production readiness: indexed join/filter columns for hot paths, transactions for multi-step writes, migration race safety, test/seed/reset isolation, backup existence, and restore-test evidence or a residual-risk note.
   - Check HTTP/runtime safety: compression for large responses, health checks, graceful shutdown, bounded request/body sizes where relevant, and no deploy-time behavior that can corrupt shared state.
   - Check outbound dependency resilience: connection timeouts, bounded retries, circuit breakers or load-shedding where relevant, fallback/degradation behavior, and clear failure logging.
   - Check logs and incident readiness: logs should not be local-disk-only for deployable services, errors should be alertable, and common incidents should have a runbook or at least an explicit residual-risk note.
   - Report each applicable item as `verified`, `finding`, `not applicable`, or `residual risk`. Do not convert every missing launch-hardening item into an automatic fix; stop for product, cost, infrastructure, data, or operational decisions.
6. Require runtime probing where applicable.
   - When the repo exposes HTTP, RPC, webhook, queue-consumer, CLI, or worker entrypoints that can be executed locally, run the service and probe the real interface.
   - Use actual requests against the running app for representative entrypoints instead of relying only on unit tests or static inspection.
   - If runtime probing is impossible, state exactly why and treat the corresponding area as a residual risk unless disproven by stronger evidence.
7. Run the normal review chain components as part of the no-edit review phase.
   - Use the prompts from `review-protocol.md` as required review components for the repo sweep.
   - For repo sweep, force the comprehensive `full-chain` coverage: Prompt A through Prompt I, one prompt at a time.
   - Treat Prompt G and Prompt H with the same applicability rules as the normal review chain, but record them explicitly as executed or `not applicable`.
   - Record findings, fixes attempted, and test or probe evidence for each prompt, even when the fix field is `none during no-edit phase`.
   - Enforce the normal review-chain completion gates during reporting: do not mark the review phase complete while material verified findings are still hidden, unclassified, or hand-waved.
   - During this pre-fix review phase, use the prompts to deepen evidence collection and categorization, not to edit files.
8. Emit the repo-wide report before repairs.
   - Open with a short `Audit Thesis` paragraph from the first-principles pre-pass.
   - Before making substantive fixes, report the verified findings already discovered, ordered by severity inside clear sections.
   - Use these sections:
     - `Security`
     - `Architecture and Design`
     - `Logic and Stability`
     - `Testing and Verification`
     - `Code Quality and Maintainability`
     - `Performance and Operations`
     - `Needs Human Decision`
     - `Residual Risks`
   - If a section has no verified findings, say `none verified`.
   - Keep the report concise, but do not bury serious production risks behind lower-priority cleanup.
9. Stop on a hard user gate after the report unless `--loop` is present.
   - After presenting the report, explicitly ask whether the user wants fixes to proceed.
   - Do not patch files, change config, or "fix while reviewing" until the user answers yes.
   - If the user declines or does not answer, stop after the report.
   - With `--loop`, skip this approval gate because the modifier is the approval to proceed with the bounded sweep/fix loop.
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

## Loop Mode

`--loop` turns repo sweep into a bounded sweep/fix/resweep workflow.

Use this mode when the user wants the agent to keep improving the repository without stopping after the first report. It is still a repo sweep: every round starts with detection, keeps evidence for findings, and uses fresh review context before deciding whether more work remains.

Rules:

- Maximum 8 rounds. If the user asks for more, cap at 8 and say so in the final summary.
- Round 1 still runs the full first-principles no-edit pre-pass, no-edit audit, runtime probes when applicable, and comprehensive review-chain coverage.
- Emit a concise Round 1 repo-wide report before fixes, but do not ask for approval unless a human decision is required.
- Fix only verified, in-scope, actionable findings where the repair is clear enough to make without changing product intent or external contracts.
- After fixes and validation for a round, start the next sweep in one fresh dedicated review subagent/thread when subagents are available.
- Each loop review subagent owns detection for that round only. The main agent owns orchestration, edits, verification, loop stop decisions, artifact cleanup, and the final user summary.
- Do not reuse the previous round's reviewer as evidence that the current state is clean. A clean stop requires a fresh resweep after the latest fixes.
- Stop early when a fresh resweep finds no verified in-scope findings that should be fixed.
- Stop early when all remaining findings require a human decision, cannot be reproduced, cannot be safely fixed, or are explicitly out of scope.
- Do not create new branches, commits, pushes, or PRs unless the user separately asked for those git actions.
- Do not loop on cosmetic preferences, speculative risks, or issues where the only remaining action is broader product redesign.

Loop round shape:

1. `Detect`: run the sweep/review pass for the current repo state.
2. `Classify`: split findings into fix-now, human-decision, residual-risk, and no-action.
3. `Fix`: address fix-now findings with the smallest correct changes.
4. `Verify`: run targeted checks plus any repo-health commands affected by the fixes.
5. `Resweep`: spawn a fresh review subagent for the next detection round, unless max rounds or a stop condition was reached.

For final output in loop mode, include:

1. Loop rounds completed and why the loop stopped.
2. Fixed findings by round.
3. Verification commands and outcomes.
4. Remaining human-decision items.
5. Residual risks.

## Artifact behavior

- By default, keep working notes minimal and do not leave behind sweep artifacts.
- If `--preserve-review-artifacts` is present, keep a concise working log under `tasks/tmp/` when that directory exists and is already part of repo workflow. Otherwise preserve notes only when explicitly requested.

## Output

Keep output compact and action-oriented.

While working:

- give short progress updates
- say what you are running, what failed, and whether you are still in review mode or have started the approved fix phase
- explicitly say when the first-principles pre-pass is complete and what risk thesis is driving the rest of the audit
- after the no-edit audit and review-chain passes, emit the structured repo-wide report before repairs begin
- after the report, stop and ask a direct yes-or-no question about whether to proceed with fixes

Before any fixes, output the repo-wide report in this order:

1. Audit Thesis
2. Security
3. Architecture and Design
4. Logic and Stability
5. Testing and Verification
6. Code Quality and Maintainability
7. Performance and Operations
8. Needs Human Decision
9. Residual Risks
10. Fix Recommendation

After approved fixes, output only:

1. Initial repo-wide report summary
2. Fixed
3. Still failing
4. Needs human decision
5. Residual risks

Success before fixes means the report is evidence-backed, broad enough to surface the major production risks on the reachable surface, and explicit about what remains unverified.

Success after fixes means the repository is measurably healthier, the approved in-scope issues were addressed or cleanly escalated, and no obvious production-safety regressions remain on the verified public surface.

For backend and API repos, do not mark the sweep successful while any of these remain true on the verified public surface:

- public unsafe admin or debug endpoints exist without auth
- credentialed wildcard CORS is allowed
- committed secrets or secret fallbacks remain
- dev or mock behavior is enabled by default
- unguarded destructive data scripts, tests, migrations, or maintenance commands can target production, shared dev, or ambiguous databases
