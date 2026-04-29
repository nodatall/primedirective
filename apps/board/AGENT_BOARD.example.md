# Agent Board optional repo policy

# Off by default. If true, only Quick Track PRs with absent checks may auto-merge,
# and only when all immutable guardrails still pass.
allowQuickNoCheckAutomerge: false

maxActiveRuns: 5
maxActiveCardsPerRepo: 5
protectedRiskExtraPatterns: payments,credentials
