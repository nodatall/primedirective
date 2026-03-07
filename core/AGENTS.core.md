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
- `begin review` -> `review-chain`
- `begin review <task-id>` -> `review-chain`

Planning defaults:

- Planning treats user input as source-plan material to improve and normalize.
- Planning always outputs:
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
- Socratic flow is conversational: one question per turn, plain language, targeted gap-checking.
- Final planning artifacts must not contain `Open questions` or `Open technical questions`.
- Plain-language summaries are required in the Socratic flow, PRD, and TDD.

Execution behavior:

- `execute-task` requires PRD + TDD + tasks-plan before coding starts.
- Standard `begin task ...` execution is single-agent.
- `begin one-shot ...` uses one sequential worker subagent per sub-task, with the main agent owning review, integration, task updates, and commits.
- `review-chain` exists for explicit review triggers (`begin review` and `begin review <task-id>`).

Shared references:

- Planning: `skills/shared/references/planning/`
- Execution: `skills/shared/references/execution/`
- Review: `skills/shared/references/review/`

## Repo-Specific Norms

- Branch naming: `<short-task-name>` (concise, concrete).
- Update `tasks/tasks-plan-<plan-key>.md` after each completed sub-task in task-mode execution.
- For ad-hoc work outside `begin task ...` / `begin one-shot ...`, task-list updates are not required unless explicitly requested.
- Update `README.md` only when setup/commands/env requirements change.
- Tests: prefer `npm test`; if skipped, say why.
- Bugs: add regression test when it fits.
- When working on browser E2E tests (especially files under `tests/e2e/**`, `playwright.config.*`, or Playwright CI scripts), use the `playwright` skill by default.
