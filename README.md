# Prime Directive

Shared source-of-truth for agent instruction files across repos.

## What this manages

- `AGENTS.md`
- `CLAUDE.md`
- `rules/*.md`

for each consumer repo listed in `repos/<name>/repo.path`.

## Layout

- `core/` shared canonical content
- `repos/<name>/overlay/` local-only repo-specific overrides (gitignored)
- `templates/` optional starter template(s)
- `scripts/sync-repo.sh` render one consumer
- `scripts/sync-all.sh` render all consumers
- `scripts/validate.sh` CI-style sync check
- `scripts/sync-open-prs.sh` sync, commit, and open PRs in consumer repos
- `scripts/sync-all-automerge.sh` one-command sync + PR + auto-merge for all repos

## Local-only config

- `repos/` is intentionally ignored by git and should not be pushed.
- Each machine should create its own `repos/<name>/repo.path` and optional overlays.

## Overlay behavior

For root files:

1. `AGENTS.md` supports overlays:
   - `overlay/AGENTS.full.md` fully replaces core.
   - `overlay/AGENTS.append.md` appends to core.
2. `CLAUDE.md` is always generated as an exact copy of `AGENTS.md` across all repos.

For rule files:

- `core/rules/<name>.md` is used by default.
- If `overlay/rules/<name>.md` exists, it fully overrides core for that repo.

## Commands

Run commands from the repository root.

Sync one repo:

```bash
./scripts/sync-repo.sh --repo-name <repo-name>
```

Sync all repos:

```bash
./scripts/sync-all.sh
```

Validate all repos are current:

```bash
./scripts/validate.sh
```

Sync and open PRs for all configured repos:

```bash
./scripts/sync-open-prs.sh
```

Sync and open PRs for one repo:

```bash
./scripts/sync-open-prs.sh --repo-name <repo-name>
```

One-command sync + PR + auto-merge for all configured repos:

```bash
./scripts/sync-all-automerge.sh
```

## Recommended workflow

1. Edit files under `core/`.
2. Add repo-specific deltas only in `repos/<name>/overlay/`.
3. Run `scripts/sync-all.sh`.
4. Commit changes in consumer repos.
5. Run `scripts/validate.sh` in CI to prevent drift.
