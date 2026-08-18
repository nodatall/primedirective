# Deliver Skill Review: Test-Value Gate v2

Invocation: `$skill-review skill=deliver scenario=evals/deliver/suite.md baseline=a4116bb candidate=83cf702 --preserve-review-artifacts`

- Skill: `deliver`
- Baseline contract: `a4116bb`
- Candidate contract: `83cf702`
- Frozen harness: `50fa61e`
- Scenario suite: `evals/deliver/suite.md`
- Runner and judge: `gpt-5.6-sol`, `xhigh`
- Arm budget: 90 cumulative active minutes across pre-packet and remediation
- Inactivity timeout: 15 minutes without a structurally valid Codex JSONL event
- Preserved artifacts: `agent-scratch/skill-review/deliver-deliver-deliver-eval-test-value-gate-v2/`
- Runtime root: `/private/tmp/deliver-eval-50fa61e-v2/`
- Status: comparison in progress

The 900-second and 1,800-second v1 attempts are invalid diagnostics and are excluded from every v2 score. Both v2 arms receive the same clean fixture, contract-specific package, model, reasoning level, tools, sandbox, cumulative budget, inactivity policy, and staged review packet. Any frozen-ledger failure, material correctness loss, incomplete arm, or verdict other than `candidate_better` stops this version without tuning or another retry.
