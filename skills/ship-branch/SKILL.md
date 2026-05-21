---
name: ship-branch
description: Finish the current feature branch by handling dirty work safely, pushing, creating or using a PR, merging it, deleting the remote branch, switching back to the base branch, pulling the merged base, and deleting the local branch. Use when invoked with `$ship-branch`, or when the user asks to ship, finish, merge, clean up, and return to main from the current branch.
---

# Ship Branch Skill

Finish the current feature branch safely.

This skill is for the active branch, not for cleaning up old already-merged branches. Use `$cleanup-merged-branches` for broad cleanup scans.

## Activation

Invoke explicitly with `$ship-branch`, or for plain-language requests such as "ship this branch", "finish this branch", "push, PR, merge, and clean up", or "merge this branch and return to main".

## Requirements

- Use local `git` for branch, status, commit, push, switch, pull, and local deletion.
- Use GitHub CLI `gh` for auth checks, PR discovery, PR creation, merge, and remote branch deletion.
- Stop if `gh` is unavailable or unauthenticated.

## Workflow

1. Establish the branch and base.
   - Run `git status --short --branch`.
   - Detect the current branch with `git branch --show-current`.
   - Detect the base branch from the remote default branch, then fall back to `origin/main` or `origin/master`.
   - Run `git fetch origin --prune`.
   - Stop if detached `HEAD`.
   - Stop if already on the base branch; do not "ship" `main` or `master`.
2. Handle dirty work before any push or PR action.
   - If there are unstaged, staged, or untracked changes, print a compact summary before doing anything:
     - `git status --short`
     - `git diff --stat`
     - `git diff --cached --stat`
     - untracked file names from `git status --short`
   - Ask the user whether to commit the changes or stash them.
   - Do not auto-commit, auto-stage, or auto-stash dirty work.
   - If committing, stage only the user-approved files and use a user-approved or clearly supplied commit message.
   - If stashing, use a named stash such as `ship-branch/<branch>/<timestamp>` and report that the stashed work is not included in the shipped branch.
   - After committing or stashing, re-run `git status --short --branch`; stop if the tree is still dirty and the remaining changes were not explicitly handled.
3. Check branch content.
   - Compare the branch to the resolved base with `git log --oneline <base>..HEAD`.
   - If there are no unique commits after dirty-work handling, stop and report that there is nothing to ship.
   - Run the relevant repo validation command when it is obvious from the repo or recent workflow. If no obvious command exists, say that no validation command was found.
4. Push the branch.
   - Use `git push -u origin <current-branch>`.
   - Stop and report the exact blocker on push failure.
5. Create or find the PR.
   - Use `gh pr view --head <current-branch>` to find an existing PR.
   - If no PR exists, create one against the resolved base branch.
   - Use a normal ready PR by default because this skill's purpose is to merge. Do not create a draft PR unless the user explicitly asks for a draft.
   - Include a concise PR title and body from the branch commits when no explicit title/body was provided.
6. Merge the PR.
   - Check PR state and mergeability with `gh pr view`.
   - If checks are failing, required checks are pending, the PR is not mergeable, or review requirements block merge, stop and report the blocker.
   - Merge with the repo's normal merge path. Prefer `gh pr merge --merge --delete-branch` unless the repo or PR clearly requires squash or rebase.
   - Do not use admin merge, force push, or bypass checks.
7. Return to the base branch and clean local state.
   - Switch to the local base branch.
   - Pull or fast-forward from the resolved remote base.
   - If the local base branch has unpublished commits or cannot fast-forward cleanly, stop and report the blocker instead of resetting.
   - Delete the local shipped branch with `git branch -d <branch>`.
   - Verify the remote branch is gone with `git ls-remote --heads origin <branch>`.
8. Report compactly.
   - PR URL and merge result.
   - Branch deleted locally and remotely.
   - Current branch.
   - Validation run or skipped reason.
   - Any stash left behind.
   - Final `git status --short --branch`.

## Safety Rules

- Never delete the base branch.
- Never use `git branch -D`.
- Never run `git reset --hard`.
- Never commit or stash dirty work without asking.
- Never delete local or remote branches until the PR merge is confirmed.
- Never merge a PR with failing or pending required checks unless the user explicitly changes the request and accepts the risk.
- If branch state, PR state, or local base state is ambiguous, stop and ask.
