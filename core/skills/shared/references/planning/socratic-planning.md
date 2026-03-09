# Rule: Socratic Planning as Source-Plan Intake and Refinement

## Goal

Run a planning conversation that strengthens the source plan and prepares three required execution artifacts:

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`
- `tasks/tasks-plan-<plan-key>.md`

Planning is not blank-page generation by default. Treat the user's input as source material to refine, preserve, and normalize.

## Start Trigger

Accepted command:

- `start planning "<unformed-plan>"`

The quoted payload may contain:

- a rough prompt
- a partial plan
- a rich Codex/Claude plan that already includes product, design, test, and execution detail

## Preflight (Required)

Before asking planning questions:

1. Confirm trigger matches this workflow.
2. Confirm these references are readable:
   - `skills/shared/references/planning/socratic-planning.md`
   - `skills/shared/references/planning/create-prd.md`
   - `skills/shared/references/planning/create-tdd.md`
   - `skills/shared/references/planning/generate-tasks.md`
   - `skills/shared/references/planning/improve-plan.md`
3. Choose a stable `<plan-key>` from user context (slug form).
4. If `<plan-key>` is unclear, ask one short clarifying question and stop.
5. Classify the planning input:
   - `rich source plan` if it already contains meaningful product/design/execution structure
   - `sparse source prompt` if it does not

Default assumption:

- Treat the input as a `rich source plan` unless it is clearly sparse.

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
- missing migration, rollout, backfill, or failure-path details
- unclear defaults that would force implementer guesswork

Do not re-walk the whole plan if the plan already covers it.

### Sparse-plan mode

Use this simple loop:

1. Goal
2. Context
3. Constraints
4. Done when

Ask example or failure-path questions only when they materially clarify one of those four buckets or change implementation behavior.

## Socratic Output Requirements

Before document generation, produce and lock:

1. an intake summary with `Goal`, `Context`, `Constraints`, and `Done when`
2. a final plain-language summary that a 12-year-old could follow
3. resolved decisions or explicit defaults for anything that would otherwise remain ambiguous
4. confirmation that important source-plan content will survive normalization

Rules:

- Ask one follow-up if an answer is vague.
- If the answer is still vague, choose a reasonable default and state it explicitly.
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

## Normalization Rules

When transforming a rich source plan into PRD, TDD, and tasks-plan:

1. Preserve and map the locked intake summary across PRD, TDD, and tasks-plan rather than letting it disappear during normalization.
2. Do not collapse detailed sections into vague summaries.
3. Preserve route, API, schema, migration, rollout, and test content.
4. Preserve product rules, UX rules, missing-data behavior, and non-goals.
5. Split mixed sections across PRD and TDD only when needed; do not drop any part.
6. Ensure the tasks-plan is derived from finalized PRD and TDD, not directly from the raw source plan.

## Execution Trigger Gate (Hard Stop)

After planning outputs are complete:

- Stop and wait for explicit build trigger.
- Do not begin implementation.

Accepted build triggers:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`

Legacy trigger wording with `prd-key`/`prd-id` must be rejected and corrected.

## Validation Scenarios

- Rich source plan provided: ask only targeted refinement questions, preserve structure, then generate PRD/TDD/tasks-plan.
- Sparse request provided: ask enough questions to reach decision completeness, then generate PRD/TDD/tasks-plan.
- Source plan contains unresolved ambiguity: convert to explicit default or ask until resolved.
- Source plan contains detailed route/schema/test content: preserve it during normalization.
- No build trigger after planning: hard stop with accepted build commands only.
