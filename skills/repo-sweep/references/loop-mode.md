# Repo Sweep Loop Mode

`--loop` turns repo sweep into a bounded sweep/fix/resweep workflow.

Use this mode when the user wants the agent to keep improving the repository without stopping after the first report. It is still a repo sweep: every round starts with detection, keeps evidence for findings, and uses fresh review context before deciding whether more work remains.

Rules:

- Maximum 8 rounds. If the user asks for more, cap at 8 and say so in the final summary.
- Round 1 still runs the full first-principles no-edit pre-pass, no-edit audit, runtime probes when applicable, and comprehensive review-chain coverage.
- Emit a concise Round 1 repo-wide report before fixes, but do not ask for approval unless a human decision is required.
- Fix only findings with `Disposition: fix`, where the repair is clear enough to make without changing product intent or external contracts.
- After fixes and validation for a round, start the next sweep in one fresh dedicated review subagent/thread when subagents are available.
- Each loop review subagent owns detection for that round only. The main agent owns orchestration, edits, verification, loop stop decisions, artifact cleanup, and the final user summary.
- Do not reuse the previous round's reviewer as evidence that the current state is clean. A clean stop requires a fresh resweep after the latest fixes.
- Stop early when a fresh resweep finds no remaining `Disposition: fix` findings.
- Stop early when all remaining findings require a human decision, cannot be reproduced, cannot be safely fixed, or are explicitly out of scope.
- Do not create new branches, commits, pushes, or PRs unless the user separately asked for those git actions.
- Do not loop on cosmetic preferences, speculative risks, or issues where the only remaining action is broader product redesign.

Loop round shape:

1. `Detect`: run the sweep/review pass for the current repo state.
2. `Classify`: split findings into `fix`, `needs human decision`, `residual risk`, and `no action`.
3. `Fix`: address `fix` findings with the smallest correct changes.
4. `Verify`: run targeted checks plus any repo-health commands affected by the fixes.
5. `Resweep`: spawn a fresh review subagent for the next detection round, unless max rounds or a stop condition was reached.

For final output in loop mode, include:

1. Loop rounds completed and why the loop stopped.
2. Fixed findings by round.
3. Verification commands and outcomes.
4. Remaining human-decision items.
5. Residual risks.
