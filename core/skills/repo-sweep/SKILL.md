---
name: repo-sweep
description: Use when the user requests `begin repo review [--report-only] [--preserve-review-artifacts]` and needs a full-repository sweep that starts with an adversarial no-edit security/config/API-surface audit, then either reports verified issues only or continues into repair and a closing production-readiness pass.
---

# Repo Sweep Skill

Run a full-repository sweep that separates adversarial detection from repair. The sweep should expose production risks even when the repo "works" locally, then fix what is safe and in scope.

## Trigger

Accept:

- `begin repo review [--report-only] [--preserve-review-artifacts]`

## Scope

- Treat the whole checked-out repository as the review and repair scope.
- Use code, config, CI definitions, and runtime behavior as ground truth.
- Use docs or specs only as secondary evidence when they clarify intent or reveal contradictions.
- Detect before repairing.
- Prefer verified findings over plausible theory.
- Prefer fixing over reporting only after the first findings checkpoint.

## Workflow

Mode selection:

- Default mode: audit, findings checkpoint, stabilization fixes, final production-readiness pass.
- `--report-only`: audit, findings checkpoint, optional verification commands needed to confirm impact, then stop without making code edits.

1. Establish the baseline.
   - Detect repo structure, frameworks, languages, package managers, monorepo layout, and tooling.
   - Read the actual verification sources: manifests, task runners, CI workflows, test configs, lint/typecheck/build scripts, docker files, and migration tooling.
   - Check `git status`, note whether the tree is dirty, and do not revert unrelated changes.
   - Identify missing env vars, broken assumptions, and install blockers.
2. Run a no-edit security, config, and API-surface audit first.
   - Do not edit code in this step.
   - Inventory entrypoints, routes, jobs, background workers, config defaults, auth boundaries, CORS policy, secret sources, and public state-changing endpoints before touching build or test failures.
   - For backend or API repos, identify the concrete runtime entrypoints such as `main.py`, `server.js`, framework boot files, compose services, or dev scripts that expose the public surface.
   - Treat "works locally" as insufficient evidence. Look for "works, but unsafe in production" risks before stabilization work begins.
3. Perform mandatory high-risk checks with evidence.
   - Public `POST`/`PUT`/`PATCH`/`DELETE` endpoints: probe for missing auth, weak authz, missing CSRF protection when relevant, and absent rate limiting.
   - CORS: probe with arbitrary hostile origins and verify the real response headers, credential behavior, and origin matching rules.
   - Secrets and config: scan for committed credentials, hardcoded secrets, unsafe defaults, and insecure fallbacks.
   - Dev or mock behavior: verify debug, bootstrap, seed, admin, bypass, and mock flags default off for a fresh deployment.
   - Env validation: verify required env vars fail closed rather than silently degrading to insecure or mock behavior.
   - Public admin, debug, or internal endpoints: verify they are absent, disabled, or properly authenticated.
   - For each check, capture concrete evidence from code, config, logs, command output, or runtime probes. Do not mark a check complete from code reading alone when the behavior can be executed.
4. Require runtime probing where applicable.
   - When the repo exposes HTTP, RPC, webhook, queue-consumer, CLI, or worker entrypoints that can be executed locally, run the service and probe the real interface.
   - Use actual requests against the running app for representative entrypoints instead of relying only on unit tests or static inspection.
   - If runtime probing is impossible, state exactly why and treat the corresponding area as a residual risk unless disproven by stronger evidence.
5. Emit a findings checkpoint before repairs.
   - Before making substantive fixes, report the top verified findings already discovered, ordered by severity.
   - Keep the checkpoint short, but do not bury serious production risks behind later stabilization notes.
   - If no verified findings exist yet, say so explicitly and continue.
6. If `--report-only` is set, continue gathering evidence without edits, then stop after the final production-readiness summary.
   - You may still run verification commands, start services, and probe runtime behavior to confirm severity or scope.
   - Do not patch files, change config, or "fix while reviewing" in this mode.
   - Prefer breadth after the first verified finding: continue enumerating additional high-value issues instead of stopping at the first blocker unless the environment cannot be exercised further.
7. Run everything that defines repo health.
   - Run every relevant install, lint, format check, typecheck, test, build, migration, and security command defined by the repo or CI.
   - Treat any failing verification command as top priority.
8. Work in a fix-first stabilization loop.
   - Reproduce the failure.
   - Find the root cause from code.
   - Apply the smallest correct fix.
   - Re-run the affected command or flow.
   - Continue until green or blocked.
9. Sweep for high-value issues beyond verification.
   - Trace the top 5-10 core user or system journeys through entrypoint, handler, business logic, DB or side effects, and response or error handling.
   - Check actual routes, pages, jobs, integrations, schema, migrations, auth, validation, error handling, observability, and deployability.
   - Fix weak links when the remediation is clear and low-risk.
10. Run a dedicated final production-readiness and security pass.
   - Always run this pass after stabilization, regardless of model or prompt profile.
   - In `--report-only` mode, run this as an evidence-gathering and risk-summarization pass with no code edits.
   - Use a Prompt-H-style review: verify deployment readiness with evidence, not assertions.
   - Re-check configuration externalization, rollback or migration safety, dependency and security hygiene, logging and monitoring visibility, performance-sensitive paths, and operational failure handling.
   - Re-confirm the high-risk API-surface findings against the post-fix state so repaired systems are not accidentally re-opened by later changes.
11. Stop only on a real blocker.
   - Ask the user only when the correct fix would change product behavior, auth rules, schema semantics, billing logic, customer-visible UX intent, or public API behavior in a non-obvious way.

## Artifact behavior

- By default, keep working notes minimal and do not leave behind sweep artifacts.
- If `--preserve-review-artifacts` is present, keep a concise working log under `tasks/tmp/` when that directory exists and is already part of repo workflow. Otherwise preserve notes only when explicitly requested.

## Output

Keep output compact and action-oriented.

While working:

- give short progress updates
- say what you are running, what failed, and what you are fixing next
- after the no-edit audit, emit a brief findings checkpoint before repairs begin
- in `--report-only` mode, say what evidence you are collecting next instead of what you are fixing next

At the end, output only:

1. Findings checkpoint
2. Fixed
3. Still failing
4. Needs human decision
5. Residual risks

In `--report-only` mode:

- `Fixed` should be `none`
- `Still failing` should list verified breakages or unsafe behaviors without proposing that they were remediated
- `Residual risks` should include anything that could not be executed or disproven

Success means the repository is measurably healthier and no obvious production-safety regressions remain on the verified public surface.

In `--report-only` mode, success means the report is evidence-backed, broad enough to surface the major production risks on the reachable surface, and explicit about what remains unverified.

For backend and API repos, do not mark the sweep successful while any of these remain true on the verified public surface:

- public unsafe admin or debug endpoints exist without auth
- credentialed wildcard CORS is allowed
- committed secrets or secret fallbacks remain
- dev or mock behavior is enabled by default
