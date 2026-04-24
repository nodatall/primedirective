See `skills/shared/references/execution/task-management.md` for execution workflow and review guidelines.

# Contract Ownership Refactor

## Scope Summary

This plan makes Prime Directive workflow contracts owned in one place, reduces detailed mirrors in the most drift-prone docs, and adds a lightweight validator to catch metadata and stale-mirror drift. The highest-risk concerns are over-pruning useful local context, making the validator too broad, and silently landing the work on a branch whose name belongs to prior challenger-lane work.

## Relevant Files

- `skills/shared/references/contract-ownership.md` - New ownership convention and contract inventory.
- `skills/plan-and-execute/SKILL.md` - High-level orchestrator that should reference lower-level owned contracts.
- `skills/shared/references/execution/task-file-contract.md` - Canonical activation, path, mode, temp-file, and archive-file contract.
- `skills/shared/references/execution/task-management.md` - Owned execution task-list behavior referenced by higher-level docs.
- `skills/shared/references/review/review-protocol.md` - Owned review and finalization workflow behavior.
- `README.md` - Public skill invocation table and verification commands.
- `.github/workflows/validate.yml` - CI wiring for the new validator.
- `scripts/validate-skill-contracts.py` - New stdlib validator.

## Task Ordering Notes

- Before task `1.1`, run branch preflight: identify the current branch and upstream, verify it is non-base and not detached, look up any open PR for the branch, and keep it without switching or renaming only when the branch/PR disposition is safe. If an open PR exists and its title/scope does not match `contract-ownership-refactor`, stop for user direction unless explicit reuse approval is already recorded. If continuing, commit the three planning artifacts before implementation edits and retain the refinement log through final review/finalization. Final handoff must disclose the existing-branch/no-default-PR path and any existing PR updated by the commits.
- Add the ownership convention before refactoring consumers so the docs have a stable reference target.
- Refactor docs before writing stale-mirror checks so the validator can encode the intended final ownership model.
- Keep all public skill names and modifier lists unchanged.
- Use focused validation for the script, then run installer checks and final validation before review.

## Tasks

- [x] 1.0 Establish contract ownership documentation
  - covers_prd: `FR-001`, `FR-006`
  - covers_tdd: `TDR-001`
  - [x] 1.1 Add the shared contract ownership reference
    - covers_prd: `FR-001`
    - covers_tdd: `TDR-001`
    - output: `skills/shared/references/contract-ownership.md`
    - verify: `test -f skills/shared/references/contract-ownership.md && rg -n "contract_key \\| owner_path \\| consumers \\| mirror_policy|public-skill-metadata|planning-intake|prd-generation|tdd-generation|task-plan-generation|plan-improvement|deep-research|pro-analysis|task-file-contract|task-management|finalization-gate|review-protocol|review-calibration|plan-refine|plan-and-execute|execute-task|harness-drift|reasoning-budget" skills/shared/references/contract-ownership.md`
    - done_when: The reference names exact `contract_key`, parseable semicolon-separated `owner_path`, consumers, and mirror policy rows for every required owner inventory key from the TDD.

- [x] 2.0 Refactor drift-prone docs around the ownership model
  - covers_prd: `FR-002`, `FR-003`, `FR-006`
  - covers_tdd: `TDR-002`, `TDR-003`
  - [x] 2.1 Slim `plan-and-execute` into a thin orchestrator with owner references
    - covers_prd: `FR-002`, `FR-006`
    - covers_tdd: `TDR-002`
    - output: `skills/plan-and-execute/SKILL.md`
    - verify: `rg -n "plan-work|plan-refine|execute-task|finalization-gate|contract-ownership" skills/plan-and-execute/SKILL.md`
    - done_when: The skill preserves activation, branch/PR defaults, and sequencing while routing detailed child behavior to owner files.
  - [x] 2.2 Refactor the task-file contract to own paths and mode gates without duplicating child workflows
    - covers_prd: `FR-003`, `FR-006`
    - covers_tdd: `TDR-003`
    - output: `skills/shared/references/execution/task-file-contract.md`
    - verify: `rg -n "Owner references|Plan key resolution|Temporary workflow files|Archive workflow files" skills/shared/references/execution/task-file-contract.md && ! rg -n "previous_reviewer_round_had_blocker_or_material|pro_synthesis_complete: yes|Deep Research Completion Stamp.*evidence_bar_met" skills/shared/references/execution/task-file-contract.md`
    - done_when: The reference remains canonical for activations, plan-key resolution, artifact paths, temp/archive paths, and mode entry gates, but child workflow details point to their owners and banned detailed child terms are absent.
  - [x] 2.3 Adjust nearby references for coherent cross-links and mirror policy
    - covers_prd: `FR-001`, `FR-006`
    - covers_tdd: `TDR-001`, `TDR-003`
    - output: `skills/shared/references/execution/task-management.md`, `skills/shared/references/review/review-protocol.md`, or other directly affected shared references if needed
    - verify: `rg -n "contract-ownership|Task File Contract|finalization-gate|review-protocol" skills/shared/references skills/*.md`
    - done_when: Cross-references point to owner files and no edited reference becomes a second owner for a detailed contract.

- [x] 3.0 Add automated drift validation
  - covers_prd: `FR-004`, `FR-005`, `FR-006`
  - covers_tdd: `TDR-004`, `TDR-005`, `TDR-006`, `TDR-007`, `TDR-008`
  - [x] 3.1 Inventory stale-mirror hits and finalize the allowlist
    - covers_prd: `FR-005`, `FR-006`
    - covers_tdd: `TDR-006`
    - output: `tasks/tmp/stale-mirror-inventory-contract-ownership-refactor.md`
    - verify: `python3 scripts/validate-skill-contracts.py --inventory-only` after the script's shared scanner helper exists, or an equivalent temporary scanner using the same file/block token semantics later copied into the validator
    - done_when: Every current hit for the planned stale-mirror patterns is recorded as `owner`, `allowed_summary`, `allowed_gate/check`, or `refactor/remove`; multi-token checks use the same file/block scanner semantics as the final validator; every `allowed_gate/check` hit is promoted into the final validator allowlist with exact path, pattern key, and reason; and the final validator allowlist follows that inventory.
  - [x] 3.2 Add the contract validator script
    - covers_prd: `FR-004`, `FR-005`
    - covers_tdd: `TDR-004`, `TDR-005`, `TDR-006`
    - output: `scripts/validate-skill-contracts.py`
    - verify: `python3 scripts/validate-skill-contracts.py`
    - done_when: The script checks README/front matter skill metadata, supported modifiers, ownership-table owner paths, exact required `contract_key` rows, and narrow known stale-mirror patterns with stable error ids.
  - [x] 3.3 Exercise validator negative cases without leaving mutations behind
    - covers_prd: `FR-004`, `FR-005`
    - covers_tdd: `TDR-004`, `TDR-005`, `TDR-006`
    - output: `scripts/validate-skill-contracts.py`, `tasks/tmp/validator-negative-evidence-contract-ownership-refactor.md`, temporary local mutations reverted before commit
    - verify: `python3 scripts/validate-skill-contracts.py` plus temporary failure checks for README flag mismatch, README non-flag option mismatch, no-modifier row mismatch, missing owner path, missing required owner row, and banned stale-mirror phrase
    - done_when: Each negative case is recorded in `tasks/tmp/validator-negative-evidence-contract-ownership-refactor.md` with mutation class, command, nonzero exit status, stable error id plus file or contract key, relevant output excerpt, revert confirmation with `git diff --exit-code -- <mutated-files>` or equivalent, and the final clean validator run passes. Keep the proof through final full-branch review/finalization, then delete it unless preservation was requested.
  - [x] 3.4 Wire validator into README and CI
    - covers_prd: `FR-004`, `FR-005`, `FR-006`
    - covers_tdd: `TDR-007`, `TDR-008`
    - output: `README.md`, `.github/workflows/validate.yml`
    - verify: `python3 scripts/validate-skill-contracts.py && rg -n "validate-skill-contracts" README.md .github/workflows/validate.yml`
    - done_when: Developers and CI both run the validator as part of the documented verification surface.

- [x] 4.0 Validate, review, and finalize
  - covers_prd: `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-006`
  - covers_tdd: `TDR-001`, `TDR-002`, `TDR-003`, `TDR-004`, `TDR-005`, `TDR-006`, `TDR-007`, `TDR-008`
  - [x] 4.1 Run final repo validation and archive the planning artifacts
    - covers_prd: `FR-006`
    - covers_tdd: `TDR-008`
    - output: `tasks/archive/2026-04-24-contract-ownership-refactor/`
    - verify: `python3 scripts/validate-skill-contracts.py && HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh && HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh`
    - done_when: All tasks are checked, all three planning artifacts are archived, temp files are cleaned unless needed for finalization, and final validation passes.
