# Finalization Gate

Portable hard gate for `$deliver` and legacy task-artifact execution.

This gate uses normal shell commands and workflow evidence. It does not depend on a Prime Directive script being available in the target repository.

See `skills/shared/references/contract-ownership.md` for shared contract ownership. This file owns baseline capture and terminal handoff checks.

## Kickoff Baseline

Capture the current dirty state before the workflow creates new task artifacts or implementation changes:

- `$deliver`: capture after branch-state decisions and before writing the readable execution plan, goal plan, or implementation changes.
- Legacy task-artifact execution: capture after resolving `<plan-key>` and before the first execution edit.

```sh
mkdir -p tasks/tmp
baseline_tmp="$(mktemp)"
git status --porcelain=v1 > "$baseline_tmp"
mv "$baseline_tmp" tasks/tmp/finalization-baseline-<plan-key>.status
```

If `tasks/tmp/` is gitignored, leave the baseline uncommitted. If it is tracked or appears in `git status`, delete this baseline after the final comparison.

The baseline is a guardrail, not a clean-tree requirement. Dirty files that existed before this workflow began may remain dirty at completion. The run may not leave new uncommitted implementation, test, planning, archive, or cleanup changes that it created.

If a pre-existing dirty file overlaps the planned implementation surface, treat it as an explicit risk: inspect carefully, work with the existing changes, and make sure the final diff/commit accounts for your additions instead of silently hiding them behind the baseline.

## Deliver With `--no-artifacts`

For `$deliver --no-artifacts` only, use the storage rules in `skills/deliver/references/no-artifacts.md` and these substitutions for the default file checks below:

- At kickoff, record `HEAD` and the exact initial `git status --porcelain=v1` output in chat. If a baseline file is useful, write it only in the run-owned external temporary directory; do not create `tasks/tmp/`. Keep the original baseline across approval pauses and resumed work.
- For check 1, inspect the complete final-review log in that temporary directory, including any required rereview-scope validator results. Missing or incomplete review evidence still blocks completion. Preserve the review outcome and material dispositions in chat before cleanup.
- For check 2, inspect the entire latest approved chat plan and checkbox state. Every in-scope item must be complete or explicitly deferred by the user. A missing plan file is expected; a missing or incomplete chat plan still blocks completion.
- Replace check 3's archive requirement with an absence check: inspect the working tree, index, and commits created since kickoff for generated workflow files. Check recorded scratch paths too; a clean git status alone does not prove ignored files or committed-then-deleted artifacts are absent. Preserve pre-existing user files and requested deliverables.
- Keep checks 4–6: implementation and requested deliverable changes must be committed, and final status must be compared with the original baseline. After checking the review evidence, remove the run-owned temporary files, verify their absence, and rerun final status. Cleanup failure blocks a no-artifacts completion claim.

The final handoff reports cleanup instead of an archive path. These substitutions change storage and archive checks only; they do not waive review, validation, commits, or completion checks. Default Deliver and legacy execution retain the file-based checks below.

## Before Terminal Handoff

Run this gate immediately before any final user-visible completion message:

Before running the numbered checks, classify the next user-visible message you are tempted to send. If it would summarize implementation changes, tests, generated artifacts, sources, or remaining closeout work, treat it as a terminal completion message and run this gate first. Do not send an implementation recap as a progress update after the last implementation validation passes.

1. For `$deliver` and legacy task-artifact execution, verify the final full-branch review evidence exists and is complete:

   ```sh
   review_log="tasks/tmp/review-task-final-<plan-key>.md"
   # For $deliver, use:
   # review_log="tasks/tmp/review-deliver-final-<plan-key>.md"
   test -f "$review_log"
   rg -n "^[[:space:]]*- \[ \]" "$review_log"
   ```

   No output from the `rg` command means the review-log checklist check passed. If the review log is missing, contains unchecked prompt entries, or records unresolved blocker/material/final-audit issues without accepted-risk or blocked status, do not hand off. Run or finish the final full-branch review first.

2. Re-open the task plan before archiving, or the archived task plan after archiving, and verify no unchecked task entries remain. For `$deliver`, use the readable execution plan instead:

   ```sh
   task_file="tasks/tasks-plan-<plan-key>.md"
   test -f "$task_file" || task_file="$(find tasks/archive -path "*/tasks-plan-<plan-key>.md" -type f -print -quit)"
   # For $deliver, use:
   # task_file="tasks/execution-plan-<plan-key>.md"
   # test -f "$task_file" || task_file="$(find tasks/archive -path "*/execution-plan-<plan-key>.md" -type f -print -quit)"
   rg -n "^[[:space:]]*- \[ \]" "$task_file"
   ```

   No output means the unchecked-task check passed. If this command finds any unchecked task entry, do not hand off. Continue execution unless a real blocker prevents progress. For `$deliver`, the scan covers the entire readable execution plan, not only the last phase or current section.

3. Verify the PRD, TDD, and task plan are archived unless the user requested preservation. For `$deliver`, verify the readable execution plan is archived:

   ```sh
   test -n "$(find tasks/archive -path "*/prd-<plan-key>.md" -type f -print -quit)"
   test -n "$(find tasks/archive -path "*/tdd-<plan-key>.md" -type f -print -quit)"
   test -n "$(find tasks/archive -path "*/tasks-plan-<plan-key>.md" -type f -print -quit)"
   # For $deliver, use:
   # test -n "$(find tasks/archive -path "*/execution-plan-<plan-key>.md" -type f -print -quit)"
   ```

4. Run the final status check:

   ```sh
   git status --porcelain=v1
   ```

5. Compare final status to `tasks/tmp/finalization-baseline-<plan-key>.status`.
   - Pre-existing dirty entries from the baseline may remain.
   - No new uncommitted entries from the run may remain.
   - Archive moves, checklist updates, cleanup edits, implementation edits, and test edits created by the run must be committed before handoff.
   - If the baseline file itself is the only new status entry, remove it and rerun the final status check before handoff.

6. If finalization itself changes files, commit those changes before terminal handoff.

If this gate would fail only because final review, commit, archiving, final status/baseline comparison, push, or PR creation has not been attempted yet, that is not a blocker to report. Continue the missing closeout work instead of handing the checklist back to the user.

The final completion handoff must be based on post-gate evidence. Include the final review outcome, disposition of any material findings, material Agent-Loop Backprop proposals when final review produced them, final validation, archive or preservation result, commit/PR or documented existing-branch/no-PR status, and final working-tree status.

If the gate fails, do not send a final completion message. Either finish the missing finalization work or stop with a blocker that names the exact failed gate item and the user action required.
