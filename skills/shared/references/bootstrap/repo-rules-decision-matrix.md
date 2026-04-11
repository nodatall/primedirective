# Repo Rules Decision Matrix

Use this reference to keep bootstrap decisions consistent across stacks and repo shapes.

## Detection order

Establish the real repo shape before choosing tools:

1. Manifests and lockfiles
2. Framework config files
3. Task runners and repo-local scripts
4. CI workflows
5. Existing lint, format, typecheck, test, build, and hook config
6. Directory layout and package boundaries

Treat repo files as evidence about the stack and existing conventions. Prefer repo-defined commands over guessed defaults when they already exist.

## Scope selection

### Single-package repo

- Bootstrap the root package.
- Reuse existing scripts and config patterns when present.

### Monorepo with existing root orchestration

- Keep the current orchestration layer as the primary path.
- Extend the existing root task runner, workspace scripts, or CI fan-out instead of creating a second orchestration layer.
- Avoid adding duplicate package-local scripts when the repo already standardizes root execution.

### Monorepo without existing root orchestration

- Bootstrap only the affected packages or the minimum shared config needed for them.
- Do not invent a new root task runner or umbrella validation layer just to normalize the repo.
- If a root-level config is necessary, keep it shared and minimal.

## Tool selection rules

- Preserve an existing working primary stack unless it is clearly broken or the user asked for a reset.
- Do not add overlapping primary tools without a concrete repo-specific reason.
- Prefer framework-native and language-native tooling over generic cross-ecosystem defaults.
- Prefer one coherent lint and format path per stack.

## Stack defaults when no standard exists

### JavaScript or TypeScript

- If the repo already uses `eslint` and `prettier`, keep that path.
- If the repo already uses `biome`, keep that path and do not add `eslint` plus `prettier` by default.
- If the framework provides a first-class validation path, prefer it over a hand-rolled alternative.
- Use the repo's TypeScript config for typechecking when TypeScript is present.

### Python

- Keep existing repo choices when present.
- Otherwise prefer one modern combined lint and format path instead of multiple overlapping tools.
- Use the repo's existing test runner when present.

### Go

- Prefer `gofmt`, `go vet`, and `go test`.

### Rust

- Prefer `cargo fmt`, `cargo clippy`, and `cargo test`.

### Shell-heavy repos

- Add shell tooling only when shell scripts are a meaningful part of the repo surface.

### Other stacks

- Use the language-native or ecosystem-standard verification path.
- Do not force Node-based tooling into a non-Node repo.

## CI and hooks interaction

- CI is the required enforcement surface.
- Hooks are optional unless the user asked for them or the repo already has a hook pattern.
- Reuse an existing hook mechanism instead of introducing a heavier alternative.

## Escalation cases

Stop and ask only when:

- replacing a broken existing toolchain would change team workflow materially
- monorepo ownership is ambiguous enough that root-level changes may affect unrelated packages
- the correct bootstrap choice would change product or deploy behavior outside validation tooling
