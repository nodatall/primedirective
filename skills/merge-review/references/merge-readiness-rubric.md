# Merge Readiness Rubric

Use this reference before each `$merge-review` review round.

Review the current branch as a merge gate. Prefer concrete bugs, verified maintainability risks, and weak verification findings over broad taste comments.

## Required Inputs

- `git diff --stat <base>...HEAD`
- `git diff --name-only <base>...HEAD`
- Relevant diff hunks
- Full contents of changed files
- Nearby callers, importers, routes, tests, config, or docs when the change touches boundaries
- Current working-tree changes when present

## Review Priorities

### Correctness

- User or system flows that are display-only, stubbed, or not wired end to end.
- Hardcoded behavior pretending to be dynamic behavior.
- Validation that accepts invalid input or rejects valid input.
- Async, concurrency, retry, idempotency, or ordering errors.
- Error handling that hides failures or makes recovery impossible.

### Structural Quality

- Shallow wrappers, pass-through modules, hooks, adapters, or services that do not remove complexity.
- Complexity moved into helpers, callbacks, config, generated glue, or callers instead of being simplified.
- Domain logic leaked into UI, routing, storage, CLI, tests, or orchestration when an existing boundary should own it.
- Already-large files made larger without a strong locality reason and a credible split-or-delete path.
- New abstractions with only one real implementation unless they protect a real boundary.

### Test And Verification Quality

- Tests that simply restate constants, copied literals, helper internals, implementation details, or snapshots without behavior value.
- Tests that mock away the logic or integration they claim to verify.
- Missing tests or probes for edge cases, failure paths, side effects, or real caller-facing interfaces.
- Verification evidence that proves only compilation, formatting, or happy-path rendering when the change risk is behavioral.
- Uncommitted implementation fixes left after validation; a merge-ready branch should not require the next agent to infer which local edits belong to the branch.

### Frontend Merge Readiness

Use the frontend evidence rules from `review-protocol.md` when UI, layout, styling, interaction flows, responsive behavior, animation, or rendered content changed.

Look for:

- broken or untested interactions
- missing loading, empty, error, disabled, hover, focus, or responsive states
- layout clipping, overlap, generic visuals, or incoherent copy
- visual changes not inspected in a browser or app when practical

### Production Readiness

Use Prompt H from `review-protocol.md` when backend, config, deploy, data, security, tools, private data, untrusted input, or outbound actions changed.

Look for:

- hardcoded secrets or unsafe defaults
- config/env behavior that fails open
- destructive scripts or migrations without target guards
- missing auth/authz/rate-limit/CORS/CSRF checks where relevant
- missing timeouts, retries, idempotency, logging, rollback, or observability on risky paths

## Bounded Adversarial Priors

Use the bounded adversarial-prior rules from `skills/shared/references/review/review-protocol.md` during each merge-readiness review round.

- `bug_prior`: assume the branch still has a real merge-blocking bug, then try to prove the strongest candidate with a concrete path, scenario, missing guard, or missing verification signal.
- `smaller_delta`: assume the branch can preserve the user goal with less code, less surface area, fewer abstractions, or narrower validation. Report only reductions that lower real merge risk or maintenance cost without removing required scope.
- `skeptic_falsifier`: reject unsupported hostile findings. When suspicion fails, record `no action` with the evidence that cleared it.

Do not keep searching until a bug is found. A clean hostile pass is acceptable only when the falsifying evidence is recorded.

## Disposition Rules

Use `skills/shared/references/review/finding-disposition.md`.

- `fix`: verified, in scope, local, and safe to repair without changing product intent or external contracts.
- `needs human decision`: the right fix depends on product behavior, API/schema, security policy, billing, customer-visible UX, migration semantics, infrastructure cost, or similar intent.
- `residual risk`: important but not safely verifiable or repairable in this local run.
- `no action`: inspected and not a problem, not reachable, already guarded, duplicated by stronger evidence, or out of scope.

Do not report cosmetic nits while structural or behavioral findings exist. Do not convert speculative redesign ideas into `fix` findings.
