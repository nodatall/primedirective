# Deliver Without Saved Artifacts

Read this before any workflow writes when `$deliver --no-artifacts` is active. These substitutions override file creation, persistence, archive, and file-link instructions in Deliver and its delegated planning and review workflows. Approval, refinement, research evidence, validation, review, commits, and stop conditions still apply. `--fast` independently controls the first approval pause.

## Plan And Resume In Chat

- Keep the canonical plan, checkbox state, implementation findings, open questions, and resume checkpoint in this chat. Follow the plan format and its readability review, but omit the file-specific implementation footer. Do not save execution plans, goal plans, companion notes, or archives.
- Show the refined plan inline for normal approval. With `--fast`, continue from the refined chat plan. On resume, use the latest approved chat plan and findings; retain `--no-artifacts` even when the user does not repeat the flag.
- Read existing plans and authoritative guides as source material without modifying, moving, or deleting them as workflow housekeeping. Requested product code, tests, documentation, and other deliverables remain normal repo changes; this mode suppresses Deliver's own process files.
- Give reviewers and workers the exact plan text, relevant findings, active flag, and temporary workspace location instead of nonexistent plan or notes paths. Update the chat checklist after each item and inspect the entire checklist before continuing or finishing.
- Optional research and Pro analysis use the same plan and evidence gates. Supply the current chat plan as their input and keep adopted implementation findings in chat. Put required machine-readable records or browser evidence in the temporary workspace; do not create a repo plan to satisfy a file-path default.
- For goal-shaped work, apply `$plan-to-goal`'s planning checks and show the goal plan and a self-contained `/goal` start prompt inline. The prompt must include the objective, completion criteria, verifier, boundaries, stop conditions, and no-artifacts storage policy instead of referencing an unsaved plan. Stop at that handoff unless the user explicitly asks to start the goal.

## Temporary Files And Cleanup

When tooling needs files, create one run-owned temporary directory outside every repo/worktree, for example with `mktemp -d "${TMPDIR:-/tmp}/deliver-no-artifacts.XXXXXX"`. Verify its resolved location before using it and record the exact path. Pass it to every delegated worker and reviewer.

Use that directory for the kickoff baseline, review logs, rereview JSON, research and Pro memos, HTML mockups, screenshots, active-step notes, and disposable probes. Redirect tool caches and generated reports there or disable them. Required evidence fields, completion stamps, and validator phases remain unchanged. Run bundled validators in place against the relocated records. Preview a required frontend mockup from this directory before approval and verify the real UI after implementation.

Before every commit, inspect the staged paths and exclude generated workflow files. Never commit a plan or log with the intention of deleting it later: it would remain in git history. Do not delete or unstage pre-existing user files to enforce this mode.

Before any handoff, including the plan-review pause, a blocker, cancellation, or final completion, preserve the necessary findings, baseline, and resume state in chat, then remove only the run-owned temporary directory and any other explicitly recorded run-owned scratch files. Do not clean by broad filename patterns. On resume, recreate temporary evidence from the recorded state or rerun the relevant checks; preserve the original kickoff baseline rather than replacing it with the current dirty state.

For final completion, use the `--no-artifacts` path in `skills/shared/references/execution/finalization-gate.md`. Check review evidence before removing it. Report the completed work, validation, review result, and cleanup result in chat; omit archive links. If cleanup fails, report the exact remaining path and do not claim that no artifacts remain.
