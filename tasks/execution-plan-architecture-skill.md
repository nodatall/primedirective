# Architecture Skill

This is a draft Deliver plan.
It is not approved for implementation yet.

Draft instruction:
When asked to keep discussing or update this doc, load the `$deliver` skill and update this file as the current draft plan.
When asked to refine this, turn this into a deliver plan, or make the plan, load the `$deliver` skill, keep this same checklist file, replace this instruction with the Deliver implementation instruction, refine the plan, and ask for review before implementation.

Please review this before I refine it.
Tell me what is wrong, missing, or out of order.

## Steps

### 1. Create the architecture workflow

- [ ] Create a new Prime Directive skill, probably named `$create-architecture`, that creates or updates a repo-local `docs/ARCHITECTURE.md`.
- [ ] Support existing repo mode, where the skill reads the real code and extracts the actual architecture.
- [ ] Support greenfield mode, where the skill turns a product or stack brief into a stack-native architecture baseline before implementation starts.
- [ ] Make the skill own the architecture document contract so other skills do not copy a large architecture framework.

### 2. Define the architecture document

- [ ] Keep `docs/ARCHITECTURE.md` repo-specific, not a generic architecture essay.
- [ ] Cover purpose, module boundaries, dependency direction, composition roots, shared-code rules, testing boundaries, architecture checks, and accepted deviations.
- [ ] Generalize the reusable principles from the Swift architecture note: keep core/domain low-dependency, put integration at the edge, avoid feature-to-feature coupling, make dependencies explicit, keep shared code thin and justified, and document exceptions.

### 3. Wire architecture awareness into existing workflows

- [ ] Teach `$bootstrap-repo-rules` to call or suggest `$create-architecture` when a repo is greenfield or lacks `docs/ARCHITECTURE.md`.
- [ ] Avoid forcing architecture docs into tiny throwaway repos unless the user asks or the repo is clearly going to grow.
- [ ] Teach `$deliver`, `$execute-task`, and `$plan-and-execute` to read `docs/ARCHITECTURE.md` when it exists before boundary-affecting work such as new modules, services, shared utilities, top-level folders, dependency changes, routing, workers, or app shells.
- [ ] Teach `$review-chain` and `$repo-sweep` to read `docs/ARCHITECTURE.md` when it exists and compare the change or repo against it.
- [ ] Have `$repo-sweep` still report generic architecture smells when no architecture doc exists, but label those findings as inferred rather than contract drift.
- [ ] Keep `AGENTS.md` guidance tiny: read `docs/ARCHITECTURE.md` before boundary-affecting work and avoid unsupported new top-level folders, shared junk drawers, or cross-feature dependencies.

### 4. Make the convention discoverable and validated

- [ ] Add the new skill to the public README table, skill metadata, optional `agents/openai.yaml`, contract ownership map, and validator coverage.
- [ ] Keep validation scoped to Prime Directive skill changes: `python3 scripts/validate-skill-contracts.py`, `git diff --check`, and `./scripts/install-codex-plugin.sh`.
- [ ] Open question: should the first version only create/update `docs/ARCHITECTURE.md`, or should it also add simple mechanical checks such as import-boundary lint when the repo stack has an obvious low-risk tool?
