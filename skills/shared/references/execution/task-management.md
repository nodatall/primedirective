# Task List Management

Guidelines for managing task lists in markdown files.

## Execution Entry Gate (Required)

- This execution workflow may start only from:
  - explicit `$execute-task` activation with a specific `<task-id>` and optional `<plan-key>` when the key can be inferred
  - explicit `$execute-task --one-shot` activation with optional `<plan-key>` when the key can be inferred
  - either execution activation may include `--stay-on-current-branch`
- Execution requires:
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
- If that activation context or those files are missing, do not implement code.

## Standard task mode

- Standard mode is single-agent.
- Standard mode requires `<task-id>` and may infer `<plan-key>` when `/tasks/` contains exactly one complete planning set.
- Work one sub-task at a time starting from the requested task scope.
- Stop after each completed sub-task for user approval.

## One-shot mode

- One-shot mode is a sequential worker-subagent loop.
- One-shot mode is activated with `--one-shot`.
- One-shot mode may infer `<plan-key>` when `/tasks/` contains exactly one complete planning set.
- One-shot review runs once at the end in a fresh `full-branch` review subagent.
- One-shot execution scope is the entire unchecked remainder of `tasks/tasks-plan-<plan-key>.md`, not just the current parent task, milestone, or section.
- If kickoff begins with only `tasks/prd-<plan-key>.md`, `tasks/tdd-<plan-key>.md`, and `tasks/tasks-plan-<plan-key>.md` uncommitted, commit them on the active execution branch before the first implementation sub-task.
- For each sub-task:
  1. Main agent selects the next unchecked sub-task in file order.
  2. Main agent creates/updates `tasks/tmp/plan-task-<task-id>.md` as the sub-task contract before coding starts, including acceptance checks, reference pattern choice, test-first plan, and any required trust-boundary notes.
  3. Main agent spawns one worker subagent with:
     - `tasks/prd-<plan-key>.md`
     - `tasks/tdd-<plan-key>.md`
     - `tasks/tasks-plan-<plan-key>.md`
     - `tasks/tmp/plan-task-<task-id>.md`
     - the exact sub-task block
  4. Worker implements one sub-task only and returns control.
  5. Main agent integrates the result, reruns relevant tests, marks the checklist complete, and creates the commit.
  6. Main agent immediately re-opens `tasks/tasks-plan-<plan-key>.md` after that commit and re-scans for the next unchecked sub-task in file order.
  7. If another unchecked sub-task exists, main agent starts it immediately instead of producing a terminal-style handoff.
  8. After the final sub-task, main agent spawns one fresh review subagent for the automatic `full-branch` review round before finalization, passing `tasks/prd-<plan-key>.md`, `tasks/tdd-<plan-key>.md`, `tasks/tasks-plan-<plan-key>.md`, and any still-relevant temp sub-task contract that remains available. This final round owns Prompt G frontend/browser verification for one-shot frontend work.

- Do not run sub-task workers in parallel. One-shot execution is strictly sequential.
- Do not have a worker subagent spawn or own its own reviewer. The final review subagent is a sibling spawned by the main agent after all workers return.
- Do not stop one-shot execution after completing a parent task such as `1.0` or at any section boundary while unchecked sub-tasks remain later in the file.
- Do not end the run on an intermediate checkpoint just because the branch is in a clean, committable state.
- Do not present “work is in progress, not finished” as the terminal outcome of a one-shot unless a real blocker prevented continuation.
- Do not emit user-visible one-shot progress updates while unchecked sub-tasks remain. Keep executing silently instead of sending checkpoint summaries, verification lists, or “continuing into X” notes.
- Do not surface internal worker-handoff state to the user as a stopping point. A user-visible recap of completed items, passing verify commands, an already-started next sub-task, or a remaining-work list is an invalid handoff while unchecked sub-tasks remain.
- Treat any user-visible one-shot message before final completion as potentially terminal or stall-inducing for the run.
- Before any terminal handoff, re-open `tasks/tasks-plan-<plan-key>.md` and verify there are no remaining `- [ ]` sub-task entries anywhere in the file. If any unchecked sub-task remains, continue execution rather than handing off.

## Temporary plan doc workflow

1. Create `tasks/tmp/plan-task-<task-id>.md` before coding starts for every sub-task.
2. Use it as the sub-task contract and keep it brief but explicit.
3. Minimum contract fields:
   - goal: what this slice changes
   - in_scope / out_of_scope: what is and is not part of this slice
   - surfaces: files, routes, screens, or jobs expected to change
   - acceptance_checks: concrete behaviors the reviewer must verify, including at least one user-visible or system-visible success path and any relevant failure path, edge case, or state transition
   - reference_patterns: repo-local paths or symbols for the implementation, test, and validation examples being followed; record `none found` only after searching, and justify any deliberate deviation from the closest usable pattern
   - test_first_plan: the targeted test to add or update first and the exact command expected to fail before implementation; if failing-first is not practical, record the exception reason here before coding starts
   - verify: the exact checks that will prove the slice works
4. Add `trust_boundary_notes` only when the slice touches agents, secrets, untrusted input, or outbound actions. Record the boundary, approval gate, or separation rule that implementation and review must preserve.
5. For frontend-facing work, also record:
   - changed screens and states
   - visual direction or design intent
   - anti-goals to avoid generic or off-brand output
6. Before coding, search the repo for similar implementations, tests, and validation commands or config, record the chosen local pattern in `reference_patterns`, and justify any decision to introduce a new pattern instead of following the existing one.
7. Default to a red/green loop for code-bearing, practically testable slices: add or update the targeted test first, run the failure-first command, then implement. Only skip that order when the recorded `test_first_plan` exception makes the reason explicit.
8. Update the contract when implementation or review reveals a better-scoped slice, a better local pattern, or a missing verification step.
9. Delete temp plan docs only after they are no longer needed for review: after the standard sub-task review completes, or after the final full-branch review completes in one-shot mode, unless `--preserve-review-artifacts` was supplied on the parent execution trigger.

## Pre-coding contract critique

Run this critique before coding for high-risk slices. This is agent-owned work inside the existing execution flow; do not add a mandatory human approval step or extra user-facing checkpoint.

Trigger the critique when the sub-task is any of:

- frontend-facing or product-workflow-facing
- agent, tool-use, private-data, secret, untrusted-input, or outbound-action work
- auth, authorization, billing, security, migration, backfill, rollback, production-readiness, or source-of-truth work
- a one-shot slice whose `acceptance_checks`, `verify`, or `done_when` are broad, manual, vague, or mostly visual

Critique the contract before implementation starts:

1. Does it name the real behavior to be delivered, not just files to edit?
2. Are `acceptance_checks` concrete enough for a reviewer to exercise without extra investigation?
3. Can the checks catch display-only UI, stubbed integrations, mocked-away logic, or state that does not persist?
4. Does the contract avoid over-specifying helpers, file layout, schemas, or APIs before repo inspection supports them?
5. Does `verify` include the strongest practical automated check and any required browser, API, CLI, database, or log evidence?
6. Are failure paths, edge cases, trust boundaries, and state transitions explicit when they materially affect correctness?

If the answer to any item is no, tighten `tasks/tmp/plan-task-<task-id>.md` before coding. Ask the user only when the missing decision would change product intent, external behavior, or stakeholder scope.

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

1. Before first sub-task, create/switch to a dedicated feature branch if not already on one. If `--stay-on-current-branch` is present, keep the current non-base branch and do not create, switch, or rename branches.
2. If kickoff dirtiness is only the current plan's required planning artifacts, commit them on the active execution branch before implementation commits begin.
3. Regularly update task list after significant work.
4. Create one dedicated commit per completed sub-task.
5. Keep checklist status accurate for sub-task and parent tasks.
6. Keep `Relevant Files` accurate.
7. In standard mode, pause after each sub-task for approval.
8. In one-shot mode, continue automatically after main-agent integration, verification, and commit completion for each sub-task.
9. In one-shot mode, do not run per-sub-task review chains. Spawn one fresh review subagent for the final `full-branch` review after all sub-tasks complete.
10. When all tasks complete, archive artifacts under `tasks/archive/<yyyy-mm-dd>-<plan-key>/` before final PR handoff.
11. In one-shot mode, do not pause or summarize as complete merely because the next remaining work starts under a new parent task number like `2.0` or `3.0`.
12. If `--preserve-review-artifacts` is present, keep `tasks/tmp/` plan and review files created during execution and list them in the final handoff.
13. Before producing a terminal handoff in one-shot mode, re-open the task file and verify there are no remaining unchecked sub-tasks.
14. In one-shot mode, the only valid terminal outcomes are:
    - all remaining unchecked sub-tasks completed, reviewed, finalized, the feature branch pushed, the PR opened, and then handed off with the PR URL
    - execution blocked by an unresolved issue that is explicitly described, with the exact next required user action
15. Before any user-visible one-shot completion message, run a liveness check against `tasks/tasks-plan-<plan-key>.md`: if any `- [ ]` entry remains, do not hand off and do not summarize as a stopping point.
16. Do not emit a one-shot progress update between sub-tasks. Keep executing silently unless a real blocker requires a user-visible interruption.
17. Treat a recap shaped like `completed items + passing verifies + already started next task + remaining unchecked work` as a terminal-style handoff attempt. Suppress it and continue execution.
18. Assume any user-visible one-shot message before Step 9 finalization may end or stall the run, so intermediate status reporting is forbidden.
19. Before final handoff, run the relevant repo-defined validation commands for the touched surface when they exist, such as lint, format-check, typecheck, test, and build. If the current plan added that tooling, use the newly introduced commands and mention any commands that remain intentionally absent.
20. Treat branch publication and PR creation as explicit finalization work, not implied behavior. If the environment supports native PR actions, use them; otherwise push with git and open the PR with a concrete provider CLI.
21. For substantial one-shot runs, include a short harness load-bearing note in the final handoff: which contract, review, browser, or production-readiness checks caught real issues; which were not applicable; and whether a lighter or heavier harness would be appropriate for similar future work. Do not create a separate artifact unless the user asked for preserved review artifacts.
