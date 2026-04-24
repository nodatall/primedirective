# Finalization Gate

Portable hard gate for `$execute-task --one-shot` and `$plan-and-execute`.

This gate uses normal shell commands and repo artifacts only. It does not depend on a Prime Directive script being available in the target repository.

See `skills/shared/references/contract-ownership.md` for shared contract ownership. This file owns baseline capture and terminal handoff checks.

## Kickoff Baseline

Capture the current dirty state before the workflow creates new task artifacts or implementation changes:

- `$plan-and-execute`: capture after branch-state decisions and before PRD/TDD/tasks-plan generation.
- `$execute-task`: capture after resolving `<plan-key>` and before the first execution edit.

```sh
mkdir -p tasks/tmp
baseline_tmp="$(mktemp)"
git status --porcelain=v1 > "$baseline_tmp"
mv "$baseline_tmp" tasks/tmp/finalization-baseline-<plan-key>.status
```

If `tasks/tmp/` is gitignored, leave the baseline uncommitted. If it is tracked or appears in `git status`, delete this baseline after the final comparison.

The baseline is a guardrail, not a clean-tree requirement. Dirty files that existed before this workflow began may remain dirty at completion. The run may not leave new uncommitted implementation, test, planning, archive, or cleanup changes that it created.

If a pre-existing dirty file overlaps the planned implementation surface, treat it as an explicit risk: inspect carefully, work with the existing changes, and make sure the final diff/commit accounts for your additions instead of silently hiding them behind the baseline.

## Before Terminal Handoff

Run this gate immediately before any final user-visible completion message:

1. Re-open the task plan before archiving, or the archived task plan after archiving, and verify no unchecked task entries remain:

   ```sh
   task_file="tasks/tasks-plan-<plan-key>.md"
   test -f "$task_file" || task_file="$(find tasks/archive -path "*/tasks-plan-<plan-key>.md" -type f -print -quit)"
   rg -n "^[[:space:]]*- \[ \]" "$task_file"
   ```

   No output means the unchecked-task check passed. If this command finds any unchecked task entry, do not hand off. Continue execution unless a real blocker prevents progress.

2. Verify the PRD, TDD, and task plan are archived unless the user requested preservation:

   ```sh
   test -n "$(find tasks/archive -path "*/prd-<plan-key>.md" -type f -print -quit)"
   test -n "$(find tasks/archive -path "*/tdd-<plan-key>.md" -type f -print -quit)"
   test -n "$(find tasks/archive -path "*/tasks-plan-<plan-key>.md" -type f -print -quit)"
   ```

3. Run the final status check:

   ```sh
   git status --porcelain=v1
   ```

4. Compare final status to `tasks/tmp/finalization-baseline-<plan-key>.status`.
   - Pre-existing dirty entries from the baseline may remain.
   - No new uncommitted entries from the run may remain.
   - Archive moves, checklist updates, cleanup edits, implementation edits, and test edits created by the run must be committed before handoff.
   - If the baseline file itself is the only new status entry, remove it and rerun the final status check before handoff.

5. If finalization itself changes files, commit those changes before terminal handoff.

## Existing Branch Exception

Starting `$plan-and-execute` on an existing non-base branch skips default PR creation only.

It does not skip task completion, final review, archiving, cleanup, commits, validation, baseline comparison, or the final status check.

If that branch already has an open PR, the gate does not require the PR title or scope to match the new plan. Do not push to or mutate the existing PR by default; include any visible mismatch in the final handoff as context for the user's next action.

If the gate fails, do not send a final completion message. Either finish the missing finalization work or stop with a blocker that names the exact failed gate item and the user action required.
