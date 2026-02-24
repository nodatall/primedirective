---
description:
globs:
alwaysApply: false
---
# Rule: Socratic Planning System (Repo-Agnostic, Standalone Handoff)

## Goal

Run a mandatory decision-clarification workflow before PRD/TDD/task generation so implementation can start without guessing.

This is a **process gate**

## Start Trigger

Accepted command:

`start planning "<unformed-plan>"`

Example:

`start planning "1. do this 2. do this next thing 3. this is a list 4. etc"`

Optional payload:

- `feature: <feature-name>`
- `goal: ...`
- `constraints: ...`
- `must-have: ...`
- `out-of-scope: ...`

## Output Files

Store generated planning artifacts in `/tasks/`:

- `socratic-<feature>.md`
- `decision-log-<feature>.md`
- `prd-<feature>.md`
- `tdd-<feature>.md`
- `tasks-prd-<feature>.md`

## Phase 0: Planning Preflight (Required)

Before asking any Socratic questions:

1. Verify trigger intent matches this workflow (`start planning "<unformed-plan>"`).
2. Verify required rule files exist and are readable:
   - `rules/socratic-planning.md`
   - `rules/create-prd.md`
   - `rules/create-tdd.md`
   - `rules/generate-tasks.md`
3. Verify planning artifact paths under `/tasks/` and create missing artifacts when needed.
4. Confirm feature slug and source reference in one short line. If feature is missing, ask one short question and stop.

If preflight fails, ask one plain-language corrective question and stop until resolved.

## Phase 0.5: Unformed Plan Quote Capture (Required)

Before any Socratic question round:

1. Collect all currently available raw plan input from the trigger's quoted text and follow-up messages.
2. Present it as a quoted list titled `Unformed Plan So Far (Quoted)` using block quotes.
3. Preserve wording as closely as possible; split into short quote lines for readability.
4. Ask one quick confirmation question: "What did I miss or misquote?"
5. Persist this capture in `socratic-<feature>.md` as `raw_plan_quotes`.

If trigger text is not quoted or no raw plan text is present, ask one short corrective question and stop until provided.

## Phase 1: Socratic Rounds (Mandatory)

Run micro-rounds with **1-2 high-impact questions per round**.

### Conversation Style (Required)

- Ask questions in plain language suitable for a non-technical stakeholder.
- Default to product/operational wording; only ask deep technical questions when they are strictly required by the current sequence step.
- Prefer concrete options over open-ended technical prompts (use simple A/B choices when helpful).
- Avoid process narration in user-facing replies (for example: "locking decisions", "gates", "auditable chain", "handoff integrity").
- Keep each user turn short: one recap paragraph plus the next 1-2 questions.
- Maintain schemas/files in the background without narrating internal bookkeeping each turn.

### Round Interaction Contract (Required)

- Ask at most 2 questions per turn.
- Ask one concept per question.
- For ambiguous topics, present options with a recommended default first.
- Do not proceed to a new sequence step while prior-step ambiguity remains unresolved.

User-facing turn format:

1. `Unformed Plan So Far (Quoted)` (block quotes, required until confirmed complete)
2. `Recap` (2-4 sentences, plain language)
3. `Questions` (1-2 items, each answerable quickly)

Each round must include:

- Questions asked
- User answers
- Locked decisions
- Remaining unknowns
- Plain-language recap (short)

Persist round history in `socratic-<feature>.md` using this schema:

- `raw_plan_quotes` (required in first round; update if corrected later)
- `round`
- `questions`
- `answers`
- `locked_decisions`
- `remaining_unknowns`
- `plain_recap`

Maintain `decision-log-<feature>.md` with this schema:

- `id`
- `decision`
- `reason`
- `alternatives`
- `impact`
- `status` (`active` | `superseded`)
- `superseded_by` (optional decision id)

### Ambiguity Handling (Required)

- If user answer is vague (for example: "sure", "not sure", "depends"), do not silently lock it.
- Respond with:
  - one-sentence interpretation,
  - one confirmation question (`yes/no` or `A/B`),
  - optional recommended default.
- Record decision only after explicit confirmation.

### Required Socratic Sequence (in order)

1. Problem clarity: exact user problem being solved.
2. Success clarity: measurable done outcomes.
3. Scope clarity: in-scope vs out-of-scope.
4. Constraint clarity: legal/compliance/ops boundaries.
5. Data clarity: required data, quality expectations, ownership.
6. Execution clarity: command paths, runtime behavior, dependencies.
7. Failure clarity: what can fail, detection, recovery, rollback.
8. Rollout clarity: release shape, monitoring, operator workflow.
9. Plain-language readiness: 12-year-old summary + checklist.

Sequence behavior:

- Do not jump ahead to execution-level technical details during Problem/Success/Scope clarity unless the user explicitly asks.
- Convert vague answers into simple measurable criteria using non-technical wording first, then map to technical artifacts later in PRD/TDD.
- By the end of Success Clarity, convert quality goals into observable pass/fail criteria (percentages, thresholds, or explicit rule sets).

### Contradiction Check (Required After Every Round)

- Run a contradiction sweep against all prior locked decisions.
- If conflict exists:
  - mark older decision(s) as `superseded`,
  - reference the replacement via `superseded_by`,
  - include one-line plain-language note in round recap.
- Do not leave two active decisions that conflict.

## Gate to Move Forward

PRD/TDD generation is allowed only when all are true:

- No unresolved high-impact unknowns remain.
- Core behavior decisions are explicit.
- Execution path is concrete enough to implement without guessing.
- User accepts the plain-language summary + checklist.

If any gate fails, continue Socratic rounds.

## Non-Technical Approval Layer (Mandatory)

Before implementation handoff, present:

- 3 short paragraphs understandable by a 12-year-old.
- 5 yes/no checklist items.

If any checklist item is `No`, return to Socratic rounds. Do not proceed to implementation handoff.

## Phase 2: PRD Generation Handoff

After Phase 1 gate passes, generate `prd-<feature>.md` using `rules/create-prd.md`.

PRD remains product truth (`what/why`) and must not include deep implementation details.

## Phase 3: TDD Generation Handoff

After PRD approval, generate `tdd-<feature>.md` using `rules/create-tdd.md`.

TDD is execution truth (`how`) and must include:

- Architecture and component boundaries
- Data model/storage changes
- Interfaces/contracts (API/CLI/events)
- Command contract (exact run commands + expected outcomes)
- Failure modes and rollback
- Observability/monitoring
- Test strategy (unit/integration/e2e)
- Rollout plan and operational runbook

Use stable technical requirement IDs in TDD: `TDR-*`.

## Phase 4: Task Generation Handoff

Generate tasks only after both `prd-<feature>.md` and `tdd-<feature>.md` exist and are reconciled.

Use `rules/generate-tasks.md`, which must enforce:

- PRD coverage map (`FR-*`)
- TDD coverage map (`TDR-*`)
- Stop on PRD/TDD conflicts until reconciled
- Sub-task metadata: `covers_prd`, `covers_tdd`, `verify`, `done_when`

## Execution Trigger Gate (Mandatory Hard Stop)

After planning artifacts are complete (`socratic-*`, `decision-log-*`, `prd-*`, `tdd-*`, `tasks-prd-*`, and plan-improvement pass):

- Stop the flow and wait for an explicit build-start command.
- Do NOT begin implementation, code edits, branch creation, or Step 1-9 execution from planning flow.
- Accepted build-start commands are only:
  - `begin task <task-id> in <prd-key>`
  - `begin one-shot in <prd-id>`
  - `begin 1 shot in <prd-id>` (alias of one-shot mode)
- If user requests to "continue" or "start building" without one of the accepted commands, ask for one of the exact commands and do not proceed.

Execution cleanup/archive behavior belongs to `rules/task-management.md` and `AGENTS.md` finalization flow, not Socratic planning.

## Process Validation Scenarios

- PRD exists but TDD missing:
  - Expected: do not generate tasks.
- PRD and TDD disagree on behavior:
  - Expected: stop and reconcile first.
- Task missing `covers_tdd` or `verify`:
  - Expected: task list is incomplete.
- Socratic rounds skipped:
  - Expected: do not proceed to PRD/TDD generation.
- Plain-language checklist not approved:
  - Expected: return to Socratic rounds, no implementation handoff.
- PRD/TDD/task plan complete but no build trigger command:
  - Expected: hard stop and wait; do not start implementation.
- Ambiguous user answer left unconfirmed:
  - Expected: do not lock decision; ask one clarification before continuing sequence.
- Conflicting decisions both marked active:
  - Expected: mark prior decision superseded before advancing.

## Assumptions and Defaults

- This process is human-enforced, not lint/CI-enforced.
- PRD is product truth (`what/why`), TDD is execution truth (`how`).
- Task generation always requires both PRD + TDD.
- Unknowns must be resolved through micro-round questions, not hidden as assumptions.
- Optimize for low cognitive load for approvers and high clarity for implementers.
