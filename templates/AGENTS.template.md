# Agents

Primary workflow uses skills under `skills/`.

## Skill Router
- `start planning "<plan-from-llm>" [--deep-research] [--preserve-planning-artifacts]` -> `plan-task`
- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]` -> `execute-task`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]` -> `execute-task`
- `begin review [--preserve-review-artifacts]` -> `review-chain`
- `begin review <task-id> [--preserve-review-artifacts]` -> `review-chain`
- `begin repo review [--preserve-review-artifacts]` -> `repo-sweep`

## Repo-Specific Norms
- <repo-specific norms>

## Shared Workflow
<shared workflow content injected from core>
