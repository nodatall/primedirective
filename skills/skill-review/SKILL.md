---
name: skill-review
description: Review Prime Directive skill changes before merge by running the baseline and candidate skill contracts on the same realistic scenario, preserving artifacts, and using a fresh judge to decide whether the candidate is materially better, neutral, or regressive.
---

# Skill Review Skill

Evaluate changed skills by comparing behavior, not just prose.

This skill is a pre-merge gate for Prime Directive skill contract changes. It does not replace `$review-plan`, `$review-chain`, or `$merge-review`; it adds an evidence-backed A/B review for the skill behavior itself.

## Activation

Invoke explicitly with `$skill-review` when a Prime Directive skill change should be judged before merge.

Activation examples:

- `$skill-review`
- `$skill-review skill=<skill-name>`
- `$skill-review scenario=<path-or-name>`
- `$skill-review baseline=<git-ref> candidate=<git-ref-or-worktree>`
- `$skill-review skill=<skill-name> scenario=<path-or-name> --preserve-review-artifacts`

Supported modifiers:

- `skill=<skill-name>`: review one changed skill instead of inferring from the diff.
- `scenario=<path-or-name>`: use a provided scenario prompt, artifact, or named local case.
- `baseline=<git-ref>`: compare against this baseline instead of the resolved merge base or `origin/main`.
- `candidate=<git-ref-or-worktree>`: compare against this candidate instead of the current checkout.
- `--preserve-review-artifacts`: keep scratch artifacts after the review completes.

## Required References

Load these before running:

- `skills/shared/references/contract-ownership.md`
- `skills/shared/references/review/finding-disposition.md`
- `skills/shared/references/review/review-protocol.md`
- `skills/shared/references/reasoning-budget.md`

Load the baseline and candidate versions of the reviewed skill contract before each shadow run. Load related owner references only when the reviewed skill names them as required for the selected scenario.

## Scope

Review only Prime Directive skill behavior and directly related contract surfaces:

- `skills/<skill-name>/SKILL.md`
- `skills/<skill-name>/references/**`
- `skills/<skill-name>/agents/openai.yaml`
- shared references or README text that the changed skill owns or consumes
- validator or installer changes that enforce the changed skill contract

Do not use this skill for ordinary application-code branch review. Use `$review-chain` or `$merge-review` for that.

If the branch changes no skill contract, stop and route to the appropriate review skill.

## State Document

Write one durable state document:

- `tasks/skill-review-<skill-name>-<branch-slug>.md`

Build `<branch-slug>` from the current branch name or candidate ref by replacing filename-unsafe characters with `-`.

Use scratch artifacts under:

- `agent-scratch/skill-review/<skill-name>-<branch-slug>/`

Keep all disposable prompts, extracted old skill files, temporary worktrees, run outputs, judge packets, screenshots, and logs under that scratch directory unless the user provided a different scenario path.

## Scenario Selection

Prefer realistic scenarios over synthetic edge cases.

Scenario order:

1. Use the explicit `scenario=<path-or-name>` when provided.
2. Reuse an existing recent task, plan, merge-review state doc, or archived execution plan that naturally exercises the changed behavior.
3. Build the smallest realistic scenario from the current diff and the reviewed skill's activation contract.
4. If no realistic scenario can be built without inventing the user's intent, stop and ask for one.

Good scenarios include:

- a real `$deliver` plan before and after a contract wording change
- a branch with actual review findings for `$merge-review`
- a rough plan that should route to `$plan-to-goal`
- a repo-sweep report where a changed rubric should alter the finding quality
- a writing sample for `$clarifier` or `$plain-language`

Avoid scenarios whose only purpose is to make the candidate win.

## Workflow

1. Establish baseline and candidate.
   - Run `git status --short --branch`.
   - Identify changed skill files with `git diff --name-only <baseline>...<candidate>` when refs are available, plus current working-tree changes when reviewing the checkout.
   - Infer `skill=<skill-name>` only when exactly one public skill is materially changed.
   - If multiple skills changed, review them one at a time or stop and ask which skill to judge first.
2. Create or refresh `tasks/skill-review-<skill-name>-<branch-slug>.md`.
   - Record invocation, refs, changed files, dirty-state summary, selected scenario, required references, and scratch directory.
3. Prepare isolated shadow-run inputs.
   - Extract the baseline skill contract and references into `agent-scratch/skill-review/<skill-name>-<branch-slug>/baseline/`.
   - Extract the candidate skill contract and references into `agent-scratch/skill-review/<skill-name>-<branch-slug>/candidate/`.
   - Copy or link only the scenario inputs needed for the run.
   - Do not mutate the user's working tree during shadow runs.
4. Run the baseline skill and candidate skill on the same scenario.
   - Use one fresh subagent per run when subagents are available.
   - Give each run the same user prompt, scenario artifacts, repo snapshot, allowed tools, and stop boundary.
   - Give the baseline run only the baseline skill contract and required references.
   - Give the candidate run only the candidate skill contract and required references.
   - For implementation-capable skills, run in a disposable worktree or scratch copy and stop at the scenario's declared boundary.
   - For planning or review skills, require the actual output artifact the skill would normally write.
   - Capture commands, file changes, final answer, created artifacts, validation evidence, blockers, and time/cost-relevant friction.
5. Judge the outputs.
   - Use a fresh judge subagent when available.
   - Blind the judge to old/new labels when practical by calling the outputs Run A and Run B.
   - Give the judge the original user goal, scenario, expected skill contract, both run artifacts, and the changed diff after the initial pairwise comparison.
   - Ask for a verdict: `candidate_better`, `candidate_neutral`, `candidate_regression`, or `inconclusive`.
6. Calibrate the judge locally.
   - A candidate is better only when it improves goal fit, safety, routing, artifact quality, validation discipline, user friction, or merge readiness in a way visible in the run artifacts.
   - More words, stricter process, or extra review rounds are not benefits unless they catch a real issue, prevent a real mistake, or make the handoff materially clearer.
   - Treat lost activation paths, invented constraints, unavailable-tool assumptions, weaker stop gates, dirtier working-tree behavior, or noisier user handoff as regressions.
   - Use `inconclusive` when the scenario did not exercise the changed behavior.
7. Record findings using the shared disposition shape when a regression or inconclusive result would block merge readiness.
8. End with the Skill Review Completion Stamp.
9. Delete scratch artifacts after a successful non-preserved run only when the state doc contains enough evidence to audit the verdict. Keep artifacts for regressions, inconclusive reviews, blockers, or `--preserve-review-artifacts`.

## Judge Rubric

The judge must compare the run outputs against these criteria:

- user goal satisfaction
- correct skill activation and routing
- adherence to the skill's owner contract
- quality and usefulness of produced artifacts
- evidence and validation discipline
- stop-gate correctness
- protection of user changes and working-tree state
- avoidance of unnecessary ceremony
- clarity of final handoff
- whether the candidate change improved the actual outcome rather than only sounding better

The judge must cite concrete run artifacts. Do not accept a verdict that only says one version is "more robust" or "more comprehensive" without naming the artifact-level difference.

## Stop Conditions

Stop without a pass verdict when:

- no realistic scenario is available
- the baseline or candidate skill cannot be reconstructed
- the old/new runs did not receive comparable inputs
- a run mutates the real working tree unexpectedly
- the judge cannot inspect the artifacts needed for a fair comparison
- the result is inconclusive and the changed behavior still matters before merge

## Output

Final output must say:

- whether the candidate skill change is better, neutral, regressive, or inconclusive
- which skill and scenario were reviewed
- what baseline and candidate were compared
- where the state doc lives
- what artifacts were produced or preserved
- what validation and judge evidence supports the verdict
- whether the change is ready for normal `$merge-review` or needs another skill edit first

## Skill Review Completion Stamp

Append this stamp to the state document:

```text
## Skill Review Completion Stamp

skill_review_complete: yes|no
skill_name: <skill-name>
state_doc: tasks/skill-review-<skill-name>-<branch-slug>.md
baseline_ref: <git-ref-or-path>
candidate_ref: <git-ref-or-path>
scenario: <path-or-name>
baseline_run_complete: yes|no
candidate_run_complete: yes|no
comparable_inputs: yes|no
judge_run_complete: yes|no
judge_blinded: yes|no|not_practical
verdict: candidate_better|candidate_neutral|candidate_regression|inconclusive
artifact_evidence_preserved: yes|no
ready_for_merge_review: yes|no
stop_reason: clean_benefit|neutral_no_regression|candidate_regression|inconclusive_scenario|missing_scenario|missing_baseline|missing_candidate|uncomparable_runs|shadow_run_mutated_real_tree|missing_judge
```

Set `ready_for_merge_review: yes` only when the verdict is `candidate_better` or `candidate_neutral`, all comparable run gates are `yes`, and no regression findings remain.
