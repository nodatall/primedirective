---
name: repo-sweep
description: Use when the user requests a fix-first full repository sweep via `begin repo review [--preserve-review-artifacts]` and needs repo-wide verification, issue discovery, safe fixes, critical-path tracing, and a short list of only unresolved blockers or human decisions.
---

# Repo Sweep Skill

Run a full-repository sweep that prioritizes fixing real issues over producing a long audit.

## Trigger

Accept:

- `begin repo review [--preserve-review-artifacts]`

## Scope

- Treat the whole checked-out repository as the review and repair scope.
- Use code, config, CI definitions, and runtime behavior as ground truth.
- Use docs or specs only as secondary evidence when they clarify intent or reveal contradictions.
- Prefer fixing over reporting.

## Workflow

1. Establish the baseline.
   - Detect repo structure, frameworks, languages, package managers, monorepo layout, and tooling.
   - Read the actual verification sources: manifests, task runners, CI workflows, test configs, lint/typecheck/build scripts, docker files, and migration tooling.
   - Check `git status`, note whether the tree is dirty, and do not revert unrelated changes.
   - Identify missing env vars, broken assumptions, and install blockers.
2. Run everything that defines repo health.
   - Run every relevant install, lint, format check, typecheck, test, build, migration, and security command defined by the repo or CI.
   - Treat any failing verification command as top priority.
3. Work in a fix-first loop.
   - Reproduce the failure.
   - Find the root cause from code.
   - Apply the smallest correct fix.
   - Re-run the affected command or flow.
   - Continue until green or blocked.
4. Sweep for high-value issues beyond verification.
   - Trace the top 5-10 core user or system journeys through entrypoint, handler, business logic, DB or side effects, and response or error handling.
   - Check actual routes, pages, jobs, integrations, schema, migrations, auth, validation, error handling, observability, and deployability.
   - Fix weak links when the remediation is clear and low-risk.
5. Run explicit high-risk checks.
   - Verify, do not assume, common failure modes such as missing rate limiting, weak authz, token storage in XSS-exposed browser storage, missing validation, unsafe webhook handling, unbounded queries, missing pagination, missing indexes, missing env validation, overly broad CORS, unsafe sync side effects, weak connection handling, missing error boundaries, leaked secrets, debug bypasses, dead code, or false-confidence CI gates.
6. Stop only on a real blocker.
   - Ask the user only when the correct fix would change product behavior, auth rules, schema semantics, billing logic, customer-visible UX intent, or public API behavior in a non-obvious way.

## Artifact behavior

- By default, keep working notes minimal and do not leave behind sweep artifacts.
- If `--preserve-review-artifacts` is present, keep a concise working log under `tasks/tmp/` when that directory exists and is already part of repo workflow. Otherwise preserve notes only when explicitly requested.

## Output

Keep output compact and action-oriented.

While working:

- give short progress updates
- say what you are running, what failed, and what you are fixing next

At the end, output only:

1. Fixed
2. Still failing
3. Needs human decision
4. Residual risks

Success means the repository is measurably healthier, not that you produced a long report.
