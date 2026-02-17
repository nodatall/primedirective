# Prime Directive

Shared source-of-truth for agent instruction files across repos.

## What this manages

- `AGENTS.md`
- `CLAUDE.md`
- `rules/*.md`

for each consumer repo listed in `repos/<name>/repo.path`.

## Layout

- `core/` shared canonical content
- `repos/<name>/overlay/` repo-specific overrides
- `scripts/sync-repo.sh` render one consumer
- `scripts/sync-all.sh` render all consumers
- `scripts/validate.sh` CI-style sync check

## Overlay behavior

For root files (`AGENTS.md`, `CLAUDE.md`):

1. If `overlay/<FILE>.full.md` exists, it fully replaces core.
2. Else if `overlay/<FILE>.append.md` exists, it is appended to core.
3. Else core is used as-is.

For rule files:

- `core/rules/<name>.md` is used by default.
- If `overlay/rules/<name>.md` exists, it fully overrides core for that repo.

## Commands

Sync one repo:

```bash
/Volumes/Code/primedirective/scripts/sync-repo.sh --repo-name autoprophet
```

Sync all repos:

```bash
/Volumes/Code/primedirective/scripts/sync-all.sh
```

Validate all repos are current:

```bash
/Volumes/Code/primedirective/scripts/validate.sh
```

## Recommended workflow

1. Edit files under `core/`.
2. Add repo-specific deltas only in `repos/<name>/overlay/`.
3. Run `scripts/sync-all.sh`.
4. Commit changes in consumer repos.
5. Run `scripts/validate.sh` in CI to prevent drift.
