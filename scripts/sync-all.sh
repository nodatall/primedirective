#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

CHECK_FLAG=""
if [[ "${1:-}" == "--check" ]]; then
  CHECK_FLAG="--check"
fi

for repo_dir in "$ROOT_DIR"/repos/*; do
  [[ -d "$repo_dir" ]] || continue
  name=$(basename "$repo_dir")
  "$SCRIPT_DIR/sync-repo.sh" --repo-name "$name" $CHECK_FLAG
done
