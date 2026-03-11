# Agents

Primary workflow uses skills under `skills/`.

## Skill Router
- `start planning "<unformed-plan>"` -> `plan-task`
- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]` -> `execute-task`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]` -> `execute-task`
- `begin review [--preserve-review-artifacts]` -> `review-chain`
- `begin review <task-id> [--preserve-review-artifacts]` -> `review-chain`

## Repo-Specific Norms
- <repo-specific norms>

## Shared Workflow
<shared workflow content injected from core>
