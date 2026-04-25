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
- Do not claim success until the relevant check has run or you clearly state what could not be checked.
