# Contract Ownership Refactor TDD

## Plain-Language Summary

Prime Directive should keep each workflow rule in one file. Other files should link to that rule instead of copying it.

The implementation will add a small ownership reference, reduce the most important duplicated sections, and add a script that checks the contracts that are easiest to validate automatically.

The work should not change what users type or how the skills behave. It should change how maintainers edit the repo and how CI catches obvious drift.

## Technical Summary

Add `skills/shared/references/contract-ownership.md` as the durable source for ownership conventions. Refactor the highest-risk docs so `plan-and-execute` remains a thin orchestrator and `task-file-contract.md` owns file/path/mode resolution without duplicating the full behavior of `$plan-refine`, `$plan-work`, `$execute-task`, review, deep research, and Pro analysis.

Add `scripts/validate-skill-contracts.py` using only Python stdlib. Wire it into `.github/workflows/validate.yml` and document it in README verification. The validator should check public skill metadata, README invocation-table consistency, ownership-table file existence, a required owner inventory, and narrow known stale-mirror patterns. Implementation must exercise both green-path validation and deliberate negative mutations so the script proves it can fail for the drift classes it claims to catch.

## Scope Alignment to PRD

- `FR-001` maps to the ownership reference and validator ownership-table checks.
- `FR-002` maps to `plan-and-execute` orchestration cleanup.
- `FR-003` maps to `task-file-contract.md` contract cleanup.
- `FR-004` maps to README/front matter modifier checks.
- `FR-005` maps to CI wiring.
- `FR-006` maps to installer validation and non-semantic workflow preservation.

## Current Technical Diagnosis

The repo is a markdown-first Codex plugin source repo. Public skills live under `skills/<skill-name>/SKILL.md`; shared references live under `skills/shared/references/`; scripts live under `scripts/`; CI currently runs `.github/workflows/validate.yml` to verify Codex installer idempotence.

There is no existing contract validator. README has a manually maintained skill invocation table. Public skill files have front matter plus `Supported modifiers` sections. The current duplication risk is highest around plan-and-execute composition, plan-refine challenger behavior, temporary artifact retention, deep-research and Pro gates, and finalization rules.

## Architecture / Approach

Use a simple documentation ownership model:

- Public skill files own public activation, modifiers, workflow sequencing unique to that skill, and concise composition instructions.
- Shared references own reusable contracts such as artifact paths, finalization gates, task management, review protocol, planning generation, deep research, and Pro escalation.
- Higher-level skills reference lower-level owner files for detailed behavior.
- Intentional mirrors are limited to short summaries needed for local readability.

The validator should remain conservative. It should catch deterministic metadata drift and known stale-mirror classes without attempting to understand arbitrary prose.

Known stale-mirror checks must be explicit. The implementation may hardcode this table or parse equivalent data from the ownership reference, but each check needs a stable error id:

| pattern_key | match_semantics | canonical_owner_path | allowed_summary_paths | allowed_gate_check_paths | prohibited_scope | error_id |
| --- | --- | --- | --- | --- | --- | --- |
| `plan-refine-challenge-schema` | file/block token check: `previous_reviewer_round_had_blocker_or_material`, or both `challenge_id` and `pressure_type` in the same markdown section/file, or `reviewer_dispositions` | `skills/plan-refine/SKILL.md` | `skills/shared/references/contract-ownership.md` | none until inventory proves a gate/check consumer | `skills/**/*.md` except owner and allowed paths | `PD-CONTRACT-MIRROR-PLAN-REFINE` |
| `deep-research-stamp-detail` | file/block token check: `Deep Research Completion Stamp` and `evidence_bar_met` in the same markdown section/file, or single-token line check for `evidence_bar_met: yes` | `skills/shared/references/planning/deep-research.md` | `skills/shared/references/analysis/pro-oracle-escalation.md`, `skills/shared/references/contract-ownership.md` | inventory may promote exact gate/check paths such as `skills/shared/references/planning/generate-tasks.md` or `skills/shared/references/planning/improve-plan.md` with reason | `skills/**/*.md` except owner and allowed paths | `PD-CONTRACT-MIRROR-DEEP-RESEARCH` |
| `pro-synthesis-stamp-detail` | file/block token check: `oracle_result_read` and `findings_reconciled` in the same markdown section/file, or single-token line check for `pro_synthesis_complete: yes` | `skills/shared/references/analysis/pro-oracle-escalation.md` | `skills/shared/references/contract-ownership.md` | inventory may promote exact gate/check paths such as `skills/shared/references/planning/generate-tasks.md` or `skills/shared/references/planning/improve-plan.md` with reason | `skills/**/*.md` except owner and allowed paths | `PD-CONTRACT-MIRROR-PRO` |
| `finalization-baseline-detail` | single-token line checks for `finalization-baseline-<plan-key>` and `git status --porcelain=v1 > "\$baseline_tmp"` | `skills/shared/references/execution/finalization-gate.md` | `skills/shared/references/execution/task-file-contract.md`, `skills/shared/references/contract-ownership.md` | inventory may promote exact gate/check paths that enforce finalization without duplicating the baseline command | `skills/**/*.md` except owner and allowed paths | `PD-CONTRACT-MIRROR-FINALIZATION` |

## System Boundaries / Source of Truth

`skills/shared/references/contract-ownership.md` is the source of truth for ownership conventions and contract-owner inventory.

The minimum required inventory is deterministic. The ownership reference and validator must use these exact `contract_key` values and owner paths:

| contract_key | owner_path | mirror_policy |
| --- | --- | --- |
| `public-skill-metadata` | `README.md; skills/*/SKILL.md` | README owns public overview; each skill owns its own front matter and supported modifiers; validator compares them. |
| `planning-intake` | `skills/shared/references/planning/socratic-planning.md` | Public skills may summarize direct or Socratic mode only. |
| `prd-generation` | `skills/shared/references/planning/create-prd.md` | Consumers reference PRD structure instead of copying it. |
| `tdd-generation` | `skills/shared/references/planning/create-tdd.md` | Consumers reference TDD structure instead of copying it. |
| `task-plan-generation` | `skills/shared/references/planning/generate-tasks.md` | Consumers reference task-plan structure instead of copying it. |
| `plan-improvement` | `skills/shared/references/planning/improve-plan.md` | Consumers may state that the improvement pass runs, not restate audit details. |
| `deep-research` | `skills/shared/references/planning/deep-research.md` | Consumers may state gate names only; evidence ledger and stamp details stay here. |
| `pro-analysis` | `skills/shared/references/analysis/pro-oracle-escalation.md` | Consumers may state synthesis gate names only; Pro ledger and stamp details stay here. |
| `task-file-contract` | `skills/shared/references/execution/task-file-contract.md` | Owns activations, plan-key resolution, artifact paths, temp paths, archive paths, and mode entry gates. |
| `task-management` | `skills/shared/references/execution/task-management.md` | Owns task-list lifecycle, one-shot worker cadence, temp sub-task contract shape, and cleanup phase. |
| `finalization-gate` | `skills/shared/references/execution/finalization-gate.md` | Owns baseline capture and terminal handoff checks. |
| `review-protocol` | `skills/shared/references/review/review-protocol.md` | Owns review topology, prompt profile selection, review logs, and final review/finalization sequencing. |
| `review-calibration` | `skills/shared/references/review/review-calibration.md` | Owns reviewer judgment examples. |
| `plan-refine` | `skills/plan-refine/SKILL.md` | Owns challenger/reviewer loop, challenge schema, severity gate, and stop discipline. |
| `plan-and-execute` | `skills/plan-and-execute/SKILL.md` | Owns orchestration order plus branch/PR defaults unique to the combined workflow. |
| `execute-task` | `skills/execute-task/SKILL.md` | Owns public execution activation and mode-level delegation into task management/review/finalization. |
| `harness-drift` | `skills/shared/references/harness-drift.md` | Owns drift-check report shape and decision rules. |
| `reasoning-budget` | `skills/shared/references/reasoning-budget.md` | Owns reasoning tier mapping by workflow role. |

`README.md` remains the public repo overview and skill invocation table, but it is validated against skill files rather than trusted manually.

Each public `skills/*/SKILL.md` remains the source of truth for that skill's public front matter and supported modifiers. The validator reads these files directly.

## Dependencies

- Python 3 from the runner environment.
- Existing shell scripts remain unchanged unless validation reveals installer assumptions.
- GitHub Actions continues using `actions/checkout@v4`.

## Route / API / Public Interface Changes

No runtime API changes.

Public skill invocations remain unchanged:

- `$plan-work`
- `$plan-refine`
- `$execute-task`
- `$plan-and-execute`
- `$review-chain`
- `$repo-sweep`
- existing other Prime Directive skills

The only new command surface is a developer validation command: `python3 scripts/validate-skill-contracts.py`.

## Data Model / Schema / Storage Changes

No application data model changes.

The ownership reference should use a simple markdown table so it is readable by humans and parseable by the validator:

`| contract_key | owner_path | consumers | mirror_policy |`

`owner_path` grammar is deterministic: semicolon-separated repo-relative literal paths or glob paths only. Literal paths must exist. Glob paths must match at least one file. Prose such as "plus", "front matter", or semantic qualifiers belongs in `mirror_policy`, not `owner_path`.

Stale-mirror inventory and validation must share the same scanner helper and semantics. Single-token checks may use line-oriented regex. Multi-token checks must be explicit file/block token checks and cannot rely on ambiguous `.*` across Markdown line breaks. The inventory artifact must report hits using the same scanner output that the validator will use. Any `allowed_gate/check` inventory result must be promoted into the final validator allowlist for that exact `pattern_key` with path and reason before hardcoding; otherwise it must be refactored or rejected.

## Technical Requirements

- `TDR-001`: Add an ownership reference that names owner files for major public skill and shared workflow contracts.
- `TDR-002`: Refactor `plan-and-execute` so detailed child behavior is referenced, not duplicated, while preserving its unique branch/PR/default continuation rules.
- `TDR-003`: Refactor `task-file-contract.md` so it owns activation/path/mode/file-resolution contracts and points detailed behavior to the owning workflow files.
- `TDR-004`: Add a Python stdlib validator that checks README skill rows against public skill files and their supported modifiers.
- `TDR-005`: Add validator checks that every owner path listed in the ownership table exists and that every exact required `contract_key` row is represented.
- `TDR-006`: Add narrow stale-mirror checks for known drift-prone detailed terms using the pattern owner/allowlist/error-id table above.
- `TDR-007`: Wire the validator into GitHub Actions and README verification.
- `TDR-008`: Preserve existing installer validation and run it locally before finalization.

## Ingestion / Backfill / Migration / Rollout Plan

No data migration is needed.

Rollout follows the `$plan-and-execute` existing non-base branch path. Before task `1.1`, the executor must run a branch preflight:

1. identify the current branch
2. verify it is not detached, `main`, `master`, or the resolved base branch
3. keep the branch without switching or renaming
4. run `gh pr list --head "$(git branch --show-current)" --json number,title,state,url` when `gh` is available, or record that open-PR lookup was unavailable
5. if an open PR exists and its title/scope does not match `contract-ownership-refactor`, stop for user direction unless explicit reuse approval is already recorded
6. commit the three planning artifacts on the current branch before implementation edits
7. keep `tasks/tmp/plan-refine-contract-ownership-refactor.md` through final full-branch review/finalization
8. require final handoff to name the existing-branch/no-default-PR path and any existing PR that received the new commits

If the branch becomes base/detached, unrelated dirty changes overlap the implementation surface before task `1.1`, or an open PR scope mismatch has no explicit reuse approval, stop for user direction.

## Failure Modes / Recovery / Rollback

- If the validator is too broad, it may block legitimate summaries. Keep pattern checks narrow and owner-scoped.
- If deduplication removes useful local orientation, maintainers may need to chase references too often. Keep tiny summaries in high-level skills where they explain sequence or a unique override.
- If README parsing is brittle, valid docs may fail CI. Use straightforward table parsing and clear error messages.
- If branch scope is mixed, the final handoff could hide that this work landed on a branch named for a different feature. Finalization must name the branch and PR behavior explicitly.
- Rollback is a normal git revert of the docs/script/CI changes.

## Operational Readiness

The validator runs in CI on pull requests and pushes to main. It should print actionable error messages naming the file and failed contract.

The validator should require no network, credentials, generated files, or installed Python packages.

## Verification and Test Strategy

Expected checks:

- `python3 scripts/validate-skill-contracts.py`
- a stale-mirror hit inventory generated before hardcoding validator allowlists. For each planned stale-mirror pattern, record every current hit as `owner`, `allowed_summary`, `allowed_gate/check`, or `refactor/remove`, using the same scanner helper and semantics the validator will use. Multi-token checks must be reported as file/block token checks rather than plain line-regex results.
- negative validator checks that temporarily introduce: a README modifier mismatch, a README non-flag option mismatch, a no-modifier row mismatch, a missing owner path, a missing required owner inventory row, and a banned stale-mirror phrase outside an allowed owner file. Each case must be recorded in `tasks/tmp/validator-negative-evidence-contract-ownership-refactor.md` with mutation class, command, nonzero exit status, stable error id plus file or contract key in output, relevant output excerpt, revert confirmation with `git diff --exit-code -- <mutated-files>` or equivalent, and a final clean `python3 scripts/validate-skill-contracts.py` run. Keep that proof artifact through final full-branch review and finalization, then delete it unless artifact preservation was requested.
- `HOME="$(mktemp -d)" ./scripts/install-codex-plugin.sh`
- `HOME="$(mktemp -d)" ./scripts/install-claude-skills.sh`
- CI workflow includes the validator before or alongside installer idempotence checks.

Test-first note: the validator is code-bearing and practically testable by running it before and after the doc changes plus temporary negative mutations. It may not be useful to commit a failing test file first because the validator itself is the test harness; the sub-task contract should record the red/green exception for script introduction.
