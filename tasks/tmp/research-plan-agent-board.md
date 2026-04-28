# Deep Research Memo: Prime Directive Agent Board

accessed_date: 2026-04-28
timezone: America/Los_Angeles
plan_key: agent-board

## Research Framing

This pass evaluated a local Prime Directive Board under `/Volumes/Code/primedirective/apps/board`: Vite/React/Tailwind frontend, Node backend, SQLite persistence, per-card git worktrees, Codex subprocess execution, GitHub PR/merge lifecycle through `gh`, and Voidgrid-inspired Kanban UI.

Highest-priority quality attributes: operability, process safety, restart recovery, concurrency correctness, GitHub/merge safety, frontend usability, and agent-legible workflow contracts.

Constraints: v1 is local-only and single-user; no Linear; GitHub through `gh`; cards are local-first; Quick/Planned tracks are visible; default concurrency is 5 global and 5 per repo; worktrees must be cleaned after PR merge; Quick Track must avoid PRD/TDD/tasks-plan overhead.

## Draft-Linked Research Agenda

| question_id | draft anchor | bucket | research question | possible impact |
| --- | --- | --- | --- | --- |
| RQ-001 | TDD `Agent runner`, `TDR-008`, `TDR-009` | core technical approach | Should v1 drive Codex through `codex exec --json`, App Server, or another interface? | runner architecture, event model, implementation sequence |
| RQ-002 | TDD `TDR-006`, cleanup requirements | recovery / operational safety | What git worktree rules matter for creating, preserving, and cleaning isolated card workspaces? | worktree manager invariants and cleanup tasks |
| RQ-003 | PRD auto-merge requirements, TDD `TDR-011`, `TDR-012` | APIs / integration | What GitHub/`gh` fields and merge semantics should drive PR status, checks, auto-merge, and merge queues? | GitHub wrapper contract and auto-merge guardrails |
| RQ-004 | TDD persistence layer | storage / concurrency | What SQLite mode and persistence cautions matter for a local runner database? | SQLite setup, backup/export, runtime file handling |
| RQ-005 | PRD UI rules, Voidgrid template | frontend / verification | Is Atlaskit pragmatic drag/drop and Tailwind v4 still a reasonable board UI baseline? | frontend dependency and visual implementation strategy |
| RQ-006 | PRD/TDD orchestration model | testing / operational readiness | What operator lessons apply to parallel agent runs and auto-merge safety? | validation gates, logs, review/merge constraints |

## Evidence Ledger

| source_id | source_type | source_family | url | publication_date | last_updated_date | version_or_scope | supported_claims | counts_toward_external_primary_minimum | current_enough_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S-001 | official spec | OpenAI Symphony | https://github.com/openai/symphony/blob/main/SPEC.md | 2026-04 | unknown | Draft v1 | scheduler/runner separation, bounded concurrency, deterministic per-issue workspaces, repo-owned workflow file, restart reconciliation, safety invariants | yes | Spec is the direct source requested by the user and current as of the article release. |
| S-002 | official docs | OpenAI Codex | https://developers.openai.com/codex/noninteractive | unknown | unknown | Codex CLI non-interactive mode | `codex exec` is intended for scripts/CI, supports JSONL streaming events, sandbox flags, and resume | yes | Official OpenAI Codex docs, current enough for CLI runner selection. |
| S-003 | official docs | OpenAI Codex | https://developers.openai.com/codex/app-server | unknown | unknown | Codex App Server | App Server gives deep product integration and JSON-RPC streamed events but is experimental; local WebSocket requires careful auth | yes | Official docs clarify app-server fit and maturity tradeoff. |
| S-004 | official docs | Node.js | https://nodejs.org/api/child_process.html | unknown | 2026 | Node v25.9 docs | `spawn`/`execFile` are async; `cwd` should be explicit; avoid shell with unsanitized input; AbortController can stop processes | yes | Current Node API docs for subprocess supervision. |
| S-005 | official docs | Git | https://git-scm.com/docs/git-worktree.html | unknown | 2026-02 | Git worktree | linked worktrees have shared refs/private git dirs; use `git worktree remove` and prune stale entries; do not assume raw `.git` layout | yes | Official Git docs for worktree lifecycle. |
| S-006 | official docs | GitHub CLI | https://cli.github.com/manual/gh_pr_view | unknown | current | `gh pr view` | JSON fields include state, mergeStateStatus, mergeable, statusCheckRollup, url, number, head/base refs | yes | Official CLI docs for PR polling contract. |
| S-007 | official docs | GitHub CLI | https://cli.github.com/manual/gh_pr_merge | unknown | current | `gh pr merge` | `--auto`, `--squash`, `--delete-branch`, merge queue behavior through CLI | yes | Official CLI docs for merge/auto-merge behavior. |
| S-008 | official docs | GitHub Docs | https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/merging-a-pull-request-with-a-merge-queue | unknown | current | GitHub merge queue | merge queues wait for required checks and validate changes against latest target branch; failed checks/conflicts remove PRs | yes | Official GitHub docs for auto-merge/merge queue guardrails. |
| S-009 | official docs | SQLite | https://www.sqlite.org/wal.html | unknown | current | SQLite WAL | WAL mode improves local concurrency but WAL files/checkpointing matter for backups and disk growth | yes | Official SQLite docs for local DB runtime behavior. |
| S-010 | official docs | Atlassian | https://atlassian.design/components/pragmatic-drag-and-drop/core-package/ | unknown | current | Pragmatic drag/drop | adapters, monitors, optional packages, framework-agnostic core | yes | Official docs match Voidgrid dependency choice. |
| S-011 | official docs/blog | Tailwind CSS | https://tailwindcss.com/blog/tailwindcss-v4 | 2025-01 | current | Tailwind v4 | first-party Vite plugin, automatic content detection, performance improvements | yes | Official Tailwind source for v4/Vite integration. |
| S-012 | official docs | Express | https://expressjs.com/en/guide/error-handling | unknown | current | Express error handling | route/middleware errors require explicit async handling patterns | yes | Official Express guidance for backend error surface. |
| O-001 | operator practice | OpenAI | https://openai.com/index/harness-engineering/ | 2026-02-11 | 2026 | Harness engineering | repo-local artifacts, agent-legible architecture, mechanical guardrails/lints increase agent reliability | no | Operator lesson directly applicable to Prime Directive Board. |
| O-002 | operator practice | OpenAI | https://openai.com/index/open-source-codex-orchestration-symphony/ | 2026-04-27 | 2026 | Symphony article | context switching bottleneck, dedicated workspaces, tracker-as-state-machine, App Server scalability, managing work not sessions | no | User-requested source and current release article. |
| O-003 | operator practice | GitHub Engineering | https://github.blog/engineering/engineering-principles/how-github-uses-merge-queue-to-ship-hundreds-of-changes-every-day/ | 2024 | current | GitHub merge queue operation | merge queue as single shipping entrypoint, required checks, conflict detection, developer UX | no | Real production-scale merge/CI practice. |
| O-004 | research paper | arXiv | https://arxiv.org/abs/2601.20109 | 2026-01-27 | 2026 | agent-generated PR quality | merge success alone does not prove post-merge code quality; systematic quality checks are needed | no | Current empirical paper relevant to auto-merge caution. |
| O-005 | research paper | arXiv | https://arxiv.org/abs/2603.25723 | 2026-03-26 | 2026 | natural-language agent harnesses | harness behavior benefits from explicit contracts, durable artifacts, lightweight adapters | no | Current research supports repo-owned natural-language workflow contracts. |

## Finding-to-Artifact Delta

| finding_id | research_question_id | bucket | disposition | recommendation | recommendation_level | support_type | source_ids | prd_tdd_sections_changed | task_plan_inputs_created | disposition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-001 | RQ-001 | core technical approach | adopted | Use `codex exec --json` for v1 runner, with a runner interface that can later support App Server. | adopt-now | directly supported | S-002, S-003, S-004, O-002 | TDD runner/requirements updated | Add runner adapter tasks and fake-runner tests. | `codex exec` is stable and script-oriented with JSONL events; App Server is better for deep product integration but experimental. |
| F-002 | RQ-002 | workspace safety | adopted | Treat per-card worktrees as durable workspaces; remove only through `git worktree remove` after merged/clean guardrails. | adopt-now | directly supported | S-001, S-005 | TDD worktree/failure sections updated | Add worktree manager and cleanup tests. | Matches Symphony invariant and official Git lifecycle. |
| F-003 | RQ-003 | GitHub integration | adopted | Poll `gh pr view --json` fields and gate auto-merge on checks/mergeability; use `gh pr merge --auto --squash` only after board guardrails pass. | adopt-now | directly supported | S-006, S-007, S-008, O-003 | PRD/TDD auto-merge requirements reinforced | Add GitHub wrapper tests with fake `gh`. | Official GitHub/CLI docs expose needed fields and merge queue semantics. |
| F-004 | RQ-004 | storage/concurrency | adopted | Use SQLite WAL mode for local app concurrency, but treat DB/WAL files as runtime data and avoid naive file-copy backups. | adopt-now | directly supported | S-009 | TDD persistence/operational sections updated | Add DB setup task and data ignore rules. | WAL is appropriate for local read/write concurrency but has checkpoint/backup caveats. |
| F-005 | RQ-005 | frontend | adopted | Keep Voidgrid's Atlaskit/Tailwind direction; adapt the card model to agent state and verify board UX in browser. | adopt-now | directly supported | S-010, S-011, repo-local Voidgrid files | PRD/TDD frontend sections retained | Add frontend board/detail tasks and browser smoke. | Dependencies are current and already proven in Voidgrid. |
| F-006 | RQ-006 | operational readiness | adopted | Add mechanical guardrails: structured events, explicit state transitions, protected-path checks, final checks, and blocked-card evidence. | adopt-now | synthesis | S-001, O-001, O-002, O-004, O-005 | PRD/TDD guardrails preserved and tightened | Add scheduler/guardrail/reconciliation tests. | Parallel agents need visible, durable state and quality gates; merge alone is insufficient proof. |
| F-007 | RQ-001 | emerging | deferred | Consider Codex App Server as a later adapter for richer thread/session control. | watchlist | directly supported | S-003, O-002 | TDD records future adapter, not v1 dependency | No v1 task except interface boundary. | App Server is powerful but experimental; v1 should ship with stable `codex exec --json`. |

## Adopt-Now Guidance

- Build the runner around stable `codex exec --json` in v1, not raw TUI automation.
- Use `node:child_process.spawn` or `execFile` with explicit cwd/env/argv; avoid shell interpolation for user-controlled values.
- Preserve worktrees across retries and remove through Git's worktree commands only after PR merge and clean-state checks.
- Use `gh pr view --json` as the PR state surface and `gh pr merge --auto --squash` only behind board guardrails.
- Enable SQLite WAL mode and keep all DB/WAL/runtime files under ignored `apps/board/data`.
- Keep `AGENT_BOARD.md` optional but repo-owned; default policy should make repos easy to add while allowing local contract overrides.

## Watchlist / Deferred

- Codex App Server should remain a later adapter after the v1 runner interface is proven.
- GitHub merge queue visualization is deferred; v1 only needs enough state to avoid unsafe merges and report queue/check status.
- Direct GitHub API/Octokit is deferred until the app needs hosted auth or richer PR views.

## Avoid Guidance

- Do not drive Codex by scraping terminal UI output.
- Do not use manual `rm -rf` for worktree cleanup.
- Do not treat merged or mergeable PR state as proof of code quality.
- Do not let Quick Track auto-merge without a recorded passing check unless a repo workflow explicitly allows that narrow case.
- Do not bake workflow policy solely into UI/database state when repo-owned contracts can make agent behavior legible.

## Plan-Specific Implementation Checklist

- Runner adapter: `codex exec --json` first, typed event parsing, process cancellation, fake runner for tests.
- Worktree manager: sanitized card/workspace keys, cwd invariant, `git worktree add/remove`, cleanup blockers.
- GitHub wrapper: `gh pr create`, `gh pr view --json`, `gh pr checks`, `gh pr merge --auto --squash`, fake `gh` tests.
- Scheduler: global and per-repo concurrency default 5, integration locks, retry/backoff, stall detection, restart reconciliation.
- Persistence: SQLite schema, WAL mode, ignored runtime data, durable event log.
- UI: Voidgrid-inspired board, agent-state card front, drawer with logs/prompts/actions, blocked resume.

## Deep Research Completion Stamp

- external_primary_sources_count: 12
- operator_practice_sources_count: 5
- source_family_count: 10
- research_questions_answered: 6
- buckets_reviewed: 6
- follow_up_passes_completed: 3
- adopted_findings_count: 6
- rejected_or_deferred_findings_count: 1
- prd_tdd_sections_changed: PRD Constraints, PRD Success Guardrails, TDD Architecture, TDD Dependencies, TDD Requirements, TDD Failure Modes, TDD Operational Readiness, TDD Verification
- task_plan_inputs_created: runner adapter, worktree manager, GitHub wrapper, scheduler, persistence, workflow loader, frontend board, verification
- evidence_bar_met: yes
