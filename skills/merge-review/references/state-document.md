# Merge Review State Document

Use this reference before creating or updating `tasks/merge-review-<branch-slug>.md`.

The state document is the controlling artifact for `/goal $merge-review`. Keep it current enough that another agent can resume without reading the full conversation.

## Template

```md
# Merge Review: <branch>

Goal: Make `<branch>` merge-ready by reviewing `<remote-base>...HEAD`, fixing verified local findings, validating, and rereviewing until no `Disposition: fix` findings remain.

## Branch And Base

- Branch: `<branch>`
- Branch slug: `<branch-slug>`
- Base: `<remote-base>`
- Review scope: `<remote-base>...HEAD`
- Started at: `<timestamp>`
- Starting status: `<git status --short --branch summary>`

## End Condition

The merge-review goal is complete only when:

- A fresh full-branch review of `<remote-base>...HEAD` finds no remaining `Disposition: fix` findings.
- Every earlier `Disposition: fix` finding is fixed, validated, and marked closed, or reclassified with evidence.
- Remaining findings, if any, are only `needs human decision`, `residual risk`, or `no action`.
- Relevant validation commands pass, or failures are recorded as human-blocked or residual with evidence.
- No uncommitted implementation fixes from the merge-review loop remain. The only allowed dirty file is this state document when the repo treats review artifacts as uncommitted working notes.
- This document's `Resume State` says `Current status: done`.

Do not stop because one round passed after fixes unless that round was a fresh rereview of the latest branch state.

## Round Log

| Round | Scope | Result | Next action |
| --- | --- | --- | --- |
| 1 | `<remote-base>...HEAD` | pending | review |

## Findings

| ID | Round | Severity | Disposition | Scope | Status | Evidence | Fix or reason |
| --- | --- | --- | --- | --- | --- | --- | --- |

Status values:

- `open`
- `fixed`
- `validated`
- `reclassified`
- `blocked`
- `no action`

## Fix Log

| Finding ID | Change | Files | Validation |
| --- | --- | --- | --- |

## Validation Log

| Command or flow | Result | Evidence | Remaining gap |
| --- | --- | --- | --- |

## Remaining Human Decisions

- None currently.

## Residual Risks

- None currently.

## Resume State

- Current status: in_progress
- Current phase: establishing scope
- Last completed step: none yet
- Active step: create initial state
- Next exact action: run the first review round
- Blockers: none
- Last validation: none yet
- Protected paths: none beyond unrelated user changes
- Evidence paths: this file

## Final Merge-Readiness Verdict

- Verdict: pending
- Reason: merge review has not completed yet.
```

## Update Rules

- Build `<branch-slug>` from the current branch name by replacing `/` and other filename-unsafe characters with `-`.
- Append a round row before starting each fresh review.
- Add every material finding before fixing it.
- Close or reclassify findings with evidence; do not silently delete them.
- Keep `Resume State` accurate after each meaningful step.
- Set `Current status: done` only after the End Condition is satisfied.
- If blocked, set `Current status: blocked`, name the exact blocker, and state the smallest user or external action needed.
