#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE_DIR="${HOME}/.agents/plugins"
MARKETPLACE_PATH="${MARKETPLACE_DIR}/marketplace.json"
CODEX_CONFIG_DIR="${HOME}/.codex"
CODEX_CONFIG_PATH="${CODEX_CONFIG_DIR}/config.toml"
CODEX_SKILLS_DIR="${CODEX_CONFIG_DIR}/skills"

mkdir -p "$MARKETPLACE_DIR"
mkdir -p "$CODEX_CONFIG_DIR"
mkdir -p "$CODEX_SKILLS_DIR"

python3 - "$MARKETPLACE_PATH" "$CODEX_CONFIG_PATH" "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

marketplace_path = Path(sys.argv[1]).expanduser()
config_path = Path(sys.argv[2]).expanduser()
repo_root = Path(sys.argv[3]).resolve()
plugin_name = "prime-directive"
marketplace_name = "local-marketplace"
plugin_config_key = f'{plugin_name}@{marketplace_name}'

plugin_entry = {
    "name": plugin_name,
    "source": {
        "source": "local",
        "path": str(repo_root),
    },
    "policy": {
        "installation": "AVAILABLE",
        "authentication": "NEVER",
    },
    "category": "Coding",
}

if marketplace_path.exists():
    try:
        data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
else:
    data = {}

if not isinstance(data, dict):
    data = {}

plugins = data.get("plugins")
if not isinstance(plugins, list):
    plugins = []

updated = False
new_plugins = []
for plugin in plugins:
    if not isinstance(plugin, dict):
        continue
    if plugin.get("name") == plugin_name:
        new_plugins.append(plugin_entry)
        updated = True
    else:
        new_plugins.append(plugin)

if not updated:
    new_plugins.append(plugin_entry)

data["name"] = data.get("name") or marketplace_name
interface = data.get("interface")
if not isinstance(interface, dict):
    interface = {}
interface["displayName"] = interface.get("displayName") or "Local plugins"
data["interface"] = interface
data["plugins"] = new_plugins

marketplace_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

section_header = f'[plugins."{plugin_config_key}"]'
enabled_line = "enabled = true"

if config_path.exists():
    config_text = config_path.read_text(encoding="utf-8")
else:
    config_text = ""

if section_header not in config_text:
    suffix = "" if not config_text or config_text.endswith("\n") else "\n"
    config_text = f"{config_text}{suffix}\n{section_header}\n{enabled_line}\n"
else:
    lines = config_text.splitlines()
    output_lines = []
    in_target_section = False
    enabled_written = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_target_section and not enabled_written:
                output_lines.append(enabled_line)
                enabled_written = True
            in_target_section = stripped == section_header
        if in_target_section and stripped.startswith("enabled"):
            output_lines.append(enabled_line)
            enabled_written = True
        else:
            output_lines.append(line)
    if in_target_section and not enabled_written:
        output_lines.append(enabled_line)
    config_text = "\n".join(output_lines) + "\n"

config_path.write_text(config_text, encoding="utf-8")

print(f"Registered {plugin_name} in {marketplace_path}")
print(f"Enabled {plugin_config_key} in {config_path}")
PY

for skill_dir in "$ROOT_DIR"/skills/*; do
  if [[ ! -d "$skill_dir" ]]; then
    continue
  fi
  if [[ ! -f "$skill_dir/SKILL.md" ]]; then
    continue
  fi
  skill_name="$(basename "$skill_dir")"
  target_path="${CODEX_SKILLS_DIR}/${skill_name}"
  if [[ -e "$target_path" && ! -L "$target_path" ]]; then
    echo "Skipped skill ${skill_name}: ${target_path} already exists as a real directory"
    continue
  fi
  ln -sfn "$skill_dir" "$target_path"
  echo "Linked skill ${skill_name} -> ${target_path}"
done
