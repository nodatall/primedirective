---
name: create-architecture
description: Create or update a repo-specific `docs/ARCHITECTURE.md` that records module boundaries, dependency direction, composition roots, shared-code rules, testing boundaries, lightweight architecture checks, and accepted deviations. Use when invoked with `$create-architecture`, when bootstrapping a non-trivial repo, or before boundary-affecting work when no architecture doc exists.
---

# Create Architecture Skill

Create or update one repo-local architecture document that agents can use as the standing boundary contract.

This skill is not a generic architecture essay generator. It must describe the repository as it exists or, for greenfield work, the concrete shape the repo should start with.

## Activation

Invoke explicitly with `$create-architecture`.

Also use this skill when a Prime Directive workflow is about to make boundary-affecting changes in a non-trivial repo and `docs/ARCHITECTURE.md` is missing.

## Required References

Load before starting:

- `skills/shared/references/architecture/architecture-guidance.md`

## Modes

- Existing repo mode: inspect the current code, docs, entrypoints, module boundaries, dependency direction, test seams, and validation surface before writing or changing `docs/ARCHITECTURE.md`.
- Greenfield mode: use the user's product, stack, or repo brief to create a stack-native architecture baseline before implementation starts.

## Workflow

1. Classify the repo and scope.
   - Decide whether this is existing repo mode or greenfield mode.
   - Use `architecture-guidance.md` to decide whether the repo is non-trivial enough to need an architecture doc.
   - Do not block tiny local fixes, disposable spikes, one-off scripts, or narrow work inside one existing boundary.
2. Inspect the repo or source brief.
   - Existing repo mode: inspect manifests, top-level directories, packages/modules, app shells, route registration, workers/jobs, CLI entrypoints, service registration, tests, and existing docs.
   - Greenfield mode: identify the stack, expected runtime entrypoints, major product areas, integration surfaces, and test strategy from the brief.
3. Draft or update `docs/ARCHITECTURE.md`.
   - Use the template in `architecture-guidance.md`.
   - Name concrete paths and entrypoints when they exist.
   - Record module responsibilities, allowed dependencies, forbidden dependencies, composition roots, shared-code rules, testing boundaries, architecture checks, and accepted deviations.
   - Keep durable boundary notes and accepted deviations in this file. Do not create a second document unless the repo already has its own convention.
4. Preserve local truth.
   - If existing code conflicts with an ideal pattern, document the actual state first.
   - Recommend a small future cleanup only when the current boundary creates a concrete maintenance risk.
   - Do not invent mechanical checks unless the repo already has an obvious low-risk ecosystem fit.
5. Validate the doc.
   - Re-read `docs/ARCHITECTURE.md` against the inspected repo or source brief.
   - Remove generic advice that is not tied to this repo.
   - Ensure every listed boundary has a path, purpose, and dependency rule when that information is knowable.

## Output

Return a short handoff:

- path written or updated
- whether this was existing repo mode or greenfield mode
- the top architecture boundaries captured
- any stale/missing boundary facts that could not be resolved
- any optional mechanical checks recommended, with why they are low-risk

Do not implement the architecture changes themselves unless the user separately asks for implementation.
