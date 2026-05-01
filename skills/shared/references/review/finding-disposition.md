# Finding Disposition

Use this reference when a review or sweep must turn findings into an actionable report or repair queue.

## Finding Shape

Each material finding should include:

- `Severity`: `P0`, `P1`, `P2`, or `P3`.
- `Disposition`: `fix`, `needs human decision`, `residual risk`, or `no action`.
- `Confidence`: `high`, `medium`, or `low`.
- `Evidence`: the concrete code, config, command, probe, log, screenshot, or artifact that proves or weakens the finding.
- `Impact`: the user, security, reliability, data, operational, or maintenance consequence.
- `Fix path`: the smallest credible repair or the reason the sweep cannot safely repair it.

Do not split actionable work into `fix now` and `fix soon`. If the issue is verified, in scope, and safe to repair without changing product intent or external contracts, its disposition is `fix`. If not, choose one of the non-fix dispositions.

## Dispositions

`fix` means the issue is verified, in scope, and safe to repair in the current execution context.

`needs human decision` means the correct repair depends on product behavior, auth/security policy, schema semantics, billing, customer-visible UX, public API contracts, infrastructure cost, legal/compliance posture, or another decision the agent should not silently make.

`residual risk` means the risk is plausible or important, but cannot be safely verified or repaired in the current local sweep. Include the missing evidence, blocker, or external dependency.

`no action` means the sweep investigated the concern and intentionally decided it is not a problem, not reachable, already guarded, duplicated by a stronger control, or out of scope.

## Looks Bad But Is Fine

Use a short `Looks bad but is fine` section when a repo contains patterns that are easy for future reviewers to misclassify.

Examples:

- Destructive SQL appears only in a test-only reset script that positively verifies a disposable database name before running.
- A publishable test key appears in `.env.example` and is not a secret.
- A broad permission exists only in a local dev fixture that cannot be reached from production startup paths.

Each entry still needs evidence. Do not use this section to bury unresolved risk.

## Loop Control

For repair loops:

1. Repair every `fix` finding that remains verified and in scope.
2. Stop for `needs human decision`.
3. Carry `residual risk` into the final handoff without silently patching it.
4. Do not repair `no action` items.
5. Resweep after repairs and stop only when a fresh sweep finds no remaining `fix` findings.
