---
name: cleanup-merged-branches
description: Safely clean up merged feature branches locally and on `origin` without deleting active, unmerged, or still-open work. Optionally target a specific branch.
---

# Cleanup Merged Branches Skill

Clean up merged feature branches safely.

## Activation

Invoke explicitly with `$cleanup-merged-branches`.

The current user request may optionally name a specific branch. Without one, inspect safe merged candidates using the workflow rules below.

## Required references

Load these files before running:

- `skills/shared/references/review/review-protocol.md`

Use Step 10 in `review-protocol.md` as the source of truth for safety rules.

## Workflow

1. Establish the base branch and refresh remote state.
   - Run `git fetch origin --prune`.
   - Detect the base branch in this order:
     - `git symbolic-ref refs/remotes/origin/HEAD`
     - `origin/main`
     - `origin/master`
   - Treat the resolved remote branch as the merge target for all safety checks.
2. Resolve cleanup candidates.
   - If the trigger includes `<branch-name>`, only inspect that branch.
   - Otherwise:
     - if the current branch is a non-base feature branch, inspect it first
     - if the current branch is already the base branch, inspect all local branches whose tips are already merged into the resolved remote base branch
3. For each candidate, enforce hard safety gates before deleting anything.
   - Never delete the base branch.
   - Never delete a branch that does not exist locally or on `origin`.
   - Never delete a branch whose tip is not reachable from the resolved remote base branch.
   - Never delete a branch tied to an open PR when GitHub CLI can verify that state.
   - If GitHub CLI is unavailable or cannot verify PR state, skip remote deletion rather than guessing.
4. Delete safely.
   - If the candidate is currently checked out, switch to the base branch before local deletion.
   - Delete the local merged branch with `git branch -d <branch>`.
   - If the remote branch still exists and passes safety checks, delete it with `git push origin --delete <branch>`.
5. Report compactly.
   - `Deleted`: local and/or remote branches removed
   - `Skipped`: candidate not safe to delete, with reason
   - `Needs human decision`: ambiguous branch state, verification failure, or conflicting repo state

## Safety rules

- Prefer skipping to force-deleting.
- Do not use `git branch -D`.
- Do not delete branches with unmerged local commits.
- Do not delete branches tied to open PRs.
- If cleanup would require a non-obvious branch switch or the repo is in a confusing state, stop and ask.

## Output

Keep the final output short and action-oriented:

1. Deleted
2. Skipped
3. Needs human decision
