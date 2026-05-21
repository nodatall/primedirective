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
- For UI, layout, styling, or product-surface changes, read DESIGN.md before editing when present.
- For any UI, layout, styling, or rendered-content change, inspect the affected UI in a browser or app when practical. Capture a screenshot of the changed state, visually check it for layout, clipping, spacing, copy, and responsive issues, and mention the evidence in the handoff. If the UI cannot be run, state why.
- For backend, integration, runtime, deployment, or agent/tooling changes, capture the current state before editing: relevant routes, config, env var presence, schema/migrations, services, provider state, and validation commands. Prefer structured output such as `--json`, health checks, metadata commands, or diagnostics when available, and do not expose secret values. After the first failed runtime or integration attempt, classify the failure layer before patching again.
- Do not claim success until the relevant check has run or you clearly state what could not be checked.
- Before boundary-affecting work, read `docs/ARCHITECTURE.md` when it exists.

## Prime Directive Rules

- For board/worktree changes, remember git worktrees do not copy ignored env files such as `.env` or `.env.local`; either preserve/prepare those env files explicitly or block with a clear missing-env reason rather than assuming the worktree matches the source checkout.
- For skill or shared-contract changes, run `python3 scripts/validate-skill-contracts.py`, `git diff --check`, and `./scripts/install-codex-plugin.sh` before claiming the local Codex skill install is current.
- When a request uses `reference: <link or pasted text>`, treat it as "what can Prime Directive skills learn from this?" Inspect the reference, compare it to existing skill owners, and return only reusable lessons or small owned-contract changes; do not give a broad summary or create a new skill unless asked.
