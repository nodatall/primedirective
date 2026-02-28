# Agents

Primary workflow lives in skills under `skills/`.

## Skill Router

Use these skills for workflow triggers:

- `skills/plan-task/SKILL.md`
- `skills/execute-task/SKILL.md`
- `skills/review-chain/SKILL.md`

Trigger mapping:

- `start planning "<unformed-plan>"` -> `plan-task`
- `begin task <task-id> in <plan-key>` -> `execute-task`
- `begin one-shot in <plan-key>` -> `execute-task`
- `begin review <task-id>` -> `review-chain`
- `resume review <task-id>` -> `review-chain`
- `begin review ad-hoc` -> `review-chain`
- `resume review ad-hoc` -> `review-chain`

Planning defaults:

- Default planning output is `tasks/tasks-plan-<plan-key>.md`.
- Socratic flow is conversational: one question per turn, plain language.
- Optional PRD/TDD docs are generated only by explicit request or complexity-confirmed escalation.

Execution behavior:

- `execute-task` includes automatic review rounds for task-based implementation flow.
- `review-chain` exists for explicit review triggers, including ad-hoc and resume review flows.

Shared references:

- Planning: `skills/shared/references/planning/`
- Execution: `skills/shared/references/execution/`
- Review: `skills/shared/references/review/`

## Repo-Specific Norms

- Branch naming: `nodatall/<short-task-name>` (concise, concrete).
- Update `tasks/tasks-plan-<plan-key>.md` after each completed sub-task in task-mode execution.
- For ad-hoc work outside `begin task ...` / `begin one-shot ...`, task-list updates are not required unless explicitly requested.
- Update `README.md` only when setup/commands/env requirements change.
- Tests: prefer `npm test`; if skipped, say why.
- Bugs: add regression test when it fits.
- When working on browser E2E tests (especially files under `tests/e2e/**`, `playwright.config.*`, or Playwright CI scripts), use the `playwright` skill by default.
