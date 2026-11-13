# Deliver With Cleanup After Completion

Read this before any workflow writes when `$deliver --no-artifacts` is active. Create and use the normal planning and review documents on disk. This flag changes their retention after successful delivery; planning, approval, research, implementation, validation, and review still use their normal documents and gates. `--fast` independently controls the first approval pause.

## During The Work

- Create the execution plan, implementation notes, review logs, research and Pro memos, rereview records, and other workflow files at their normal paths. Link the plan for approval and pass real document paths to workers and reviewers. Update and reopen the plan normally.
- Record the exact workflow-owned paths created during this run, including ignored files and documents from earlier turns of the same run. Keep the path inventory with the temporary review records and include the inventory itself in final cleanup. Preserve pre-existing source documents, authoritative guides, unrelated user files, and requested deliverables.
- Keep the planning and review documents through approval pauses, plan-only or goal-plan handoffs, blockers, cancellation, and resumed work. Those states do not mean the whole delivery is complete. Retain `--no-artifacts` on resume even when the user does not repeat the flag.
- Keep generated workflow files out of implementation commits. Inspect staged paths before every commit; never commit an artifact with the intention of deleting it later. This exception applies only to workflow files, not requested code, tests, or product documentation. Do not unstage pre-existing user changes.
- Record any generated scratch files, screenshots, caches, or reports outside the normal task paths too. Do not delete still-needed planning or review evidence merely because one phase has finished.

## After Successful Completion

Use the `--no-artifacts` sequence in `skills/shared/references/execution/finalization-gate.md`:

1. Finish the entire approved plan, focused validation, final review, authorized repairs, and required commits. Inspect the live plan, review log, required rereview records, and kickoff baseline while they still exist. Missing documents or failed gates block cleanup and completion.
2. Capture the final review result, material findings, validation, and baseline comparison needed for the final handoff. Then delete every recorded workflow-owned document and scratch file, including the plan, notes, review logs, optional memos, mockups, rereview records, baseline, and path inventory. Delete them instead of moving them into an archive. Do not clean by broad filename patterns.
3. Verify the recorded paths are absent, preserve requested deliverables and pre-existing files, commit any required tracked cleanup, and rerun final status. Report cleanup in the final handoff instead of linking an archive. If cleanup fails, name the remaining paths and do not claim that no artifacts remain.

If the run stops before successful delivery, keep its documents for review and resumption unless the user explicitly asks to discard them. A goal-plan handoff must retain the goal plan for its `/goal` start prompt; it is not permission to start the goal or delete its inputs.
