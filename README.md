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
| `first-principles-mode` | `$first-principles-mode` | `--pro` |
| `frontend-design-improve` | `$frontend-design-improve` | None |
| `plan-and-execute` | `$plan-and-execute` | `--deep-research`, `--pro-analysis`, `--refine-plan`, `--check-harness-drift`, `--preserve-artifacts` |
| `plan-refine` | `$plan-refine [plan-key=<plan-key>]` | `plan-key=<plan-key>`, `--max-rounds=<n>`, `--preserve-refine-artifacts`; max rounds default to 8 and are capped at 8 |
| `plan-work` | `$plan-work` | `--from-thread`, `--direct`, `--grill`, `--deep-research`, `--preserve-planning-artifacts` |
| `repo-sweep` | `$repo-sweep` | `--pro-analysis`, `--loop`, `--preserve-review-artifacts` |
| `review-chain` | `$review-chain` | `--preserve-review-artifacts`; optional task ID in the request for task-scoped review |

## Layout

- `.codex-plugin/plugin.json` Codex plugin metadata
- `skills/` canonical skills and shared references
- `scripts/install-codex-plugin.sh` idempotent Codex marketplace installer
- `scripts/install-claude-skills.sh` idempotent Claude skills installer
- `scripts/oracle-pro.sh` ChatGPT Pro browser escalation wrapper for Prime Directive analysis flows

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

## Optional ChatGPT Pro Escalation

Prime Directive can use ChatGPT Pro browser mode as an internal escalation path for:

- `$first-principles-mode --pro`
- `$plan-and-execute --pro-analysis`
- `$repo-sweep --pro-analysis`

The public workflow stays on those skill modifiers. The implementation detail is the repo wrapper:

```bash
./scripts/oracle-pro.sh setup
./scripts/oracle-pro.sh session
./scripts/oracle-pro.sh dry-run -p "Analyze this repo" --file .
./scripts/oracle-pro.sh run -p "Analyze this repo" --file .
```

Run setup once when the browser profile needs ChatGPT login. If setup reports a duplicate running session, use `./scripts/oracle-pro.sh session` to reattach or `./scripts/oracle-pro.sh setup --force` to start a fresh setup check. The setup action skips thinking-time UI selection because it is only a login/profile check. Normal dry-run/run/render actions use extended thinking by default because the ChatGPT Pro picker may expose only Standard and Extended; set `ORACLE_PRO_THINKING=heavy` only when that option exists, or `ORACLE_PRO_THINKING=off` if the thinking-time control is unavailable. The wrapper owns Oracle defaults for browser mode, Pro model, manual-login profile reuse, file bundling, timeouts, dry-run previews, and local temp cleanup. Set `ORACLE_PRO_KEEP_TMP=1` to keep the wrapper temp directory for debugging.
