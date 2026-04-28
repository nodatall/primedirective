# Prime Directive Agent Board

Local single-user Kanban cockpit for supervising Codex work across isolated git worktrees.

## Run

```bash
npm install --prefix apps/board
npm run build --prefix apps/board
npm run test --prefix apps/board
npm run dev --workspace @prime-board/web --prefix apps/board
npm run start --workspace @prime-board/api --prefix apps/board
```

The API binds to `127.0.0.1` by default and rejects unexpected origins on state-changing routes.

## Tracks

Quick Track uses compact Codex prompts and backend-owned finalization: changed-file detection, protected-risk classification, commit, push, and PR creation. Zero-diff runs block as `no_changes_detected`.

Planned Track sends prompt text beginning `$plan-and-execute --refine-plan`. The Prime Directive skill owns local commits and finalization; the board verifies branch/PR state and avoids duplicate PRs.

## Guardrails

- Five active runs globally and five active cards per repo by default.
- Per-card deterministic worktrees and branches.
- Per-repo critical sections for shared Git metadata operations.
- Auto-merge is off by default, SHA-pinned, non-admin, and blocked by protected risk or unresolved blockers.
- Cleanup uses non-force worktree removal only after GitHub reports the PR merged and local state is clean.

## Live runner evidence

Run the gated smoke with:

```bash
npm run live:smoke --prefix apps/board
```

It exercises the real `codex exec --json --full-auto --sandbox workspace-write` adapter against a disposable local fixture. PR creation is intentionally skipped in that probe unless a safe remote fixture is configured later.
