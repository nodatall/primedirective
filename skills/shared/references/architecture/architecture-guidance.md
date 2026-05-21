# Architecture Guidance

Use this reference when a workflow creates or updates `docs/ARCHITECTURE.md`, or when planned work may change repo boundaries.

## Boundary-Affecting Work

Work is boundary-affecting when it adds, removes, moves, or rewires any of these:

- modules, packages, major directories, or top-level folders
- shared utilities, common libraries, design systems, or cross-feature helpers
- routes, app shells, CLI entrypoints, workers, jobs, schedulers, or runtime startup files
- services, adapters, dependency registration, external integrations, or infrastructure seams
- cross-module imports, feature-to-feature dependencies, or dependency direction
- test boundaries, public package exports, or composition roots

Small local edits inside one existing boundary are not boundary-affecting. Do not block a focused bug fix, copy edit, or narrow implementation detail only because `docs/ARCHITECTURE.md` is missing.

## Non-Trivial Repo Signal

A repo is non-trivial enough to benefit from `docs/ARCHITECTURE.md` when it has any of these:

- a framework app, backend service, mobile app, desktop app, or deployable worker
- a monorepo or multiple packages/modules
- multiple binaries, commands, jobs, workers, or runtime entrypoints
- several major top-level product areas or feature surfaces
- clear growth intent, repeated agent work, or recurring boundary decisions

Disposable spikes, one-off scripts, tiny single-purpose CLIs, and obvious local fixes can defer architecture documentation until a real boundary decision appears.

## Architecture Doctrine

- Architecture is about ownership and allowed dependencies, not abstract layer names.
- Every major module, package, feature, service, or app area should have a clear purpose, public entrypoint, owner boundary, allowed dependencies, and forbidden dependencies.
- Keep domain or core logic dependency-light. It should not casually import UI, framework, transport, persistence, vendor SDKs, or app-shell code.
- Put integration at the edge. Network clients, databases, external APIs, routing, startup wiring, workers, CLI entrypoints, and framework-specific glue should live outside core policy code.
- Make dependency direction explicit. Outer code may depend inward; inner policy code should not depend outward unless the repo records an accepted deviation.
- Avoid feature-to-feature dependencies. Features should communicate through the composition root, callbacks, events, interfaces, shared domain types, or explicit service boundaries.
- Keep the main app, server startup, CLI command, or worker bootstrap as a small composition root. It wires concrete dependencies and feature entrypoints together; it should not collect business logic.
- Hide feature internals behind small public APIs such as builders, routes, commands, service interfaces, package exports, or module entrypoints.
- Prefer deep modules over pass-through abstractions. A module earns its boundary when callers get meaningful behavior through a smaller interface; it is shallow when its public surface is nearly as complex as its implementation.
- Use the deletion test when judging extracted, shared, or adapter-like modules: if deleting the module makes complexity disappear, it was probably a pass-through; if the same complexity reappears across callers, the boundary was probably earning its keep.
- Prefer explicit dependency passing or constructor injection. Global containers, framework magic, and singletons can provide defaults, but tests and callers should be able to inject dependencies directly.
- Treat the module interface as the main test surface. Tests should exercise observable behavior through the same surface callers use and should usually survive internal refactors.
- Preserve test seams. A new boundary should have a believable unit, contract, module integration, or end-to-end test strategy that does not require booting the whole app for simple behavior.
- Do not introduce ports, adapters, or interface layers only for ceremony. A single adapter usually marks a hypothetical seam; prefer a real seam only when at least two adapters are justified, such as production plus local test, or when an external runtime boundary forces the separation.

## Module And Folder Shape

- Prefer feature boundaries first when the product is feature-shaped. Do not create new top-level technical buckets such as `components`, `services`, or `utils` unless the repo already uses that structure intentionally.
- Keep sibling foundation areas parallel when possible. Service/integration code, design/UI primitives, shared routing, and utility layers should not casually depend on each other.
- Keep shared code small, stable, and earned. A shared helper should usually have at least two real consumers or a framework-level reason to exist.
- Avoid generic `shared`, `common`, `utils`, and `helpers` dumping grounds. If the name does not explain ownership, the boundary is probably too weak.
- Do not over-modularize. Tiny repos, disposable spikes, one-off scripts, and local fixes do not need heavy architecture ceremony.
- Do not under-modularize growing repos. Framework apps, monorepos, multiple packages, multiple binaries, multiple workers, or multiple major top-level areas should usually record their architecture early.

## Architecture Document Template

Use this shape for `docs/ARCHITECTURE.md`. Keep it concrete and repo-specific.

```md
# Architecture

## Purpose

What this repo is, what this file governs, and when agents should read or update it.

## Current System Shape

A short description of the repo's top-level structure and runtime shape.

## Module Map

For each major module, package, directory, feature, service, or app area:

- Path:
- Responsibility:
- Public API or entrypoint:
- May depend on:
- Must not depend on:

## Dependency Rules

The repo's global dependency direction and cross-boundary rules.

## Composition Roots And Runtime Entrypoints

Where concrete dependencies are wired, such as app bootstrap, route registration, main files, worker startup, service registration, CLI commands, schedulers, or task runners.

## Shared Code Rules

What belongs in shared/common code, what does not, and when new shared utilities are allowed.

## Testing Boundaries

Preferred unit, contract, module integration, and end-to-end seams by boundary.

## Architecture Checks

Existing mechanical checks and review expectations.

## Accepted Deviations

Specific exceptions with scope, reason, owner if known, date, and removal trigger.
```

## Agent Behavior

- Before boundary-affecting work, read `docs/ARCHITECTURE.md` if it exists.
- If the architecture doc is missing and the repo is non-trivial, create or update it before making the boundary change unless the user asked for a narrow local fix.
- If the work is a small local fix inside one existing boundary, do not block on a missing architecture doc.
- When code and `docs/ARCHITECTURE.md` disagree, do not silently follow stale docs. Report the mismatch or update the doc as part of the work.
- When intentionally changing a boundary, update `docs/ARCHITECTURE.md` in the same run.
- During review or repo sweep, compare the current code graph to the architecture doc and flag stale paths, missing modules, forbidden dependency edges, undocumented entrypoints, expired deviations, and shared-code drift.
- When no architecture doc exists, repo sweep may report architecture smells, but should label them as inferred rather than contract drift.

## Mechanical Checks

Recommend mechanical checks only when the target ecosystem already has a low-risk, normal tool for the boundary. Good examples include Nx module-boundary tags, ESLint import restrictions, ArchUnit, Import Linter, Go `internal/` and `cmd/` conventions, or existing lint rules.

Do not build or require a universal cross-stack architecture validator from this reference.
