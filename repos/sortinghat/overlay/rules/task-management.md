---
description:
globs:
alwaysApply: false
---
# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

## Task Implementation
- **One sub-task at a time:** Do **NOT** start the next sub-task until you ask the user for permission and they say "yes" or "y".
  - Exception: when task mode is explicitly `--one-shot`, proceed automatically to the next sub-task after completing the current one.
- **Temporary plan doc workflow:**
  1. For each sub-task, create a temporary plan document in `tasks/tmp/`.
  2. Name the file `plan-task-<task-id>.md` (example: `plan-task-0.3.md`).
  3. Implement the sub-task based on the plan doc.
  4. Run a review and provide the plan doc + task list to the reviewer using `/review`.
  5. After review completion, delete the temporary plan file and only then mark the sub-task complete.
- **Completion protocol:**
  1. When you finish a **sub‑task**, immediately mark it as completed by changing `[ ]` to `[x]`.
  2. If **all** subtasks underneath a parent task are now `[x]`, also mark the **parent task** as completed.
- Stop after each sub-task and wait for the user's go-ahead.
  - Exception: when task mode is explicitly `--one-shot`, do not pause between sub-tasks.

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the “Relevant Files” section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. Before beginning the first sub-task on a workstream, create and switch to a dedicated feature branch (if not already on one).
2. Regularly update the task list file after finishing any significant work.
3. After completing each sub-task, create a dedicated git commit summarizing the work before moving to the next sub-task.
4. Follow the completion protocol:
   - Mark each finished **sub-task** `[x]`.
   - Mark the **parent task** `[x]` once **all** its subtasks are `[x]`.
5. Add newly discovered tasks.
6. Keep “Relevant Files” accurate and up to date.
7. Before starting work, check which sub-task is next.
8. After implementing a sub-task, update the file and then pause for user approval.
   - Exception: when task mode is explicitly `--one-shot`, continue directly to the next sub-task after commit + review completion.
