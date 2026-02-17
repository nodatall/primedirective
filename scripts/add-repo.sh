#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $(basename "$0") --repo-path <path> [--repo-name <name>] [--force]

Options:
  --repo-path <path>  Absolute or relative path to the consumer repo
  --repo-name <name>  Name under repos/ (default: basename of repo path)
  --force             Overwrite existing repos/<name>/repo.path
  -h, --help          Show this help
USAGE
}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

REPO_PATH=""
REPO_NAME=""
FORCE=0

while (($# > 0)); do
  case "$1" in
    --repo-path)
      REPO_PATH="${2:-}"
      shift 2
      ;;
    --repo-name)
      REPO_NAME="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
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

if [[ -z "$REPO_PATH" ]]; then
  echo "--repo-path is required" >&2
  usage >&2
  exit 2
fi

if [[ ! -d "$REPO_PATH" ]]; then
  echo "Repo path does not exist: $REPO_PATH" >&2
  exit 1
fi

if ! git -C "$REPO_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Repo path is not a git repository: $REPO_PATH" >&2
  exit 1
fi

REPO_PATH_ABS=$(cd "$REPO_PATH" && pwd -P)

if [[ -z "$REPO_NAME" ]]; then
  REPO_NAME=$(basename "$REPO_PATH_ABS")
fi

if [[ ! "$REPO_NAME" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "Invalid repo name: $REPO_NAME" >&2
  echo "Use only letters, numbers, dot, underscore, or dash." >&2
  exit 2
fi

REPO_DIR="$ROOT_DIR/repos/$REPO_NAME"
REPO_PATH_FILE="$REPO_DIR/repo.path"

mkdir -p "$REPO_DIR/overlay/rules"

if [[ -f "$REPO_PATH_FILE" && $FORCE -ne 1 ]]; then
  echo "Config already exists: $REPO_PATH_FILE" >&2
  echo "Use --force to overwrite it." >&2
  exit 1
fi

printf '%s\n' "$REPO_PATH_ABS" > "$REPO_PATH_FILE"

echo "Configured repo:"
echo "  name: $REPO_NAME"
echo "  path: $REPO_PATH_ABS"
echo "  config: $REPO_PATH_FILE"
