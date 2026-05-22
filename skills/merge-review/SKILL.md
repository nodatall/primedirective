---
name: merge-review
description: Run a goal-backed current-branch merge-readiness loop. Use when invoked with `$merge-review`, especially inside `/goal $merge-review`, before a branch should be merged. Reviews `origin/main...HEAD`, records state in `tasks/merge-review-<branch>.md`, fixes verified local findings, validates, and rereviews until no `Disposition: fix` findings remain or a real blocker is proven.
---

# Merge Review Skill

Make the current branch merge-ready through a durable review -> fix -> validate -> rereview loop.

This skill is a branch merge gate. It is not a whole-repo audit like `$repo-sweep`, and it does not push, create PRs, merge, or clean branches like `$ship-branch`.

## Activation

Invoke inside a Codex goal:

```text
/goal $merge-review
```

If invoked outside a goal, prepare or update the state document and give the exact `/goal $merge-review` command unless the user explicitly asks for a one-pass report. The normal workflow is loop-first.

## References

Load references by path, not all up front:

- Always load `skills/shared/references/review/review-protocol.md`, `skills/shared/references/review/finding-disposition.md`, and `skills/shared/references/reasoning-budget.md`.
- `skills/merge-review/references/state-document.md` before creating or updating the state doc.
- `skills/merge-review/references/merge-readiness-rubric.md` before each review round.
- `skills/shared/references/architecture/architecture-guidance.md` when the branch is boundary-affecting or `docs/ARCHITECTURE.md` exists.

## State Document

Use one durable state document:

- `tasks/merge-review-<branch>.md`

The state document is the source of truth for the run. Keep it current after every meaningful review, finding classification, fix batch, validation result, blocker, resume point, and final verdict.

Do not finish the goal if the state document is stale.

## Scope

- Keep the current branch. Do not create, rename, switch, push, merge, or delete branches.
- Stop if the current branch is `main`, `master`, the resolved base branch, or detached `HEAD`.
- Fetch `origin` before establishing scope.
- Use `origin/main...HEAD` as the default review scope. If the remote default branch is not `main`, use that remote default branch.
- Include committed branch changes and current working-tree changes in the review scope.
- Stop if there is no branch diff and no working-tree change to review.
- If the working tree is dirty at start, record it in the state doc before editing. Do not overwrite unrelated user changes.

## End Condition

The goal is complete only when all of these are true:

- A fresh full-branch review over the latest `origin/main...HEAD` finds no remaining `Disposition: fix` findings.
- Every earlier `Disposition: fix` finding is fixed and validated, or reclassified with evidence.
- Remaining findings, if any, are only `needs human decision`, `residual risk`, or `no action`.
- Relevant validation commands pass, or failures are recorded as human-blocked or residual with evidence.
- No uncommitted implementation fixes from the merge-review loop remain. The only allowed dirty file is the state document when the repo treats review artifacts as uncommitted working notes.
- `tasks/merge-review-<branch>.md` has an up-to-date `Resume State` with `Current status: done`.

Do not stop because one round passed after fixes unless that round was a fresh rereview of the latest branch state.

## Workflow

1. Establish branch and baseline.
   - Run `git status --short --branch`.
   - Detect the current branch and resolved remote base branch.
   - Fetch `origin`.
   - Record branch, base, starting status, and review scope in `tasks/merge-review-<branch>.md`.
2. Collect review context.
   - Inspect `git diff --stat`, `git diff --name-only`, and the relevant committed diff from base to `HEAD`.
   - Read full contents of changed files, not only hunks.
   - Trace nearby callers, importers, routes, tests, or config when the branch touches boundaries.
3. Run a merge-readiness review round.
   - Use `skills/merge-review/references/merge-readiness-rubric.md`.
   - Use `review-protocol.md` Prompt G when frontend behavior changed.
   - Use `review-protocol.md` Prompt H when deploy, runtime, data, security, tools, private data, untrusted input, or outbound actions changed.
   - Record findings in the shared finding shape from `finding-disposition.md`.
4. Classify findings.
   - `fix`: verified, in scope, local, and safe to repair without changing product intent or external contracts.
   - `needs human decision`: product behavior, API/schema, security policy, billing, customer-visible UX, migration semantics, or infrastructure cost is unclear.
   - `residual risk`: important but not safely verifiable or repairable in this local run.
   - `no action`: investigated and not a real issue, not reachable, already guarded, duplicated by stronger evidence, or out of scope.
5. Repair all current `fix` findings.
   - Apply the smallest safe change.
   - Do not repair `needs human decision`, `residual risk`, or `no action` findings.
   - Do not turn merge review into a broad redesign.
6. Validate.
   - Run focused checks for each fix.
   - Run broader branch-relevant checks when the branch touches shared behavior, build surfaces, tests, frontend, deploy, data, security, or tooling.
   - Record every command, result, and unverified surface in the state doc.
7. Commit validated fixes.
   - Commit coherent merge-review fix batches after validation unless the user explicitly asked for no commits.
   - Never commit unrelated pre-existing dirty work.
   - Do not commit the state document unless the repo convention or user request says review artifacts belong in the branch.
8. Rereview fresh state.
   - Start a new review round after every fix batch.
   - Do not reuse an earlier reviewer conclusion as proof that the latest branch is clean.
   - Continue until the End Condition is met or a real blocker is proven.
9. Stop only on real blockers.
   - Stop for human decisions, missing env/services/credentials, unsafe destructive operations, unresolved merge conflicts, or validation failures that cannot be fixed without changing out-of-scope intent.
   - Record the exact blocker and next required user action in the state doc.
10. Finalize the goal.
   - Ensure the state doc says `Current status: done` only when the End Condition is satisfied.
   - Do not ship or merge the branch.
   - Final output names the state doc, rounds completed, fixes made, validation run, remaining human-decision or residual-risk items, and final git status.

## Output

During the goal, keep user-visible updates short and tied to loop progress: current round, findings fixed, validation status, rereview status, or blocker.

For final output:

- say whether the branch is merge-ready under `$merge-review`
- list rounds completed
- summarize fixes made
- list validation commands run
- list remaining `needs human decision` or `residual risk` items
- name the state doc path
- include final `git status --short --branch`
