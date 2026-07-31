# Skill Review: Clarifier Parallel Direction Search

## Invocation

`$skill-review skill=clarifier scenario=agent-scratch/skill-review/clarifier-main/scenario/two-case-suite.md baseline=HEAD candidate=worktree`

## Scope

- Skill: `clarifier`
- Baseline: `HEAD` at `c1a8116`
- Candidate: current worktree
- Candidate-owned files: `skills/clarifier/SKILL.md`, `README.md`, `scripts/validate-skill-contracts.py`
- Pre-existing unrelated dirty files excluded from the review: `skills/first-principles-mode/SKILL.md`, `skills/first-principles-mode/references/analysis-rubric.md`
- Required Clarifier references: none; the behavior contract is self-contained in `skills/clarifier/SKILL.md`
- Scratch directory: `agent-scratch/skill-review/clarifier-main/`

## Scenario

The same two-case suite is used for both runs:

1. A rough engineering essay with a stronger verification-and-judgment thesis buried beneath an apparent AI-speed frame. The factual causality is intentionally unresolved.
2. A near-done flash-fiction paragraph whose delayed reveal and restraint should be preserved without a whole-paragraph rewrite or manufactured criticism.

This pair exercises the new breadth search while also checking that its gate prevents over-editing.

## Comparable Run Protocol

- One fresh subagent per shadow run.
- Same model, reasoning level, tools, scenario, and stop boundary.
- Baseline receives only the extracted `HEAD` Clarifier contract.
- Candidate receives only the current-worktree Clarifier contract.
- Shadow runs may write only their named output under the scratch directory.
- A fresh judge receives blinded `Run A` and `Run B` outputs before seeing the contract diff.

## Results

### Baseline

- The baseline found the buried code-versus-judgment thesis, preserved the unresolved patch causality, and correctly left the near-done narrative unchanged.
- It produced two useful expository versions and five specific sentence-level findings.
- It handled the underdeveloped interview point mainly by cutting it or moving it to another piece.
- Private-process summary: four candidates, no subagents, three refinement passes.

### Initial Candidate And Finding

- The first candidate run used two worker lanes in parallel while the orchestrator covered the third.
- It found two materially useful centers: fast implementation can outrun understanding, and engineering judgment is becoming the scarce part of the work.
- It connected the incident to tests, monitoring, and interviews instead of removing the interview point.
- The blinded judge preferred the candidate, but found the private work disproportionate for the short source: 42 direction sketches and 48 sentence variants.
- Disposition: fixed before readiness. The contract changed the normal first pool to 12-24 directions, the normal sentence pool to 3-6 variants with a 24-variant section cap, and normal critic passes to local orchestration.

### Corrected Candidate

- The corrected run stopped at about 20 direction sketches and 18 sentence variants.
- Two direction workers and two sentence-refiner workers ran in parallel waves; the orchestrator covered the unavailable third lane and ran two local refinement passes.
- The result preserved the original constraints and strongest line, produced exactly two materially different complete directions, explicitly labeled the idea shift, connected tests and interviews to the judgment thesis, and retained the original-draft sentence review.
- The near-done narrative again triggered no rewrite search, no subagents, and no manufactured criticism.
- The full two-case corrected run took about three minutes from dispatch marker to completion check; that includes two complete expository rewrites, editorial diagnosis, and the narrative no-op.

### Judge

- The first pairwise comparison was blinded as Run A and Run B.
- Both runs passed factual fidelity, narrative restraint, and original-draft diagnosis.
- The initial candidate and baseline each scored 11/12; the candidate's stronger expository structure offset its process-friction deduction.
- After the budget correction and rerun, the judge returned `candidate_better` and `Ready: yes`.
- Judge evidence: the corrected candidate kept the material thesis and structure improvement while reducing search from 42 to about 20 directions and from 48 to 18 sentence variants.

### Remaining Risk

The suite covers a buried-thesis engineering essay and a near-done narrative. Long drafts, voice dumps, professional messages, and no-subagent fallback behavior remain useful future calibration cases, but the current run found no blocker.

## One-Minute Follow-up

- User decisions: keep the deep search automatic for substantial, exploratory, and unsettled voice-dump drafts; do not pause for permission before a labeled idea shift; keep process explanations concise without pool or pass counts; and do not preserve raw private artifacts.
- Contract change: use one bounded parallel generator wave, then keep sentence refinement and the three-lens self-review local. Direction workers return only their two strongest source-anchored sketches, use the user's selected model at low reasoning when available, and may be cut off after 25 seconds; the orchestrator covers any missing lane locally.
- Current focused rerun: a fresh voice-dump post about AI coding, verification, interviews, and engineering judgment completed in 52.3 seconds from dispatch marker to final response under the user's selected model. It used one generator wave only, produced two complete distinct versions, preserved the source's factual uncertainty and conversational voice, and gave a concise original-draft diagnosis. The idea-shift heading was not required because the alternative stayed within the same main point.
- The earlier roughly three-minute result remains historical evidence for the superseded multi-wave topology. An intermediate current-model calibration took 76.8 seconds; the final 52.3-second run is the current calibration. "About one minute" remains a target rather than a wall-clock guarantee because model scheduling varies.
- Raw prompt, worker results, response, traces, and judge packet were not written to the repository and were not preserved.

## Validation

- `python3 scripts/validate-skill-contracts.py`: passed
- `git diff --check`: passed
- Ruby UTF-8 YAML frontmatter check: passed
- `./scripts/install-codex-plugin.sh`: passed
- Generic skill-creator `quick_validate.py`: unavailable because the system Python does not include `PyYAML`; the repository contract validator and independent frontmatter check covered the changed contract

## Skill Review Completion Stamp

skill_review_complete: yes
skill_name: clarifier
state_doc: tasks/skill-review-clarifier-main.md
baseline_ref: HEAD@c1a8116
candidate_ref: current-worktree
scenario: two-case buried-thesis and near-done narrative suite
baseline_run_complete: yes
candidate_run_complete: yes
comparable_inputs: yes
judge_run_complete: yes
judge_blinded: yes
verdict: candidate_better
artifact_evidence_preserved: no
ready_for_merge_review: yes
stop_reason: clean_benefit
