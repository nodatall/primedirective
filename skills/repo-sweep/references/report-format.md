# Repo Sweep Report Format

Use this reference when emitting the repo-wide report before repairs and the final summary after approved fixes.

## Before Repairs

Open with a short `Audit Thesis` paragraph from the first-principles pre-pass.

Report verified findings ordered by severity inside these sections:

1. Audit Thesis
2. Security
3. Architecture and Design
4. Logic and Stability
5. Testing and Verification
6. Code Quality and Maintainability
7. Performance and Operations
8. Looks Bad But Is Fine
9. Needs Human Decision
10. Residual Risks
11. Fix Recommendation

Use the finding shape from `skills/shared/references/review/finding-disposition.md` for each material finding: severity, execution gate, disposition, confidence, scope, evidence, impact, fix path, and owner.

Use only these dispositions: `fix`, `needs human decision`, `residual risk`, and `no action`.

Classify technical debt findings by the actual failure mode:

- `Code Quality and Maintainability`: default for maintainability issues.
- `Architecture and Design`: boundary, coupling, ownership, abstraction, or god-object problems.
- `Testing and Verification`: missing or brittle safety nets.
- `Performance and Operations`: runtime cost or operational fragility.
- `Looks Bad But Is Fine`: inspected hotspots that look concerning but have no verified cost.

If a section has no verified findings, say `none verified`. If `Looks Bad But Is Fine` has no entries, say `none found`.

Keep the report concise, but do not bury serious production risks behind lower-priority cleanup.

## After Approved Fixes

Output only:

1. Initial repo-wide report summary
2. Fixed
3. Still failing
4. Needs human decision
5. Residual risks

Success before fixes means the report is evidence-backed, broad enough to surface the major production risks on the reachable surface, and explicit about what remains unverified.

Success after fixes means the repository is measurably healthier, the approved in-scope issues were addressed or cleanly escalated, and no obvious production-safety regressions remain on the verified public surface.

For backend and API repos, do not mark the sweep successful while any of these remain true on the verified public surface:

- public unsafe admin or debug endpoints exist without auth
- credentialed wildcard CORS is allowed
- committed secrets or secret fallbacks remain
- dev or mock behavior is enabled by default
- unguarded destructive data scripts, tests, migrations, or maintenance commands can target production, shared dev, or ambiguous databases
