# Task List Management

Guidelines for managing task lists in markdown files.

## Execution Entry Gate (Required)

- This execution workflow may start only from:
  - `begin task <task-id> in <plan-key>`
  - `begin one-shot in <plan-key>`
- If those commands were not provided, do not implement code or run task execution flow.

## Task Implementation

- **One sub-task at a time:** do not start the next sub-task until the user approves (`yes`/`y`).
  - Exception: in one-shot mode (`begin one-shot in <plan-key>`), continue automatically.
- **Temporary plan doc workflow:**
  1. Create `tasks/tmp/plan-task-<task-id>.md`.
  2. Implement the sub-task from that plan.
  3. Run review chain and capture findings/fixes/tests.
  4. Delete temp plan doc only after review completion.
  5. Mark sub-task complete.
- **Completion protocol:**
  1. Mark completed sub-task `[x]` immediately.
  2. Mark parent `[x]` when all child sub-tasks are `[x]`.
- Stop after each sub-task for approval in standard mode.

## Cleanup Phase (Required)

When the final checkbox in `tasks/tasks-plan-<plan-key>.md` is marked `[x]`, run archive cleanup.

Archive target:

- `tasks/archive/<plan-key>/`

Files:

- Always move `tasks/tasks-plan-<plan-key>.md`.
- Move `tasks/prd-<plan-key>.md` only if it exists.
- Move `tasks/tdd-<plan-key>.md` only if it exists.

Rules:

1. Create `tasks/archive/<plan-key>/` if missing.
2. Move required task file after final completion is confirmed.
3. If optional files are expected by user but missing, ask before proceeding.
4. Perform cleanup before opening the final task-based PR.

## Task List Maintenance

1. Update checklist and add new tasks as they emerge.
2. Maintain `Relevant Files` with every modified/created file and purpose.

## AI Instructions

1. Before first sub-task, create/switch to dedicated feature branch if not already on one.
2. Regularly update task list after significant work.
3. Create one dedicated commit per completed sub-task.
4. Keep checklist status accurate for sub-task and parent tasks.
5. Keep `Relevant Files` accurate.
6. In standard mode, pause after each sub-task for approval.
7. In one-shot mode, continue automatically after commit + review completion.
8. When all tasks complete, archive artifacts under `tasks/archive/<plan-key>/` before final PR handoff.
