# Dependency Audit Checklist

Use this reference for dependency, supply-chain, and package-manager hygiene in repo-wide sweeps and production-readiness reviews.

## Baseline Inventory

Identify package managers and lockfiles before running checks:

- JavaScript/TypeScript: `package.json`, `package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`, `bun.lockb`.
- Python: `pyproject.toml`, `requirements*.txt`, `poetry.lock`, `uv.lock`, `Pipfile.lock`.
- Rust: `Cargo.toml`, `Cargo.lock`.
- Ruby: `Gemfile`, `Gemfile.lock`.
- Go: `go.mod`, `go.sum`.
- Swift: `Package.swift`, `Package.resolved`, Xcode project package references.
- Docker and CI: Dockerfiles, compose files, workflow actions, setup scripts, and base images.

Record which ecosystems are present and which lockfiles are missing.

## Checks

Run the strongest available safe checks for the detected stack. Prefer repo-defined scripts when they already exist.

- Known vulnerabilities: `npm audit`, `pnpm audit`, `yarn npm audit`, `bun audit`, `pip-audit`, `uv pip audit`, `poetry audit`, `cargo audit`, `bundle audit`, `govulncheck`, or ecosystem equivalents when installed.
- Outdated or abandoned critical dependencies when the package manager can report them without a risky upgrade.
- Lockfile consistency: install commands should fail or warn when manifests and lockfiles drift.
- Install script risk: note postinstall/build scripts, binary downloads, native builds, and unpinned remote installers.
- CI action pinning: inspect whether GitHub Actions and reusable workflows are pinned to immutable SHAs or trusted version tags.
- Container supply chain: inspect base image tags, privileged containers, root runtime defaults, and whether image scanning such as Trivy or Grype is available.
- License/compliance posture: identify whether the repo has a license policy or tooling. Do not invent legal conclusions; report missing policy as a residual risk or human decision.
- SBOM posture: identify whether the repo can generate an SBOM through existing tooling such as Syft, CycloneDX, package-manager export, or CI.

## Tool Availability

If a scanner is unavailable, do not install global tools without user approval. Record the skipped command, why it was skipped, and the next concrete command a maintainer could run.

If a scan requires network access and the environment blocks it, classify the result as `residual risk` unless local lockfile evidence proves the issue either way.

## Reporting

Dependency findings use the shared finding disposition shape:

- `fix`: verified vulnerable or unsafe dependency state with a clear local repair that does not change product behavior unexpectedly.
- `needs human decision`: upgrade, license, base-image, or support-policy choices that can change compatibility, cost, or legal posture.
- `residual risk`: scanner unavailable, network blocked, missing credentials, unsupported ecosystem, or unverified SBOM/license posture.
- `no action`: checked and either clean, not applicable, or protected by an equivalent stronger control.
