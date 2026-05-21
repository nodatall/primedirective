# Architecture Skill

Goal: Add a lightweight Prime Directive architecture workflow that creates repo-specific `docs/ARCHITECTURE.md` files and makes existing skills respect them during boundary-affecting work.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The new skill should be named `$create-architecture`.
- Architecture guidance should be stack-agnostic, but it should preserve the useful principles from the Swift modular architecture note and the Deep Research output.
- The workflow should avoid extra human ceremony. Accepted deviations and boundary notes belong inside `docs/ARCHITECTURE.md`; do not add a second document.
- `AGENTS.md` should stay tiny. It can point agents to `docs/ARCHITECTURE.md`, but it should not duplicate the doctrine.
- Mechanical checks are recommendations only in v1. Do not build a universal cross-stack architecture validator.

## Steps

### 1. Add the shared architecture reference

Goal: Put the reusable doctrine, triggers, and document template in one shared place.

- [x] Add one shared reference for stack-agnostic architecture guidance, probably under `skills/shared/references/architecture/`.
- [x] Define boundary-affecting work: new or moved modules, packages, top-level folders, shared utilities, routes, app shells, workers, services, dependency registration, runtime entrypoints, or cross-module imports.
- [x] Define the small-fix exemption: local edits inside one existing boundary should not block on a missing architecture doc.
- [x] Define when a repo is non-trivial enough to need an architecture doc: framework app, monorepo, multiple packages, multiple binaries, multiple workers, multiple major top-level areas, or clear growth intent.
- [x] Include the `docs/ARCHITECTURE.md` template with sections for purpose, current system shape, module map, dependency rules, composition roots, shared-code rules, testing boundaries, architecture checks, and accepted deviations.
- [x] Include mechanical-check recommendations as optional examples only: Nx tags, ESLint import restrictions, ArchUnit, Import Linter, Go `internal/` and `cmd/`, or existing lint rules.

### 2. Create `$create-architecture`

Goal: Add a skill that can create or update a repo-local architecture doc without forcing a generic template onto every repo.

- [x] Add `skills/create-architecture/SKILL.md`.
- [x] Support existing repo mode: inspect the actual repo shape, entrypoints, module boundaries, dependency direction, test seams, and existing docs before writing `docs/ARCHITECTURE.md`.
- [x] Support greenfield mode: turn a product or stack brief into a stack-native architecture baseline before implementation starts.
- [x] Make the skill write a repo-specific architecture doc, not an architecture essay.
- [x] Keep durable boundary notes and accepted deviations inside `docs/ARCHITECTURE.md`.
- [x] Add `skills/create-architecture/agents/openai.yaml` if `$create-architecture` should appear as a launcher preset; otherwise leave launcher metadata out intentionally.

### 3. Wire architecture awareness into implementation skills

Goal: Make agents read the repo architecture only when it can change the implementation.

- [x] Teach `$deliver` to read `docs/ARCHITECTURE.md` before boundary-affecting implementation work when the file exists.
- [x] Teach `$execute-task` to read `docs/ARCHITECTURE.md` before boundary-affecting task execution when the file exists.
- [x] Teach `$plan-and-execute` to read `docs/ARCHITECTURE.md` before boundary-affecting planning or implementation when the file exists.
- [x] Tell these skills to update `docs/ARCHITECTURE.md` in the same run when they intentionally change a boundary.
- [x] Do not make these skills block small local fixes only because `docs/ARCHITECTURE.md` is missing.

### 4. Wire architecture awareness into bootstrap and review skills

Goal: Make architecture docs appear early enough to help, and keep them from becoming stale.

- [x] Teach `$bootstrap-repo-rules` to suggest or invoke `$create-architecture` for greenfield or non-trivial repos that lack `docs/ARCHITECTURE.md`.
- [x] Teach `$review-chain` to compare relevant code changes against `docs/ARCHITECTURE.md` when it exists.
- [x] Teach `$repo-sweep` to compare the repo against `docs/ARCHITECTURE.md` when it exists.
- [x] Have review workflows flag stale docs, missing modules, forbidden dependency edges, undocumented entrypoints, expired deviations, and shared-code drift.
- [x] Have `$repo-sweep` still report generic architecture smells when no architecture doc exists, but label them as inferred rather than contract drift.
- [x] Add only tiny AGENTS guidance if this repo owns a shared instruction surface: read `docs/ARCHITECTURE.md` before boundary-affecting work.

### 5. Make the convention discoverable and validated

Goal: Keep the new architecture workflow visible and prevent contract drift.

- [x] Add `$create-architecture` to the public README table and skill detail section.
- [x] Add skill metadata and plugin install coverage consistent with existing Prime Directive skills.
- [x] Update `skills/shared/references/contract-ownership.md` so the shared architecture reference owns the architecture doctrine and template.
- [x] Extend `scripts/validate-skill-contracts.py` to check the new skill, README entries, contract ownership, and the key architecture touchpoints in existing skills.
- [x] Run `python3 scripts/validate-skill-contracts.py`.
- [x] Run `git diff --check`.
- [x] Run `./scripts/install-codex-plugin.sh`.

## Resource: What Good Architecture Looks Like

These notes are source material for the new skill and shared architecture reference. They combine the Swift modular architecture note with the Deep Research synthesis, but the final guidance should stay stack-agnostic.

### Core principles

- Architecture is about ownership and allowed dependencies, not abstract layer names.
- Every major module, package, feature, service, or app area should have a clear purpose, public entrypoint, owner boundary, allowed dependencies, and forbidden dependencies.
- Keep domain or core logic dependency-light. It should not casually import UI, framework, transport, persistence, vendor SDKs, or app-shell code.
- Put integration at the edge. Network clients, databases, external APIs, routing, startup wiring, workers, CLI entrypoints, and framework-specific glue should live outside core policy code.
- Make dependency direction explicit. Outer code may depend inward; inner policy code should not depend outward unless the repo intentionally records that exception.
- Avoid feature-to-feature dependencies. Features should communicate through the composition root, callbacks, events, interfaces, shared domain types, or explicit service boundaries.
- Keep the main app, server startup, CLI command, or worker bootstrap as a small composition root. It wires concrete dependencies and feature entrypoints together; it should not collect business logic.
- Hide feature internals behind small public APIs such as builders, routes, commands, service interfaces, package exports, or module entrypoints.
- Prefer explicit dependency passing or constructor injection. Global containers, framework magic, and singletons can provide defaults, but tests and callers should be able to inject dependencies directly.
- Preserve test seams. A new boundary should have a believable unit, contract, module integration, or end-to-end test strategy that does not require booting the whole app for simple behavior.

### Module and folder shape

- Prefer feature boundaries first when the product is feature-shaped. Do not create new top-level technical buckets such as `components`, `services`, or `utils` unless the repo already uses that structure intentionally.
- Keep sibling foundation areas parallel when possible. For example, service/integration code, design/UI primitives, shared routing, and utility layers should not casually depend on each other.
- Keep shared code small, stable, and earned. A shared helper should usually have at least two real consumers or a framework-level reason to exist.
- Avoid generic `shared`, `common`, `utils`, and `helpers` dumping grounds. If the name does not explain ownership, the boundary is probably too weak.
- Do not over-modularize. Tiny repos, disposable spikes, one-off scripts, and local fixes do not need heavy architecture ceremony.
- Do not under-modularize growing repos. Framework apps, monorepos, multiple packages, multiple binaries, multiple workers, or multiple major top-level areas should usually record their architecture early.

### Architecture document shape

- `docs/ARCHITECTURE.md` should describe the repo as it actually exists, not copy a template.
- The document should name concrete paths, modules, packages, entrypoints, runtime roots, allowed dependency direction, shared-code rules, test seams, mechanical checks, and accepted deviations.
- The module map should be path-backed. For each major area, record its responsibility, public API or entrypoint, allowed dependencies, and forbidden dependencies.
- The document should identify composition roots: app bootstrap, route registration, `main` files, worker startup, service registration, CLI commands, schedulers, or task runners.
- Accepted deviations should be explicit. Record scope, reason, owner if known, date, and removal trigger.
- Keep durable boundary notes and exceptions in `docs/ARCHITECTURE.md` unless the repo already has its own convention.
- Update the architecture doc when a boundary changes: new module, new top-level folder, new shared utility, new dependency edge, new runtime entrypoint, changed routing/composition, or intentional exception.

### Agent behavior rules

- Before boundary-affecting work, read `docs/ARCHITECTURE.md` if it exists.
- Boundary-affecting work includes adding or moving modules, packages, top-level folders, shared utilities, routes, app shells, workers, services, dependency registrations, or cross-module imports.
- If the architecture doc is missing and the repo is non-trivial, create or update it before making the boundary change.
- If the work is a small local fix inside one existing boundary, do not block on a missing architecture doc.
- When code and `docs/ARCHITECTURE.md` disagree, do not silently follow stale docs. Report the mismatch or update the doc as part of the work.
- During review or repo sweep, compare the current code graph to the architecture doc and flag stale paths, missing modules, forbidden edges, undocumented entrypoints, expired deviations, and shared-code drift.
- When no architecture doc exists, repo sweep can still report architecture smells, but should label them as inferred rather than contract drift.

### Mechanical checks

- Recommend mechanical checks only when the ecosystem already has a low-risk, normal tool for the boundary.
- Good examples include Nx module-boundary tags, ESLint import restrictions, ArchUnit for JVM projects, Import Linter for Python, Go `internal/` and `cmd/` conventions, and existing lint rules.
- Do not build a universal cross-stack Prime Directive architecture validator in v1. That would become brittle and would likely produce false confidence.
