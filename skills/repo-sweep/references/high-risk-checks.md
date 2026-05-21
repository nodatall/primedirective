# Repo Sweep High-Risk Checks

Use this reference during `$repo-sweep` no-edit security, config, API-surface, and runtime probing.

## API And Config Inventory

- Do not edit code during this pass.
- Inventory entrypoints, routes, jobs, background workers, config defaults, auth boundaries, CORS policy, secret sources, and public state-changing endpoints before touching build or test failures.
- For backend or API repos, identify the concrete runtime entrypoints such as `main.py`, `server.js`, framework boot files, compose services, or dev scripts that expose the public surface.
- Treat "works locally" as insufficient evidence. Look for "works, but unsafe in production" risks before stabilization work begins.

## Mandatory Checks

- Public `POST`/`PUT`/`PATCH`/`DELETE` endpoints: probe for missing auth, weak authz, missing CSRF protection when relevant, and absent rate limiting.
- CORS: probe with arbitrary hostile origins and verify the real response headers, credential behavior, and origin matching rules.
- Secrets and config: scan for committed credentials, hardcoded secrets, unsafe defaults, and insecure fallbacks.
- Dev or mock behavior: verify debug, bootstrap, seed, admin, bypass, and mock flags default off for a fresh deployment.
- Env validation: verify required env vars fail closed rather than silently degrading to insecure or mock behavior.
- Destructive data paths: search scripts, tests, migrations, seed/reset/bootstrap jobs, and helper CLIs for `DROP`, `TRUNCATE`, broad `DELETE`, `CASCADE`, reset/recreate commands, and production-like connection strings. Verify they prefer isolated test env vars, positively identify disposable targets before mutating data, and refuse to run against production, shared dev, or ambiguous databases unless the user explicitly approved the exact operation.
- Public admin, debug, or internal endpoints: verify they are absent, disabled, or properly authenticated.
- For each check, capture concrete evidence from code, config, logs, command output, or runtime probes. Do not mark a check complete from code reading alone when the behavior can be executed safely. Do not execute destructive paths as proof unless the target is disposable and the command scope is explicit.
- When `--dep-scan` is present, run the dependency and supply-chain checklist after the baseline inventory and before the report. Record scanner output, missing tools, lockfile drift, install-script risk, CI action pinning, container base-image posture, license posture, and SBOM posture where applicable.

## Runtime Probing

- When the repo exposes HTTP, RPC, webhook, queue-consumer, CLI, or worker entrypoints that can be executed locally, run the service and probe the real interface.
- Use actual requests against the running app for representative entrypoints instead of relying only on unit tests or static inspection.
- If runtime probing is impossible, state exactly why and treat the corresponding area as a residual risk unless disproven by stronger evidence.
