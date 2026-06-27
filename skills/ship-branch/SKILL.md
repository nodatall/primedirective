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
- Prefer the repo's explicit local merge gate over ad hoc validation when present.

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
   - Discover the repo's explicit local merge gate before choosing validation:
     - First honor repo instructions that name a local pre-merge, merge-readiness, or local CI gate, such as `AGENTS.md`, `README.md`, `docs/`, runbooks, package scripts, task-runner config, or recent workflow notes.
     - Prefer an explicitly named gate command over decomposing it into its underlying checks. Examples include `ci:local`, `local:ci`, `merge:check`, `premerge`, `verify:local`, `scripts/local-ci.sh`, or a documented equivalent.
     - For package scripts, use the repo's package manager from `packageManager` or lockfiles. For example, if a Bun repo exposes `ci:local`, run `bun run ci:local`; for npm, pnpm, or yarn repos, use that repo's equivalent runner.
     - If more than one plausible local merge gate exists and the owner is ambiguous, stop and ask which gate is authoritative.
   - Run the explicit local merge gate when present. Treat failure as a merge blocker; classify whether it is a branch-scoped failure, environment/auth/provider issue, flaky local-only check, or an unrelated baseline problem before making another patch.
   - If no explicit local merge gate exists, run the relevant repo validation command when it is obvious from the repo or recent workflow. If no obvious command exists, say that no local merge gate or validation command was found.
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
   - If the PR is not mergeable or review requirements block merge, stop and report the blocker.
   - If required checks are pending or queued, keep checking until all required checks pass or any check fails. Prefer `gh pr checks --watch` when available; otherwise poll `gh pr checks` or `gh pr view` about every 60 seconds and report compact progress.
   - If required checks fail, inspect the failed check output with `gh pr checks`, `gh run view --log-failed`, or the check URL. If the failure is actionable and within the branch scope, make the smallest fix, run the explicit local merge gate when available, otherwise run the relevant local validation command when available, commit only the fix with a concise message, push it, and return to the pending/queued check watch.
   - Stop and report the blocker if the check failure is infrastructure, auth, permission, flaky without a clear branch fix, impossible to reproduce locally, or requires a product/scope decision from the user.
   - Do not treat pending or queued checks as a final blocker by themselves. After required checks pass, re-check PR state and mergeability, then continue.
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
   - Local merge gate or validation run, or skipped reason.
   - Any stash left behind.
   - Final `git status --short --branch`.

## Safety Rules

- Never delete the base branch.
- Never use `git branch -D`.
- Never run `git reset --hard`.
- Never commit or stash dirty work without asking.
- During the failed-check repair loop, commit only agent-made fixes for failed PR checks after verifying the branch was clean before the fix; never include unrelated dirty work.
- Never delete local or remote branches until the PR merge is confirmed.
- Never merge a PR with failing or pending required checks unless the user explicitly changes the request and accepts the risk; pending or queued checks are a wait state before merge.
- If branch state, PR state, or local base state is ambiguous, stop and ask.
