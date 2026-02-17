#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# One-command flow:
# 1) sync all configured repos
# 2) open PRs for generated changes
# 3) enable auto-merge on those PRs
"$SCRIPT_DIR/sync-open-prs.sh" --auto-merge "$@"
