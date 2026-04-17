---
name: repo-sweep
description: Run a full-repository sweep that always starts with a first-principles no-edit audit, then the full review chain, and pauses for approval before fixes. Supports `--preserve-review-artifacts`.
---

# Repo Sweep Skill

Run a full-repository sweep that separates first-principles detection from repair. The sweep should start from a broad mechanism-level understanding of the repository, expose production risks even when the repo "works" locally, cover the same review components and gates as the normal review chain, present a structured repo-wide report, and only then ask whether fixes should begin.

## Activation

Invoke explicitly with `$repo-sweep`.

Supported modifier:

- `--preserve-review-artifacts`

## Required references

Load these files before running:

- `skills/shared/references/review/review-protocol.md`
- `skills/first-principles-mode/references/analysis-rubric.md`

## Scope

- Treat the whole checked-out repository as the review and repair scope.
- Use code, config, CI definitions, and runtime behavior as ground truth.
- Use docs or specs only as secondary evidence when they clarify intent or reveal contradictions.
- Detect before repairing.
- Always run a first-principles no-edit pre-pass before normal review-chain prompts or fixes.
- Prefer verified findings over plausible theory.
- Do not edit files before the repo-wide report and explicit user approval to proceed with fixes.
- Include all normal review-chain components. For repo sweep, force a comprehensive review pass rather than a shortened provider-specific subset.

## Workflow

1. Establish the baseline.
   - Detect repo structure, frameworks, languages, package managers, monorepo layout, and tooling.
   - Read the actual verification sources: manifests, task runners, CI workflows, test configs, lint/typecheck/build scripts, docker files, and migration tooling.
   - Check `git status`, note whether the tree is dirty, and do not revert unrelated changes.
   - Identify missing env vars, broken assumptions, and install blockers.
2. Run a first-principles no-edit pre-pass.
   - Use `analysis-rubric.md` as the working rubric every time, not as an optional modifier.
   - Start wide before drilling into local issues: read enough of the repository to understand product intent, entrypoints, trust boundaries, data flow, runtime surfaces, operational wiring, and deploy assumptions.
   - Infer the repo's real risk shape from code and configuration rather than accepting docs, green tests, or the user's initial framing as sufficient.
   - Build materially different candidate risk explanations when more than one is plausible, such as auth-boundary weakness, configuration drift, untested integration behavior, operational fragility, or overbroad abstraction.
   - Look for evidence that would disconfirm the leading risk story before settling on it.
   - Keep the standalone first-principles skill's read-only posture, but do not stop after this pre-pass. In repo sweep, continue into the no-edit audit and review-chain evidence collection, then stop before fixes at the normal approval gate.
   - Carry one concise audit thesis into the repo-wide report so the findings are organized around mechanism, not only around file-local defects.
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
   - Public admin, debug, or internal endpoints: verify they are absent, disabled, or properly authenticated.
   - For each check, capture concrete evidence from code, config, logs, command output, or runtime probes. Do not mark a check complete from code reading alone when the behavior can be executed.
5. Require runtime probing where applicable.
   - When the repo exposes HTTP, RPC, webhook, queue-consumer, CLI, or worker entrypoints that can be executed locally, run the service and probe the real interface.
   - Use actual requests against the running app for representative entrypoints instead of relying only on unit tests or static inspection.
   - If runtime probing is impossible, state exactly why and treat the corresponding area as a residual risk unless disproven by stronger evidence.
6. Run the normal review chain components as part of the no-edit review phase.
   - Use the prompts from `review-protocol.md` as required review components for the repo sweep.
   - For repo sweep, force the comprehensive `full-chain` coverage: Prompt A through Prompt I, one prompt at a time.
   - Treat Prompt G and Prompt H with the same applicability rules as the normal review chain, but record them explicitly as executed or `not applicable`.
   - Record findings, fixes attempted, and test or probe evidence for each prompt, even when the fix field is `none during no-edit phase`.
   - Enforce the normal review-chain completion gates during reporting: do not mark the review phase complete while material verified findings are still hidden, unclassified, or hand-waved.
   - During this pre-fix review phase, use the prompts to deepen evidence collection and categorization, not to edit files.
7. Emit the repo-wide report before repairs.
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
8. Stop on a hard user gate after the report.
   - After presenting the report, explicitly ask whether the user wants fixes to proceed.
   - Do not patch files, change config, or "fix while reviewing" until the user answers yes.
   - If the user declines or does not answer, stop after the report.
9. After approval, run everything that defines repo health.
   - Run every relevant install, lint, format check, typecheck, test, build, migration, and security command defined by the repo or CI.
   - Treat any failing verification command as top priority.
10. Work in a fix-first stabilization loop.
   - Reproduce the failure.
   - Find the root cause from code.
   - Apply the smallest correct fix.
   - Re-run the affected command or flow.
   - Continue until green or blocked.
11. Sweep for high-value issues beyond verification.
   - Trace the top 5-10 core user or system journeys through entrypoint, handler, business logic, DB or side effects, and response or error handling.
   - Check actual routes, pages, jobs, integrations, schema, migrations, auth, validation, error handling, observability, and deployability.
   - Fix weak links when the remediation is clear and low-risk.
12. Run a dedicated final production-readiness and security pass after fixes.
   - Always run this pass after stabilization, regardless of model or prompt profile.
   - Re-run the relevant normal review-chain components needed to validate the repaired state, including Prompt H and Prompt I, plus Prompt G when frontend work was touched.
   - Re-check configuration externalization, rollback or migration safety, dependency and security hygiene, logging and monitoring visibility, performance-sensitive paths, and operational failure handling.
   - Re-confirm the high-risk API-surface findings against the post-fix state so repaired systems are not accidentally re-opened by later changes.
13. Stop only on a real blocker.
   - Ask the user only when the correct fix would change product behavior, auth rules, schema semantics, billing logic, customer-visible UX intent, or public API behavior in a non-obvious way.

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
