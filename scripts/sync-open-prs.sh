#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $(basename "$0") [options]

Options:
  --repo-name <name>     Consumer name under repos/ (repeatable). Default: all repos/*
  --base-branch <name>   Base branch for PRs (default: main)
  --branch-prefix <text> Branch prefix for generated branches (default: sync/primedirective)
  --title <text>         PR title (default: Sync agent instructions)
  --body <text>          PR body
  --body-file <path>     Read PR body from file
  --commit-message <text> Commit message (default: Sync agent instructions from primedirective)
  --draft                Create draft PRs
  --auto-merge           Enable auto-merge (squash + delete branch)
  --no-sync              Skip running scripts/sync-repo.sh before commit/PR steps
  -h, --help             Show this help
USAGE
}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

REPO_NAMES=()
BASE_BRANCH="main"
BRANCH_PREFIX="sync/primedirective"
TITLE="Sync agent instructions"
BODY="Automated sync from primedirective core instructions and rules."
COMMIT_MESSAGE="Sync agent instructions from primedirective"
DRAFT=0
AUTO_MERGE=0
NO_SYNC=0
BODY_FILE=""

while (($# > 0)); do
  case "$1" in
    --repo-name)
      REPO_NAMES+=("${2:-}")
      shift 2
      ;;
    --base-branch)
      BASE_BRANCH="${2:-}"
      shift 2
      ;;
    --branch-prefix)
      BRANCH_PREFIX="${2:-}"
      shift 2
      ;;
    --title)
      TITLE="${2:-}"
      shift 2
      ;;
    --body)
      BODY="${2:-}"
      shift 2
      ;;
    --body-file)
      BODY_FILE="${2:-}"
      shift 2
      ;;
    --commit-message)
      COMMIT_MESSAGE="${2:-}"
      shift 2
      ;;
    --draft)
      DRAFT=1
      shift
      ;;
    --auto-merge)
      AUTO_MERGE=1
      shift
      ;;
    --no-sync)
      NO_SYNC=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -n "$BODY_FILE" ]]; then
  if [[ ! -f "$BODY_FILE" ]]; then
    echo "Body file does not exist: $BODY_FILE" >&2
    exit 1
  fi
  BODY=$(<"$BODY_FILE")
fi

if ((${#REPO_NAMES[@]} == 0)); then
  for repo_dir in "$ROOT_DIR"/repos/*; do
    [[ -d "$repo_dir" ]] || continue
    REPO_NAMES+=("$(basename "$repo_dir")")
  done
fi

if ((${#REPO_NAMES[@]} == 0)); then
  echo "No repos found under $ROOT_DIR/repos" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required." >&2
  exit 1
fi

timestamp=$(date +%Y%m%d-%H%M%S)
created_count=0
skipped_count=0
failed_count=0
declare -a pr_urls=()

for name in "${REPO_NAMES[@]}"; do
  if [[ -z "$name" ]]; then
    echo "Encountered empty --repo-name value" >&2
    failed_count=$((failed_count + 1))
    continue
  fi

  repo_dir="$ROOT_DIR/repos/$name"
  repo_path_file="$repo_dir/repo.path"

  echo "==> $name"

  if [[ ! -f "$repo_path_file" ]]; then
    echo "  skip: missing $repo_path_file"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  target_repo=$(<"$repo_path_file")
  if [[ ! -d "$target_repo" ]]; then
    echo "  skip: target repo does not exist: $target_repo"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  if ! git -C "$target_repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "  skip: target path is not a git repo: $target_repo"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  if [[ -n "$(git -C "$target_repo" status --porcelain)" ]]; then
    echo "  skip: target repo has uncommitted changes: $target_repo"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  if ((NO_SYNC == 0)); then
    "$SCRIPT_DIR/sync-repo.sh" --repo-name "$name"
  fi

  if [[ -z "$(git -C "$target_repo" status --porcelain -- AGENTS.md CLAUDE.md rules)" ]]; then
    echo "  skip: no sync changes for $name"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  branch_name="${BRANCH_PREFIX}-${timestamp}"

  if ! git -C "$target_repo" fetch origin "$BASE_BRANCH"; then
    echo "  fail: could not fetch origin/$BASE_BRANCH"
    failed_count=$((failed_count + 1))
    continue
  fi

  if ! git -C "$target_repo" switch -c "$branch_name" "origin/$BASE_BRANCH"; then
    echo "  fail: could not create branch $branch_name from origin/$BASE_BRANCH"
    failed_count=$((failed_count + 1))
    continue
  fi

  git -C "$target_repo" add AGENTS.md CLAUDE.md rules/*.md

  if git -C "$target_repo" diff --cached --quiet; then
    echo "  skip: no staged changes after add"
    git -C "$target_repo" switch "$BASE_BRANCH" >/dev/null 2>&1 || true
    skipped_count=$((skipped_count + 1))
    continue
  fi

  if ! git -C "$target_repo" commit -m "$COMMIT_MESSAGE" >/dev/null; then
    echo "  fail: commit failed"
    failed_count=$((failed_count + 1))
    continue
  fi

  if ! git -C "$target_repo" push -u origin "$branch_name" >/dev/null; then
    echo "  fail: push failed for $branch_name"
    failed_count=$((failed_count + 1))
    continue
  fi

  pr_args=(pr create --base "$BASE_BRANCH" --head "$branch_name" --title "$TITLE" --body "$BODY")
  if ((DRAFT == 1)); then
    pr_args+=(--draft)
  fi

  set +e
  pr_url=$(cd "$target_repo" && gh "${pr_args[@]}")
  pr_create_exit=$?
  set -e

  if ((pr_create_exit != 0)); then
    set +e
    pr_url=$(cd "$target_repo" && gh pr list --head "$branch_name" --json url --jq '.[0].url')
    pr_lookup_exit=$?
    set -e
    if ((pr_lookup_exit != 0)) || [[ -z "$pr_url" ]]; then
      echo "  fail: PR creation failed and no existing PR found for $branch_name"
      failed_count=$((failed_count + 1))
      continue
    fi
  fi

  echo "  pr: $pr_url"
  pr_urls+=("$pr_url")
  created_count=$((created_count + 1))

  if ((AUTO_MERGE == 1)); then
    if (cd "$target_repo" && gh pr merge --auto --squash --delete-branch "$pr_url" >/dev/null); then
      echo "  auto-merge enabled for $pr_url"
    else
      echo "  warn: could not enable auto-merge for $pr_url"
    fi
  fi
done

echo
echo "Summary: created=$created_count skipped=$skipped_count failed=$failed_count"
if ((${#pr_urls[@]} > 0)); then
  echo "PRs:"
  for url in "${pr_urls[@]}"; do
    echo "  - $url"
  done
fi

if ((failed_count > 0)); then
  exit 1
fi
