---
name: execute-task
description: Execute planned work from existing `prd`, `tdd`, and `tasks-plan` artifacts. Supports standard task mode, `--one-shot`, `--stay-on-current-branch`, `--check-harness-drift`, and `--preserve-review-artifacts`.
---

# Execute Task Skill

Implement task work from the required planning artifact set:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

## Activation

Invoke explicitly with `$execute-task`.

Required request context:

- standard mode: a specific `<task-id>` plus `<plan-key>` when it cannot be inferred
- one-shot mode: `--one-shot` plus `<plan-key>` when it cannot be inferred

Supported modifiers:

- `--one-shot`
- `--stay-on-current-branch`
- `--check-harness-drift`
- `--preserve-review-artifacts`

Activation examples:

- Standard mode with explicit key: `$execute-task task-id=<task-id> plan-key=<plan-key>`
- Standard mode with inferred key: `$execute-task task-id=<task-id>`
- Standard mode on the current branch: `$execute-task --stay-on-current-branch task-id=<task-id> plan-key=<plan-key>`
- One-shot with explicit key: `$execute-task --one-shot plan-key=<plan-key>`
- One-shot with inferred key: `$execute-task --one-shot`
- One-shot on the current branch: `$execute-task --one-shot --stay-on-current-branch plan-key=<plan-key>`
- One-shot with harness drift check: `$execute-task --one-shot --check-harness-drift plan-key=<plan-key>`

## Required references

Load these files before running:

- `skills/shared/references/execution/task-file-contract.md`
- `skills/shared/references/execution/task-management.md`
- `skills/shared/references/execution/finalization-gate.md`
- `skills/shared/references/reasoning-budget.md`
- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/review/review-calibration.md`
- `skills/shared/references/harness-drift.md`

## Workflow

1. Resolve artifact files from trigger using `task-file-contract.md`.
2. Require PRD, TDD, and tasks-plan before doing any execution work.
3. Run kickoff branch setup from `review-protocol.md` Step 1 rules. By default, create/switch to a new feature branch and carry/commit the required planning artifacts there when they are the only uncommitted kickoff files. If `--stay-on-current-branch` is present, keep the current non-base branch and apply the current-branch kickoff rules instead.
4. Execute according to mode:
   - Standard mode: implement the requested task/sub-task in the main agent.
   - One-shot mode: treat the entire unchecked remainder of the task plan as the execution scope; if kickoff carried uncommitted planning artifacts, commit them before the first implementation sub-task, then for each sub-task in file order the main agent reads the full planning context, creates a compact implementation packet from `tasks/tmp/plan-task-<task-id>.md`, spawns one worker subagent with that packet, waits for completion, integrates the result, owns task updates and commit, and moves directly to the next sub-task. Do not run per-sub-task review chains in one-shot mode; run one final `full-branch` review after all sub-tasks are complete.
5. For each completed sub-task:
  - create/update `tasks/tmp/plan-task-<task-id>.md` with the sub-task contract before coding, then keep it current as implementation and review findings refine the slice
  - identify repo-local implementation, test, and validation reference patterns before coding, record the chosen pattern in the sub-task contract, and justify any deliberate deviation
  - for high-risk slices, run the agent-owned pre-coding contract critique from `task-management.md` and tighten the contract before implementation starts
  - write or update the targeted test first when the slice is practically testable
  - run the targeted test command and confirm the intended failure before implementation begins
  - implement the change using PRD + TDD + tasks-plan + exact sub-task block + the chosen local pattern in standard mode, or using the compact implementation packet from `task-management.md` in one-shot mode
  - rerun the targeted verification until the slice passes
  - in standard mode, expand to any additional relevant repo-defined checks for the touched surface such as lint, format-check, typecheck, test, or build
  - in one-shot mode, follow the focused-validation cadence from `task-management.md`: run the narrow check needed for the current slice, defer broader checks to parent-section boundaries or finalization unless the slice touches shared behavior, exposes collateral risk, or the focused check fails in a way that requires broader diagnosis
  - in standard mode, run one `sub-task` review round automatically using the active prompt profile from `review-protocol.md`, in a fresh review subagent when subagents are available
  - in standard mode, apply fixes from review findings and rerun relevant tests
  - keep temp review artifacts under `tasks/tmp/` when `--preserve-review-artifacts` is enabled; otherwise clean them up per protocol
  - mark checklist updates in `tasks/tasks-plan-<plan-key>.md`
  - create a dedicated commit for the sub-task
  - in one-shot mode, immediately re-open `tasks/tasks-plan-<plan-key>.md` after the commit, identify the next unchecked sub-task in file order, and continue directly when one exists
6. In one-shot mode, after all sub-tasks are complete, run one final `full-branch` review round automatically using the active prompt profile from `review-protocol.md` in one fresh review subagent before finalization. This is the review round that must satisfy Prompt G for frontend-facing work.
7. Run finalization from `review-protocol.md` Step 9 rules and the hard gate from `finalization-gate.md` only after all unchecked sub-tasks in the task plan are complete. Do not treat one-shot execution as finished until the feature branch is pushed and the PR has been created, unless an orchestration skill such as `$plan-and-execute` explicitly uses the existing non-base branch no-PR terminal behavior. That exception skips default PR creation only; it does not skip commits, checklist completion, final review, archiving, validation, final status checks, or baseline comparison.
8. Before any terminal handoff in one-shot mode, re-open `tasks/tasks-plan-<plan-key>.md` and confirm there are no remaining unchecked sub-tasks anywhere in the file. If any remain, continue execution instead of handing off unless a real blocker prevents further progress.
9. In one-shot mode, do not stop after an intermediate sub-task merely to report status, preserve a clean commit boundary, or hand off remaining work. Only stop early for a real blocker that cannot be resolved inside the current run.
10. In one-shot mode, do not emit user-visible mid-run progress updates while unchecked sub-tasks remain. Keep executing silently across sub-task boundaries instead of reporting intermediate completion, verification, or “continuing into X” status.
11. In one-shot mode, do not expose internal worker handoffs as user-visible content. Message shapes like “Completed and committed now: ...”, “Latest passing verifies: ...”, “I've already started X ...”, or “Remaining unchecked work is ...” are invalid while unchecked sub-tasks remain, even if they say execution is still in progress.
12. Assume any user-visible one-shot message before finalization can be treated as the run's terminal output. Only send a user-visible message early when a real blocker prevents continuation and the exact required user action is stated.

## Mode behavior

- Standard mode: single-agent execution, pause for approval between sub-tasks.
- One-shot mode: sequential worker-subagent loop across the entire remaining unchecked task file, no approval pauses between sub-tasks, focused validation per sub-task, no per-sub-task review chains, then one final full-branch review in a fresh review subagent before finalization. The run is terminal only after finalization or an explicit unresolved blocker.

## Execution defaults

- Follow `reasoning-budget.md`: standard-mode implementation uses the current execution agent's appropriate implementation tier, one-shot implementation workers use strong reasoning, final review subagents use the strongest appropriate reasoning tier, and mechanical chores use medium/standard reasoning.
- Treat a failing-test-first red/green loop as the default for code-bearing, practically testable slices.
- A test-first exception is allowed only when a failing-first loop is not practical for that exact slice; record the exception reason in `tasks/tmp/plan-task-<task-id>.md` before implementation starts.
- Prefer existing tests. If no test covers the path, create a temporary script under `/codex-scripts/` that imports or copies the relevant production code and exercises the changed behavior. Keep `/codex-scripts/` gitignored unless the probe is promoted into a real test.
- New contract critique, acceptance checks, review calibration, and harness drift checks are agent-owned. Do not add mandatory human approval steps or extra user-facing checkpoints to use them.
- Before coding, search the repo for similar implementations and tests, follow an existing local pattern when it is a good fit, and record why any new pattern or deviation is necessary.
- Before coding, inspect the repo's actual validation commands and config rather than assuming standard names exist.
- During one-shot execution, prefer concise command output: use `git diff --stat`, `git diff --name-only`, and targeted hunk reads before large full-diff dumps; only print broad diffs when they are needed for a concrete decision or final review.
- During one-shot execution, do not pass full PRD, TDD, and task-plan files to every worker by default. The main agent owns full-plan coherence and gives workers compact implementation packets; workers open full artifacts only through the escape hatches in `task-management.md`.
- When `--check-harness-drift` is present, keep planning artifacts, sub-task contracts, review logs, and relevant temp files available through final review and drift-report generation. Include the actual compact drift report from `harness-drift.md` inline in the final handoff under a visible `Harness Drift Check` heading with a one-line verdict; do not satisfy this by only mentioning an archived report path. Then run normal cleanup unless `--preserve-review-artifacts` is also present or the user explicitly asks to keep artifacts.
- Before terminal handoff in one-shot mode, run the finalization gate from `finalization-gate.md`; a clean-looking branch summary is not a substitute for the archived-artifact, unchecked-task, commit, and final-status checks.
- Do not invent lint, format, hook, or similar repo tooling mid-execution unless the planned task explicitly includes introducing that tooling or the user asks for it.

## Review relationship

Task execution includes automatic review rounds. Standard mode reviews each completed sub-task before commit. One-shot mode skips per-sub-task review chains and runs one final `full-branch` review after all implementation sub-tasks complete. Manual review runs through explicit `$review-chain` activation, optionally scoped to a specific `<task-id>`.
