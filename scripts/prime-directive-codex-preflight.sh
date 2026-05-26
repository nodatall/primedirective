#!/usr/bin/env bash
# Best-effort updater for Codex sessions before Prime Directive skill use.

set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_UPDATE="$SCRIPT_DIR/prime-directive-session-update.sh"

if [ -x "$SESSION_UPDATE" ]; then
  "$SESSION_UPDATE" >/dev/null 2>&1 || true
fi

exit 0
