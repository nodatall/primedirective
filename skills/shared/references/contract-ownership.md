# Contract Ownership

Prime Directive contracts should have one owner. Consumers may include short orientation summaries, but detailed behavior belongs in the owner file.

## Rules

- Public skills own their activation, supported modifiers, and unique orchestration choices.
- Shared references own reusable contracts that multiple skills compose.
- Higher-level skills reference lower-level owners instead of restating detailed child behavior.
- Tiny mirrors are allowed only when they help local readability; they should name the owner path.
- Gate/check files may repeat a small condition when they enforce that condition. They should not copy the owner contract's schema, workflow, or rationale.
- Validator-enforced paths use semicolon-separated repo-relative literal paths or globs in `owner_path`.

## Owner Inventory

| contract_key | owner_path | consumers | mirror_policy |
| --- | --- | --- | --- |
| `public-skill-metadata` | `README.md; skills/*/SKILL.md` | README, installer scripts, skill users | README owns public overview; each skill owns its front matter and supported modifiers; validator compares them. |
| `planning-intake` | `skills/shared/references/planning/socratic-planning.md` | `skills/plan-work/SKILL.md`, `skills/plan-and-execute/SKILL.md` | Consumers may summarize direct or Socratic mode only. |
| `prd-generation` | `skills/shared/references/planning/create-prd.md` | `skills/plan-work/SKILL.md`, `skills/plan-and-execute/SKILL.md` | Consumers reference PRD generation rather than copying structure. |
| `tdd-generation` | `skills/shared/references/planning/create-tdd.md` | `skills/plan-work/SKILL.md`, `skills/plan-and-execute/SKILL.md` | Consumers reference TDD generation rather than copying structure. |
| `task-plan-generation` | `skills/shared/references/planning/generate-tasks.md` | `skills/plan-work/SKILL.md`, `skills/plan-and-execute/SKILL.md` | Consumers reference task generation rather than copying structure. |
| `plan-improvement` | `skills/shared/references/planning/improve-plan.md` | `skills/plan-work/SKILL.md`, `skills/plan-refine/SKILL.md` | Consumers may state that improvement/audit runs; audit details stay here. |
| `deep-research` | `skills/shared/references/planning/deep-research.md` | `skills/plan-work/SKILL.md`, `skills/plan-and-execute/SKILL.md`, `skills/plan-refine/SKILL.md`, `skills/shared/references/planning/generate-tasks.md`, `skills/shared/references/planning/improve-plan.md` | Consumers may name gates and enforce stop checks; evidence ledger and stamp details stay here. |
| `pro-analysis` | `skills/shared/references/analysis/pro-oracle-escalation.md` | `skills/first-principles-mode/SKILL.md`, `skills/plan-and-execute/SKILL.md`, `skills/repo-sweep/SKILL.md`, `skills/shared/references/planning/generate-tasks.md`, `skills/shared/references/planning/improve-plan.md` | Consumers may name gates and enforce stop checks; Pro ledger and stamp details stay here. |
| `task-file-contract` | `skills/shared/references/execution/task-file-contract.md` | `skills/execute-task/SKILL.md`, `skills/plan-and-execute/SKILL.md`, `skills/plan-refine/SKILL.md`, `skills/review-chain/SKILL.md` | Owns activations, plan-key resolution, artifact paths, temp paths, archive paths, and mode entry gates. |
| `task-management` | `skills/shared/references/execution/task-management.md` | `skills/execute-task/SKILL.md`, `skills/plan-and-execute/SKILL.md` | Owns task-list lifecycle, one-shot worker cadence, temp sub-task contract shape, and cleanup phase. |
| `finalization-gate` | `skills/shared/references/execution/finalization-gate.md` | `skills/execute-task/SKILL.md`, `skills/plan-and-execute/SKILL.md`, `skills/shared/references/review/review-protocol.md` | Owns baseline capture and terminal handoff checks; consumers may enforce the gate. |
| `review-protocol` | `skills/shared/references/review/review-protocol.md` | `skills/execute-task/SKILL.md`, `skills/review-chain/SKILL.md`, `skills/plan-and-execute/SKILL.md`, `skills/repo-sweep/SKILL.md` | Owns review topology, prompt profile selection, review logs, and final review/finalization sequencing. |
| `review-calibration` | `skills/shared/references/review/review-calibration.md` | `skills/execute-task/SKILL.md`, `skills/review-chain/SKILL.md`, `skills/repo-sweep/SKILL.md` | Owns reviewer judgment examples. |
| `plan-refine` | `skills/plan-refine/SKILL.md` | `skills/plan-and-execute/SKILL.md`, `skills/shared/references/execution/task-file-contract.md` | Owns challenger/reviewer loop, challenge schema, severity gate, and stop discipline. |
| `plan-and-execute` | `skills/plan-and-execute/SKILL.md` | README, skill users | Owns orchestration order plus branch/PR defaults unique to the combined workflow. |
| `execute-task` | `skills/execute-task/SKILL.md` | `skills/plan-and-execute/SKILL.md`, skill users | Owns public execution activation and mode-level delegation into task management/review/finalization. |
| `harness-drift` | `skills/shared/references/harness-drift.md` | `skills/plan-work/SKILL.md`, `skills/execute-task/SKILL.md`, `skills/plan-and-execute/SKILL.md` | Owns drift-check report shape and decision rules. |
| `reasoning-budget` | `skills/shared/references/reasoning-budget.md` | all Prime Directive workflow skills | Owns reasoning tier mapping by workflow role. |

## Validator Mirror Checks

These checks are intentionally narrow. They catch known stale mirrors without trying to audit the whole skill graph.

| pattern_key | match_semantics | canonical_owner_path | allowed_summary_paths | allowed_gate_check_paths | error_id |
| --- | --- | --- | --- | --- | --- |
| `plan-refine-challenge-schema` | file/block token check for `previous_reviewer_round_had_blocker_or_material`, `reviewer_dispositions`, or both `challenge_id` and `pressure_type` in the same file | `skills/plan-refine/SKILL.md` | `skills/shared/references/contract-ownership.md` | none | `PD-CONTRACT-MIRROR-PLAN-REFINE` |
| `deep-research-stamp-detail` | file/block token check for `Deep Research Completion Stamp` plus `evidence_bar_met`, or line token `evidence_bar_met: yes` | `skills/shared/references/planning/deep-research.md` | `skills/shared/references/analysis/pro-oracle-escalation.md`, `skills/shared/references/contract-ownership.md` | `skills/plan-and-execute/SKILL.md`, `skills/plan-refine/SKILL.md`, `skills/shared/references/planning/generate-tasks.md`, `skills/shared/references/planning/improve-plan.md` | `PD-CONTRACT-MIRROR-DEEP-RESEARCH` |
| `pro-synthesis-stamp-detail` | file/block token check for `oracle_result_read` plus `findings_reconciled`, or line token `pro_synthesis_complete: yes` | `skills/shared/references/analysis/pro-oracle-escalation.md` | `skills/shared/references/contract-ownership.md` | `skills/plan-and-execute/SKILL.md`, `skills/plan-refine/SKILL.md`, `skills/shared/references/planning/generate-tasks.md`, `skills/shared/references/planning/improve-plan.md` | `PD-CONTRACT-MIRROR-PRO` |
| `finalization-baseline-detail` | line tokens `finalization-baseline-<plan-key>` or `git status --porcelain=v1 > "$baseline_tmp"` | `skills/shared/references/execution/finalization-gate.md` | `skills/shared/references/execution/task-file-contract.md`, `skills/shared/references/contract-ownership.md` | `skills/shared/references/review/review-protocol.md` | `PD-CONTRACT-MIRROR-FINALIZATION` |
