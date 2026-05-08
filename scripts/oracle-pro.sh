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
  ORACLE_PRO_MODEL                 default: Extended Pro (ChatGPT browser label; Oracle stores gpt-5.5-pro)
  ORACLE_PRO_MODEL_STRATEGY        default: select for dry-run/run/render, ignore for setup; set current to reuse browser state
  ORACLE_PRO_THINKING              default: extended; default Extended Pro model label skips the separate thinking UI click
  ORACLE_PRO_BROWSER_TIMEOUT        default: 3600s
  ORACLE_PRO_PROFILE_DIR            default: ~/.oracle/browser-profile
  ORACLE_PRO_REPAIR_PROFILE         default: 1; set 0 to skip Chrome crash-state repair
  ORACLE_PRO_BUNDLE_FILES           default: 1
  ORACLE_PRO_KEEP_TMP               default: 0; set 1 to keep wrapper temp files
  ORACLE_PRO_PACKAGE_SPEC           default: @steipete/oracle@0.10.0 when ORACLE_BIN is unset
  ORACLE_BIN                        default: oracle if installed, else npx -y ${ORACLE_PRO_PACKAGE_SPEC}

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

EFFECTIVE_MODEL="${ORACLE_PRO_MODEL:-Extended Pro}"
EFFECTIVE_MODEL_STRATEGY=""
EFFECTIVE_THINKING="not-requested"

if [[ -n "${ORACLE_BIN:-}" ]]; then
  ORACLE_CMD=("${ORACLE_BIN}")
elif command -v oracle >/dev/null 2>&1; then
  ORACLE_CMD=(oracle)
else
  ORACLE_CMD=(npx -y "${ORACLE_PRO_PACKAGE_SPEC:-@steipete/oracle@0.10.0}")
fi

export ORACLE_BROWSER_PROFILE_DIR="${ORACLE_PRO_PROFILE_DIR:-${HOME}/.oracle/browser-profile}"

common_args=(
  --engine browser
  --model "${EFFECTIVE_MODEL}"
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
has_model_strategy_input=0
has_thinking_input=0
requested_model_strategy=""
requested_thinking=""
pending_model_strategy=0
pending_thinking=0
for arg in "$@"; do
  if [[ "$pending_model_strategy" -eq 1 ]]; then
    has_model_strategy_input=1
    requested_model_strategy="$arg"
    pending_model_strategy=0
    continue
  fi

  if [[ "$pending_thinking" -eq 1 ]]; then
    has_thinking_input=1
    requested_thinking="$arg"
    pending_thinking=0
    continue
  fi

  case "$arg" in
    -f|--file|--files|--include|--path|--paths|--file=*|--files=*|--include=*|--path=*|--paths=*)
      has_file_input=1
      ;;
    --browser-model-strategy)
      pending_model_strategy=1
      ;;
    --browser-model-strategy=*)
      has_model_strategy_input=1
      requested_model_strategy="${arg#--browser-model-strategy=}"
      ;;
    --browser-thinking-time)
      pending_thinking=1
      ;;
    --browser-thinking-time=*)
      has_thinking_input=1
      requested_thinking="${arg#--browser-thinking-time=}"
      ;;
  esac
done

append_default_files_if_needed() {
  if [[ "$has_file_input" -eq 0 ]]; then
    CMD+=(--file .)
  fi
}

append_thinking_if_enabled() {
  if [[ "$has_thinking_input" -eq 1 ]]; then
    EFFECTIVE_THINKING="${requested_thinking:-explicit-argument}"
    return
  fi

  if [[ -z "${ORACLE_PRO_THINKING+x}" ]] && model_label_requests_extended_pro; then
    EFFECTIVE_THINKING="extended"
    return
  fi

  local thinking="${ORACLE_PRO_THINKING:-extended}"
  case "$thinking" in
    ""|0|off|none|false|disabled)
      EFFECTIVE_THINKING="off"
      return
      ;;
    *)
      EFFECTIVE_THINKING="$thinking"
      CMD+=(--browser-thinking-time "$thinking")
      ;;
  esac
}

model_label_requests_extended_pro() {
  local lower_model
  lower_model="$(printf '%s' "$EFFECTIVE_MODEL" | tr '[:upper:]' '[:lower:]')"
  case "$lower_model" in
    *"extended pro"*|*"pro extended"*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

append_model_strategy() {
  local default_strategy="${1:-}"

  if [[ "$has_model_strategy_input" -eq 1 ]]; then
    EFFECTIVE_MODEL_STRATEGY="${requested_model_strategy:-explicit-argument}"
    return
  fi

  local strategy="${ORACLE_PRO_MODEL_STRATEGY:-$default_strategy}"
  if [[ -z "$strategy" ]]; then
    EFFECTIVE_MODEL_STRATEGY="none"
    return
  fi

  case "$strategy" in
    select|current|ignore)
      EFFECTIVE_MODEL_STRATEGY="$strategy"
      CMD+=(--browser-model-strategy "$strategy")
      ;;
    *)
      echo "Invalid ORACLE_PRO_MODEL_STRATEGY: $strategy (expected select, current, or ignore)" >&2
      exit 2
      ;;
  esac
}

print_invocation_summary() {
  case "$action" in
    setup|dry-run|dry-run-json|run|render)
      printf 'Oracle Pro wrapper invocation: action=%s model=%s model_strategy=%s thinking=%s\n' \
        "$action" \
        "$EFFECTIVE_MODEL" \
        "${EFFECTIVE_MODEL_STRATEGY:-unset}" \
        "${EFFECTIVE_THINKING:-unset}" >&2
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

  if [[ "$output" == *"Unable to locate the ChatGPT model selector button"* ]]; then
    cat >&2 <<EOF

Oracle could not find ChatGPT's model picker in the logged-in browser.
This can happen when ChatGPT changes or hides the model selector. It does not
by itself mean the browser is signed out.

Recovery for setup checks:
  ./scripts/oracle-pro.sh setup --force

The wrapper tries to select the requested ChatGPT model on live runs so it does
not inherit arbitrary browser state. If you explicitly want to reuse whatever
the browser currently has selected, rerun with:
  ORACLE_PRO_MODEL_STRATEGY=current ./scripts/oracle-pro.sh run -p "<prompt>" --file .

If the prompt box is visible but UI controls drift, rerun with:
  ORACLE_PRO_MODEL_STRATEGY=ignore ORACLE_PRO_THINKING=off ./scripts/oracle-pro.sh run -p "<prompt>" --file .

This skips forced model and thinking-time selection and records the run as using
the current ChatGPT browser mode rather than a verified picker selection.
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
  print_invocation_summary
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
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}" --browser-keep-browser)
    append_model_strategy ignore
    CMD+=(--slug "${SETUP_SESSION_ID}" -p "Prime Directive Oracle Pro setup check. Reply with OK when this message is received.")
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
    append_model_strategy select
    append_thinking_if_enabled
    append_default_files_if_needed
    CMD+=("$@")
    run_with_private_tmpdir
    ;;
  dry-run-json)
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}" --dry-run json --files-report)
    append_model_strategy select
    append_thinking_if_enabled
    append_default_files_if_needed
    CMD+=("$@")
    run_with_private_tmpdir
    ;;
  run)
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}")
    append_model_strategy select
    append_thinking_if_enabled
    append_default_files_if_needed
    CMD+=("$@")
    run_with_private_tmpdir
    ;;
  render)
    CMD=("${ORACLE_CMD[@]}" "${common_args[@]}" --render --copy-markdown)
    append_model_strategy select
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
