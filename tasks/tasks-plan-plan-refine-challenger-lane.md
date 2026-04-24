See `skills/shared/references/execution/task-management.md` for execution workflow and review guidelines.

# Plan Refine Challenger Lane

## Scope Summary

- Add an internal adversarial challenger lane to `$plan-refine` without changing public invocation syntax.
- Keep reviewer-owned severity and stop rules, while making challenger objections auditable through challenge IDs and dispositions.
- Mirror only composition-relevant behavior into shared contracts and keep `$plan-and-execute` as a thin orchestrator.
- Highest-risk concerns: duplicated reviewer behavior, challenger objections becoming unreviewed edits, vague deferrals hiding blocker-grade issues, and `$plan-and-execute` continuing after hard-stop refinement failures.
- Do not invent helper/function names for this markdown-only workflow change; document behavior in skill-contract language.

## Relevant Files

- `skills/plan-refine/SKILL.md` - Primary workflow contract for challenger lane, reviewer handoff, stop rule, and output contract.
- `skills/shared/references/execution/task-file-contract.md` - Shared composition contract for `$plan-refine` and `$plan-and-execute --refine-plan`.
- `skills/plan-and-execute/SKILL.md` - Thin orchestration wording for refinement behavior, hard stops, and log retention.
- `README.md` - Public invocation surface; should remain stable unless wording needs a non-modifier clarification.
- `scripts/install-codex-plugin.sh` - Existing installer validation surface.
- `.github/workflows/validate.yml` - Existing CI validation surface.

## Task Ordering Notes

- Update `$plan-refine` first because it is the source of truth.
- Then mirror only composition-relevant behavior in `task-file-contract.md`.
- Then update `$plan-and-execute` thin wording so orchestration aligns without duplicating challenger schema.
- Run validation after all docs are updated.
- Failing-test-first is not practical for this documentation-only change because there is no executable parser for skill semantics. Use pre-change inspection as the red proxy and run installer/text validation after edits.

## Tasks

- [ ] 1.0 Add challenger lane to `$plan-refine`
  - covers_prd: `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-006`, `FR-008`, `FR-009`, `FR-010`, `FR-012`
  - covers_tdd: `TDR-001`, `TDR-002`, `TDR-003`, `TDR-004`, `TDR-005`, `TDR-011`, `TDR-012`
  - [ ] 1.1 Define the challenger role, applicable-round cadence, no-edit rule, and reasoning/subagent requirements in `skills/plan-refine/SKILL.md`.
    - covers_prd: `FR-001`, `FR-002`, `FR-003`, `FR-007`, `FR-008`
    - covers_tdd: `TDR-001`, `TDR-002`, `TDR-004`
    - output: `skills/plan-refine/SKILL.md`
    - verify: `rg -n "challenger|round == 1|previous_reviewer_round_had_blocker_or_material|no_material_challenges_found" skills/plan-refine/SKILL.md`
    - done_when: The workflow clearly runs a fresh read-only challenger in round 1 and later only when the previous reviewer round had blocker/material findings.
  - [ ] 1.2 Add the challenge brief schema, valid empty-brief behavior, reviewer normal-audit-first handoff, challenge ID dispositions, and direct-edit prohibition.
    - covers_prd: `FR-002`, `FR-004`, `FR-005`, `FR-006`, `FR-009`, `FR-010`
    - covers_tdd: `TDR-003`, `TDR-004`, `TDR-005`, `TDR-012`
    - output: `skills/plan-refine/SKILL.md`
    - verify: `rg -n "challenge_id|deferred_with_owner|promoted_to_finding|normal.*audit|reviewer owns severity" skills/plan-refine/SKILL.md`
    - done_when: Challenger objections cannot become edits without reviewer promotion, every challenge ID must be dispositioned, and blocker-grade risks cannot be vaguely deferred.
  - [ ] 1.3 Preserve research/Pro-backed decisions and update final output/log rules for challenger-sourced fixes or accepted residual challenge risks.
    - covers_prd: `FR-005`, `FR-008`, `FR-012`
    - covers_tdd: `TDR-003`, `TDR-011`, `TDR-012`
    - output: `skills/plan-refine/SKILL.md`
    - verify: `rg -n "research-backed|Pro-backed|challenger-sourced|residual.*challenge|final full-branch review|finalization|plan-refine-<plan-key>" skills/plan-refine/SKILL.md`
    - done_when: Challenger context receives the same research/Pro evidence as the reviewer, final summaries can surface material challenger-sourced fixes or accepted challenge risks, and `$plan-and-execute --refine-plan` keeps the refinement log through final full-branch review and finalization before cleanup unless preservation is active.

- [ ] 2.0 Mirror composition-relevant refinement behavior
  - covers_prd: `FR-006`, `FR-007`, `FR-011`, `FR-012`, `FR-013`
  - covers_tdd: `TDR-006`, `TDR-009`, `TDR-010`, `TDR-011`, `TDR-013`
  - [ ] 2.1 Update `task-file-contract.md` with composition-relevant challenger cadence, subagent requirements, reviewer-owned stop rule, disposition logging, hard-stop outcomes, and `$plan-and-execute` refinement-log retention.
    - covers_prd: `FR-006`, `FR-011`, `FR-012`, `FR-013`
    - covers_tdd: `TDR-006`, `TDR-009`, `TDR-010`, `TDR-011`, `TDR-013`
    - output: `skills/shared/references/execution/task-file-contract.md`
    - verify: `rg -n "challenger|hard-stop|recoverable|unresolved reviewer blocker|plan-refine-<plan-key>" skills/shared/references/execution/task-file-contract.md`
    - done_when: Shared contract mirrors only behavior needed by orchestration, does not duplicate the full challenge brief schema, and treats max-round stops with unresolved reviewer blocker/material findings as hard stops.
  - [ ] 2.2 Update `skills/plan-and-execute/SKILL.md` thin wording so `--refine-plan` references normal `$plan-refine` behavior, internal challenger lane, reviewer-owned severity gate, hard-stop outcomes, and log availability through final review/finalization.
    - covers_prd: `FR-007`, `FR-011`, `FR-012`, `FR-013`
    - covers_tdd: `TDR-007`, `TDR-009`, `TDR-010`, `TDR-011`, `TDR-013`
    - output: `skills/plan-and-execute/SKILL.md`
    - verify: `rg -n "challenger|reviewer-owned|hard-stop|recoverable|unresolved reviewer blocker|refinement log" skills/plan-and-execute/SKILL.md`
    - done_when: `$plan-and-execute` remains a thin orchestrator, no longer describes refinement as reviewer-only, and can continue only after clean refinement success or recoverable churn with no unresolved reviewer blocker/material findings.

- [ ] 3.0 Validate, install, review, and archive
  - covers_prd: `FR-007`
  - covers_tdd: `TDR-008`
  - [ ] 3.1 Run text and installer validation, then inspect public invocation surfaces for unintended syntax changes.
    - covers_prd: `FR-007`
    - covers_tdd: `TDR-008`
    - output: validation evidence in final summary and task checklist
    - verify: `git diff --check && tmp_home="$(mktemp -d)" && HOME="$tmp_home" ./scripts/install-codex-plugin.sh && HOME="$tmp_home" ./scripts/install-codex-plugin.sh && ./scripts/install-codex-plugin.sh`
    - done_when: Validation passes, README invocation syntax remains unchanged, and changed planning artifacts are ready to archive.
