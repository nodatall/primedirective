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
- `scripts/install-claude-skills.sh` idempotent Claude skills installer

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

Run from this repository root:

```bash
./scripts/install-claude-skills.sh
```

What it does:

- creates `~/.claude/skills` when missing
- symlinks each repo skill into `~/.claude/skills/<skill-name>`
- skips existing non-symlink skill directories instead of overwriting them
- preserves other Claude config and plugin state

Set `CLAUDE_SKILLS_DIR=/custom/path` if your Claude setup expects a different global skills location.

Update flow:

1. Pull the latest changes in this repo.
2. Re-run `./scripts/install-claude-skills.sh`.
3. Restart Claude or open a fresh Claude session if the updated skills do not appear immediately.

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
HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh
HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh
```

The installers are expected to be idempotent.
