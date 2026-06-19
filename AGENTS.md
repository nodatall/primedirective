# Agent Instructions

## General Rules

- Make the smallest change that solves the request.
- Match the surrounding code style.
- Do not refactor or clean up unrelated code.
- Do not revert or overwrite user changes unless explicitly asked.
- Ask only when the answer would change the implementation.
- Prefer existing tests for changed code paths.
- If no test covers the path, run the exact function or code path you changed with realistic inputs.
- Regression fixes should add or update the smallest practical test/check that would have caught the regression.
- Put disposable agent-created probes, scripts, and one-off benchmarks in `/agent-scratch/` unless the repo already has a better temp convention.
- Treat `/agent-scratch/` as disposable and gitignored; promote useful checks into real tests, benchmarks, or docs.
- For UI, layout, styling, or product-surface changes, read `docs/DESIGN.md` before editing when present.
- UI-level changes require UI-level verification. Builds, typechecks, and unit tests are not enough when the changed behavior depends on rendered UI, native windows, focus, overlays, drag behavior, loading states, responsive layout, or app/browser interaction. Reproduce the affected flow, inspect it in the real UI when practical, capture screenshot or equivalent visual evidence, and state what was verified. If that cannot be done, say so clearly and do not claim the UI behavior is fully verified.
- After a repeated user-reported UI regression, stop making assumption-based patches. First reproduce or instrument the real UI path, then patch, then verify the same path.
- For backend, integration, runtime, deployment, or agent/tooling changes, capture the current state before editing: relevant routes, config, env var presence, schema/migrations, services, provider state, and validation commands. Prefer structured output such as `--json`, health checks, metadata commands, or diagnostics when available, and do not expose secret values. After the first failed runtime or integration attempt, classify the failure layer before patching again.
- Do not claim success until the relevant check has run or you clearly state what could not be checked.
- Before boundary-affecting work, read `docs/ARCHITECTURE.md` when it exists.

## Prime Directive Rules

- For board/worktree changes, remember git worktrees do not copy ignored env files such as `.env` or `.env.local`; either preserve/prepare those env files explicitly or block with a clear missing-env reason rather than assuming the worktree matches the source checkout.
- For skill or shared-contract changes, run `python3 scripts/validate-skill-contracts.py`, `git diff --check`, and `./scripts/install-codex-plugin.sh` before claiming the local Codex skill install is current.
- When a request uses `reference: <link or pasted text>`, treat it as "what can Prime Directive skills learn from this?" Inspect the reference, compare it to existing skill owners, and discuss only reusable lessons plus any proposed small owned-contract changes. Lead with whether anything should be adopted: name what is materially different from the current contract, the specific owner that would change, or say no import/no change when the reference overlaps, conflicts, lacks a clear owner gap, or the user rejects it. Do not edit Prime Directive skills, shared contracts, validators, README text, or automation instructions during the initial reference pass unless the user explicitly asks to implement after that discussion. Do not give a broad summary. Do not create a new skill unless asked; recommend one only when the workflow is repeatable, distinct from existing owners, and has concrete proof gates.
