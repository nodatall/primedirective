#!/usr/bin/env bash
# Silent best-effort Prime Directive updater for Claude hooks and Codex preflight.

set +e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${PRIME_DIRECTIVE_STATE_DIR:-$HOME/.prime-directive}"
TEAM_MARKER="$STATE_DIR/team-mode"
THROTTLE_FILE="$STATE_DIR/.last-session-update"
LOCK_DIR="$STATE_DIR/.session-update-lock"
LOG_FILE="$STATE_DIR/session-update.log"
THROTTLE_SECONDS=3600

log_entry() {
  mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $1" >> "$LOG_FILE" 2>/dev/null || true
}

if [ ! -f "$TEAM_MARKER" ]; then
  exit 0
fi

if [ ! -d "$ROOT_DIR/.git" ]; then
  exit 0
fi

if [ -f "$THROTTLE_FILE" ]; then
  last="$(cat "$THROTTLE_FILE" 2>/dev/null || echo 0)"
  now="$(date +%s)"
  elapsed=$(( now - last ))
  if [ "$elapsed" -lt "$THROTTLE_SECONDS" ]; then
    exit 0
  fi
fi

(
  export GIT_TERMINAL_PROMPT=0
  mkdir -p "$STATE_DIR" 2>/dev/null || exit 0

  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    if [ -f "$LOCK_DIR/pid" ]; then
      lock_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || echo 0)"
      if [ "$lock_pid" -gt 0 ] 2>/dev/null && ! kill -0 "$lock_pid" 2>/dev/null; then
        rm -rf "$LOCK_DIR" 2>/dev/null
        mkdir "$LOCK_DIR" 2>/dev/null || { log_entry "SKIP lock_contested"; exit 0; }
      else
        log_entry "SKIP locked_by=$lock_pid"
        exit 0
      fi
    else
      log_entry "SKIP locked_no_pid"
      exit 0
    fi
  fi

  echo $$ > "$LOCK_DIR/pid" 2>/dev/null
  trap 'rm -rf "$LOCK_DIR" 2>/dev/null' EXIT

  old_head="$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null)"
  git -C "$ROOT_DIR" pull --ff-only -q >/dev/null 2>&1
  pull_exit=$?
  new_head="$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null)"
  date +%s > "$THROTTLE_FILE" 2>/dev/null

  if [ "$pull_exit" -ne 0 ]; then
    log_entry "PULL_FAILED exit=$pull_exit"
    exit 0
  fi

  if [ "$old_head" != "$new_head" ]; then
    log_entry "UPDATING old=$old_head new=$new_head"
    ( cd "$ROOT_DIR" && ./setup --host auto --quiet ) >/dev/null 2>&1 || log_entry "SETUP_FAILED"
    log_entry "UPDATED new=$new_head"
  else
    log_entry "UP_TO_DATE head=$old_head"
  fi
) &

exit 0
