# Blinded Deliver Eval Judge Rubric

Judge the two normalized runs without guessing workflow identity. Cite exact behavior, probe, diff, or review-action evidence. Freeze one of `candidate_better`, `candidate_neutral`, `candidate_regression`, or `inconclusive` before identity reveal.

Rank evidence in this order:

1. Material correctness and preservation of every acceptance behavior.
2. Permanent-test value: keep durable supported-path protection for credible harm, without turning one-run evidence or already-covered behavior into permanent cases.
3. Related-case consolidation into the smallest coherent table-driven coverage.
4. Rereview breadth: targeted for an evidenced isolated repair; full for a cross-boundary repair or when isolation cannot be shown.
5. Test count and total test size, interpreted as maintenance cost rather than a proxy for quality.
6. Full review-round count and whether each full round was safety-required.
7. Wall time.
8. Unnecessary ceremony or user friction.

There is no hard line-count cap. Larger code or tests lose only when the extra surface lacks durable value. A faster or smaller run cannot win by losing correctness, required permanent protection, or a safety-required full rereview.

After the blinded verdict is frozen, reveal identity and inspect candidate-only contract compliance separately. Then apply the frozen outcome ledger as a hard gate. Any ledger regression blocks `candidate_better` regardless of qualitative score.
