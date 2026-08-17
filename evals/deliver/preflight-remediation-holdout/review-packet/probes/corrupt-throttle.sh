#!/usr/bin/env bash
set -eu

checkout="${1:?usage: corrupt-throttle.sh CHECKOUT}"
probe_root="$(mktemp -d)"
trap 'rm -r "$probe_root"' EXIT
state_dir="$probe_root/state"
mkdir -p "$state_dir"
touch "$state_dir/team-mode"
printf 'not a number\n' > "$state_dir/.last-session-update"

PRIME_DIRECTIVE_STATE_DIR="$state_dir" \
  "$checkout/scripts/prime-directive-session-update.sh" \
  2>"$probe_root/stderr.txt"
sleep 1
test ! -s "$probe_root/stderr.txt"
