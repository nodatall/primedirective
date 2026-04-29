# Prime Directive Agent Board PRD

## Plain-Language Summary

We are building a local board for running many Codex jobs at once. Each card is a piece of agent work, such as a tiny UI change or a larger planned feature, and the board shows where that work is: waiting, running, blocked, ready for review, merged, or done.

The board should feel like Voidgrid visually, but it is not a team task manager. It is an operator cockpit for this machine: create a card, choose Quick or Planned, watch logs, get a PR, optionally auto-merge safe work, and clean up the temporary worktree after the PR is merged.

The first version should be real, not a mock. It should create per-card worktrees, run Codex from the backend, stream status to the UI, use GitHub through `gh`, and keep enough history that a blocked card can be resumed without searching through terminal tabs.

## Target User / Audience

The primary user is a local Prime Directive operator running many Codex/Prime Directive jobs across repositories under `/Volumes/Code`.

Secondary future users may include other developers, but v1 is explicitly single-user and local-only.

## Problem Statement

Prime Directive skills define how work should be planned, executed, reviewed, and finalized, but there is no persistent visual control surface for many concurrent runs. Managing several Codex sessions through terminal or Desktop threads makes it hard to see which jobs are active, blocked, waiting on PR checks, mergeable, or safe to clean up.

## Current-State / Product Diagnosis

Prime Directive is currently a skills/plugin source repo with Python validation and installer scripts. It has no app surface, no local database, no runner state, and no UI. Voidgrid already demonstrates a polished dark Kanban board style using Vite, React, Tailwind, Express, Socket.IO, Prisma, and drag/drop, but its product model is project/member/task collaboration rather than local agent orchestration.

The new board should borrow the visual and interaction language from Voidgrid while using a new agent-specific domain model.

## Product Goal

Ship a local web app under `apps/board` that lets the user create and supervise multiple agent-work cards in parallel, with automatic status movement, live logs, real Codex execution, GitHub PR creation, optional guarded auto-merge, and post-merge worktree cleanup.

## Success Criteria

- The first real vertical slice supports one managed repo, one Quick card, real worktree creation, real `codex exec --json` execution, streamed logs, persisted events, backend-owned commit/push/PR creation, and a visible PR Ready or Blocked result.
- The user can create a card with `Title`, `Repo`, `Instructions`, `Task type`, and `Auto-merge PR`.
- The board can run up to five active cards globally and up to five active cards for the same repo by default.
- Every active card runs in its own deterministic git worktree.
- Deterministic branch/worktree names must be card-id-based and must fail closed on collisions instead of overwriting or deleting an existing branch/path.
- The local API binds to loopback by default and does not allow arbitrary browser origins to trigger Codex, GitHub, merge, or cleanup actions.
- Quick cards run without PRD/TDD/tasks-plan artifacts.
- Planned cards invoke `$plan-and-execute --refine-plan`.
- Card status moves automatically from runner and GitHub state rather than relying on manual dragging.
- Blocked cards show the reason and can be resumed with an operator note.
- The UI shows live logs and run history.
- The board creates PRs through `gh`.
- Auto-merge only occurs when enabled on the card and guardrails pass.
- Merged cards clean up their worktree while preserving card/run history.

## First Real Vertical Slice

The first implementation slice must prove the real runner path before advanced automation polish:

- register one managed repo
- create one Quick card
- create a deterministic worktree and branch
- run real `codex exec --json`
- stream and persist run events/logs
- detect changed files
- run protected-risk classification
- backend commits and pushes the branch for Quick Track
- backend creates a PR through non-interactive `gh pr create`
- card lands in `PR Ready` or `Blocked`
- if Quick Track succeeds with no file changes, the card blocks with `no_changes_detected` instead of creating an empty commit or PR

Auto-merge, post-merge cleanup, Planned Track, full restart reconciliation, conflict repair, and refined UI polish remain part of v1, but must be sequenced after this first vertical slice.

## Explicit Non-Goals

- No Linear integration in v1.
- No multi-user auth or team collaboration in v1.
- No hosted/OAuth/GitHub App mode in v1.
- No generic workflow graph editor in v1.
- No attempt to make the board strictly Symphony-compatible.
- No reuse of Voidgrid's auth, member, project, task, or subtask domain.
- No full multi-attempt conflict solver in v1 beyond one guarded repair attempt.

## User Stories or Primary User Outcomes

- As the operator, I can create a Quick card for a small local change and get a PR without creating a full plan.
- As the operator, I can create a Planned card for substantial work and have the board run the existing Prime Directive planned workflow.
- As the operator, I can watch five cards run in parallel without losing track of logs or state.
- As the operator, I can see which cards are blocked and resume one with a note.
- As the operator, I can allow a simple card to auto-merge only when the PR is green and safe.
- As the operator, I can trust that merged card worktrees are cleaned up automatically.

## Functional Requirements (`FR-*`)

- `FR-001`: The app must provide a Voidgrid-inspired Kanban board UI for local agent-work cards.
- `FR-002`: The card creation form must expose only `Title`, `Repo`, `Instructions`, `Task type` (`Quick` or `Planned`), and `Auto-merge PR` as primary controls.
- `FR-003`: The board must persist repos, cards, runs, run events, worktrees, pull request metadata, integration jobs, and settings locally.
- `FR-004`: The board must treat cards as local-first records; repo task artifacts may be linked but are not required at creation.
- `FR-005`: The backend must automatically move card status from orchestrator and GitHub state.
- `FR-006`: Manual card moves must be recorded as operator overrides and pause autopilot until resumed.
- `FR-007`: The Quick Track must run a compact Codex prompt without PRD/TDD/tasks-plan artifacts.
- `FR-008`: The Planned Track must run Codex in the card worktree with prompt text beginning `$plan-and-execute --refine-plan`.
- `FR-009`: The board must support five active cards globally by default.
- `FR-010`: The board must support five active cards per repo by default.
- `FR-011`: Each card run must use a deterministic isolated git worktree.
- `FR-011A`: Branch and worktree names must be deterministic, card-id-based, uniqueness-constrained in SQLite, and collision-safe: same-card reuse is allowed only when ownership and cleanliness match, different-card collisions block, dirty/stale paths block, existing remote branch ambiguity blocks, and the board must never overwrite or force-delete a colliding branch/worktree.
- `FR-012`: The UI must expose live logs, run history, current/next prompt, PR links, worktree path, artifacts when present, and resume actions.
- `FR-013`: Blocked cards must show a one-line blocker summary and a detail view with failing step, command, exit code, relevant log excerpt, and recommended next action when available.
- `FR-014`: The operator must be able to resume a blocked card with a note appended to the next Codex prompt.
- `FR-015`: The backend must create PRs using the local `gh` CLI.
- `FR-015A`: For Quick Track, the backend must own post-run diff detection, protected-risk classification, commit, push, and non-interactive PR creation; Codex is not required to commit or open the PR.
- `FR-015A1`: If a successful Quick Track run produces zero changed files, the backend must not commit, push, or create a PR; it must persist evidence, move the card to `Blocked`, use blocker reason `no_changes_detected`, and allow resume or abandon.
- `FR-015B`: For Planned Track, the Prime Directive skill owns local planning, execution, review/finalization, and local commits inside the board-created branch; the backend must verify final branch state, persist artifacts/PR metadata, push when needed, detect and associate an existing PR for the board branch when present, and create or update the PR without duplicating skill-owned commits.
- `FR-015C`: If Planned Track PR detection finds multiple matching PRs or ambiguous PR metadata, the backend must block with reason `existing_pr_ambiguous` and show actionable context instead of creating a duplicate PR.
- `FR-016`: Auto-merge must be controlled by a per-card `Auto-merge PR` toggle and must remain off by default.
- `FR-017`: Auto-merge must require mergeability, passing checks, no protected-risk guardrail failure, and no unresolved runner/review blocker.
- `FR-017A`: Auto-merge must pin the expected PR head SHA and must not use admin bypass behavior.
- `FR-018`: Quick Track may create a PR without a detected verification command, but auto-merge must not proceed without a passing check unless a repo workflow override explicitly permits it.
- `FR-019`: The app must clean up a card worktree only after GitHub reports the PR is merged and final logs/history are preserved.
- `FR-020`: The app must support an optional repo-owned `AGENT_BOARD.md` workflow override, while providing useful defaults when the file is missing.
- `FR-020A`: `AGENT_BOARD.md` overrides must be allowlisted and must not weaken immutable board safety invariants: cwd containment, expected-head-SHA auto-merge pinning, no admin merge bypass, no-force cleanup, unresolved-blocker stops, protected-risk handling, and per-repo Git critical sections.
- `FR-020B`: The only allowed no-check auto-merge override is repo-scoped, off by default, explicit for Quick Track no-check PRs, and still requires protected-risk pass, expected-head-SHA pinning, mergeability, non-draft open PR state, and no unresolved blockers.
- `FR-021`: The app must reconcile card state after backend restart from the database, worktree state, and GitHub PR state.
- `FR-022`: The API must bind to loopback by default, reject non-local or unexpected browser origins for state-changing routes, avoid permissive CORS, and include tests proving unsafe remote/origin requests cannot launch Codex, push, merge, or clean worktrees.
- `FR-023`: The implementation must include a gated live smoke/probe for the real `codex exec --json` runner adapter against a disposable fixture, with explicit evidence when live GitHub PR creation is skipped for safety or environment reasons.
- `FR-024`: Planned Track must preflight that spawned Codex sessions can resolve the required Prime Directive skill/plugin path before queuing work; if unavailable, the card must block with actionable setup text.

## Acceptance Criteria

- `AC-001` (`FR-001`, `FR-002`): A user can open the local board, create a Quick or Planned card, and see it appear in the correct board column with Voidgrid-inspired styling.
- `AC-002` (`FR-003`, `FR-004`): Restarting the API preserves repos, cards, runs, logs, PR metadata, and status history.
- `AC-003` (`FR-005`, `FR-006`): Runner/GitHub events move cards automatically; manual drag creates an override record and pauses autopilot.
- `AC-004` (`FR-007`, `FR-008`): Quick and Planned cards generate different Codex prompts and do not incorrectly require the same artifact gates.
- `AC-005` (`FR-009`, `FR-010`): The scheduler can run five cards concurrently, including five cards for the same repo, while preserving per-card worktree isolation.
- `AC-006` (`FR-011`, `FR-011A`): The backend refuses to launch Codex unless the process cwd is the card worktree path inside the configured workspace root, and branch/worktree collision cases block safely without overwrite.
- `AC-007` (`FR-012`, `FR-013`, `FR-014`): A failed run moves to Blocked, shows actionable failure context, and can be resumed with an operator note.
- `AC-008` (`FR-015`, `FR-015A`, `FR-015A1`, `FR-015B`, `FR-015C`, `FR-016`, `FR-017`, `FR-017A`, `FR-018`, `FR-020B`): PR creation and auto-merge behavior can be verified with `gh` command wrappers or tests that exercise success and failure paths, including zero-diff Quick Track, existing Planned PR association, ambiguous PR blocking, expected-head-SHA protection, no-check override shape, and track-specific Git ownership.
- `AC-009` (`FR-019`): A merged PR triggers archival and safe worktree cleanup; an unmerged or dirty worktree is not removed.
- `AC-010` (`FR-020`, `FR-020A`): Missing `AGENT_BOARD.md` uses defaults; present workflow file overrides supported settings and rejects unsafe or non-allowlisted values.
- `AC-011` (`FR-021`): Restart reconciliation produces a consistent card state without assuming prior in-memory runner sessions survived.
- `AC-012` (`FR-022`): API safety tests prove loopback binding and origin restrictions protect state-changing runner/GitHub/cleanup routes.
- `AC-013` (`FR-023`): The final validation record includes a gated real-runner smoke result for `codex exec --json` or a clear environment/safety skip reason.
- `AC-014` (`FR-024`): Planned Track preflight blocks with actionable text when the Prime Directive skill/plugin is unavailable to spawned Codex sessions.

## Product Rules / UX Rules / Content Rules

- The board is an operator cockpit, not a marketing page.
- The first screen must be the usable board.
- Card fronts should prioritize agent state over generic task metadata.
- Card detail should make logs and next actions easy to find.
- Quick/Planned should be a visible two-choice control.
- Auto-merge should be a single toggle, off by default.
- The UI should use Voidgrid's dark gridded canvas, Space Grotesk typography, compact cards, lime/cyan accents, and dense board layout as inspiration.
- The UI must not bury blocker information behind decorative status text.

## Constraints and Defaults

- App path: `apps/board`.
- API host default: loopback only, not `0.0.0.0`.
- Frontend/backend split: `apps/board/web` and `apps/board/api`.
- Frontend: Vite, React, Tailwind, Atlaskit drag/drop unless research or implementation proves a better local fit.
- Backend: Node/Express-style local API unless research or implementation proves a better local fit.
- Persistence: local SQLite with ignored runtime data files.
- Codex runner: `codex exec --json` in v1, with the backend owning process supervision and event parsing.
- Codex default runner command: non-shell argv form equivalent to `codex exec --json --full-auto --sandbox workspace-write <prompt>`.
- Live updates: SSE or WebSocket; choose during implementation based on simplest reliable fit.
- GitHub: `gh` CLI in v1.
- Tracker integration: GitHub only in v1; Linear deferred.
- Default `max_active_runs`: `5`.
- Default `max_active_cards_per_repo`: `5`.
- Integration and auto-merge operations are serialized per repo.
- Shared same-repo Git metadata operations are protected by per-repo critical sections, including fetch, branch creation, worktree add/remove/prune, and shared-ref updates. Codex subprocesses may run in parallel after their isolated worktrees are safely created.
- Agent run slots and integration jobs are counted separately; PR creation, rebase/repair, auto-merge, and cleanup use per-repo integration locks but should not consume Codex run slots.
- Quick Track protected-risk classification includes path, diff/content, and task-intent heuristics for auth, billing, migrations/schema, public API contracts, destructive operations, secrets/config/deployment, broad refactors, unclear multi-file behavior changes, and unclear acceptance criteria.
- Stable blocker reason codes must include at least `no_changes_detected`, `collision_detected`, `existing_pr_ambiguous`, `checks_absent`, `protected_risk`, `runner_failed`, `approval_required`, `cleanup_blocked`, and `restart_quarantined`.
- Planned Track preflight must verify Prime Directive skill availability for spawned Codex sessions, not merely that the host repo contains the skills.

## Success Metrics / Guardrails

- A realistic Quick card can reach PR Ready without manual terminal supervision.
- A realistic Planned card can invoke the Prime Directive planned path from the board.
- Five queued cards can run concurrently without sharing worktrees or corrupting state.
- A blocked card provides enough context to resume from the board.
- Auto-merge never runs when checks are absent, failing, or guardrails trip unless a repo workflow explicitly allows the specific no-check case.
- Worktree cleanup never removes unmerged or dirty work.
