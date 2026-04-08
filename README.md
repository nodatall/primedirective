# Prime Directive

Shared source-of-truth for agent instruction files across repos.

## What this manages

- `AGENTS.md`
- `CLAUDE.md`
- `skills/**`

for each consumer repo listed in `repos/<name>/repo.path`.

## Layout

- `core/` shared canonical content
- `core/skills/` shared workflow skills and references
- `repos/<name>/overlay/` local-only repo-specific overrides (gitignored)
- `templates/` optional starter template(s)
- `scripts/add-repo.sh` register a consumer repo in `repos/`
- `scripts/sync-repo.sh` render one consumer
- `scripts/sync-all.sh` render all consumers
- `scripts/validate.sh` CI-style sync check
- `scripts/sync-open-prs.sh` sync, commit, and open PRs in consumer repos
- `scripts/sync-all-automerge.sh` one-command sync + PR + auto-merge for all repos

## Local-only config

- `repos/` is intentionally ignored by git and should not be pushed.
- Each machine should create its own `repos/<name>/repo.path` and optional overlays.

## Setup

Recommended workspace layout (siblings under one parent folder):

```text
<workspace-root>/
  primedirective/
  repo-a/
  repo-b/
```

Run setup from `primedirective/`:

1. Register each consumer repo:

```bash
./scripts/add-repo.sh --repo-path ../repo-a
./scripts/add-repo.sh --repo-path ../repo-b
```

2. Sync generated files into all configured repos:

```bash
./scripts/sync-all.sh
```

3. Optional one-command PR flow (sync + PR + auto-merge):

```bash
./scripts/sync-all-automerge.sh
```

## Overlay behavior

For root files:

1. `AGENTS.md` supports overlays:
   - `overlay/AGENTS.full.md` fully replaces core.
   - `overlay/AGENTS.append.md` appends to core.
2. `CLAUDE.md` is always generated as an exact copy of `AGENTS.md` across all repos.

For skills:

- `core/skills/**` is used by default.
- If `overlay/skills/**` contains the same relative file, overlay fully overrides that file.
- Additional files under `overlay/skills/**` are copied as additive files.

## Commands

Run commands from the repository root.

Sync one repo:

```bash
./scripts/sync-repo.sh --repo-name <repo-name>
```

Add/register one repo:

```bash
./scripts/add-repo.sh --repo-path <path-to-repo> [--repo-name <name>]
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

## Alfred

If you want an Alfred hotkey that shows the current `AGENTS` skill commands and pastes the selected trigger, use `scripts/install-alfred-skill-workflow.py` to install the workflow and `docs/alfred-skill-launcher.md` for the setup details.

## Recommended workflow

1. Edit files under `core/`.
2. Add repo-specific deltas only in `repos/<name>/overlay/`.
3. Run `scripts/sync-all.sh`.
4. Commit changes in consumer repos.
5. Run `scripts/validate.sh` in CI to prevent drift.

## Migration note

This repo now hard-cuts to `skills/**` publishing. During sync, previously generated legacy `rules/*.md` files are removed from consumer repos.
