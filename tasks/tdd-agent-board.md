# Prime Directive Agent Board TDD

## Plain-Language Summary

We are adding a local board app inside Prime Directive. The frontend shows agent-work cards in a Voidgrid-style Kanban board, and the backend stores cards, creates worktrees, starts Codex runs, streams logs, and checks GitHub PR status.

Small tasks use a Quick Track prompt so they do not need a full PRD/TDD/task plan. Bigger tasks use the existing Prime Directive planned workflow by running `$plan-and-execute --refine-plan` inside the card worktree.

The backend is the source of truth while work is running. GitHub becomes the source of truth after a PR exists. Manual UI moves are treated as operator overrides, not as proof that the work actually reached that state.

## Technical Summary

Create a new split local app under `apps/board` with a Vite/React/Tailwind frontend and a Node API backend. The backend persists orchestrator state in SQLite, exposes card/repo/run APIs, streams run events to the frontend, manages bounded parallel Codex subprocesses, creates deterministic per-card git worktrees, shells out to `gh` for PR lifecycle operations, and safely cleans worktrees after merge.

Research-backed runner decision: v1 should use `codex exec --json` as the real Codex runner because official Codex docs position it for scripts/CI and JSONL event consumption. Codex App Server is a future adapter candidate for deeper product integration, but it is experimental and should not be the v1 dependency. The default runner invocation must be non-shell argv equivalent to `codex exec --json --full-auto --sandbox workspace-write <prompt>` from the exact card worktree cwd.

## Scope Alignment to PRD

This TDD covers the first real vertical slice described in the PRD: local-only single-user board, local database, card lifecycle, Quick/Planned routing, per-card worktrees, Codex subprocess execution, GitHub PR handling through `gh`, guarded auto-merge, blocked-card resume, and post-merge cleanup.

## Current Technical Diagnosis

Prime Directive currently has no Node app scaffold. Repo validation is Python-centric: `.github/workflows/validate.yml` runs `python3 scripts/validate-skill-contracts.py` and Codex installer idempotence checks. Root `.gitignore` currently ignores `.DS_Store`, `.codex/environments/`, and `/codex-scripts/`.

Voidgrid provides a nearby reference implementation for board UI and split app shape. It uses npm workspaces, Vite, React 19, Tailwind 4, Atlaskit pragmatic drag/drop, React Query, Express 5, Socket.IO, Prisma, PostgreSQL, Vitest, ESLint, and Playwright. The Agent Board should adapt visual and interaction patterns but use a new backend/domain model and SQLite instead of Voidgrid's auth/project/member/task model.

Validation gaps for this new app must be addressed inside `apps/board`: scripts for typecheck/build/test/lint and enough API/unit/UI tests to protect runner state transitions and guardrails.

## Architecture / Approach

Add a self-contained app workspace:

- `apps/board/package.json` as the board workspace root.
- `apps/board/web` for the Vite/React/Tailwind frontend.
- `apps/board/api` for the local Node backend.
- `apps/board/data` for local SQLite/runtime data, gitignored.
- `apps/board/worktrees` or configured workspace root for per-card worktrees, gitignored.

Backend layers:

- API layer: repo/card/run/settings endpoints.
- Persistence layer: typed SQLite access for repo, card, run, run_event, worktree, pull_request, integration_job, setting, and workflow_override records.
- Workflow loader: reads optional `AGENT_BOARD.md` from managed repos and merges with defaults.
- Orchestrator: owns scheduler state, bounded concurrency, retries, stall detection, reconciliation, and dispatch.
- Workspace manager: creates/reuses per-card worktrees and enforces cwd/path invariants.
- Agent runner: spawns `codex exec --json` subprocesses, parses JSONL events, captures stdout/stderr/exit state, supports cancellation, and updates run events.
- GitHub integration: wraps non-interactive `gh` commands for PR creation/status/checks/merge.
- Integration lock manager: serializes rebase/merge/auto-merge/cleanup per repo.

Frontend layers:

- Board shell and columns.
- Card creation form.
- Agent-state cards.
- Detail drawer with logs, prompts, run history, links, and resume actions.
- Settings screen for concurrency and repo registry.
- Live event subscription via SSE or WebSocket.

## System Boundaries / Source of Truth

- SQLite is the durable local source of truth for cards, runs, events, settings, PR metadata, and operator overrides.
- In-memory orchestrator state is authoritative only for currently running processes and locks; it must be reconstructable enough from SQLite/GitHub/worktrees after restart.
- GitHub is authoritative for PR state after a PR exists.
- Git worktree state is authoritative for local branch cleanliness and cleanup safety.
- The frontend never launches Codex directly; it only asks the backend to enqueue/resume/stop work.
- Codex subprocesses must run only inside the card's validated worktree path under the configured workspace root.
- `AGENT_BOARD.md` is optional repo-owned policy. Missing file means defaults apply.

## Dependencies

- Node.js and npm for the board app.
- Vite, React, Tailwind, and Atlaskit drag/drop for the frontend.
- Node HTTP backend, likely Express based on Voidgrid precedent.
- SQLite driver or ORM selected during implementation; it must support local file persistence, tests, transactions, and WAL mode.
- Codex CLI available on the host, with `codex exec --json --full-auto --sandbox workspace-write` usable from a git worktree.
- Git CLI available on the host.
- GitHub CLI `gh` authenticated on the host.
- Browser automation/test tooling for UI validation.

## Route / API / Public Interface Changes

The board API should provide stable local endpoints for:

- repos: list/create/update/remove managed repos.
- cards: create/list/update/manual move/abandon.
- runs: start/resume/stop/retry/list events.
- logs/events: stream live updates.
- settings: read/update concurrency and workspace root defaults.
- workflow: inspect resolved defaults plus repo override.

Exact route names and handler boundaries are deferred to execution after the app scaffold is chosen.

Planned Track must be treated as prompt text. The backend does not shell-execute `$plan-and-execute`; it builds a Codex prompt that begins with `$plan-and-execute --refine-plan` and includes card title, instructions, repo context, and board constraints.

## Data Model / Schema / Storage Changes

Use SQLite-backed records for:

- `repo`: id, name, path, default branch, remote URL, created/updated timestamps.
- `card`: id, repo id, title, instructions, task type, auto-merge flag, status, branch, worktree id, PR id, blocker summary, override state, timestamps.
- `run`: id, card id, attempt, phase, status, command/prompt summary, started/ended timestamps, exit code, error.
- `run_event`: id, run id, timestamp, event type, stream/log payload, metadata.
- `worktree`: id, card id, repo id, path, branch, status, created/cleaned timestamps.
- `pull_request`: id, card id, repo id, number, URL, state, mergeability, checks state, timestamps.
- `integration_job`: id, card id, repo id, type, status, lock key, attempts, timestamps.
- `setting`: key/value.
- optional `workflow_override`: repo id, path, parsed config, parse status, errors, loaded timestamp.

Generated data files, SQLite databases, logs, and worktrees must be ignored by git.

## Technical Requirements (`TDR-*`)

- `TDR-001`: Add a self-contained `apps/board` split app without changing existing skill behavior.
- `TDR-002`: Use a Voidgrid-inspired frontend architecture and visual language while replacing the domain model with agent-work concepts.
- `TDR-003`: Implement a SQLite persistence layer for repos, cards, runs, run events, worktrees, PRs, integration jobs, and settings.
- `TDR-004`: Implement an orchestrator that supports `max_active_runs=5` and `max_active_cards_per_repo=5` by default.
- `TDR-005`: Implement per-repo integration locks for rebase, merge, auto-merge, and cleanup work.
- `TDR-006`: Implement deterministic per-card git worktree creation/reuse and validate all worktree paths stay inside the configured workspace root.
- `TDR-007`: Refuse to spawn Codex unless cwd exactly equals the card worktree path.
- `TDR-008`: Implement Quick Track prompt generation without PRD/TDD/tasks-plan artifacts.
- `TDR-009`: Implement Planned Track prompt generation where the Codex prompt begins with `$plan-and-execute --refine-plan`; do not treat that token as a backend executable.
- `TDR-010`: Implement live run-event streaming to the UI via SSE or WebSocket.
- `TDR-011`: Wrap `gh` CLI operations for non-interactive PR creation, PR status, checks, mergeability, and guarded auto-merge.
- `TDR-012`: Implement auto-merge guardrails for checks, mergeability, protected paths, unresolved blockers, and no-check Quick Track cases.
- `TDR-013`: Implement blocked-card resume with operator note appended to the next prompt.
- `TDR-014`: Implement restart reconciliation from SQLite, worktrees, and GitHub PR state.
- `TDR-015`: Implement safe post-merge cleanup that archives logs/history before removing a clean, merged worktree.
- `TDR-016`: Implement optional `AGENT_BOARD.md` parsing with defaults, validation, and safe fallback.
- `TDR-017`: Add app-local validation scripts and tests for backend state transitions, guardrails, workflow loading, and core frontend flows.
- `TDR-018`: Backend owns post-run changed-file detection, protected-path scan, verification decision, `git add`, deterministic commit message, `git push -u origin <branch>`, and `gh pr create --title ... --body ... --base ... --head ...`.
- `TDR-019`: Auto-merge must poll `gh pr view --json` fields including `headRefOid`, `mergeStateStatus`, `mergeable`, `statusCheckRollup`, `reviewDecision`, `isDraft`, `state`, `mergedAt`, `url`, and `number`, then call `gh pr merge --auto --squash --match-head-commit <verifiedHeadSha>` only when guardrails pass. Never use `--admin`.
- `TDR-020`: Cleanup must use `git worktree remove <path>` without `--force`; dirty, missing, or conflicted cleanup cases move to cleanup blocked.
- `TDR-021`: Maintain separate accounting for Codex run slots and integration jobs; integration jobs use per-repo locks and do not consume Codex run slots.
- `TDR-022`: Persist state machine transitions for cards, runs, and integration jobs so restart reconciliation can explain interrupted work.

## State Machine

Card statuses:

| status | source of truth | allowed next states |
| --- | --- | --- |
| `Inbox` | SQLite/UI | `Queued`, `Abandoned` |
| `Queued` | orchestrator | `Running`, `Blocked`, `Abandoned` |
| `Running` | runner | `Blocked`, `PR Ready`, `Checks Pending`, `Abandoned` |
| `Blocked` | orchestrator/operator | `Queued`, `Abandoned` |
| `PR Ready` | GitHub + SQLite | `Checks Pending`, `Merging`, `Done`, `Blocked`, `Abandoned` |
| `Checks Pending` | GitHub | `Merging`, `Blocked`, `PR Ready` |
| `Merging` | integration job + GitHub | `Merged`, `Blocked` |
| `Merged` | GitHub | `Done`, `Blocked` |
| `Done` | SQLite final state | none |
| `Abandoned` | operator | none |

Run phases:

| phase | terminal outcomes |
| --- | --- |
| `preflight` | `ready`, `blocked` |
| `worktree` | `ready`, `blocked` |
| `prompt` | `ready`, `blocked` |
| `codex` | `succeeded`, `failed`, `stalled`, `canceled` |
| `post_run_git` | `committed`, `blocked` |
| `pr_create` | `pr_ready`, `blocked` |

Integration job statuses:

| type | serialized scope | outcomes |
| --- | --- | --- |
| `pr_create` | repo | `succeeded`, `blocked` |
| `check_poll` | repo/card | `pending`, `passed`, `failed`, `blocked` |
| `auto_merge` | repo | `queued`, `merged`, `blocked` |
| `conflict_repair` | repo | `repaired`, `blocked` |
| `cleanup` | repo | `cleaned`, `cleanup_blocked` |

## Ingestion / Backfill / Migration / Rollout Plan

No existing board data needs migration. Rollout is additive under `apps/board`.

Implementation should begin with app scaffolding, persistence schema, and tests for the scheduler/workflow model before wiring real Codex and GitHub execution. Because the user requested a real runner in v1, simulated runner behavior may exist only as test support, not as the shipped primary path.

The first real vertical slice must be Quick Track to PR Ready: one repo, one Quick card, deterministic worktree, real `codex exec --json`, persisted streamed logs, changed-file detection, protected-path scan, backend-owned commit/push, non-interactive `gh pr create`, and visible PR Ready or Blocked state. Auto-merge, cleanup, Planned Track, and full restart reconciliation should follow after this slice is working.

## Failure Modes / Recovery / Rollback

- Codex missing or exits non-zero: mark card Blocked with command, exit code, and log excerpt.
- `gh` missing or unauthenticated: block GitHub-dependent phases with actionable setup text.
- Worktree path escapes workspace root: hard fail before process launch.
- Worktree dirty at cleanup: block cleanup and preserve worktree.
- PR not mergeable: attempt at most one guarded conflict repair pass, then block if unresolved.
- Checks absent: allow PR Ready but block auto-merge unless repo override explicitly permits no-check auto-merge.
- Backend restart: do not assume old subprocesses are recoverable; reconcile durable state and mark interrupted active runs appropriately.
- Manual UI override: pause autopilot until resume.
- Unsafe Quick Track protected path: block or require conversion to Planned Track.
- SQLite unavailable or corrupt: fail closed and do not launch new runs.
- SQLite WAL files or runtime data mishandled: keep DB, WAL, logs, and worktrees under ignored runtime directories and document that naive file-copy backup is not a supported v1 feature.
- Codex requests approval or attempts unavailable permissions: mark Blocked with the approval/sandbox reason.
- Planned Track token misused as a shell command: tests must prevent backend execution of `$plan-and-execute`; it is prompt text only.

Rollback is to remove or ignore `apps/board`; no existing Prime Directive skill behavior should be required to change for the app to be absent.

## Operational Readiness

The board runs local subprocesses that can edit code, push branches, and merge PRs. It must expose logs, status, and guardrails clearly. Secrets must not be stored in the board database; rely on existing local `gh`, git, and Codex authentication. Generated prompts and logs may contain repo paths and task content, so the app is local-only in v1.

The backend should log structured run events and preserve enough data to debug blocked cards after restart. Long-running or stalled Codex processes need timeout/stall detection and stop/retry behavior. Concurrency settings must be visible and bounded.

Commits, pushes, and PR creation are backend-owned integration steps after a successful Codex run. This keeps PR behavior deterministic and makes Quick Track independent of whether Codex chose to commit. Auto-merge must be SHA-pinned to the last verified head commit and must never bypass protection with admin privileges.

## Verification and Test Strategy

App-local verification should include:

- Unit tests for workflow config defaults and `AGENT_BOARD.md` parsing.
- Unit tests for scheduler concurrency, per-repo integration locks, status transitions, and restart reconciliation.
- Unit tests for protected-path and auto-merge guardrails.
- Integration tests with fake `codex exec --json` and fake `gh` executables to exercise Quick/Planned run lifecycles without invoking real external systems.
- Worktree safety tests that reject paths outside workspace root and cwd mismatches.
- Frontend tests for card creation, status rendering, blocked details, log stream rendering, and manual override behavior.
- Browser smoke test for the core board flow when the app can run locally.

Expected commands should be introduced by the app scaffold. Existing repo-level validation is only `python3 scripts/validate-skill-contracts.py` and installer idempotence; the board must add its own `npm` scripts under `apps/board`.
