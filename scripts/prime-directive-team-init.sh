#!/usr/bin/env bash
# Generate repo-level guidance for teams using Prime Directive.

set -euo pipefail

MODE="${1:-}"

if [[ "$MODE" != "optional" && "$MODE" != "required" ]]; then
  cat >&2 <<'EOF'
Usage: scripts/prime-directive-team-init.sh {optional|required}

  optional  Add lightweight AGENTS.md/CLAUDE.md install guidance.
  required  Add required-install guidance and a Claude PreToolUse enforcement hook.
EOF
  exit 1
fi

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Error: not in a git repository. Run from the target project root." >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_URL="$(git -C "$SOURCE_ROOT" ls-remote --get-url origin 2>/dev/null || echo "https://github.com/nodatall/primedirective.git")"
INSTALL_DIR_LITERAL='$HOME/.prime-directive/repo'
GENERATED=()

install_block() {
  cat <<EOF
\`\`\`bash
if [ ! -d "$INSTALL_DIR_LITERAL/.git" ]; then
  git clone --depth 1 $REMOTE_URL "$INSTALL_DIR_LITERAL"
fi
cd "$INSTALL_DIR_LITERAL" && git pull --ff-only && ./setup --host auto --team
\`\`\`
EOF
}

append_if_missing() {
  local file="$1"
  local section="$2"
  if [[ -f "$file" ]] && grep -q "^## Prime Directive" "$file"; then
    echo "$(basename "$file") already has a Prime Directive section. Skipping."
    return 0
  fi
  if [[ -f "$file" ]]; then
    printf '\n' >> "$file"
  fi
  printf '%s\n' "$section" >> "$file"
  GENERATED+=("${file#$REPO_ROOT/}")
  echo "  + ${file#$REPO_ROOT/} - added Prime Directive $MODE section"
}

if [[ "$MODE" == "optional" ]]; then
  AGENTS_SECTION="$(cat <<EOF
## Prime Directive (recommended)

This project can use Prime Directive for Codex workflow skills.
Install or update it globally:

$(install_block)

Use installed skills such as \`\$deliver\`, \`\$review-chain\`, \`\$repo-sweep\`, and \`\$ship-branch\` when they match the request. Do not vendor Prime Directive's \`skills/\` tree into this repo.

Before the first Prime Directive skill use in a Codex session, run the best-effort preflight if it exists:

\`\`\`bash
[ -x "$INSTALL_DIR_LITERAL/scripts/prime-directive-codex-preflight.sh" ] && "$INSTALL_DIR_LITERAL/scripts/prime-directive-codex-preflight.sh" || true
\`\`\`
EOF
)"

  CLAUDE_SECTION="$(cat <<EOF
## Prime Directive (recommended)

This project can use Prime Directive for Claude workflow skills.
Install or update it globally:

$(install_block)

Use installed skills such as \`\$deliver\`, \`\$review-chain\`, \`\$repo-sweep\`, and \`\$ship-branch\` when they match the request. Do not vendor Prime Directive's \`skills/\` tree into this repo.
EOF
)"
else
  AGENTS_SECTION="$(cat <<EOF
## Prime Directive (required)

Before using Prime Directive workflows, verify the global install:

\`\`\`bash
test -f "\$HOME/.codex/skills/deliver/SKILL.md" -o -f "\$HOME/.claude/skills/deliver/SKILL.md" && echo "PRIME_DIRECTIVE_OK" || echo "PRIME_DIRECTIVE_MISSING"
\`\`\`

If \`PRIME_DIRECTIVE_MISSING\`: stop and tell the user to install Prime Directive:

$(install_block)

Do not copy Prime Directive's \`skills/\` tree into this repo. Use the global install as the source of truth.

Before the first Prime Directive skill use in a Codex session, run the best-effort preflight:

\`\`\`bash
"$INSTALL_DIR_LITERAL/scripts/prime-directive-codex-preflight.sh"
\`\`\`
EOF
)"

  CLAUDE_SECTION="$(cat <<EOF
## Prime Directive (required)

Before using Prime Directive workflows, verify the global install:

\`\`\`bash
test -f "\$HOME/.claude/skills/deliver/SKILL.md" && echo "PRIME_DIRECTIVE_OK" || echo "PRIME_DIRECTIVE_MISSING"
\`\`\`

If \`PRIME_DIRECTIVE_MISSING\`: stop and tell the user to install Prime Directive:

$(install_block)

Do not copy Prime Directive's \`skills/\` tree into this repo. Use the global install as the source of truth.
EOF
)"
fi

append_if_missing "$REPO_ROOT/AGENTS.md" "$AGENTS_SECTION"
append_if_missing "$REPO_ROOT/CLAUDE.md" "$CLAUDE_SECTION"

if [[ "$MODE" == "required" ]]; then
  HOOKS_DIR="$REPO_ROOT/.claude/hooks"
  SETTINGS_FILE="$REPO_ROOT/.claude/settings.json"
  mkdir -p "$HOOKS_DIR"
  cat > "$HOOKS_DIR/check-prime-directive.sh" <<'HOOK'
#!/usr/bin/env bash

if [ ! -f "$HOME/.claude/skills/deliver/SKILL.md" ]; then
  cat >&2 <<'MSG'
BLOCKED: Prime Directive is not installed globally for Claude.

Install it:
  if [ ! -d "$HOME/.prime-directive/repo/.git" ]; then
    git clone --depth 1 https://github.com/nodatall/primedirective.git "$HOME/.prime-directive/repo"
  fi
  cd "$HOME/.prime-directive/repo" && git pull --ff-only && ./setup --host auto --team

Then restart your AI coding tool.
MSG
  echo '{"permissionDecision":"deny","message":"Prime Directive is required but not installed. See stderr for install instructions."}'
  exit 0
fi

echo '{}'
HOOK
  chmod +x "$HOOKS_DIR/check-prime-directive.sh"
  GENERATED+=(".claude/hooks/check-prime-directive.sh")
  echo "  + .claude/hooks/check-prime-directive.sh - enforcement hook"

  python3 - "$SETTINGS_FILE" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
try:
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

if not isinstance(settings, dict):
    settings = {}

hooks = settings.get("hooks")
if not isinstance(hooks, dict):
    hooks = {}
pre_tool_use = hooks.get("PreToolUse")
if not isinstance(pre_tool_use, list):
    pre_tool_use = []

exists = False
for entry in pre_tool_use:
    if not isinstance(entry, dict):
        continue
    if entry.get("matcher") != "Skill":
        continue
    hook_items = entry.get("hooks")
    if not isinstance(hook_items, list):
        continue
    if any(isinstance(item, dict) and "check-prime-directive.sh" in str(item.get("command", "")) for item in hook_items):
        exists = True

if not exists:
    pre_tool_use.append({
        "matcher": "Skill",
        "hooks": [{
            "type": "command",
            "command": '"$CLAUDE_PROJECT_DIR/.claude/hooks/check-prime-directive.sh"',
        }],
    })

hooks["PreToolUse"] = pre_tool_use
settings["hooks"] = hooks
settings_path.parent.mkdir(parents=True, exist_ok=True)
tmp_path = settings_path.with_suffix(settings_path.suffix + ".tmp")
tmp_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
tmp_path.replace(settings_path)
PY
  GENERATED+=(".claude/settings.json")
  echo "  + .claude/settings.json - PreToolUse hook registered"
fi

echo ""
echo "Prime Directive team mode ($MODE) initialized."
if [[ "${#GENERATED[@]}" -gt 0 ]]; then
  echo ""
  echo "Review and commit:"
  printf '  git add'
  for path in "${GENERATED[@]}"; do
    printf ' %q' "$path"
  done
  printf '\n'
  echo '  git commit -m "chore: add Prime Directive agent setup"'
fi
