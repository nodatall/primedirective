# Finding Disposition

Use this reference when a review, refinement pass, execution review, or sweep must turn findings into an actionable report or repair queue.

## Finding Shape

Each material finding should include these shared fields:

- `Severity`: `P0`, `P1`, `P2`, or `P3`.
- `Execution gate`: `blocks execution`, `blocks finalization`, `fix before completion`, `human decision`, `residual risk`, or `no action`.
- `Disposition`: `fix`, `needs human decision`, `residual risk`, or `no action`.
- `Confidence`: `high`, `medium`, or `low`.
- `Scope`: the task, branch, prompt, artifact, route, screen, command, or repo area the finding applies to.
- `Evidence`: the concrete code, config, command, probe, log, screenshot, or artifact that proves or weakens the finding.
- `Impact`: the user, security, reliability, data, operational, or maintenance consequence.
- `Fix path`: the smallest credible repair or the reason the sweep cannot safely repair it.
- `Owner`: `main agent`, `review subagent`, `planning/refinement`, `user`, or a specific repo/system owner when known.

Do not split actionable work into `fix now` and `fix soon`. If the issue is verified, in scope, and safe to repair without changing product intent or external contracts, its disposition is `fix`. If not, choose one of the non-fix dispositions.

Planning refinement may keep its local severity words `blocker`, `material`, and `minor` for stop logic. When refinement findings are reported outside `$plan-refine`, map them into the shared shape:

- `blocker` maps to `P1` or `P0` with `Execution gate: blocks execution`.
- `material` maps to `P2` with `Execution gate: fix before completion`.
- `minor` maps to `P3` with `Execution gate: no action` unless it is needed to keep a blocker/material fix coherent.

Review prompts are detect-first. A review subagent owns finding discovery and evidence. The main agent owns disposition, repair decisions, file edits, test reruns, commits, and final handoff, unless the user explicitly asked for a read-only review.

Do not use this schema as ceremony for trivial notes. Apply it to material findings that affect execution, review completion, safety, correctness, verification confidence, or operator handoff quality.

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
