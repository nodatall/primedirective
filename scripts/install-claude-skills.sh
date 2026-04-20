#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-${HOME}/.claude}"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-${CLAUDE_CONFIG_DIR}/skills}"

mkdir -p "$CLAUDE_SKILLS_DIR"

linked_count=0
skipped_count=0

for skill_dir in "$ROOT_DIR"/skills/*; do
  if [[ ! -d "$skill_dir" ]]; then
    continue
  fi
  if [[ ! -f "$skill_dir/SKILL.md" ]]; then
    continue
  fi

  skill_name="$(basename "$skill_dir")"
  target_path="${CLAUDE_SKILLS_DIR}/${skill_name}"

  if [[ -e "$target_path" && ! -L "$target_path" ]]; then
    echo "Skipped skill ${skill_name}: ${target_path} already exists as a real directory"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  ln -sfn "$skill_dir" "$target_path"
  echo "Linked Claude skill ${skill_name} -> ${target_path}"
  linked_count=$((linked_count + 1))
done

echo "Installed ${linked_count} Claude skill link(s) in ${CLAUDE_SKILLS_DIR}"
if [[ "$skipped_count" -gt 0 ]]; then
  echo "Skipped ${skipped_count} existing real skill directory/directories"
fi
