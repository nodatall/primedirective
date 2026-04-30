# Agent Instructions

- Make the smallest change that solves the request.
- Match the surrounding code style.
- Do not refactor or clean up unrelated code.
- Do not revert or overwrite user changes unless explicitly asked.
- Ask only when the answer would change the implementation.
- Prefer existing tests for changed code paths.
- If no test covers the path, run the exact function or code path you changed with realistic inputs.
- Put temporary behavior probes in `/codex-scripts/`.
- Treat `/codex-scripts/` as disposable; promote important probes into real tests.
- For any UI, layout, styling, or rendered-content change, inspect the affected UI in a browser or app when practical. Capture a screenshot of the changed state, visually check it for layout, clipping, spacing, copy, and responsive issues, and mention the evidence in the handoff. If the UI cannot be run, state why.
- Do not claim success until the relevant check has run or you clearly state what could not be checked.
- For board/worktree changes, remember git worktrees do not copy ignored env files such as `.env` or `.env.local`; either preserve/prepare those env files explicitly or block with a clear missing-env reason rather than assuming the worktree matches the source checkout.
