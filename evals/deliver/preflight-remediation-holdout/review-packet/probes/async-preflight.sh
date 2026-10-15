#!/usr/bin/env bash
set -eu

checkout="${1:?usage: async-preflight.sh CHECKOUT}"
probe_root="$(mktemp -d)"
trap 'rm -r "$probe_root"' EXIT
state_dir="$probe_root/state"
fake_bin="$probe_root/bin"
mkdir -p "$state_dir" "$fake_bin"
touch "$state_dir/team-mode"

sed 's/^+//' > "$fake_bin/git" <<'SCRIPT'
#!/usr/bin/env bash
case "$*" in
  *" rev-parse"*) printf 'deadbeef\n' ;;
  *" pull "*) sleep 2 ;;
esac
exit 0
SCRIPT
chmod +x "$fake_bin/git"

PATH="$fake_bin:$PATH" PRIME_DIRECTIVE_STATE_DIR="$state_dir" \
  "$checkout/scripts/prime-directive-codex-preflight.sh"
if [ ! -f "$state_dir/.last-session-update" ]; then
  sleep 3
  printf 'preflight returned before the updater wrote its throttle file\n' >&2
  exit 1
fi
