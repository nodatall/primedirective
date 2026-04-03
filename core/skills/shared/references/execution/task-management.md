# Task List Management

Guidelines for managing task lists in markdown files.

## Execution Entry Gate (Required)

- This execution workflow may start only from:
  - `begin task <task-id> in <plan-key> [--preserve-review-artifacts]`
  - `begin one-shot in <plan-key> [--preserve-review-artifacts]`
- Execution requires:
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
- If those commands or files are missing, do not implement code.

## Standard task mode

- Standard mode is single-agent.
- Work one sub-task at a time starting from the requested task scope.
- Stop after each completed sub-task for user approval.

## One-shot mode

- One-shot mode is a sequential worker-subagent loop.
- One-shot execution scope is the entire unchecked remainder of `tasks/tasks-plan-<plan-key>.md`, not just the current parent task, milestone, or section.
- If kickoff begins with only `tasks/prd-<plan-key>.md`, `tasks/tdd-<plan-key>.md`, and `tasks/tasks-plan-<plan-key>.md` uncommitted, move them onto the new feature branch and commit them before the first implementation sub-task.
- For each sub-task:
  1. Main agent selects the next unchecked sub-task in file order.
  2. Main agent creates/updates `tasks/tmp/plan-task-<task-id>.md` as the sub-task contract before coding starts.
  3. Main agent spawns one worker subagent with:
     - `tasks/prd-<plan-key>.md`
     - `tasks/tdd-<plan-key>.md`
     - `tasks/tasks-plan-<plan-key>.md`
     - the exact sub-task block
  4. Worker implements one sub-task only and returns control.
  5. Main agent reviews and integrates the result.
  6. Main agent runs one automatic `sub-task` review round using the active review prompt profile and relevant tests. In one-shot mode, defer Prompt G frontend/browser verification to the final branch-wide review.
  7. Main agent marks the checklist complete and creates the commit.
  8. Main agent immediately re-opens `tasks/tasks-plan-<plan-key>.md` after that commit and re-scans for the next unchecked sub-task in file order.
  9. If another unchecked sub-task exists, main agent starts it immediately instead of producing a terminal-style handoff.
  10. After the final sub-task, main agent runs one additional automatic `full-branch` review round before finalization. This final round owns Prompt G frontend/browser verification for one-shot frontend work.

- Do not run sub-task workers in parallel. One-shot execution is strictly sequential.
- Do not stop one-shot execution after completing a parent task such as `1.0` or at any section boundary while unchecked sub-tasks remain later in the file.
- Do not end the run on an intermediate checkpoint just because the branch is in a clean, committable state.
- Do not present “work is in progress, not finished” as the terminal outcome of a one-shot unless a real blocker prevented continuation.
- Do not produce checkpoint summaries like “implemented through task X” or “remaining unchecked work is ...” as the last message of a one-shot turn while unchecked sub-tasks still remain.
- If a progress update is necessary mid-run, it must be explicitly non-terminal and must include the exact next sub-task already being executed.
- Before any terminal handoff, re-open `tasks/tasks-plan-<plan-key>.md` and verify there are no remaining `- [ ]` sub-task entries anywhere in the file. If any unchecked sub-task remains, continue execution rather than handing off.

## Temporary plan doc workflow

1. Create `tasks/tmp/plan-task-<task-id>.md` before coding starts for every sub-task.
2. Use it as the sub-task contract and keep it brief but explicit.
3. Minimum contract fields:
   - goal: what this slice changes
   - in_scope / out_of_scope: what is and is not part of this slice
   - surfaces: files, routes, screens, or jobs expected to change
   - verify: the exact checks that will prove the slice works
4. For frontend-facing work, also record:
   - changed screens and states
   - visual direction or design intent
   - anti-goals to avoid generic or off-brand output
5. Update the contract when implementation or review reveals a better-scoped slice or a missing verification step.
6. Delete temp plan doc only after review completion for that sub-task, unless `--preserve-review-artifacts` was supplied on the parent execution trigger.

## Completion protocol

1. Mark completed sub-task `[x]` immediately.
2. Mark parent `[x]` when all child sub-tasks are `[x]`.
3. Keep `Relevant Files` current as work evolves.
4. Keep task coverage references (`covers_prd` / `covers_tdd`) accurate when tasks change.

## Cleanup Phase (Required)

When the final checkbox in `tasks/tasks-plan-<plan-key>.md` is marked `[x]`, run archive cleanup.

Archive target:

- `tasks/archive/<yyyy-mm-dd>-<plan-key>/`

Files:

- `tasks/tasks-plan-<plan-key>.md`
- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`

Rules:

1. Create `tasks/archive/<yyyy-mm-dd>-<plan-key>/` if missing, using the local current date in ISO format (`YYYY-MM-DD`).
2. Move all three required files after final completion is confirmed.
3. Perform cleanup before opening the final task-based PR.

## AI Instructions

1. Before first sub-task, create/switch to dedicated feature branch if not already on one.
2. If kickoff dirtiness is only the current plan's required planning artifacts, carry them onto the feature branch and commit them before implementation commits begin.
3. Regularly update task list after significant work.
4. Create one dedicated commit per completed sub-task.
5. Keep checklist status accurate for sub-task and parent tasks.
6. Keep `Relevant Files` accurate.
7. In standard mode, pause after each sub-task for approval.
8. In one-shot mode, continue automatically after main-agent review + commit completion.
9. In one-shot mode, review each completed sub-task in `sub-task` scope, defer Prompt G frontend/browser verification during those rounds, then run one final `full-branch` review after all sub-tasks complete.
10. When all tasks complete, archive artifacts under `tasks/archive/<yyyy-mm-dd>-<plan-key>/` before final PR handoff.
11. In one-shot mode, do not pause or summarize as complete merely because the next remaining work starts under a new parent task number like `2.0` or `3.0`.
12. If `--preserve-review-artifacts` is present, keep `tasks/tmp/` plan and review files created during execution and list them in the final handoff.
13. Before producing a terminal handoff in one-shot mode, re-open the task file and verify there are no remaining unchecked sub-tasks.
14. In one-shot mode, the only valid terminal outcomes are:
    - all remaining unchecked sub-tasks completed, reviewed, finalized, and handed off
    - execution blocked by an unresolved issue that is explicitly described, with the exact next required user action
15. Before any user-visible one-shot completion message, run a liveness check against `tasks/tasks-plan-<plan-key>.md`: if any `- [ ]` entry remains, do not hand off and do not summarize as a stopping point.
16. If a one-shot progress update is emitted between sub-tasks, it must say both what just finished and which exact sub-task is already in progress next.
