# Prime Directive

Prime Directive is a Codex plugin source repo that ships reusable workflow skills from a single canonical `skills/` tree.

The repo is Codex-first:

- install it globally as a local Codex plugin
- treat this checkout as the only source of truth for skill authoring

## Skill Invocations

All skills use explicit Codex-native `$skill-name` invocation text.

| Skill | Invocation | Modifiers and request options |
| --- | --- | --- |
| `bootstrap-repo-rules` | `$bootstrap-repo-rules` | `--with-hooks` |
| `cleanup-merged-branches` | `$cleanup-merged-branches` | Optional branch name in the request |
| `execute-task` | `$execute-task task-id=<task-id> [plan-key=<plan-key>]` or `$execute-task --one-shot [plan-key=<plan-key>]` | `--one-shot`, `--stay-on-current-branch`, `--check-harness-drift`, `--preserve-review-artifacts`; `plan-key=<plan-key>` when it cannot be inferred |
| `first-principles-mode` | `$first-principles-mode` | None |
| `frontend-design-improve` | `$frontend-design-improve` | None |
| `plan-and-execute` | `$plan-and-execute` | `--deep-research`, `--plan-refine`, `--check-harness-drift`, `--preserve-artifacts` |
| `plan-refine` | `$plan-refine [plan-key=<plan-key>]` | `plan-key=<plan-key>`, `--max-rounds=<n>`, `--preserve-refine-artifacts`; max rounds default to 8 and are capped at 8 |
| `plan-work` | `$plan-work` | `--from-thread`, `--direct`, `--grill`, `--deep-research`, `--preserve-planning-artifacts` |
| `repo-sweep` | `$repo-sweep` | `--preserve-review-artifacts` |
| `review-chain` | `$review-chain` | `--preserve-review-artifacts`; optional task ID in the request for task-scoped review |

## Layout

- `.codex-plugin/plugin.json` Codex plugin metadata
- `skills/` canonical skills and shared references
- `scripts/install-codex-plugin.sh` idempotent Codex marketplace installer

## Install For Codex

Run from this repository root:

```bash
./scripts/install-codex-plugin.sh
```

What it does:

- creates `~/.agents/plugins/marketplace.json` when missing
- adds or updates one local `prime-directive` plugin entry that points at this checkout
- enables `prime-directive@local-marketplace` in `~/.codex/config.toml`
- symlinks each repo skill into `~/.codex/skills/` for Codex builds that read local skills directly
- preserves other marketplace entries

Update flow:

1. Pull the latest changes in this repo.
2. Re-run `./scripts/install-codex-plugin.sh` if you added, renamed, or removed skills.
3. Restart Codex if the updated skills do not appear immediately.

## Install For Claude

Claude is documented as a secondary manual install path only. This migration does not automate Claude setup.

To expose the same skills globally for Claude:

1. Create `~/.claude/skills` if it does not exist.
2. Copy or symlink this repo's `skills/` directory into `~/.claude/skills/prime-directive`.
3. Re-copy or refresh that link after pulling updates from this repo.

Example with a symlink:

```bash
mkdir -p ~/.claude/skills
ln -sfn /absolute/path/to/primedirective/skills ~/.claude/skills/prime-directive
```

If your Claude setup expects a different global skills location, adapt the destination path but keep this repo's `skills/` tree as the source of truth.

## Skill Authoring

Each skill lives in `skills/<skill-name>/SKILL.md`.

Conventions:

- keep the front matter `name` stable; that is the public identifier
- keep `description` concise and invocation-oriented
- use `skills/...` paths for internal references
- keep shared non-invokable references under `skills/shared/`

Codex invocation is explicit; keep the complete list in `Skill Invocations` current when adding, renaming, or removing skills.

## Verification

Useful local checks:

```bash
./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh
```

The installer is expected to be idempotent.
