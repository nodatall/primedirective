# Review Loop Adversarial Priors

Goal: Add bounded adversarial-prior review behavior to Prime Directive review loops without encouraging forced or invented findings.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The useful idea is to make reviewers deliberately test stronger priors such as "there is a real bug here" and "there is a smaller delta that preserves the goal."
- The safety guard is just as important: every adversarial lane must end in a verified finding, a specific verification pivot, or `no action` with the falsifying evidence.
- `$review-plan` already has an adversarial council shape. `$review-chain` and `$merge-review` are the likely contract surfaces for branch review loops.
- The change should reuse existing review-protocol and finding-disposition contracts unless the implementation proves a small new reference removes real duplication.
- This checkout already has dirty files from earlier work. Treat them as pre-existing work, inspect overlaps before editing, and do not overwrite unrelated changes.

## Steps

### 1. Map The Current Review Contracts

Decision notes:
- No `docs/ARCHITECTURE.md` change is needed for this slice. The change stays inside existing owned contracts: `review-protocol`, `finding-disposition`, `merge-review`, and `review-plan`; no new workflow boundary or dependency direction is introduced.

- [x] Inspect `skills/shared/references/review/review-protocol.md`, `skills/review-chain/SKILL.md`, `skills/merge-review/SKILL.md`, `skills/merge-review/references/merge-readiness-rubric.md`, `skills/review-plan/SKILL.md`, and README mirrors to identify the smallest owned contract surface for the new behavior.
- [x] Inspect `scripts/validate-skill-contracts.py` before edits so the implementation can update contract checks instead of relying on prose only.
- [x] Check whether the change is boundary-affecting under the architecture guidance; if implementation changes cross-skill ownership or shared review protocol shape, add or update `docs/ARCHITECTURE.md` first, otherwise record why this is a narrow edit inside existing skill-contract boundaries.

### 2. Define The Bounded Adversarial Review Contract

- [x] Add a shared review rule that adversarial prompts may assume a bug, overengineering, or missing verification exists, but must stop at evidence instead of forcing a finding.
- [x] Define the accepted outcomes for each adversarial lane: verified `fix` finding, `needs human decision`, `residual risk`, concrete verification pivot, or `no action` with falsifying evidence.
- [x] Add a smaller-delta lane that asks whether the same user goal can be satisfied with less code, less surface area, fewer abstractions, or narrower validation, without removing required scope.
- [x] Add a skeptic/falsifier lane that rejects unsupported hostile findings and records what evidence cleared the suspicion.
- [x] Keep wording compatible with the existing finding-disposition contract and avoid creating a second finding taxonomy.
- [x] Add an explicit anti-pattern rule against unbounded "keep looking until you find a bug" loops; reviewers should try hard, record the falsifier when evidence fails, and stop.

### 3. Wire The Review Loops

- [x] Update `$review-chain` or its shared review protocol so explicit branch and task reviews run the bounded adversarial lanes at the right point in the prompt sequence.
- [x] Update `$merge-review` and its merge-readiness rubric so the loop tests bug-prior, smaller-delta, and falsifier questions before declaring the branch merge-ready.
- [x] Update `$review-plan` only if needed to make the smaller-delta or falsifier expectation explicit without weakening its existing first-principles council contract.
- [x] Preserve the existing workflow boundaries: `$review-chain` stays report-first, `$merge-review` stays review/fix/validate/rereview, `$review-plan` stays planning-only, and `$ship-branch` remains the shipping workflow.
- [x] Avoid broad prompt churn: prefer one shared review-protocol addition plus narrow skill-specific references over rewriting every review prompt.

### 4. Mirror And Validate The Contract

- [x] Update README or other public mirrors so users can tell when to use the strengthened review behavior.
- [x] Update `scripts/validate-skill-contracts.py` with focused checks for the new adversarial-prior tokens and loop safety rules.
- [x] Run `python3 scripts/validate-skill-contracts.py`.
- [x] Run `git diff --check`.
- [x] Run a targeted text scan proving the new contract does not contain wording that requires reviewers to invent a bug when evidence does not support one.
- [x] Run `./scripts/install-codex-plugin.sh` so the local Codex skill install is current.

### 5. Review And Close Out

- [x] Run the `$deliver` final full-branch review using this execution plan as scope.
- [x] Fix any in-scope material findings from final review and rerun the relevant checks.
- [x] Archive this execution plan under `tasks/archive/<yyyy-mm-dd>-review-loop-adversarial-priors/`.
- [x] Commit the implementation, validation edits, archive move, and closeout changes without committing unrelated pre-existing dirty work.
