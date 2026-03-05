# Rule: Review and Improve Task Plan

## Goal

Run a focused senior-engineering improvement pass before implementation starts.

Primary planning artifact:

- `tasks/tasks-plan-<plan-key>.md`

Optional context (when present):

- `tasks/prd-<plan-key>.md`
- `tasks/tdd-<plan-key>.md`

Treat optional PRD/TDD as additive context, not prerequisites.

## Core engineering principles

All improvements must align with these principles:

- Prefer clarity, explicitness, and maintainability over cleverness.
- Avoid under-engineering (fragile or ambiguous plans).
- Avoid over-engineering (premature abstraction or unnecessary indirection).
- Reduce meaningful duplication without abstracting too early.
- Handle edge cases conservatively where risk exists.
- Keep recommendations proportional to real impact.

When multiple solutions are valid:

- Choose the simplest option that fully solves the problem.
- Favor lower cognitive load for implementers.
- Prefer predictable behavior over speculative flexibility.

## Review and improve in this order

### 1. Architecture and scope review

Evaluate and improve:

- Goal/acceptance alignment inside `tasks/tasks-plan-<plan-key>.md`.
- Task boundaries and responsibility clarity.
- Data flow and integration boundaries (if any).
- Rollout/rollback implications for high-impact changes.
- Security boundaries where auth/data access is touched.

If PRD/TDD exist, validate alignment and resolve conflicts.

Avoid speculative redesign.

### 2. Task quality review

Evaluate and improve:

- Sequencing and dependency order.
- Actionability of each sub-task.
- Elimination of vague steps (replace with concrete outputs).
- Removal of duplicated or redundant tasks.
- Detection of missing failure-path work.

Every sub-task must remain executable with clear completion evidence.

### 3. Test and verification review

Evaluate and improve:

- Coverage of acceptance criteria by task-level verification steps.
- Regression protection for risky areas.
- Missing edge-case checks.
- Gaps in negative-path validation.
- Clarity and executability of `verify` commands.

Add tests/checks only where they materially reduce risk.

### 4. Performance and reliability review

Evaluate and improve:

- Obvious N+1 or heavy-loop risks.
- Inefficient data access or resource usage.
- Retry/timeout/error-recovery expectations.
- Reliability concerns that should be explicit in tasks.

Optimize only when warranted by realistic risk or usage.

## For every issue identified

You must:

1. State the issue clearly.
2. Explain why it matters.
3. Consider multiple fixes internally.
4. Choose one best fix.
5. Explain why that fix is best.
6. Update the task plan accordingly.

Do not dump option menus on the user unless business intent is ambiguous.

## Escalation policy (rare)

Ask a clarifying question only when one is true:

- Product behavior would materially change.
- Business intent is ambiguous.
- Scope/contract changes would affect external stakeholders.

When escalation is required:

- Ask one clear business-language question.
- Avoid technical tradeoff detail unless requested.

## Output expectations

The improved plan must be:

- Structured, concise, and implementation-ready.
- Explicit about assumptions and failure paths.
- Free of obvious over-engineering.
- Clear enough that coding can begin without guessing.

## Execution trigger gate (hard stop)

After plan improvements are complete:

- Stop and wait for explicit execution trigger.
- Do not start implementation from planning review.

Accepted build triggers:

- `begin task <task-id> in <plan-key>`
- `begin one-shot in <plan-key>`
