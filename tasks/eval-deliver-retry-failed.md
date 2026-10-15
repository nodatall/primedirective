# Deliver Workflow Eval: Retry Failed Jobs

Date: 2026-08-16

## Verdict

`$deliver` was useful for this scenario, but only as a **qualified positive**.

It produced materially safer and more correct code than the native planning workflow. It also took about eight times longer, roughly doubled the branch and test delta, and still left three review findings. The Pro variant is **inconclusive** because its required browser model-selection gate could not complete.

This is one pilot scenario, not proof that Deliver is generally better.

## Question

Did Deliver produce a materially better verified implementation or safer process than native planning, and did Pro analysis add enough value to justify its additional cost and friction?

## Controlled Setup

- Scenario: add a safe `retry-failed` command to a dependency-free Python JSON queue CLI.
- Frozen base commit: `3969de119cd5fb4598efc02ee5e5a0563cfd4fc6`.
- Three isolated local clones started from the same commit.
- Every Codex runner, worker, reviewer, and judge used `gpt-5.6-sol` with `xhigh` reasoning.
- Each runnable arm received the same source bullets and the same approval: `Approved as written. Implement the complete plan. Do not expand scope.`
- Remote actions were excluded: no push, pull request, merge, or source-fixture mutation.
- One frozen hidden suite was written before execution.
- The same read-only `$review-chain --preserve-review-artifacts` measured each completed implementation after freeze.
- A fresh judge compared blinded Run A and Run B before workflow identity and cost were revealed.

## Arm Results

| Arm | Result | Frozen checks | Approximate plan-to-freeze time | Size |
| --- | --- | --- | ---: | ---: |
| Native plan + ordinary review | Completed | 9/9 public, 7/7 frozen hidden | 7m 39s | 445 insertions, 3 deletions; 375-line test file |
| `$deliver` | Completed | 24/24 public, 7/7 frozen hidden | 61m 23s | 985 insertions, 2 deletions; 860-line test file |
| `$deliver --pro-analysis` | Blocked before submission | No implementation | about 4 minutes to gate evidence | Plan and incomplete Pro memo only |

Exact token and tool-call accounting was not exposed and was not estimated.

## What Deliver Added

Deliver's implementation passed the original frozen checks before its built-in final review. Four review/rereview rounds then found and repaired:

1. A selected job with `history: null` crashing instead of retrying.
2. Container-valued status and invalid UTF-8 escaping as tracebacks instead of status 2.
3. Mixed-offset timestamps being ordered lexically instead of chronologically.
4. Invalid timestamps bypassing the error boundary.
5. Boolean versions being accepted as version 1 and mutated.
6. Lone-surrogate IDs failing after the retry had already persisted.
7. JSON decoder integer-limit errors escaping as tracebacks.
8. Deep unknown data producing a save-time recursion traceback.

The native ordinary review found only `_positive_integer(True)` returning `1`. That issue is unreachable through the public string-valued CLI and was correctly rejected as no action. It missed the stronger public-entrypoint failures above.

## Common Measurement

Both frozen implementations passed the original hidden suite.

A post-review suite was then assembled from the union of concrete reviewer discoveries and run unchanged against both branches. It was explicitly treated as post hoc rather than part of the frozen specification:

- Deliver: 7/11 passed.
- Native: 2/11 passed.

The common review still found three issues in the completed Deliver branch:

- Non-finite or overflowing JSON numbers can violate strict JSON and unknown-data preservation.
- Timestamp parsing loses sub-microsecond precision and can select the wrong limited retry.
- Human output can emit raw control characters from a job ID.

The first two remain relevant correctness/preservation concerns. Terminal-control escaping is reasonable hardening but disproportionate as a core acceptance gate for this source task.

## Blinded Judge

Blinded mapping:

- Run A was `$deliver`.
- Run B was native planning.

Initial quality verdict: `run_a_better`, high confidence `0.88`.

After identity and cost were revealed, the judge kept the quality verdict and classified net utility as a **qualified positive**:

- Mixed-offset ordering, post-persistence failure prevention, and normal malformed-input boundaries were worth meaningful weight.
- Decoder limits, deep recursion, the fourth full rereview, and many one-case tests were disproportionate for this small CLI feature.
- Deliver improved correctness but was not cost-efficient.

## Pro Gate Outcome

The signed-in visible ChatGPT UI exposed GPT-5.6 Sol with a visible selected `Pro` effort and power state `5 of 5`. It did not expose a visible/selectable `Pro Extended` or `Extended Pro` label. The only exact text appeared in an invisible `aria-hidden` measurement element.

The current Pro contract requires the exact visible extended label. The runner correctly submitted nothing, used no fallback, and stopped with an incomplete synthesis stamp.

Pro value is therefore `inconclusive`. The evidence points to a current contract/UI-compatibility defect rather than evidence for or against Pro's reasoning value.

Smallest proposed contract change: accept either the existing visible `Pro Extended` / `Extended Pro` labels, or the expected GPT-5.6 Sol model with visible selected `Pro` effort and accessible power state `5 of 5`. Continue rejecting hidden text, unselected entries, lower effort states, and silent fallback. This proposal was not implemented by the eval.

## Limits

- One scenario cannot establish general usefulness.
- The post-review regression suite was created after reviewer discoveries, so it supports diagnosis but is not an unbiased pre-registered score.
- The common review agents did not discover identical findings, showing reviewer variance even under the same review contract.
- A future eval should use another realistic task before changing Deliver's global review-loop behavior.

## Reusable Regression Lane

This document remains the historical native-versus-Deliver pilot. Future Deliver behavior-change comparisons use the tracked baseline-versus-candidate suite at `evals/deliver/suite.md`, which pairs this known case with the independent preflight-remediation historical replay and runs through `$skill-review`.

## Artifacts

- Scratch root: `agent-scratch/deliver-eval/retry-failed/`
- Scenario: `agent-scratch/deliver-eval/retry-failed/scenario/`
- Native branch: `agent-scratch/deliver-eval/retry-failed/arm-a-plan/`
- Deliver branch: `agent-scratch/deliver-eval/retry-failed/arm-b-deliver/`
- Incomplete Pro branch: `agent-scratch/deliver-eval/retry-failed/arm-c-deliver-pro/`
- Blinded packet: `agent-scratch/deliver-eval/retry-failed/judge/blinded/`
- Blinded verdict: `agent-scratch/deliver-eval/retry-failed/judge/blinded/initial-verdict.md`
- Net-utility verdict: `agent-scratch/deliver-eval/retry-failed/judge/final-net-verdict.md`

## Completion Stamp

eval_complete: yes
scenario: retry-failed
baseline_run_complete: yes
deliver_run_complete: yes
deliver_pro_run_complete: no
comparable_inputs: yes
frozen_hidden_suite_run: yes
common_review_run: yes
judge_blinded: yes
deliver_verdict: qualified_positive
pro_verdict: inconclusive
remote_actions_performed: no
