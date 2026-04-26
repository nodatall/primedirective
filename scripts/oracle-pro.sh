#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/oracle-pro.sh setup [--force]
  ./scripts/oracle-pro.sh session [session-id]
  ./scripts/oracle-pro.sh status [oracle status args...]
  ./scripts/oracle-pro.sh dry-run -p "<prompt>" [--file <path-or-glob> ...]
  ./scripts/oracle-pro.sh dry-run-json -p "<prompt>" [--file <path-or-glob> ...]
  ./scripts/oracle-pro.sh run -p "<prompt>" [--file <path-or-glob> ...]
  ./scripts/oracle-pro.sh render -p "<prompt>" [--file <path-or-glob> ...]

Prime Directive wrapper for ChatGPT Pro browser escalation via Oracle.

Defaults can be overridden with:
  ORACLE_PRO_MODEL                 default: gpt-5.4-pro
  ORACLE_PRO_THINKING              default: extended; set off/none/0 to skip UI selection
  ORACLE_PRO_BROWSER_TIMEOUT        default: 3600s
  ORACLE_PRO_PROFILE_DIR            default: ~/.oracle/browser-profile
  ORACLE_PRO_REPAIR_PROFILE         default: 1; set 0 to skip Chrome crash-state repair
  ORACLE_PRO_BUNDLE_FILES           default: 1
  ORACLE_PRO_KEEP_TMP               default: 0; set 1 to keep wrapper temp files
  ORACLE_BIN                        default: oracle if installed, else npx -y @steipete/oracle

If no --file/--include/--path input is provided, the wrapper defaults to --file .
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

action="$1"
shift

SETUP_SESSION_ID="${ORACLE_PRO_SETUP_SESSION_ID:-prime-directive-oracle-pro-setup}"

if [[ -n "${ORACLE_BIN:-}" ]]; then
  ORACLE_CMD=("${ORACLE_BIN}")
elif command -v oracle >/dev/null 2>&1; then
  ORACLE_CMD=(oracle)
else
  ORACLE_CMD=(npx -y @steipete/oracle)
fi

export ORACLE_BROWSER_PROFILE_DIR="${ORACLE_PRO_PROFILE_DIR:-${HOME}/.oracle/browser-profile}"

common_args=(
  --engine browser
  --model "${ORACLE_PRO_MODEL:-gpt-5.4-pro}"
  --browser-manual-login
  --browser-attachments "${ORACLE_PRO_ATTACHMENTS:-auto}"
  --browser-timeout "${ORACLE_PRO_BROWSER_TIMEOUT:-3600s}"
  --browser-recheck-delay "${ORACLE_PRO_RECHECK_DELAY:-60s}"
  --browser-recheck-timeout "${ORACLE_PRO_RECHECK_TIMEOUT:-300s}"
  --browser-auto-reattach-delay "${ORACLE_PRO_AUTO_REATTACH_DELAY:-120s}"
  --browser-auto-reattach-interval "${ORACLE_PRO_AUTO_REATTACH_INTERVAL:-120s}"
  --browser-auto-reattach-timeout "${ORACLE_PRO_AUTO_REATTACH_TIMEOUT:-300s}"
)

if [[ "${ORACLE_PRO_BUNDLE_FILES:-1}" != "0" ]]; then
  common_args+=(--browser-bundle-files)
fi

has_file_input=0
for arg in "$@"; do
  case "$arg" in
    -f|--file|--files|--include|--path|--paths|--file=*|--files=*|--include=*|--path=*|--paths=*)
      has_file_input=1
      break
      ;;
  esac
done

append_default_files_if_needed() {
  if [[ "$has_file_input" -eq 0 ]]; then
    CMD+=(--file .)
  fi
}

append_thinking_if_enabled() {
  local thinking="${ORACLE_PRO_THINKING:-extended}"
  case "$thinking" in
    ""|0|off|none|false|disabled)
      return
      ;;
    *)
      CMD+=(--browser-thinking-time "$thinking")
      ;;
  esac
}

repair_chrome_crash_state() {
  if [[ "${ORACLE_PRO_REPAIR_PROFILE:-1}" == "0" ]]; then
    return
  fi

  if ! command -v node >/dev/null 2>&1; then
    return
  fi

  PROFILE_DIR="$ORACLE_BROWSER_PROFILE_DIR" node <<'NODE'
const fs = require('fs');
const path = require('path');

const profileDir = process.env.PROFILE_DIR;
if (!profileDir || !fs.existsSync(profileDir)) {
  process.exit(0);
}

const candidates = [
  path.join(profileDir, 'Default', 'Preferences')
];

for (const entry of fs.readdirSync(profileDir, { withFileTypes: true })) {
  if (entry.isDirectory() && /^Profile \d+$/.test(entry.name)) {
    candidates.push(path.join(profileDir, entry.name, 'Preferences'));
  }
}

for (const preferencesPath of candidates) {
  if (!fs.existsSync(preferencesPath)) {
    continue;
  }

  let preferences;
  try {
    preferences = JSON.parse(fs.readFileSync(preferencesPath, 'utf8'));
  } catch {
    continue;
  }

  preferences.profile = preferences.profile || {};
  const before = JSON.stringify({
    exit_type: preferences.profile.exit_type,
    exited_cleanly: preferences.profile.exited_cleanly
  });

  preferences.profile.exit_type = 'Normal';
  preferences.profile.exited_cleanly = true;

  const after = JSON.stringify({
    exit_type: preferences.profile.exit_type,
    exited_cleanly: preferences.profile.exited_cleanly
  });

  if (before !== after) {
    fs.writeFileSync(preferencesPath, `${JSON.stringify(preferences, null, 2)}\n`);
  }
}
NODE
}

print_browser_recovery_hint() {
  local output="$1"
  if [[ "$output" == *"ECONNREFUSED 127.0.0.1:"* ]]; then
    cat >&2 <<EOF

Oracle browser automation could not connect to its local Chrome DevTools port.
This often happens when the dedicated Oracle Chrome profile opens Chrome's
"Restore tabs?" crash prompt before Oracle can control the browser.

Recovery:
  1. Dismiss the restore prompt in the Oracle Chrome window if it is visible.
  2. Close extra Oracle Chrome windows that were opened by failed retries.
  3. Rerun: ./scripts/oracle-pro.sh setup --force

The wrapper already reset Chrome's crashed-session marker in:
  $ORACLE_BROWSER_PROFILE_DIR
Set ORACLE_PRO_REPAIR_PROFILE=0 to disable that repair step.
EOF
  fi
}

run_with_private_tmpdir() {
  local base_tmp="${TMPDIR:-/tmp}"
  local run_tmpdir
  run_tmpdir="$(mktemp -d "${base_tmp%/}/oracle-pro.XXXXXX")"
  local status=0
  local output_file
  output_file="$(mktemp "${run_tmpdir%/}/oracle-output.XXXXXX")"

  repair_chrome_crash_state
  TMPDIR="$run_tmpdir" "${CMD[@]}" 2>&1 | tee "$output_file" || status=${PIPESTATUS[0]}

  if [[ "$status" -ne 0 ]]; then
    print_browser_recovery_hint "$(cat "$output_file")"
  fi

  if [[ "${ORACLE_PRO_KEEP_TMP:-0}" == "1" ]]; then
    echo "Kept Oracle Pro temp directory: $run_tmpdir" >&2
  else
    rm -rf "$run_tmpdir"
  fi

  return "$status"
}

case "$action" in
  setup)
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}" --browser-keep-browser --browser-model-strategy current --slug "${SETUP_SESSION_ID}" -p "Prime Directive Oracle Pro setup check. Reply with OK when this message is received.")
    CMD+=("$@")
    run_with_private_tmpdir
    ;;
  session)
    session_id="${1:-$SETUP_SESSION_ID}"
    if [[ $# -gt 0 ]]; then
      shift
    fi
    exec "${ORACLE_CMD[@]}" session "$session_id" "$@"
    ;;
  status)
    exec "${ORACLE_CMD[@]}" status "$@"
    ;;
  dry-run)
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}" --dry-run summary --files-report)
    append_thinking_if_enabled
    append_default_files_if_needed
    CMD+=("$@")
    run_with_private_tmpdir
    ;;
  dry-run-json)
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}" --dry-run json --files-report)
    append_thinking_if_enabled
    append_default_files_if_needed
    CMD+=("$@")
    run_with_private_tmpdir
    ;;
  run)
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}")
    append_thinking_if_enabled
    append_default_files_if_needed
    CMD+=("$@")
    run_with_private_tmpdir
    ;;
  render)
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}" --render --copy-markdown)
    append_thinking_if_enabled
    append_default_files_if_needed
    CMD+=("$@")
    run_with_private_tmpdir
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown action: $action" >&2
    usage >&2
    exit 2
    ;;
esac
