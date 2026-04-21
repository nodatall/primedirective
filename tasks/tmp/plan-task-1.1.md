# Sub-task Contract: 1.1

goal: Add concrete source-count, source-type, source-family, source-authority, source-conflict, version-first, and privacy rules to the deep-research contract.

in_scope:
- Update `skills/shared/references/planning/deep-research.md`.
- Define Evidence Ledger source fields and count eligibility.
- Define source authority/conflict handling, follow-up pass counting, version-first stack discovery, and external-query privacy boundaries.

out_of_scope:
- Do not update downstream plan-work, task generation, Pro, or refine-plan rules in this slice.
- Do not add scripts or automated parsers.

surfaces:
- `skills/shared/references/planning/deep-research.md`

acceptance_checks:
- The file names the Evidence Ledger fields required by `FR-001` and `TDR-001`.
- The file states which source types count toward the external primary minimum and which do not.
- The file defines how source families and conflicting sources are handled.
- The file requires version-first stack discovery before external research.
- The file prohibits sending secrets, private customer data, unpublished business details, proprietary identifiers, or large private snippets into web searches or external research prompts.

reference_patterns:
- Follow the existing concise Markdown rule style in `skills/shared/references/planning/deep-research.md`.
- Use existing headings where possible; add narrow subheadings only where they improve auditability.

test_first_plan:
- Documentation-only change; failing-first automated test is not practical. Use targeted `rg` checks after editing.

verify:
- `rg -n "Evidence Ledger|source_id|source_type|source_family|publication_date|last_updated_date|accessed_date|version_or_scope|supported_claims|current_enough_reason|source authority|privacy" skills/shared/references/planning/deep-research.md`
- `git diff --check -- skills/shared/references/planning/deep-research.md`
