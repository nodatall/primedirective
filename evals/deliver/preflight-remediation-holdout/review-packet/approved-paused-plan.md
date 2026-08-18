# Approved Plan, Paused At Remediation

Approval: `Approved as written. Resume the paused remediation plan. Do not expand scope.`

The initial implementation at `27103d3a05eb20072d29917532326a5cbd59dc8f` and its validation evidence are the frozen starting state. A completed full-branch review has returned two verified operational findings. Resume only the following work after the evaluator stages the fixed review packet:

1. Reproduce both findings with the supplied probes.
2. Repair every verified in-scope defect with the smallest safe change.
3. Record whether each repair merits a permanent test, a related table case, a one-run probe, or no new test, with evidence.
4. Run the relevant focused probes and broad validation.
5. Choose and record the narrowest trustworthy fresh rereview for each repair under the supplied Deliver contract.
6. Freeze code, tests, probes, review actions, rereview records, and timing, then stop locally.
