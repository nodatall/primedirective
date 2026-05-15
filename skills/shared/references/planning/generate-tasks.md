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
- Must-open files or narrow surfaces only:
  - `path/to/file.ts` - Why execution likely must inspect this file.
  - `path/to/file.test.ts` - Tests for the file.
- Optional reference areas:
  - `path/to/directory/` - Broader reference area, not a required edit target.

## Task Ordering Notes
- Sequencing assumptions and dependency notes.
- Any required migration/backfill/rollout order.

## Source Acceptance Checklist
- Required when the source plan included an explicit checklist, numbered roadmap, or full-plan/all-at-once language.
- Each item should be marked `tasked`, `non-goal`, or `user-approved deferral`.
- `user-approved deferral` requires evidence from the source plan or an explicit user decision, not reviewer caution alone.

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
3. If `--deep-research` is active, verify the Deep Research Completion Stamp before generating tasks, including `operator_practice_sources_count`. If the stamp is missing, incomplete, or says `evidence_bar_met: no`, hard-stop task generation and report the unmet research checks instead of generating around the gap.
4. If `$plan-and-execute --pro-analysis` is active, verify `tasks/tmp/pro-analysis-<plan-key>.md` before generating tasks. If the memo is missing, lacks browser evidence for a real Pro browser run, lacks a Pro synthesis completion stamp, says anything other than `pro_browser_run: yes`, `pro_model_selected: yes`, and `pro_synthesis_complete: yes`, or leaves adopted Pro findings unapplied/unmapped, hard-stop task generation and report the unmet Pro synthesis gate.
5. Derive task sequencing from finalized PRD and TDD obligations.
6. Order work risk-first and dependency-aware.
7. Preserve meaningful implementation detail from the source plan by expressing it as actionable tasks.
8. Ensure every meaningful `FR-*` and `TDR-*` is covered by at least one task or sub-task.
9. Ensure every sub-task has `covers_prd`, `covers_tdd`, `output`, `verify`, and `done_when`.
   - `output` may name the known file, likely file, directory, module, command surface, or user-facing surface. Do not invent exact file paths solely to satisfy the field.
   - `output` should identify the primary surface for the slice, not every possible implementation detail.
10. Carry TDD contract detail into executable work. Every documented entity/model, state/status transition, config/default, source-of-truth rule, safety invariant, typed failure/blocker, retry/recovery path, migration/rollout step, and validation profile must appear in at least one sub-task or be explicitly deferred/non-goal in PRD/TDD before task generation.
11. If the TDD defines core vs optional/extension vs real-integration validation profiles, make the task order reflect that distinction: deterministic core checks first, optional feature checks only when that feature ships, and real-integration smoke checks gated with explicit environment/safety skip semantics.
12. When repo-local implementation or test patterns are a good fit, name only the must-open references in `Relevant Files`, `Task Ordering Notes`, or the relevant task text so execution knows what local convention to follow without adding new required task fields.
13. For code-bearing, practically testable sub-tasks, make `verify` identify the targeted test command that execution should run red first and then green after implementation; for slices where a failing-first loop is not practical, make that exception visible in the task wording or ordering notes without introducing a new required field.
14. Make every sub-task small enough that implementation and review can agree on a concrete contract before coding starts.
15. Size sub-tasks by behavior boundary, not by file count. Each normal sub-task should have:
   - one primary changed surface, such as one route, UI state, worker path, migration step, config surface, CLI command, or agent/tool boundary
   - one primary verification command class, such as unit test, browser check, API probe, migration dry-run, build/typecheck, or log/runtime probe
   - clear out-of-scope boundaries when adjacent frontend, backend, database, deployment, or CI work exists
16. Mark a sub-task as an explicit `integration slice` only when it intentionally crosses multiple primary surfaces or needs more than one verification command class. Integration slices must explain why the work cannot be split without losing end-to-end confidence.
17. Do not make a sub-task implementation-specific merely to make it smaller. The task plan owns the behavior slice, constraints, primary surface, verification intent, and done condition. Exact local file choices, helper choices, test placement, schema details, route names, and red/green contract details are finalized in `tasks/tmp/plan-task-<task-id>.md` during `$execute-task` after repo inspection.
18. For frontend-facing sub-tasks, make `verify` and `done_when` describe the actual screens, states, and interactions to be checked in the browser. Avoid generic wording such as `UI looks good`.
19. Sequence frontend work so shared layout/theming primitives land before high-polish states, unless the risk profile clearly favors a spike first.
20. If the finalized PRD or TDD show missing validation tooling that the plan depends on, add explicit early tasks for that bootstrap work: config files, scripts or task-runner entries, CI wiring, and hook integration where appropriate.
21. When validation tooling bootstrap is in scope, make later feature tasks depend on the new commands instead of pretending those commands already existed.
22. Prefer repo-native enforcement in `verify` steps. Use the repo's real lint, format-check, typecheck, test, or build commands when they exist; if they do not exist yet, make the bootstrap task introduce them first.
23. When that bootstrap is first-time repo setup, call out that the bootstrap task is executable via `$bootstrap-repo-rules [--with-hooks]`.
24. If `--deep-research` is active, use the Finding-to-Artifact Delta and durable TDD research-backed rationale to fold adopted implementation-impact findings into task ordering, task text, `verify`, and `done_when`.
25. If an adopted research finding has implementation impact but should not become a task, it must already be explicitly deferred or marked as a non-goal in PRD/TDD before task generation. Do not silently drop adopted findings as decorative evidence.
26. If `$plan-and-execute --pro-analysis` is active, use the Pro findings ledger and artifact delta to fold adopted implementation-impact findings into task ordering, task text, `verify`, and `done_when`.
27. If an adopted Pro finding has implementation impact but should not become a task, it must already be explicitly deferred or marked as a non-goal in PRD/TDD or the Pro synthesis memo before task generation. Do not silently drop adopted Pro findings as decorative evidence.
28. If `--deep-research` is active, fold research-discovered rollout, migration, verification, and cleanup work into the task ordering and sub-task details.
29. If the source plan contains an explicit checklist, numbered roadmap, or full-plan/all-at-once language, add `## Source Acceptance Checklist` before tasks and map every concrete item to `tasked`, `non-goal`, or `user-approved deferral`.
30. For source-checklist items marked `tasked`, make `done_when` prove the requested capability is actually implemented. Do not satisfy "implement OCR", "real adapter", "replace scoring", "run campaigns", or similar capability language with a stub, fallback interface, diagnostic marker, partial hook, or one representative campaign unless the source checklist explicitly allowed that narrower result.
31. If a source-checklist item is too broad, unsafe, or unverifiable for one run, hard-stop before coding and ask the user to split or confirm the deferral. Do not bury it as follow-up work in the task plan.
32. Save `tasks/tasks-plan-<plan-key>.md`.
33. Stop and wait for build trigger.

## Coverage rule

No requirement from PRD or TDD may disappear during task generation.

If something is intentionally omitted from tasks, it must already be explicitly marked as out of scope, deferred, or non-goal in PRD/TDD before task generation.

When the source plan had a source acceptance checklist, omitted items must also be marked `non-goal` or `user-approved deferral` in the task plan checklist. Reviewer caution, Pro advice, or implementation convenience is not enough to defer an item the user asked to implement fully.

Contract details are requirements when they affect implementation. Do not let state machines, config defaults, error classes, invariants, recovery paths, operator intervention points, or validation profiles remain only as descriptive TDD prose if they require code, tests, docs, or runtime behavior.

If a parent task or candidate sub-task mixes frontend, backend, database, deployment, CI, and runtime validation work, split it by primary surface before finalizing the task plan unless it is explicitly justified as an integration slice.

When `--deep-research` is active, this coverage rule also applies to adopted findings from the Finding-to-Artifact Delta. Adopted findings that create `task_plan_inputs_created` must appear in the task plan, or the PRD/TDD must explicitly explain why they are deferred or non-goals.

## Hard stop

Do not start coding after generating the task plan. Build starts only from:

- explicit `$execute-task` activation with a specific `<task-id>` and optional `<plan-key>` when it can be inferred from `/tasks/`
- explicit `$execute-task --one-shot` activation with optional `<plan-key>` when it can be inferred from `/tasks/`
- an orchestration skill such as `$plan-and-execute` that explicitly owns continued execution
