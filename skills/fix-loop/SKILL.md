---
name: fix-loop
description: Reproduce a concrete failing behavior, root-cause it, patch it, rerun the actual failing flow, inspect fresh evidence, and repeat until verified fixed or blocked. Use when invoked with `$fix-loop`, or when the user asks to root-cause and fix a specific broken backend, frontend, app, CLI, test, runtime, integration, or UI behavior.
---

# Fix Loop Skill

Run a bounded reproduce/fix/retry loop for one concrete broken behavior.

This skill is for targeted repair, not repo-wide audit or planned multi-step execution. Use `$deliver` for planned implementation, `/goal $repo-sweep` for broad repository repair/resweep goals, and `$review-chain` for review-only work.

Load `skills/shared/references/analysis/verification-pivot.md` before starting.

## Activation

Invoke explicitly with `$fix-loop`.

Use this skill for plain-language requests to diagnose, root-cause, and fix one concrete broken behavior, even when the user does not type `$fix-loop`.

Examples:

- `$fix-loop checkout is 500ing locally`
- `$fix-loop settings page flashes blank on launch`
- `$fix-loop root cause the OAuth failure`
- `$fix-loop mobile cards overlap the filter bar`

The user should not need to say "keep trying until it works." That is the core contract of this skill.

## Defaults

- Maximum 8 rounds.
- Stay on the current branch.
- Do not commit, push, open a PR, or create task artifacts unless the user explicitly asks.
- Ask only when the answer would change product behavior, auth rules, schema semantics, billing logic, customer-visible UX intent, public API behavior, or a destructive action.
- Make the smallest change that can plausibly fix the verified root cause.

## Workflow

1. Define the pass condition.
   - Infer it from the user's bug report when obvious.
   - If the expected behavior is ambiguous enough to change the implementation, ask one direct question before editing.
   - Keep the pass condition concrete: a route returns the expected status/body, a test passes, a command exits cleanly, the app no longer crashes, the UI no longer flashes or overlaps, or the integration persists the expected state.
2. Establish the baseline.
   - Inspect `git status --short` and do not revert unrelated changes.
   - Identify the likely app, service, command, test, route, page, or user flow from repo evidence.
   - Find existing run/test scripts before inventing commands.
3. Reproduce before editing.
   - Run the failing command, request, test, app flow, browser flow, simulator flow, or integration path.
   - Capture the useful evidence: error output, logs, stack traces, console/network failures, database state, screenshots, or runtime traces.
   - If direct reproduction is blocked by missing env, credentials, device access, unavailable services, or unsafe side effects, state the blocker and use the closest safe focused check.
4. Loop until fixed or blocked.
   - Diagnose the root cause from the current evidence.
   - Patch the smallest correct surface.
   - Rerun the same failing flow, not only a convenient adjacent check.
   - Read fresh output/logs/state after each attempt.
   - Classify the result as fixed, same failure, changed failure, or blocked.
   - If the same hypothesis fails twice, or if the next patch would be another guess, use the verification pivot before another fix attempt: add the smallest useful log, deterministic test, replay, behavior probe, or harness that would expose the missing evidence.
   - If a temporary behavior probe is needed, put it under `/agent-scratch/`; promote it into a real test only when it is worth keeping.
5. Verify the actual behavior.
   - Backend/API: rerun the concrete request, job, webhook, CLI, or test path and inspect persisted side effects when relevant.
   - Frontend/UI: run the app when practical, inspect the affected state in a browser or app, and capture visual evidence for layout, clipping, spacing, copy, responsiveness, and console errors.
   - Runtime/desktop/mobile: relaunch the app or executable when the bug is launch/runtime-visible, then exercise the broken flow again and inspect logs.
   - Tests/builds: run the targeted test first, then any broader repo-defined check needed by the changed surface.
6. Stop only when one of these is true:
   - The pass condition is verified against the actual failing flow.
   - The remaining fix requires a human decision listed in Defaults.
   - Required env, credentials, services, paid resources, hardware, or device access are missing.
   - The safe reproduction path cannot be run and no focused substitute can prove the fix.
   - The 8-round cap is reached.

## Output

Keep the handoff short and evidence-based:

- bug fixed and root cause
- files changed
- rounds completed and why the loop stopped
- exact verification commands or flows run
- visual/log/runtime evidence when relevant
- any verification pivot used, including the missing evidence and probe result
- remaining blocker, skipped check, or residual risk if not fully verified

Do not claim success until the actual failing flow or a clearly stated substitute check has passed.
