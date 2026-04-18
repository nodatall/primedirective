# Harness Drift Check

Use this reference to decide whether the planning and execution harness is still load-bearing as models and repo workflows improve.

## Goal

Treat every harness component as a hypothesis about what the current model still needs help doing. Keep components that catch real failures, make conditional the ones that help only on risky task classes, and remove or demote pieces only after evidence shows they no longer change outcomes.

This check is agent-owned. Do not add mandatory human approval steps, extra user-facing checkpoints, or new recurring paperwork.

## Evidence sources

Use evidence already produced by the normal workflow. When `--check-harness-drift` is active, defer normal cleanup of planning, sub-task, and review artifacts until after the drift report is written so the check can inspect the full run evidence.

- `tasks/tmp/plan-task-<task-id>.md` sub-task contracts
- `tasks/tmp/review-task-*.md` and `tasks/tmp/review-task-final-*.md` review logs
- planning artifacts before archive cleanup, plus archived PRD/TDD/tasks-plan after cleanup
- final handoff summaries
- task checklist changes and commit boundaries
- validation commands and browser/API/CLI evidence
- blockers, user interventions, and review findings

If evidence is unavailable because the run started before this policy, the run failed before artifact creation, or a prior cleanup already removed the files, say the check is evidence-limited rather than guessing.

## Cleanup behavior

`--check-harness-drift` changes cleanup timing, not preservation policy:

1. Keep planning artifacts, sub-task contracts, review logs, and relevant temp files available through final review and drift-report generation.
2. Generate the compact drift report from those artifacts.
3. Then run normal cleanup and archive behavior.
4. Keep temp artifacts only when the matching preserve flag is active, such as `--preserve-review-artifacts` or `$plan-and-execute --preserve-artifacts`.
5. Always include the drift report in the final handoff even when temp artifacts are cleaned afterward.

## When to run

Run a compact check:

- in the final handoff for substantial one-shot or `$plan-and-execute` runs
- when `$execute-task` is invoked with `--check-harness-drift`
- when the user explicitly asks whether a skill or harness step is still worth keeping

During `$plan-work`, do not run a drift audit. If prior drift notes are present in source material, preserved artifacts, or archived handoffs, use them only to calibrate task granularity, verification expectations, and which checks should be conditional.

## Output shape

Keep the output short. The terminal user-facing handoff must include the actual
compact report inline under a visible `Harness Drift Check` heading. It is not
enough to say that a drift report was written, archived, or available at a path.
If a full artifact exists, mention its path only after the inline summary.

Start with a one-line verdict:

- `Verdict: Still load-bearing` when one or more harness components caught,
  prevented, or clarified real risk.
- `Verdict: Maybe conditional` when the evidence suggests a narrower default
  should be tested next, but no removal is justified.
- `Verdict: No material harness drift found` when the check ran and produced no
  action-worthy simplification or removal evidence.
- `Verdict: Evidence-limited` when required artifacts were missing or cleaned
  up before inspection.

Then include only the non-empty sections needed to support the verdict. Prefer
this shape:

```markdown
## Harness Drift Check

Verdict: <Still load-bearing | Maybe conditional | No material harness drift found | Evidence-limited>

Still load-bearing:
- <component>: <evidence that it caught or prevented a real issue>

Maybe conditional:
- <component>: <task class where it helped or looked unnecessary>

Candidate simplifications:
- <component>: <specific narrower default to test next>

Do not remove:
- <component>: <evidence or risk that makes removal unsafe>

Evidence gap:
- <what was not preserved or not measured>
```

Omit empty sections except `Evidence gap` when evidence is missing. When no
section has bullets, keep the verdict and add one sentence explaining why.

## Harness lift entries

When a review or final handoff records a real harness contribution, use this compact shape:

```text
harness_lift:
- component: <contract critique | acceptance_checks | Prompt G | Prompt H | Prompt I | final full-branch review | one-shot sub-task boundary | other>
  evidence: <specific finding, correction, or prevented failure>
  caught_by_standard_checks: yes | no | unclear
  action_taken: <fixed | contract tightened | accepted risk | blocker raised>
```

Do not manufacture `harness_lift` entries for checks that merely ran. A check is load-bearing only when it changes implementation, catches a real issue, prevents likely drift, or gives meaningful confidence that was not already available from cheaper checks.

## Decision rules

- Do not remove or weaken a harness component based on one clean run.
- Keep a component when it repeatedly catches issues, guards high-risk behavior, or provides evidence that cheaper checks do not.
- Make a component conditional when it helps only for identifiable task classes such as frontend, agent/tool, auth/security, migration, production-readiness, or broad one-shot work.
- Consider simplification when a component repeatedly finds nothing across similar low-risk tasks and duplicates cheaper evidence.
- Prefer a small A/B-style comparison before major simplification: run a similar task with and without the component, then compare bugs found, validation results, time/cost, and human interventions.
- When in doubt, record the uncertainty and keep the safer default for high-risk work.
