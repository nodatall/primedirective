#!/usr/bin/env bash
# Add or remove the Prime Directive Claude SessionStart update hook.

set -euo pipefail

ACTION="${1:-}"
HOOK_CMD="${2:-}"
SETTINGS_FILE="${PRIME_DIRECTIVE_CLAUDE_SETTINGS_FILE:-$HOME/.claude/settings.json}"

if [[ -z "$ACTION" || -z "$HOOK_CMD" ]]; then
  echo "Usage: prime-directive-settings-hook.sh {add|remove} <hook-command>" >&2
  exit 1
fi

case "$ACTION" in
  add|remove) ;;
  *)
    echo "Unknown action: $ACTION (expected add or remove)" >&2
    exit 1
    ;;
esac

mkdir -p "$(dirname "$SETTINGS_FILE")"

python3 - "$ACTION" "$HOOK_CMD" "$SETTINGS_FILE" <<'PY'
import json
import sys
from pathlib import Path

action, hook_cmd, settings_arg = sys.argv[1:4]
settings_path = Path(settings_arg).expanduser()

try:
    data = json.loads(settings_path.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError):
    data = {}

if not isinstance(data, dict):
    data = {}

hooks = data.get("hooks")
if not isinstance(hooks, dict):
    hooks = {}

session_start = hooks.get("SessionStart")
if not isinstance(session_start, list):
    session_start = []

def has_prime_directive_hook(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    hook_items = entry.get("hooks")
    if not isinstance(hook_items, list):
        return False
    for item in hook_items:
        if isinstance(item, dict) and "prime-directive-session-update.sh" in str(item.get("command", "")):
            return True
    return False

if action == "add":
    if not any(has_prime_directive_hook(entry) for entry in session_start):
        session_start.append({"hooks": [{"type": "command", "command": hook_cmd}]})
    hooks["SessionStart"] = session_start
    data["hooks"] = hooks
else:
    session_start = [entry for entry in session_start if not has_prime_directive_hook(entry)]
    if session_start:
        hooks["SessionStart"] = session_start
    else:
        hooks.pop("SessionStart", None)
    if hooks:
        data["hooks"] = hooks
    else:
        data.pop("hooks", None)

tmp_path = settings_path.with_suffix(settings_path.suffix + ".tmp")
tmp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
tmp_path.replace(settings_path)
PY
