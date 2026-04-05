# Agents

Primary workflow lives in skills under `skills/`.

## Skill Router

Use these skills for workflow triggers:

- `skills/plan-task/SKILL.md`
- `skills/execute-task/SKILL.md`
- `skills/review-chain/SKILL.md`
- `skills/repo-sweep/SKILL.md`
- `skills/cleanup-merged-branches/SKILL.md`

Trigger mapping:

- `start planning "<plan-from-llm>" [--deep-research] [--preserve-planning-artifacts]` -> `plan-task`
- `begin task <task-id> in <plan-key> [--preserve-review-artifacts]` -> `execute-task`
- `begin one-shot in <plan-key> [--preserve-review-artifacts]` -> `execute-task`
- `begin review [--preserve-review-artifacts]` -> `review-chain`
- `begin review <task-id> [--preserve-review-artifacts]` -> `review-chain`
- `begin repo review [--preserve-review-artifacts]` -> `repo-sweep`
- `clean up merged branches [<branch-name>]` -> `cleanup-merged-branches`

Planning defaults:

- Planning treats user input as source-plan material to improve and normalize.
- `--deep-research` runs a substantial staged research pass focused on technical design, rollout/migration, security/ops, and verification strategy after initial PRD/TDD drafting and before task generation; it is not satisfied by a token search burst.
- `--deep-research` must be anchored to the exact current date, scoped to the plan's actual stack and constraints, and backed by current external primary sources with freshness notes.
- `--deep-research` must produce plan-specific implementation guidance in addition to improving the current PRD/TDD.
- `--preserve-planning-artifacts` keeps temporary planning research artifacts under `tasks/tmp/`.
- Planning always outputs:
  - `tasks/prd-<plan-key>.md`
  - `tasks/tdd-<plan-key>.md`
  - `tasks/tasks-plan-<plan-key>.md`
- Socratic flow is conversational: one question per turn, plain language, targeted gap-checking.
- Before drafting PRD, TDD, or tasks-plan, planning must present a separate plain-language checkpoint in exactly three short paragraphs and give the user a chance to correct it.
- Final planning artifacts must not contain `Open questions` or `Open technical questions`.
- Plain-language summaries are required in the Socratic flow, PRD, and TDD.

Execution behavior:

- `execute-task` requires PRD + TDD + tasks-plan before coding starts.
- Standard `begin task ...` execution is single-agent.
- `begin one-shot ...` uses one sequential worker subagent per sub-task across the entire remaining unchecked task file, with the main agent owning review, integration, task updates, and commits.
- One-shot execution must continue until the remaining unchecked task file is fully complete and finalized; a clean intermediate commit boundary is not a valid stopping point.
- In one-shot mode, any mid-run progress update must be non-terminal and must name the next sub-task already being continued; partial-progress handoffs are invalid unless a real blocker exists.
- `review-chain` exists for explicit review triggers (`begin review` and `begin review <task-id>`).
- `repo-sweep` exists for explicit full-repository sweeps (`begin repo review`) and always stops on a report-and-approval gate before any fixes begin.
Shared references:

- Planning: `skills/shared/references/planning/`
- Execution: `skills/shared/references/execution/`
- Review: `skills/shared/references/review/`

## Repo-Specific Norms

- Branch naming: `<short-task-name>` (concise, concrete).
- After a feature branch is confirmed merged into `origin/main`, delete it locally and on `origin` when safe. Use `clean up merged branches [<branch-name>]` for this. Never delete `main`, the currently checked out branch, a branch with unmerged local commits, or a branch tied to an open PR.
- Update `tasks/tasks-plan-<plan-key>.md` after each completed sub-task in task-mode execution.
- For ad-hoc work outside the explicit workflow commands above, task-list updates are not required unless explicitly requested.
- For ad-hoc code changes, follow existing local implementation and test patterns before introducing a new pattern.
- For ad-hoc code changes, prefer the fastest meaningful verification for the exact slice being changed.
- For ad-hoc changes that are practically testable with a targeted unit, component, or narrow integration test, prefer a failing test first before implementing the change.
- For ad-hoc frontend work, do not default to broad browser or E2E runs during normal iteration; use them only when the change touches a user-critical flow that cannot be validated well with cheaper checks, when the relevant files or repo norms already require them, or when the user explicitly asks for them.
- If a failing-test-first loop is not practical for an ad-hoc change, say why briefly and run the best relevant verification instead.
- Update `README.md` only when setup/commands/env requirements change.
- Tests: prefer `npm test`; if skipped, say why.
- Bugs: add regression test when it fits.
- When working on browser E2E tests (especially files under `tests/e2e/**`, `playwright.config.*`, or Playwright CI scripts), use the `playwright` skill by default.
