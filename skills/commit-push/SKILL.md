---
name: commit-push
description: Commit all working-tree changes and push the current branch to GitHub. Use when the user asks for a quick commit and push without PR creation, merging, or branch cleanup.
---

# Commit and Push

Invoke with `$commit-push`. Invocation authorizes committing all working-tree changes and pushing the current branch; do not ask for another confirmation.

1. Inspect the current branch, status, diff, and configured remotes/upstream. Stop on a detached HEAD, unresolved conflicts, or an ambiguous push destination.
2. From the repository root, stage all staged, unstaged, and untracked changes with `git add -A`, respecting `.gitignore`. Read the staged diff and commit with a concise message describing the changes, or use the user's supplied message. If there are no changes, skip the commit.
3. Push the current branch to its configured GitHub upstream. If no upstream exists and `origin` is an unambiguous GitHub destination, use `git push -u origin <current-branch>`. Push existing unpushed commits even when no new commit was needed. Stop and report a rejected push; do not automatically pull, rebase, or retry with force.
4. Report the commit hash, branch, and push destination, or the exact blocker.

Honor required repository checks and normal Git hooks. Keep this workflow limited to committing and pushing; do not add optional review or test workflows, create or merge PRs, or switch or delete branches. Never force-push or rewrite existing commits.
