# Rule: Socratic Planning as Source-Plan Intake and Refinement

## Goal

Run a planning conversation that strengthens the source plan and prepares three required execution artifacts:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

Planning is not blank-page generation by default. Treat the user's input as source material to refine, preserve, and normalize.

## Activation Input

Accepted activation:

- `$plan-work`

Supported modifiers:

- `--deep-research`
- `--preserve-planning-artifacts`

The current user request may contain:

- a rough prompt
- a partial plan
- a rich Codex/Claude plan that already includes product, design, test, and execution detail

## Preflight (Required)

Before asking planning questions:

1. Detect the current collaboration mode.
   - If the agent is currently in collaboration `Plan` mode, stop immediately.
   - Alert the user that `$plan-work` cannot run from collaboration `Plan` mode and they must exit back to collaboration `Default` mode first.
   - Do not ask planning questions, do not generate artifacts, and do not continue the workflow.
   - This guard refers to the agent's collaboration mode, not the `rich source plan` / `sparse source prompt` intake classification below.
2. Confirm trigger matches this workflow.
3. Confirm these references are readable:
   - `skills/shared/references/planning/socratic-planning.md`
   - `skills/shared/references/planning/deep-research.md`
   - `skills/shared/references/planning/create-prd.md`
   - `skills/shared/references/planning/create-tdd.md`
   - `skills/shared/references/planning/generate-tasks.md`
   - `skills/shared/references/planning/improve-plan.md`
4. Choose a stable `<plan-key>` from user context (slug form).
5. If `<plan-key>` is unclear, ask one short clarifying question and stop.
6. Classify the planning input:
   - `rich source plan` if it already contains meaningful product/design/execution structure
   - `sparse source prompt` if it does not

Default assumption:

- Treat the input as a `rich source plan` unless it is clearly sparse.
- Treat a source-plan payload as the expected shape, but continue to support sparse prompts when that is what the user provides.

## Intake Normalization (Required)

Before asking planning questions, normalize the request into these four buckets:

1. `Goal`: What needs to change or be built, and why it matters.
2. `Context`: The files, flows, docs, examples, systems, errors, or current-state details that matter.
3. `Constraints`: Requirements, conventions, architecture boundaries, safety rules, and defaults that must be respected.
4. `Done when`: The observable conditions that must be true before the work is considered complete.

Rules:

- Do not skip a bucket just because the user's wording is informal.
- If a bucket is implicit, extract it and restate it plainly.
- If a bucket is missing, ask the smallest clarifying question needed or choose an explicit default.
- Use this intake shape to drive the rest of the planning conversation; do not let important request context remain scattered or unstated.
- Early in intake, inspect the repo's current validation surface: build manifests, scripts or task runners, CI workflows, lint or format configs, typecheck or build configs, and any git hook setup.
- Treat missing validation/tooling as planning input, not an implementation surprise. If the repo lacks meaningful checks for its stack, lock that fact into `Context` or `Constraints` and decide whether bootstrap work belongs in scope.

## Source-Plan Intake Rules

For a rich source plan:

1. Preserve all substantive sections.
2. Do not discard content because it fails an older template shape.
3. Track product-facing content for PRD.
4. Track technical/design content for TDD.
5. Track sequencing, verification, and file-impact content for tasks-plan.
6. Normalize structure only after the content is strengthened.

For a sparse source prompt:

1. Ask enough targeted questions to reach decision completeness.
2. Build the same final artifact set.
3. Do not use a separate lean-mode contract.
4. Use `Goal`, `Context`, `Constraints`, and `Done when` as the minimum intake structure.

## Conversational Question Loop

Ask one question per turn in plain language.

### Rich-plan mode

Ask only targeted questions that expose:

- missing decisions
- contradictions between sections
- risky assumptions
- missing acceptance or verification coverage
- missing frontend design direction or frontend quality criteria for user-facing work
- missing migration, rollout, backfill, or failure-path details
- missing validation, formatting, typecheck, build, CI, or hook enforcement for the stack already in use
- unclear defaults that would force implementer guesswork

Do not re-walk the whole plan if the plan already covers it.

#### Challenge-question minimum

For any non-trivial rich source plan, ask at least one targeted challenge question before document generation unless the plan is clearly small, local-only, and already decision-complete.

Asking at least one challenge question is required when the plan introduces any of:

- new infrastructure, hosting, or deployment behavior
- new schedulers, background jobs, cron-style automation, or always-on services
- source-of-truth changes, replication, backup, or sync behavior
- new external systems, secrets, networking, or connectivity assumptions
- migration, rollout, backfill, rollback, or operational recovery behavior

The challenge question must test an assumption that could materially change implementation, operations, or ownership. Do not spend the question on something cosmetic or already explicit.

It should also probe repo hygiene when that could materially affect delivery quality, such as:

- no lint, format-check, typecheck, or build command despite a sizable code-bearing change
- no CI validation path for checks the plan expects to rely on
- no pre-commit or pre-push enforcement when the team expects local guardrails

### Sparse-plan mode

Use this simple loop:

1. Goal
2. Context
3. Constraints
4. Done when

Ask example or failure-path questions only when they materially clarify one of those four buckets or change implementation behavior.

## Socratic Output Requirements

Before tasks-plan generation, produce and lock:

1. an intake summary with `Goal`, `Context`, `Constraints`, and `Done when`
2. a final plain-language summary that a 12-year-old could follow, written as exactly three short paragraphs
3. a standalone summary checkpoint turn that shows those three paragraphs before tasks-plan drafting starts
4. resolved decisions or explicit defaults for anything that would otherwise remain ambiguous
5. confirmation that important source-plan content will survive normalization

Rules:

- Ask one follow-up if an answer is vague.
- If the answer is still vague, choose a reasonable default and state it explicitly.
- Do not silently default through required challenge-question categories in rich-plan mode.
- Do not collapse the summary checkpoint into tasks-plan generation output.
- End the checkpoint turn with one plain-language question asking what is wrong or missing.
- Do not start tasks-plan generation until the checkpoint question has been answered or there is nothing left for the user to correct.
- Stop when the plan is decision-complete.
- Prefer structured dialog questions when client supports them.
- Fallback to plain-text one-question turns when dialog is unavailable.

## No-Open-Questions Rule

Final planning artifacts must not contain:

- `Open questions`
- `Open technical questions`

Resolve each such item by either:

1. asking during refinement, or
2. converting it into an explicit default/assumption before finalizing PRD, TDD, and tasks-plan

If unresolved ambiguity would change implementation behavior, planning is not complete.

## Output Contract

Required planning outputs:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

All three are mandatory for execution.

Optional temporary planning artifact:

- `tasks/tmp/research-plan-<plan-key>.md` when `--deep-research --preserve-planning-artifacts` is used

## Normalization Rules

When transforming a rich source plan into PRD, TDD, and tasks-plan:

1. Preserve and map the locked intake summary across PRD, TDD, and tasks-plan rather than letting it disappear during normalization.
2. Do not collapse detailed sections into vague summaries.
3. Preserve route, API, schema, migration, rollout, and test content.
4. Preserve product rules, UX rules, missing-data behavior, and non-goals.
5. Preserve concrete frontend design direction and visible quality expectations for user-facing work.
6. Preserve current validation/tooling facts and any explicit decision to add missing lint, format, typecheck, build, CI, or hook enforcement.
7. Split mixed sections across PRD and TDD only when needed; do not drop any part.
8. Ensure the tasks-plan is derived from finalized PRD and TDD, not directly from the raw source plan.
9. If `--deep-research` is active, draft PRD and TDD first, then apply research findings to revise them before generating tasks-plan.
10. If `--deep-research` is active, complete the evidence bar and working memo in `deep-research.md` before tasks-plan generation begins.

## Execution Trigger Gate (Hard Stop)

After planning outputs are complete:

- Stop and wait for explicit build trigger.
- Do not begin implementation.

Accepted execution activations:

- `$execute-task` with a specific `<task-id>` and `<plan-key>`
- `$execute-task` in one-shot mode with a specific `<plan-key>`

Legacy `prd-key`/`prd-id` wording must be rejected and corrected.

## Validation Scenarios

- Rich source plan provided: ask only targeted refinement questions, including at least one challenge question when the plan changes infrastructure, operations, scheduling, or source-of-truth behavior, preserve structure, then generate PRD/TDD/tasks-plan.
- Decision-complete plan provided: generate PRD/TDD from the locked decisions, present the three-paragraph summary checkpoint, resolve any correction, then generate tasks-plan.
- Deep-research planning requested: lock the intake summary first, generate initial PRD/TDD drafts, run the deep research pass to improve them, present the three-paragraph summary checkpoint from the refined decisions, then generate tasks-plan.
- Sparse request provided: ask enough questions to reach decision completeness, then generate PRD/TDD/tasks-plan.
- Source plan contains unresolved ambiguity: convert to explicit default or ask until resolved.
- Source plan contains detailed route/schema/test content: preserve it during normalization.
- No build trigger after planning: hard stop with accepted build commands only.
