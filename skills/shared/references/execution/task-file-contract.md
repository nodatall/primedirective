# Task File Contract

Canonical path and activation contract for planning, execution, and review skills.

## Accepted activations

- Planning: `$plan-work` with the source plan or request in the same user message
- Plan and execute: `$plan-and-execute` with the source plan already present in the current thread; may include `--deep-research`, `--refine-plan`, `--check-harness-drift`, and/or `--preserve-artifacts`
- Plan refinement: `$plan-refine` with optional `plan-key=<plan-key>`
- Standard task execution: `$execute-task` with a specific `<task-id>` and optional `<plan-key>`; may include `--stay-on-current-branch` and/or `--check-harness-drift`
- One-shot execution: `$execute-task --one-shot` with optional `<plan-key>`; may include `--stay-on-current-branch` and/or `--check-harness-drift`
- Task review: `$review-chain` with a specific `<task-id>`
- Ad-hoc review (default): `$review-chain` without a task ID

## Execution branch modifier

`--stay-on-current-branch` is valid only with `$execute-task`, in standard or one-shot mode.

When present:

- Keep the current non-base branch instead of creating/switching to a new branch from `origin/main`.
- Do not create, switch, or rename branches during kickoff.
- Do not use this mode on `main`, `master`, a resolved local base branch, or detached `HEAD`; stop and ask if that is the current state.
- Do not skip execution gates, review rounds, commits, final rebase, push, or PR creation, except for the `$plan-and-execute` existing non-base branch no-PR terminal behavior documented in the review protocol.

## Harness drift modifier

`--check-harness-drift` is valid with `$execute-task` and `$plan-and-execute`.

When present:

- Run the compact harness drift check from `skills/shared/references/harness-drift.md` during final handoff.
- Keep planning artifacts, sub-task contracts, review logs, and relevant temp files available until the drift report is generated.
- After the report is generated, run normal cleanup and archive behavior.
- Do not add mandatory human approval steps, extra user-facing checkpoints, or standalone artifacts unless preservation was requested.
- If evidence is missing because the run failed before artifact creation or a prior cleanup already removed files, report the evidence gap instead of guessing.

## Plan-and-execute refinement modifier

`--refine-plan` is valid with `$plan-and-execute`.

When present:

- Run `$plan-refine plan-key=<plan-key>` after PRD, TDD, and tasks-plan generation and before `$execute-task --one-shot`.
- Use the generated plan key explicitly; do not infer across multiple planning sets.
- Use `$plan-refine`'s normal default round cap, fresh reviewer rounds, and artifact-editing rules.
- Treat refinement as an automatic repair pass, not a separate readiness gate.
- Apply fixes for blocker and material findings in the PRD, TDD, and tasks-plan before execution.
- If the loop reaches max rounds or churn, choose the safest concrete artifact fix available, record the accepted assumption or residual risk, and continue.
- Ask the user only when the remaining issue is unsafe, impossible to infer, or would change external scope in a way the artifacts cannot safely default.
- Continue into execution with the refined artifacts.
- If `$plan-and-execute --preserve-artifacts` is also present, keep the refinement log with the other temp artifacts and surface its path in the final summary.

## Plan-and-execute deep research modifier

`--deep-research` is valid with `$plan-and-execute`.

When present:

- Compose `$plan-work --from-thread --direct --deep-research` during the planning phase.
- Run the normal deep-research pass after initial PRD/TDD drafting and before tasks-plan generation.
- Apply adopted findings back into PRD, TDD, and tasks-plan sequencing before execution begins.
- Do not add a revised-summary checkpoint, planning approval gate, or other user-facing pause before execution. `$plan-and-execute` remains a direct orchestration flow.
- Stop only when live web research is unavailable or the research reveals a true blocker that is unsafe, contradictory, or impossible to default without changing external scope or product intent.
- If `$plan-and-execute --preserve-artifacts` is also present, keep the research memo with the other temp artifacts and surface its path in the final summary.

## Plan key resolution

Resolve `<plan-key>` in this order for plan refinement, standard execution, and one-shot execution:

1. If the activation includes an explicit `<plan-key>`, use it.
2. Otherwise inspect `/tasks/` for complete planning sets:
   - `tasks/prd-<plan-key>.md`
   - `tasks/tdd-<plan-key>.md`
   - `tasks/tasks-plan-<plan-key>.md`
3. If exactly one `<plan-key>` has all three files, infer that key and continue.
4. If no complete planning set exists, stop immediately and tell the user planning is incomplete.
5. If more than one complete planning set exists, stop and ask for an explicit `<plan-key>`.

Resolve files exactly as:

- Required PRD: `tasks/prd-<plan-key>.md`
- Required TDD: `tasks/tdd-<plan-key>.md`
- Required task list: `tasks/tasks-plan-<plan-key>.md`

## Temporary workflow files

- Planning research memo: `tasks/tmp/research-plan-<plan-key>.md`
- Plan refinement log: `tasks/tmp/plan-refine-<plan-key>.md`
- Per-sub-task plan doc: `tasks/tmp/plan-task-<task-id>.md`
- Task review log: `tasks/tmp/review-task-<task-id>.md`
- One-shot final review log: `tasks/tmp/review-task-final-<plan-key>.md`
- Ad-hoc review log: `tasks/tmp/review-task-ad-hoc-<yyyy-mm-dd>.md`

## Archive workflow files

- Final archive directory: `tasks/archive/<yyyy-mm-dd>-<plan-key>/`

Use the local current date in ISO format (`YYYY-MM-DD`) when creating the archive directory so archived PRD/TDD/task artifacts preserve completion timing in-repo.

By default, planning, refinement, and review temporary files are deleted after successful completion. If the activation includes `--preserve-planning-artifacts`, `--preserve-refine-artifacts`, `--preserve-review-artifacts`, or `$plan-and-execute --preserve-artifacts`, keep the matching temporary files in place and surface their paths in the final summary.

## Execution artifact gate

Execution requires all three planning artifacts.

If any one of these is missing:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

Then:

- stop immediately
- do not code
- do not auto-generate missing planning docs
- instruct the user to complete planning first

## Mode rules

### Standard mode

- Requires `<task-id>`.
- `<plan-key>` may be explicit or inferred through the resolution rules above.
- Executes the requested task/sub-task in the main agent.
- Pause for user confirmation between sub-tasks.
- If `--stay-on-current-branch` is present, keep the current non-base branch during kickoff.
- If `--preserve-review-artifacts` is present, keep per-sub-task temp plan docs and review logs.

### Plan refinement mode

- Requires a complete planning artifact set.
- `<plan-key>` may be explicit or inferred through the resolution rules above.
- Edits only `tasks/prd-<plan-key>.md`, `tasks/tdd-<plan-key>.md`, and `tasks/tasks-plan-<plan-key>.md`.
- Defaults to 8 refinement rounds and treats 8 as the hard maximum; higher requested values are capped at 8 and noted in the final summary.
- Uses `tasks/tmp/plan-refine-<plan-key>.md` as the temporary refinement log.
- Uses one fresh read-only reviewer subagent per refinement round.
- The main agent owns orchestration, artifact edits, audit checks, refinement-log updates, and the final user summary.
- If fresh reviewer subagents cannot be spawned, stop immediately instead of falling back to local self-review.
- Deletes the refinement log after successful completion unless `--preserve-refine-artifacts` is present.
- Keeps the refinement log when the run stops with unresolved blockers, material findings, missing artifacts, max rounds, or repeated/contradictory churn.

### One-shot mode

- Requires `--one-shot`.
- `<plan-key>` may be explicit or inferred through the resolution rules above.
- Start at first unchecked sub-task and continue in file order.
- If `--stay-on-current-branch` is present, keep the current non-base branch during kickoff.
- If kickoff begins with only the current plan's required planning artifacts uncommitted, commit them on the active execution branch before the first implementation sub-task begins.
- Continue until there are no unchecked sub-tasks left anywhere in the file; do not stop at parent-task or section boundaries.
- Do not emit user-visible mid-run progress updates while unchecked sub-tasks remain; keep executing silently across sub-task boundaries.
- A clean commit boundary, milestone boundary, or partially completed checklist is not a valid stopping point.
- Treat any user-visible one-shot message before final completion as potentially terminal for the run.
- Only return control early when a real blocker remains unresolved after reasonable attempts to proceed, such as missing required artifacts, unrelated dirty-tree changes that need user choice before branch creation, or an external approval/dependency failure that prevents continued execution.
- Use one worker subagent per sub-task.
- Do not run per-sub-task review chains.
- Use one fresh review subagent for the final `full-branch` review round.
- Main agent owns full PRD, TDD, and task-plan context across the run.
- One-shot worker context should be compact by default and must include:
  - `plan_key` and `task_id`
  - the exact sub-task block or a faithful concise copy of it
  - the compact implementation packet from `tasks/tmp/plan-task-<task-id>.md`
  - PRD/TDD anchors such as `covers_prd` / `covers_tdd` when present, not full artifact text by default
  - relevant file paths, symbols, reference patterns, acceptance checks, and focused verification command
- One-shot workers may open full PRD, TDD, or task-plan files only when the compact packet is insufficient, contradictory, or the slice touches product intent, trust boundaries, public contracts, data shape, architecture, or cross-task assumptions.
- Review subagent context must include:
  - for the final `full-branch` review: `tasks/prd-<plan-key>.md`, `tasks/tdd-<plan-key>.md`, `tasks/tasks-plan-<plan-key>.md`, plus any still-relevant temp sub-task contract that remains available and materially informs the branch-wide review
- Review subagents are siblings of the worker subagent. Do not have the worker spawn or own its own reviewer.
- Main agent owns task-list updates, review orchestration, review decisions, commits, integration checks, and finalization.
- No pauses between sub-tasks.
- Run finalization once after all sub-tasks complete.
- If `--preserve-review-artifacts` is present, keep per-sub-task temp plan docs plus the final full-branch review log.

## Legacy syntax

Do not depend on legacy `start planning`, `begin task`, `begin one-shot`, or `begin review` command phrases.
Do not accept legacy `prd-key`/`prd-id` wording. Use explicit skill activation plus `plan-key` or `task-id` context instead.
