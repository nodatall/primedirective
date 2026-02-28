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
BODY="Automated sync from primedirective core instructions and skills."
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

restore_repo_state() {
  local repo_path="$1"
  local original_branch="$2"
  local stashed_changes="$3"
  local stash_ref="$4"
  local current_branch

  current_branch=$(git -C "$repo_path" symbolic-ref --quiet --short HEAD || true)
  if [[ -n "$original_branch" && "$current_branch" != "$original_branch" ]]; then
    git -C "$repo_path" switch "$original_branch" >/dev/null 2>&1 || true
  fi

  if ((stashed_changes == 1)); then
    if ! git -C "$repo_path" stash pop --index "$stash_ref" >/dev/null 2>&1; then
      echo "  warn: could not restore stashed changes ($stash_ref) in $repo_path"
      echo "  run manually: git -C \"$repo_path\" stash list"
    fi
  fi
}

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

  original_branch=$(git -C "$target_repo" symbolic-ref --quiet --short HEAD || true)
  stashed_changes=0
  stash_ref=""

  if [[ -n "$(git -C "$target_repo" status --porcelain)" ]]; then
    if [[ -z "$original_branch" ]]; then
      echo "  skip: target repo has uncommitted changes and detached HEAD: $target_repo"
      skipped_count=$((skipped_count + 1))
      continue
    fi

    if [[ "$original_branch" == "$BASE_BRANCH" ]]; then
      echo "  skip: target repo has uncommitted changes on $BASE_BRANCH: $target_repo"
      skipped_count=$((skipped_count + 1))
      continue
    fi

    stash_marker="sync-open-prs-${timestamp}-${name}"
    if ! git -C "$target_repo" stash push --include-untracked -m "$stash_marker" >/dev/null; then
      echo "  fail: could not stash uncommitted changes on $original_branch"
      failed_count=$((failed_count + 1))
      continue
    fi
    stashed_changes=1
    stash_ref=$(git -C "$target_repo" stash list --format='%gd %s' | awk -v marker="$stash_marker" '$0 ~ marker {print $1; exit}')
    if [[ -z "$stash_ref" ]]; then
      stash_ref="stash@{0}"
    fi
    echo "  note: stashed uncommitted changes from $original_branch ($stash_ref)"
  fi

  branch_name="${BRANCH_PREFIX}-${name}-${timestamp}"

  if ! git -C "$target_repo" fetch origin "$BASE_BRANCH"; then
    echo "  fail: could not fetch origin/$BASE_BRANCH"
    failed_count=$((failed_count + 1))
    restore_repo_state "$target_repo" "$original_branch" "$stashed_changes" "$stash_ref"
    continue
  fi

  if ! git -C "$target_repo" switch -c "$branch_name" "origin/$BASE_BRANCH"; then
    echo "  fail: could not create branch $branch_name from origin/$BASE_BRANCH"
    failed_count=$((failed_count + 1))
    restore_repo_state "$target_repo" "$original_branch" "$stashed_changes" "$stash_ref"
    continue
  fi

  if ((NO_SYNC == 0)); then
    "$SCRIPT_DIR/sync-repo.sh" --repo-name "$name"
  fi

  if [[ -z "$(git -C "$target_repo" status --porcelain -- AGENTS.md CLAUDE.md skills rules)" ]]; then
    echo "  skip: no sync changes for $name"
    if [[ -n "$original_branch" && "$original_branch" != "$branch_name" ]]; then
      git -C "$target_repo" switch "$original_branch" >/dev/null 2>&1 || true
    fi
    git -C "$target_repo" branch -D "$branch_name" >/dev/null 2>&1 || true
    skipped_count=$((skipped_count + 1))
    restore_repo_state "$target_repo" "$original_branch" "$stashed_changes" "$stash_ref"
    continue
  fi

  git -C "$target_repo" add -A

  if git -C "$target_repo" diff --cached --quiet; then
    echo "  skip: no staged changes after add"
    if [[ -n "$original_branch" && "$original_branch" != "$branch_name" ]]; then
      git -C "$target_repo" switch "$original_branch" >/dev/null 2>&1 || true
    fi
    git -C "$target_repo" branch -D "$branch_name" >/dev/null 2>&1 || true
    skipped_count=$((skipped_count + 1))
    restore_repo_state "$target_repo" "$original_branch" "$stashed_changes" "$stash_ref"
    continue
  fi

  if ! git -C "$target_repo" commit -m "$COMMIT_MESSAGE" >/dev/null; then
    echo "  fail: commit failed"
    failed_count=$((failed_count + 1))
    restore_repo_state "$target_repo" "$original_branch" "$stashed_changes" "$stash_ref"
    continue
  fi

  if ! git -C "$target_repo" push -u origin "$branch_name" >/dev/null; then
    echo "  fail: push failed for $branch_name"
    failed_count=$((failed_count + 1))
    restore_repo_state "$target_repo" "$original_branch" "$stashed_changes" "$stash_ref"
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
      restore_repo_state "$target_repo" "$original_branch" "$stashed_changes" "$stash_ref"
      continue
    fi
  fi

  echo "  pr: $pr_url"
  pr_urls+=("$pr_url")
  created_count=$((created_count + 1))

  if ((AUTO_MERGE == 1)); then
    set +e
    auto_merge_output=$(cd "$target_repo" && gh pr merge --auto --squash --delete-branch "$pr_url" 2>&1)
    auto_merge_exit=$?
    set -e

    if ((auto_merge_exit == 0)); then
      echo "  auto-merge enabled for $pr_url"
    else
      set +e
      direct_merge_output=$(cd "$target_repo" && gh pr merge --squash --delete-branch "$pr_url" 2>&1)
      direct_merge_exit=$?
      set -e

      if ((direct_merge_exit == 0)); then
        echo "  merged immediately for $pr_url (auto-merge not available)"
      else
        echo "  warn: could not auto-merge or merge immediately for $pr_url"
        echo "  auto-merge error: ${auto_merge_output%%$'\n'*}"
        echo "  direct-merge error: ${direct_merge_output%%$'\n'*}"
      fi
    fi
  fi

  restore_repo_state "$target_repo" "$original_branch" "$stashed_changes" "$stash_ref"
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
