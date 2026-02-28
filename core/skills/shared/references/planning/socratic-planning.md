# Rule: Socratic Planning System

## Goal

Run a lightweight planning conversation that produces a usable task plan in one file:

- `tasks/tasks-plan-<plan-key>.md`

PRD/TDD docs are optional and only generated when explicitly requested or complexity-confirmed.

## Start Trigger

Accepted command:

- `start planning "<unformed-plan>"`

## Preflight (Required)

Before asking planning questions:

1. Confirm trigger matches this workflow.
2. Confirm these references are readable:
   - `skills/shared/references/planning/socratic-planning.md`
   - `skills/shared/references/planning/generate-tasks.md`
   - `skills/shared/references/planning/create-prd.md`
   - `skills/shared/references/planning/create-tdd.md`
3. Choose a stable `<plan-key>` from user context (slug form).
4. If `<plan-key>` is unclear, ask one short clarifying question and stop.

## Conversational Question Loop (Default)

Ask one question per turn in plain language.

Use this loop only:

1. **Intent:** what outcome the user wants.
2. **Example:** one concrete scenario.
3. **Acceptance:** how user decides it is good enough.

Rules:

- Ask constraint questions only when a blocker/risk appears.
- If answer is vague, ask one follow-up.
- Stop when user says "enough".
- Prefer structured dialog questions when client supports it.
- Fallback to plain-text one-question turns when dialog is unavailable.

## Major Complexity Detection

Run this after core loop answers are captured.

### Step 1: Hard triggers (any one => major complexity)

1. Schema/data migration or irreversible transformation.
2. New or changed external contract (API/event/webhook/public CLI behavior).
3. Security/compliance-sensitive behavior (authz, PII, payments, regulated flows).
4. Multi-service or cross-repo integration.
5. Rollout/rollback requiring runbook-level coordination.

### Step 2: Score-based triggers (when no hard trigger)

Assign 1 point for each signal:

1. Touches 3 or more subsystems/layers.
2. Requires non-trivial failure recovery logic.
3. Strict latency/reliability targets likely to affect architecture.
4. Unresolved ambiguity remains after two clarifying questions.
5. Backward compatibility or migration behavior needed for existing users/data.

If score is `>= 3`, mark major complexity.

### Step 3: Escalation behavior

If major complexity is detected, ask exactly one confirmation question:

- "This looks complex because <reasons>. Generate optional PRD/TDD before tasks?"

If user says yes:

- Generate optional PRD/TDD, then generate task plan.

If user says no:

- Continue single-artifact mode and record elevated assumptions in task plan.

## Output Contract

Required planning output:

- `tasks/tasks-plan-<plan-key>.md`

Optional outputs (only by request or complexity-confirmed escalation):

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`

## Execution Trigger Gate (Hard Stop)

After planning outputs are complete:

- Stop and wait for explicit build trigger.
- Do not begin implementation.

Accepted build triggers:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`

Legacy trigger wording with `prd-key`/`prd-id` must be rejected and corrected.

## Validation Scenarios

- User provides simple request and says "enough" early: produce `tasks/tasks-plan-<plan-key>.md` only.
- Hard trigger detected (e.g., schema migration): ask one escalation question.
- Score-based complexity reaches 3+: ask one escalation question.
- User declines escalation: continue without PRD/TDD.
- User accepts escalation: generate PRD/TDD optionally, then task plan.
- No build trigger after planning: hard stop with instruction to use accepted build commands.
