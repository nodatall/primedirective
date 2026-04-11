# Alfred Skill Launcher

Use Alfred to open a searchable picker of Prime Directive Codex skills and presets, then paste the selected invocation into the frontmost app.

The launcher is backed by `scripts/alfred-skill-router.py`, which reads:

- `skills/*/SKILL.md` for skill discovery
- `skills/presets.json` for optional Alfred presets

If those files change, Alfred reflects the new list the next time the workflow runs.

## Alfred setup

1. Create a new blank workflow in Alfred.
2. Add a `Hotkey` input and bind it to the shortcut you want. The installer script in this repo uses `command + option + v`.
3. Add a `Script Filter` and configure it with:

```text
Language: /usr/bin/python3
Script: /absolute/path/to/primedirective/scripts/alfred-skill-router.py
with input as argv
Argument: Optional
Alfred Filters Results: enabled
Placeholder Title: Prime Directive skills
Placeholder Subtext: Filter and paste a skill command
```

4. Connect the `Hotkey` to the `Script Filter`.
5. Add a `Copy to Clipboard` output and set the copied text to:

```text
{query}
```

6. Enable `Automatically paste to frontmost app`.
7. Connect the `Script Filter` to the `Copy to Clipboard` output.

That gives you:

- hotkey opens the skill picker
- typing filters skills and presets
- `Return` pastes the selected `$skill-name` or `$skill-name <modifier>` text
- `cmd + 1` through `cmd + 9` picks and pastes the visible result in that slot, just like Alfred's other result lists

## Terminal check

You can inspect the generated list without Alfred:

```bash
python3 scripts/alfred-skill-router.py --format list
```

To install the workflow into Alfred and export a backup `.alfredworkflow` bundle:

```bash
python3 scripts/install-alfred-skill-workflow.py
```
