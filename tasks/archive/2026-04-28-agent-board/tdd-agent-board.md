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

- API layer: repo/card/run/settings endpoints with loopback-only defaults and origin checks for state-changing routes.
- Persistence layer: typed SQLite access for repo, card, run, run_event, worktree, pull_request, integration_job, setting, and workflow_override records.
- Workflow loader: reads optional `AGENT_BOARD.md` from managed repos and merges with defaults.
- Orchestrator: owns scheduler state, bounded concurrency, retries, stall detection, reconciliation, and dispatch.
- Workspace manager: creates/reuses per-card worktrees and enforces cwd/path invariants.
- Agent runner: spawns `codex exec --json` subprocesses, parses JSONL events, captures stdout/stderr/exit state, supports cancellation, and updates run events.
- GitHub integration: wraps non-interactive `gh` commands for PR creation/status/checks/merge.
- Git critical-section manager: serializes same-repo shared Git metadata operations such as fetch, branch creation, worktree add/remove/prune, and shared-ref updates.
- Integration lock manager: serializes PR creation, rebase/repair, merge/auto-merge, and cleanup jobs per repo without consuming Codex run slots.

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
- Prime Directive skill/plugin availability inside spawned Codex sessions for Planned Track.
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

Before runner and UI work, the implementation must define a minimal shared API/event contract: card DTO, run DTO, run event DTO, PR DTO, status enum, blocker reason enum, status transition event, log event, blocker event, prompt preview event, and live-stream reconnect cursor semantics. Exact route paths may still be chosen during implementation, but DTO/event names and enum values must be shared by frontend, backend, and tests.

Planned Track must be treated as prompt text. The backend does not shell-execute `$plan-and-execute`; it builds a Codex prompt that begins with `$plan-and-execute --refine-plan` and includes card title, instructions, repo context, and board constraints.

Track ownership differs after Codex returns. Quick Track is backend-finalized: the backend detects changes, classifies protected risk, commits, pushes, and creates the PR. If no changes are detected, it records `no_changes_detected`, blocks, and does not create an empty commit or PR. Planned Track is skill-finalized inside the board-created branch: `$plan-and-execute --refine-plan` owns local planning artifacts, review/finalization behavior, and local commits. The backend verifies and records the resulting branch/PR state, pushes when needed, detects and associates an existing PR for the board branch when present, and creates or updates the PR without adding duplicate finalization commits. Multiple matching PRs block with `existing_pr_ambiguous`.

## Data Model / Schema / Storage Changes

Use SQLite-backed records for:

- `repo`: id, name, path, default branch, remote URL, created/updated timestamps.
- `card`: id, repo id, title, instructions, task type, auto-merge flag, status, branch, worktree id, PR id, blocker summary, override state, timestamps.
- `run`: id, card id, attempt, phase, status, command/prompt summary, started/ended timestamps, exit code, error.
- `run_event`: id, run id, timestamp, event type, stream/log payload, metadata.
- `worktree`: id, card id, repo id, path, branch, status, created/cleaned timestamps. Branch and path must be unique and card-owned.
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
- `TDR-012`: Implement auto-merge guardrails for checks, mergeability, protected-risk classification, unresolved blockers, and no-check Quick Track cases.
- `TDR-013`: Implement blocked-card resume with operator note appended to the next prompt.
- `TDR-014`: Implement restart reconciliation from SQLite, worktrees, and GitHub PR state.
- `TDR-015`: Implement safe post-merge cleanup that archives logs/history before removing a clean, merged worktree.
- `TDR-016`: Implement optional `AGENT_BOARD.md` parsing with defaults, validation, and safe fallback.
- `TDR-017`: Add app-local validation scripts and tests for backend state transitions, guardrails, workflow loading, and core frontend flows.
- `TDR-018`: For Quick Track, backend owns post-run changed-file detection, protected-risk classification, verification decision, `git add`, deterministic commit message, `git push -u origin <branch>`, and `gh pr create --title ... --body ... --base ... --head ...`.
- `TDR-019`: Auto-merge must poll `gh pr view --json` fields including `headRefOid`, `mergeStateStatus`, `mergeable`, `statusCheckRollup`, `reviewDecision`, `isDraft`, `state`, `mergedAt`, `url`, and `number`, then call `gh pr merge --auto --squash --match-head-commit <verifiedHeadSha>` only when guardrails pass. Never use `--admin`.
- `TDR-020`: Cleanup must use `git worktree remove <path>` without `--force`; dirty, missing, or conflicted cleanup cases move to cleanup blocked.
- `TDR-021`: Maintain separate accounting for Codex run slots and integration jobs; integration jobs use per-repo locks and do not consume Codex run slots.
- `TDR-022`: Persist state machine transitions for cards, runs, and integration jobs so restart reconciliation can explain interrupted work.
- `TDR-023`: Protect same-repo shared Git metadata operations with a per-repo critical section while allowing already-created isolated worktrees to run Codex in parallel.
- `TDR-024`: Implement protected-risk classification using path, diff/content, and task-intent heuristics, including semantic risk outside obvious protected paths.
- `TDR-025`: Persist runner lease/process metadata and quarantine ambiguous active runs after restart rather than launching a second runner into the same worktree.
- `TDR-026`: Parse `AGENT_BOARD.md` through an allowlisted schema and reject overrides that weaken immutable safety invariants.
- `TDR-027`: Define shared DTOs, status enums, blocker reason enums, event type enums, and live-stream reconnect cursor semantics before runner/UI implementation.
- `TDR-028`: Implement deterministic card-id-based branch/worktree naming with SQLite uniqueness constraints, same-card reuse validation, different-card collision blocking, stale/dirty path blocking, existing remote branch ambiguity blocking, and no overwrite/force-delete behavior.
- `TDR-029`: Implement Quick Track zero-diff handling as a blocked outcome with reason `no_changes_detected` and no commit/push/PR.
- `TDR-030`: Implement Planned Track existing-PR association for the board branch, with duplicate/ambiguous matches blocked as `existing_pr_ambiguous`.
- `TDR-031`: Implement the no-check auto-merge override as an allowlisted repo-scoped Quick Track-only setting that is off by default and cannot bypass protected-risk, expected-head-SHA, mergeability, draft/open-state, or blocker guardrails.
- `TDR-032`: Bind the local API to loopback by default, reject unexpected origins on state-changing routes, avoid permissive CORS, and test that remote/origin requests cannot trigger Codex, GitHub, merge, or cleanup actions.
- `TDR-033`: Add a gated live smoke/probe for the real `codex exec --json` runner adapter against a disposable fixture; record live GitHub PR creation as run or explicitly skipped for environment/safety reasons.
- `TDR-034`: Preflight Planned Track skill/plugin availability from the perspective of spawned Codex sessions and block with actionable setup text if `$plan-and-execute --refine-plan` cannot resolve.

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

Immutable board safety invariants:

- Codex cwd must equal the validated card worktree path under the configured workspace root.
- Auto-merge must use expected-head-SHA pinning and must never use admin bypass.
- Cleanup must use non-force `git worktree remove` and must block dirty, missing, unmerged, or conflicted worktrees.
- Unresolved runner/review blockers must stop autopilot until explicit resume.
- Protected-risk classification cannot be disabled by repo override.
- Same-repo shared Git metadata operations must remain in per-repo critical sections.
- No-check auto-merge exceptions are Quick Track-only and cannot bypass expected-head-SHA, protected-risk, mergeability, open/non-draft PR state, or unresolved-blocker checks.

Stable blocker reason codes:

- `no_changes_detected`
- `collision_detected`
- `existing_pr_ambiguous`
- `checks_absent`
- `protected_risk`
- `runner_failed`
- `approval_required`
- `cleanup_blocked`
- `restart_quarantined`
- `origin_rejected`
- `planned_skill_unavailable`

## Ingestion / Backfill / Migration / Rollout Plan

No existing board data needs migration. Rollout is additive under `apps/board`.

Implementation should begin with app scaffolding, persistence schema, and tests for the scheduler/workflow model before wiring real Codex and GitHub execution. Because the user requested a real runner in v1, simulated runner behavior may exist only as test support, not as the shipped primary path.

The first real vertical slice must be Quick Track to PR Ready: one repo, one Quick card, deterministic collision-safe worktree, real `codex exec --json`, persisted streamed logs, changed-file detection, protected-risk classification, backend-owned Quick Track commit/push, non-interactive `gh pr create`, zero-diff blocking, and visible PR Ready or Blocked state. Auto-merge, cleanup, Planned Track, and full restart reconciliation should follow after this slice is working.

## Failure Modes / Recovery / Rollback

- Codex missing or exits non-zero: mark card Blocked with command, exit code, and log excerpt.
- `gh` missing or unauthenticated: block GitHub-dependent phases with actionable setup text.
- Unsafe API bind/origin configuration: fail closed and do not start state-changing routes.
- Planned Track skill/plugin unavailable to spawned Codex: block with `planned_skill_unavailable` before launching the runner.
- Worktree path escapes workspace root: hard fail before process launch.
- Branch/worktree collision or ambiguous remote branch: block with `collision_detected`; never overwrite, delete, or force-reuse a colliding branch/path.
- Quick Track produces no changes: block with `no_changes_detected`; do not create an empty commit, push, or PR.
- Planned Track has multiple matching PRs for the board branch: block with `existing_pr_ambiguous`.
- Worktree dirty at cleanup: block cleanup and preserve worktree.
- PR not mergeable: attempt at most one guarded conflict repair pass, then block if unresolved.
- Checks absent: allow PR Ready but block auto-merge unless repo override explicitly permits no-check auto-merge.
- Backend restart: do not assume old subprocesses are recoverable; reconcile durable state and mark interrupted active runs appropriately.
- Ambiguous active runner after restart: persist runner lease/process metadata where possible, probe conservatively, and quarantine/block the card instead of launching another runner into the same worktree.
- Manual UI override: pause autopilot until resume.
- Unsafe Quick Track protected risk: block or require conversion to Planned Track.
- Unsafe workflow override: reject unsupported or invariant-weakening `AGENT_BOARD.md` values and continue with safe defaults where possible.
- SQLite unavailable or corrupt: fail closed and do not launch new runs.
- SQLite WAL files or runtime data mishandled: keep DB, WAL, logs, and worktrees under ignored runtime directories and document that naive file-copy backup is not a supported v1 feature.
- Codex requests approval or attempts unavailable permissions: mark Blocked with the approval/sandbox reason.
- Planned Track token misused as a shell command: tests must prevent backend execution of `$plan-and-execute`; it is prompt text only.

Rollback is to remove or ignore `apps/board`; no existing Prime Directive skill behavior should be required to change for the app to be absent.

## Operational Readiness

The board runs local subprocesses that can edit code, push branches, and merge PRs. It must expose logs, status, and guardrails clearly. Secrets must not be stored in the board database; rely on existing local `gh`, git, and Codex authentication. Generated prompts and logs may contain repo paths and task content, so the app is local-only in v1.

The backend should log structured run events and preserve enough data to debug blocked cards after restart. Long-running or stalled Codex processes need timeout/stall detection and stop/retry behavior. Concurrency settings must be visible and bounded.

Quick Track commits, pushes, and PR creation are backend-owned integration steps after a successful Codex run. Planned Track local commits and finalization are skill-owned, while the backend verifies, records, pushes, and creates or updates PR metadata. Auto-merge must be SHA-pinned to the last verified head commit and must never bypass protection with admin privileges.

## Verification and Test Strategy

App-local verification should include:

- Unit tests for workflow config defaults and `AGENT_BOARD.md` parsing.
- Unit tests for loopback binding, origin checks, and no permissive CORS on state-changing routes.
- Unit tests for scheduler concurrency, per-repo Git critical sections, per-repo integration locks, status transitions, and restart reconciliation.
- Unit tests for protected-risk and auto-merge guardrails.
- Integration tests with fake `codex exec --json` and fake `gh` executables to exercise Quick/Planned run lifecycles without invoking real external systems.
- Worktree safety tests that reject paths outside workspace root and cwd mismatches.
- Frontend tests for card creation, status rendering, blocked details, log stream rendering, and manual override behavior.
- Browser smoke test for the core board flow when the app can run locally.
- Gated live runner smoke for the actual `codex exec --json` adapter against a disposable fixture, with PR creation either safely exercised or explicitly skipped with evidence.

Expected commands should be introduced by the app scaffold. Existing repo-level validation is only `python3 scripts/validate-skill-contracts.py` and installer idempotence; the board must add its own `npm` scripts under `apps/board`.
