#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE_DIR="${HOME}/.agents/plugins"
MARKETPLACE_PATH="${MARKETPLACE_DIR}/marketplace.json"

mkdir -p "$MARKETPLACE_DIR"

python3 - "$MARKETPLACE_PATH" "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

marketplace_path = Path(sys.argv[1]).expanduser()
repo_root = Path(sys.argv[2]).resolve()
plugin_name = "prime-directive"

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

data["name"] = data.get("name") or "local-marketplace"
interface = data.get("interface")
if not isinstance(interface, dict):
    interface = {}
interface["displayName"] = interface.get("displayName") or "Local plugins"
data["interface"] = interface
data["plugins"] = new_plugins

marketplace_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Registered {plugin_name} in {marketplace_path}")
PY
