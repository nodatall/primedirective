See `skills/shared/references/execution/task-management.md` for execution workflow and review guidelines.

# Prime Directive Agent Board

## Scope Summary

- Build a local single-user agent-work Kanban app under `apps/board`.
- Prove the real Quick Track to PR Ready vertical slice before advanced automation.
- Keep full v1 scope: Quick/Planned tracks, local SQLite, Codex runner, worktrees, GitHub PRs, guarded auto-merge, cleanup, restart reconciliation, and Voidgrid-inspired UI.
- Highest risks: subprocess safety, worktree cleanup, PR/merge guardrails, state-machine drift, and UI that looks like a generic task board instead of an agent cockpit.

## Relevant Files

- `apps/board/package.json` - Board workspace scripts and dependencies.
- `apps/board/api/src/**` - Local API, persistence, orchestration, runner, Git/worktree/GitHub integrations.
- `apps/board/web/src/**` - Voidgrid-inspired board UI, card form, card detail/log surface.
- `apps/board/tests/**` - Backend and integration tests with fake Codex/gh/git where useful.
- `apps/board/playwright/**` - Browser smoke coverage for the board.
- `apps/board/AGENT_BOARD.example.md` - Example optional workflow override.
- `.gitignore` - Runtime DB/log/worktree ignores.

## Task Ordering Notes

- Build backend contracts and tests before polishing UI.
- The first real vertical slice is Quick Track to PR Ready; it must land before Planned Track, auto-merge, cleanup, and conflict repair.
- Use fake runner/gh tests for deterministic lifecycle coverage, then wire the real runner command.
- Keep exact routes, file layout, and helper boundaries flexible where the implementation finds a simpler local structure.

## Tasks

- [ ] 1.0 Scaffold the board app and validation surface
  - covers_prd: `FR-001`, `FR-003`
  - covers_tdd: `TDR-001`, `TDR-002`, `TDR-017`
  - [ ] 1.1 Add `apps/board` npm workspace scaffold with `api` and `web` packages, TypeScript configs, lint/test/build scripts, and ignored runtime directories.
    - covers_prd: `FR-001`, `FR-003`
    - covers_tdd: `TDR-001`, `TDR-017`
    - output: `apps/board/package.json`, `apps/board/api`, `apps/board/web`, `.gitignore`
    - verify: `npm run build --prefix apps/board`
    - done_when: The board workspace can install/build/test independently without changing existing skill validation behavior.
  - [ ] 1.2 Seed Voidgrid-inspired Tailwind theme, board shell, and basic API server health endpoint.
    - covers_prd: `FR-001`
    - covers_tdd: `TDR-002`, `TDR-017`
    - output: `apps/board/web/src`, `apps/board/api/src`
    - verify: `npm run test --prefix apps/board`
    - done_when: Tests can render the board shell and call the API health endpoint.

- [ ] 2.0 Implement persistence, state machine, and workflow defaults
  - covers_prd: `FR-003`, `FR-004`, `FR-005`, `FR-006`, `FR-020`, `FR-021`
  - covers_tdd: `TDR-003`, `TDR-016`, `TDR-022`
  - [ ] 2.1 Add SQLite schema and data access for repos, cards, runs, run events, worktrees, PRs, integration jobs, settings, and workflow overrides.
    - covers_prd: `FR-003`, `FR-004`
    - covers_tdd: `TDR-003`
    - output: `apps/board/api/src/db`
    - verify: `npm run test --prefix apps/board -- api`
    - done_when: Unit tests prove records persist and WAL/runtime paths stay under ignored app data.
  - [ ] 2.2 Add typed state machine transitions for cards, runs, and integration jobs.
    - covers_prd: `FR-005`, `FR-006`, `FR-021`
    - covers_tdd: `TDR-022`
    - output: `apps/board/api/src/domain`
    - verify: `npm run test --prefix apps/board -- state`
    - done_when: Invalid transitions are rejected and manual overrides pause autopilot.
  - [ ] 2.3 Add optional `AGENT_BOARD.md` loader with safe defaults and example file.
    - covers_prd: `FR-020`
    - covers_tdd: `TDR-016`
    - output: `apps/board/api/src/workflow`, `apps/board/AGENT_BOARD.example.md`
    - verify: `npm run test --prefix apps/board -- workflow`
    - done_when: Missing files use defaults; malformed or unsafe overrides produce visible validation errors.

- [ ] 3.0 Add repo preflight and worktree management
  - covers_prd: `FR-011`, `FR-019`, `FR-021`
  - covers_tdd: `TDR-006`, `TDR-007`, `TDR-020`
  - [ ] 3.1 Implement repo registry/preflight for path canonicalization, git repo detection, remote/default branch detection, Codex availability, and `gh` availability.
    - covers_prd: `FR-004`, `FR-011`
    - covers_tdd: `TDR-006`
    - output: `apps/board/api/src/repos`
    - verify: `npm run test --prefix apps/board -- repo`
    - done_when: Invalid repos/tools block runs with actionable errors.
  - [ ] 3.2 Implement deterministic per-card worktree creation/reuse and cwd/workspace-root safety checks.
    - covers_prd: `FR-011`
    - covers_tdd: `TDR-006`, `TDR-007`
    - output: `apps/board/api/src/worktrees`
    - verify: `npm run test --prefix apps/board -- worktree`
    - done_when: Tests prove escaped paths/cwd mismatches are rejected before Codex can launch.
  - [ ] 3.3 Implement safe post-merge cleanup using non-force `git worktree remove`.
    - covers_prd: `FR-019`
    - covers_tdd: `TDR-020`
    - output: `apps/board/api/src/worktrees`
    - verify: `npm run test --prefix apps/board -- cleanup`
    - done_when: Dirty/unmerged worktrees move to cleanup blocked instead of being deleted.

- [ ] 4.0 Implement runner, scheduler, and Quick Track to PR Ready
  - covers_prd: `FR-005`, `FR-007`, `FR-009`, `FR-010`, `FR-011`, `FR-012`, `FR-013`, `FR-014`, `FR-015`, `FR-015A`, `FR-018`
  - covers_tdd: `TDR-004`, `TDR-005`, `TDR-008`, `TDR-010`, `TDR-011`, `TDR-018`, `TDR-021`
  - [ ] 4.1 Implement fake runner plus real `codex exec --json --full-auto --sandbox workspace-write` runner adapter with JSONL parsing, cancellation, timeout, and event persistence.
    - covers_prd: `FR-012`, `FR-013`
    - covers_tdd: `TDR-008`, `TDR-010`
    - output: `apps/board/api/src/runner`
    - verify: `npm run test --prefix apps/board -- runner`
    - done_when: Tests exercise successful, failed, stalled, and unknown-event runs without invoking real Codex.
  - [ ] 4.2 Implement scheduler with default five global run slots, five per-repo run slots, blocked slot release, and separate per-repo integration locks.
    - covers_prd: `FR-005`, `FR-009`, `FR-010`
    - covers_tdd: `TDR-004`, `TDR-005`, `TDR-021`
    - output: `apps/board/api/src/orchestrator`
    - verify: `npm run test --prefix apps/board -- scheduler`
    - done_when: Tests prove five same-repo cards may run while integration jobs serialize per repo.
  - [ ] 4.3 Implement Quick Track prompt generation, protected-path scan, post-run diff detection, backend-owned commit/push, and non-interactive PR creation.
    - covers_prd: `FR-007`, `FR-011`, `FR-015`, `FR-015A`, `FR-018`
    - covers_tdd: `TDR-008`, `TDR-011`, `TDR-018`
    - output: `apps/board/api/src/quick-track`, `apps/board/api/src/github`
    - verify: `npm run test --prefix apps/board -- quick`
    - done_when: Fake git/gh tests prove Quick Track reaches PR Ready or Blocked with persisted evidence.
  - [ ] 4.4 Implement blocked-card resume with operator notes appended to the next prompt.
    - covers_prd: `FR-013`, `FR-014`
    - covers_tdd: `TDR-013`
    - output: `apps/board/api/src/orchestrator`, `apps/board/api/src/runner`
    - verify: `npm run test --prefix apps/board -- resume`
    - done_when: A blocked card can resume and the next run records the operator note.

- [ ] 5.0 Build the core board UI and live status surface
  - covers_prd: `FR-001`, `FR-002`, `FR-005`, `FR-006`, `FR-012`, `FR-013`, `FR-014`
  - covers_tdd: `TDR-002`, `TDR-010`, `TDR-017`
  - [ ] 5.1 Implement repo/card APIs and frontend card creation form with `Title`, `Repo`, `Instructions`, `Task type`, and `Auto-merge PR`.
    - covers_prd: `FR-002`, `FR-003`, `FR-004`
    - covers_tdd: `TDR-003`
    - output: `apps/board/api/src/routes`, `apps/board/web/src/features/cards`
    - verify: `npm run test --prefix apps/board -- cards`
    - done_when: Creating a card persists it and renders it on the board.
  - [ ] 5.2 Implement Voidgrid-inspired board columns, agent-state cards, progress strip, PR/check badge, and auto-merge marker.
    - covers_prd: `FR-001`, `FR-005`, `FR-012`
    - covers_tdd: `TDR-002`
    - output: `apps/board/web/src/features/board`
    - verify: `npm run test --prefix apps/board -- board`
    - done_when: Card status is readable at a glance and manual moves create overrides.
  - [ ] 5.3 Implement detail drawer with instructions, prompt preview, live logs, run history, artifacts/links, blocker context, and resume action.
    - covers_prd: `FR-012`, `FR-013`, `FR-014`
    - covers_tdd: `TDR-010`, `TDR-013`
    - output: `apps/board/web/src/features/card-detail`
    - verify: `npm run test --prefix apps/board -- detail`
    - done_when: A blocked card can be diagnosed and resumed from the UI.

- [ ] 6.0 Add Planned Track, GitHub polling, auto-merge, and reconciliation
  - covers_prd: `FR-005`, `FR-008`, `FR-016`, `FR-017`, `FR-017A`, `FR-018`, `FR-019`, `FR-021`
  - covers_tdd: `TDR-009`, `TDR-011`, `TDR-012`, `TDR-014`, `TDR-015`, `TDR-019`, `TDR-020`
  - [ ] 6.1 Implement Planned Track prompt generation as Codex prompt text beginning `$plan-and-execute --refine-plan`.
    - covers_prd: `FR-008`
    - covers_tdd: `TDR-009`
    - output: `apps/board/api/src/planned-track`
    - verify: `npm run test --prefix apps/board -- planned`
    - done_when: Planned Track never attempts to shell-execute `$plan-and-execute`.
  - [ ] 6.2 Implement GitHub PR polling for state, checks, mergeability, and PR-ready/checks-pending transitions.
    - covers_prd: `FR-005`, `FR-016`, `FR-017`, `FR-018`
    - covers_tdd: `TDR-011`, `TDR-012`
    - output: `apps/board/api/src/github`
    - verify: `npm run test --prefix apps/board -- github`
    - done_when: Fake `gh` tests cover passing, pending, failing, no-check, draft, and closed PR states.
  - [ ] 6.3 Implement guarded auto-merge with expected-head-SHA pinning and no admin bypass.
    - covers_prd: `FR-016`, `FR-017`, `FR-017A`, `FR-018`
    - covers_tdd: `TDR-012`, `TDR-019`
    - output: `apps/board/api/src/github`, `apps/board/api/src/orchestrator`
    - verify: `npm run test --prefix apps/board -- automerge`
    - done_when: Auto-merge only runs when enabled and all guardrails pass.
  - [ ] 6.4 Implement restart reconciliation from SQLite, worktrees, and GitHub PR state.
    - covers_prd: `FR-021`
    - covers_tdd: `TDR-014`, `TDR-022`
    - output: `apps/board/api/src/orchestrator`
    - verify: `npm run test --prefix apps/board -- reconcile`
    - done_when: Interrupted active runs become explainable states after API restart.
  - [ ] 6.5 Wire post-merge cleanup into merged/done lifecycle.
    - covers_prd: `FR-019`
    - covers_tdd: `TDR-015`, `TDR-020`
    - output: `apps/board/api/src/orchestrator`, `apps/board/api/src/worktrees`
    - verify: `npm run test --prefix apps/board -- cleanup`
    - done_when: Merged clean PRs clean up worktrees and dirty/unmerged cases block cleanup.

- [ ] 7.0 Final validation, browser evidence, and docs
  - covers_prd: `FR-001` through `FR-021`
  - covers_tdd: `TDR-001` through `TDR-022`
  - [ ] 7.1 Add README/runbook for local board setup, repo registration, Quick/Planned behavior, auto-merge guardrails, and cleanup rules.
    - covers_prd: `FR-020`
    - covers_tdd: `TDR-016`, `TDR-017`
    - output: `apps/board/README.md`
    - verify: `npm run build --prefix apps/board`
    - done_when: A local operator can start the board and understand required host tools.
  - [ ] 7.2 Add browser smoke test for creating a card, seeing it run/block/PR-ready with fake backend state, and opening the detail drawer.
    - covers_prd: `FR-001`, `FR-002`, `FR-012`, `FR-013`
    - covers_tdd: `TDR-002`, `TDR-017`
    - output: `apps/board/playwright`
    - verify: `npm run test:e2e --prefix apps/board`
    - done_when: Browser evidence covers board, card creation, log/detail, and responsive layout.
  - [ ] 7.3 Run final app validation and existing Prime Directive validation.
    - covers_prd: `FR-001` through `FR-021`
    - covers_tdd: `TDR-001` through `TDR-022`
    - output: validation evidence
    - verify: `npm run test --prefix apps/board && npm run build --prefix apps/board && python3 scripts/validate-skill-contracts.py`
    - done_when: All relevant checks pass or any unavoidable environment gap is explicitly documented.
