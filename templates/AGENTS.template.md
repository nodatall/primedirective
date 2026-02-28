# Agents

Primary workflow uses skills under `skills/`.

## Skill Router
- `start planning "<unformed-plan>"` -> `plan-task`
- `begin task <task-id> in <plan-key>` -> `execute-task`
- `begin one-shot in <plan-key>` -> `execute-task`
- `begin review <task-id>` -> `review-chain`
- `resume review <task-id>` -> `review-chain`
- `begin review ad-hoc` -> `review-chain`
- `resume review ad-hoc` -> `review-chain`

## Repo-Specific Norms
- <repo-specific norms>

## Shared Workflow
<shared workflow content injected from core>
