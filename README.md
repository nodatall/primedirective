# Prime Directive

Prime Directive is a Codex plugin source repo that ships reusable workflow skills from a single canonical `skills/` tree.

The repo is Codex-first:

- install it globally as a local Codex plugin
- use Alfred as an optional launcher for skills and presets
- treat this checkout as the only source of truth for skill authoring

## Layout

- `.codex-plugin/plugin.json` Codex plugin metadata
- `skills/` canonical skills and shared references
- `scripts/install-codex-plugin.sh` idempotent Codex marketplace installer
- `scripts/install-alfred-skill-workflow.py` Alfred workflow installer/exporter
- `scripts/alfred-skill-router.py` Alfred data source for skills and presets
- `docs/alfred-skill-launcher.md` Alfred setup and behavior details

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

## Install For Alfred

Install or refresh the workflow:

```bash
python3 scripts/install-alfred-skill-workflow.py
```

The Alfred picker reads `skills/*/SKILL.md` plus `skills/presets.json` and pastes Codex-native invocation text such as:

- `$plan-work`
- `$plan-work --grill`
- `$plan-work --deep-research`
- `$execute-task --preserve-review-artifacts`

Modifiers are plain text owned by the skill conventions. Alfred does not parse them as platform flags.

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

Codex invocation is explicit:

```text
$plan-work
$review-chain
$execute-task
```

## Presets And Modifiers

Alfred presets are defined in `skills/presets.json`.

Each preset should provide:

- `skill` stable skill identifier
- `title` Alfred-visible label
- `subtitle` short explanation
- `paste` exact text Alfred should paste

Preset text should stay Codex-native and explicit. Use modifier conventions like `--deep-research` or `--preserve-review-artifacts` as skill-level textual contracts, not platform-level flags.

## Verification

Useful local checks:

```bash
python3 scripts/alfred-skill-router.py --format list
./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh
HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh
```

The installer is expected to be idempotent, and the Alfred router should list both base skills and configured presets.
