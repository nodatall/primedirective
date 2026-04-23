# Rule: Generating the Task Plan

## Goal

Generate one implementation-ready task plan file from finalized PRD and TDD:

- `tasks/tasks-plan-<plan-key>.md`

Tasks-plan is always required, but it is no longer the sole planning artifact.

## Inputs

Required:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- locked planning decisions and defaults
- direct source interpretation and assumptions when `--direct` is active
- deep-research findings when `--deep-research` is active, already applied to finalized PRD/TDD
- `tasks/tmp/research-plan-<plan-key>.md` when `--deep-research` is active, so task generation can verify the completion stamp and carry adopted implementation-impact findings forward

Tasks must be generated from finalized PRD and TDD, not directly from the raw source plan.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tasks-plan-<plan-key>.md`

## Required structure

```markdown
See `skills/shared/references/execution/task-management.md` for execution workflow and review guidelines.

# <Plan Title>

## Scope Summary
- Short summary of what this plan covers.
- Call out the highest-risk implementation concerns.

## Relevant Files
- `path/to/file.ts` - Why this file matters.
- `path/to/file.test.ts` - Tests for the file.

## Task Ordering Notes
- Sequencing assumptions and dependency notes.
- Any required migration/backfill/rollout order.

## Tasks
- [ ] 1.0 Parent task title
  - covers_prd: `FR-001`, `FR-002`
  - covers_tdd: `TDR-001`
  - [ ] 1.1 Sub-task description
    - covers_prd: `FR-001`
    - covers_tdd: `TDR-001`
    - output: `path/to/file.ts`
    - verify: `npm test -- path/to/file.test.ts`
    - done_when: Observable pass condition
```

## Generation rules

1. Confirm `<plan-key>` is known.
2. Confirm PRD and TDD are both finalized first. If `--deep-research` is active, confirm they were revised after the research pass before continuing.
3. If `--deep-research` is active, verify the Deep Research Completion Stamp before generating tasks. If the stamp is missing, incomplete, or says `evidence_bar_met: no`, hard-stop task generation and report the unmet research checks instead of generating around the gap.
4. If `$plan-and-execute --pro-analysis` is active, verify `tasks/tmp/pro-analysis-<plan-key>.md` before generating tasks. If the memo is missing, lacks a Pro synthesis completion stamp, says anything other than `pro_synthesis_complete: yes`, or leaves adopted Pro findings unapplied/unmapped, hard-stop task generation and report the unmet Pro synthesis gate.
5. Derive task sequencing from finalized PRD and TDD obligations.
6. Order work risk-first and dependency-aware.
7. Preserve meaningful implementation detail from the source plan by expressing it as actionable tasks.
8. Ensure every meaningful `FR-*` and `TDR-*` is covered by at least one task or sub-task.
9. Ensure every sub-task has `covers_prd`, `covers_tdd`, `output`, `verify`, and `done_when`.
   - `output` may name the known file, likely file, directory, module, command surface, or user-facing surface. Do not invent exact file paths solely to satisfy the field.
10. When repo-local implementation or test patterns are a good fit, name them in `Relevant Files`, `Task Ordering Notes`, or the relevant task text so execution knows what local convention to follow without adding new required task fields.
11. For code-bearing, practically testable sub-tasks, make `verify` identify the targeted test command that execution should run red first and then green after implementation; for slices where a failing-first loop is not practical, make that exception visible in the task wording or ordering notes without introducing a new required field.
12. Make every sub-task small enough that implementation and review can agree on a concrete contract before coding starts.
13. Task-plan sub-tasks should define the outcome, constraints, affected surface, verification intent, and done condition. Exact local file choices, helper choices, test placement, and red/green contract details are finalized in `tasks/tmp/plan-task-<task-id>.md` during `$execute-task` after repo inspection.
14. For frontend-facing sub-tasks, make `verify` and `done_when` describe the actual screens, states, and interactions to be checked in the browser. Avoid generic wording such as `UI looks good`.
15. Sequence frontend work so shared layout/theming primitives land before high-polish states, unless the risk profile clearly favors a spike first.
16. If the finalized PRD or TDD show missing validation tooling that the plan depends on, add explicit early tasks for that bootstrap work: config files, scripts or task-runner entries, CI wiring, and hook integration where appropriate.
17. When validation tooling bootstrap is in scope, make later feature tasks depend on the new commands instead of pretending those commands already existed.
18. Prefer repo-native enforcement in `verify` steps. Use the repo's real lint, format-check, typecheck, test, or build commands when they exist; if they do not exist yet, make the bootstrap task introduce them first.
19. When that bootstrap is first-time repo setup, call out that the bootstrap task is executable via `$bootstrap-repo-rules [--with-hooks]`.
20. If `--deep-research` is active, use the Finding-to-Artifact Delta and durable TDD research-backed rationale to fold adopted implementation-impact findings into task ordering, task text, `verify`, and `done_when`.
21. If an adopted research finding has implementation impact but should not become a task, it must already be explicitly deferred or marked as a non-goal in PRD/TDD before task generation. Do not silently drop adopted findings as decorative evidence.
22. If `$plan-and-execute --pro-analysis` is active, use the Pro findings ledger and artifact delta to fold adopted implementation-impact findings into task ordering, task text, `verify`, and `done_when`.
23. If an adopted Pro finding has implementation impact but should not become a task, it must already be explicitly deferred or marked as a non-goal in PRD/TDD or the Pro synthesis memo before task generation. Do not silently drop adopted Pro findings as decorative evidence.
24. If `--deep-research` is active, fold research-discovered rollout, migration, verification, and cleanup work into the task ordering and sub-task details.
25. Save `tasks/tasks-plan-<plan-key>.md`.
26. Stop and wait for build trigger.

## Coverage rule

No requirement from PRD or TDD may disappear during task generation.

If something is intentionally omitted from tasks, it must already be explicitly marked as out of scope, deferred, or non-goal in PRD/TDD before task generation.

When `--deep-research` is active, this coverage rule also applies to adopted findings from the Finding-to-Artifact Delta. Adopted findings that create `task_plan_inputs_created` must appear in the task plan, or the PRD/TDD must explicitly explain why they are deferred or non-goals.

## Hard stop

Do not start coding after generating the task plan. Build starts only from:

- explicit `$execute-task` activation with a specific `<task-id>` and optional `<plan-key>` when it can be inferred from `/tasks/`
- explicit `$execute-task --one-shot` activation with optional `<plan-key>` when it can be inferred from `/tasks/`
- an orchestration skill such as `$plan-and-execute` that explicitly owns continued execution
