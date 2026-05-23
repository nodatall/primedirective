# Nitpick Depth

Use this reference whenever `$repo-sweep --swarm` is active.

Nitpick depth is an aggressive evidence-backed maintainability review. It is for finding high-value code-quality, test-quality, and product-surface slop that normal production-readiness review can miss.

It is not a style-preference pass and not a mandate to redesign the repo. Report a nitpick finding only when it has:

- exact files, paths, commands, or UI states inspected
- a concrete user, operator, reviewer, or future-maintainer cost
- evidence that the issue is reachable or likely to affect future changes
- the smallest safe fix path

Do not report:

- file size, churn, or style alone
- speculative rewrites
- personal taste
- refactors that only move complexity
- issues already covered by stronger security, runtime, or production findings

## Hotspot Selection

Start from evidence, then inspect the most suspicious areas first:

- largest files and most frequently changed files, especially overlap between the two
- files touched by the current branch or recent commits
- entrypoints, orchestrators, hooks, providers, adapters, and state managers
- generated files and their sources
- tests and fixtures around critical user/system journeys
- files where future agents would have to infer behavior from scattered clues

Record the inspected hotspots in the repo-sweep report. If time or blockers prevent inspecting an obvious hotspot, record it as residual risk instead of implying it was clean.

## Code And Structure Checks

Look for:

- dead code, unused branches, stale feature flags, and abandoned fallback paths
- duplicated domain rules across UI, API, worker, or desktop boundaries
- shallow pass-through modules that add indirection without owning behavior
- over-broad abstractions with one real implementation
- god objects, god files, or components whose responsibilities are hard to name
- scattered state transitions that make the lifecycle hard to reason about
- hidden coupling through globals, env vars, local storage, generated bindings, or naming conventions
- inconsistent command strings, enum values, route names, setting keys, or event names
- TODOs, comments, docs, or mocks that contradict the current code path
- error handling that swallows failures or converts them into misleading success states
- async work that is not awaited, cancelled, timed out, or cleaned up
- hard-to-test paths where a small extraction would make the real behavior testable

For shallow modules, apply the deletion test from architecture guidance: would deleting the module remove complexity, or would the same complexity spread into callers?

## Test And Verification Checks

Look for:

- tests that mostly restate implementation instead of proving behavior
- tests that mock away the production path they claim to protect
- assertions that only check that something exists, not that the right behavior happened
- fixtures that encode impossible, stale, or too-perfect states
- critical user/API/browser paths with unit-only coverage and no integration or runtime proof
- skipped, flaky, or timeout-prone tests that hide a real wiring problem
- generated bindings, schemas, translations, snapshots, or fixtures that are not regenerated and diff-checked
- validation commands that pass without compiling or exercising the production path

Report whether the existing safety net would have caught each accepted nitpick finding. If it would not, include the smallest practical test or check in the fix path.

## Frontend And Product-Surface Checks

When the repo has UI, rendered content, mockups, or browser flows, inspect for:

- visible dead controls or controls wired only in mockups
- stale copy, stale mockup structure, or docs that no longer match the product surface
- clipped text, hidden overflow, poor empty/loading/error states, or responsive regressions
- screenshots or browser checks that prove only that the page loaded, not that the interaction works
- routes or controls that appear interactive but do not complete the user workflow
- state that is lost after refresh, logout/login, navigation, or retry when persistence is expected

Use browser or app evidence when practical. If the UI cannot run, say exactly why and treat unverified UI behavior as residual risk.

## Looks Bad But Fine

When a suspicious pattern is investigated and cleared, report it under `Looks Bad But Fine` with the guard that made it acceptable. This keeps the sweep nitpicky without creating busywork.

Examples:

- large file is cohesive because it is a generated binding
- duplicate-looking code is intentionally split across trust boundaries
- a fallback is dev-only and proven disabled in production
- a mock is only used in a focused test and the production path has separate coverage

## Output

Each nitpick lane or section should return:

- hotspots inspected
- accepted findings using the shared finding shape
- rejected false positives under `Looks Bad But Fine`
- obvious hotspots not inspected and why
- recommended fix order when there are multiple `Disposition: fix` findings
