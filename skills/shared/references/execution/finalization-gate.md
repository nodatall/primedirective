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

For `$deliver --no-artifacts` only, use the normal kickoff baseline and live planning/review documents, with the retention rules in `skills/deliver/references/no-artifacts.md`. Run finalization in this order instead of archiving:

1. Finish implementation, validation, final review, authorized repairs, and required implementation commits. Run checks 1 and 2 below against the normal live review log and execution plan; verify required rereview-scope validator results too. Every in-scope item must be complete or explicitly deferred by the user. Missing or incomplete documents still block completion.
2. Read the kickoff baseline and recorded artifact inventory before deleting anything. Compare current status with the baseline, accounting for the run-owned workflow documents intentionally left uncommitted. Any other new implementation or deliverable changes must be committed. Preserve the baseline comparison, validation, and review outcome needed for the final handoff.
3. Replace check 3's archive requirement with deletion of the recorded workflow-owned files, including ignored and external scratch files, the live plan, implementation notes, review logs, optional memos, mockups, rereview records, baseline, and inventory. Do not delete pre-existing user files, authoritative guides, or requested deliverables. Keep documents intact on approval pauses, blockers, and unfinished runs.
4. Verify every recorded cleanup path is absent. Inspect the index and commits created during the run to confirm generated workflow documents were excluded. A clean git status alone does not prove ignored files or committed-then-deleted documents are absent.
5. Run checks 4–6 below using the baseline already read before deletion. Commit any required tracked cleanup and rerun final status. If cleanup fails or new uncommitted run changes remain, stop with the exact blocker rather than claiming completion.

The final handoff reports cleanup instead of an archive path. Do not rerun file-presence checks after intentionally deleting documents that passed them. These substitutions change closeout retention and sequencing only; they do not waive document-based planning, review, validation, commits, or completion checks. Default Deliver and legacy execution retain the archive checks below.

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
