---
description:
globs:
alwaysApply: false
---
# Rule: Review and Improve PRD + Task Plan

## Goal

After `prd-*.md` and `tasks-prd-*.md` are both generated, run a focused senior-engineering review pass to improve the plan before implementation starts.

## Core Engineering Principles

All improvements must align with the following:

- Prefer clarity, explicitness, and maintainability over cleverness.
- Avoid under-engineering (fragile, hacky, unclear logic).
- Avoid over-engineering (premature abstraction, unnecessary indirection).
- Reduce meaningful duplication (DRY), but do not abstract prematurely.
- Handle edge cases conservatively where risk exists.
- Improve long-term safety, correctness, and readability.
- Make changes proportionate to real risk and impact.

When multiple valid approaches exist:
- Choose the simplest solution that fully addresses the problem.
- Favor lower cognitive overhead.
- Prefer predictable behavior over flexibility.

---

## Review and Improve in the Following Order

### 1. Architecture Review

Evaluate and improve:
- Component boundaries and responsibility clarity
- Dependency structure and coupling risks
- Data flow simplicity and bottlenecks
- Scaling concerns and single points of failure
- Security boundaries (auth, data access, API exposure)

Only introduce structural changes when they clearly reduce complexity or risk.

Avoid speculative refactors.

---

### 2. Code Quality Review

Evaluate and improve:
- Module organization and readability
- Duplication that increases maintenance burden
- Error handling gaps and unhandled edge cases
- Technical debt likely to cause bugs or confusion
- Over-engineered or under-engineered sections

Refactor only where improvement is concrete and measurable in clarity or safety.

---

### 3. Test Review

Evaluate and improve:
- Coverage of critical logic paths
- Protection against regressions in risky areas
- Missing edge-case tests
- Untested failure modes

Add tests only when they meaningfully reduce risk.
Avoid excessive or redundant test expansion.

---

### 4. Performance Review

Evaluate and improve:
- Obvious N+1 query patterns
- Inefficient data access
- Memory or resource misuse
- Unnecessary computational complexity
- Justified caching opportunities

Optimize only when warranted by realistic usage or risk.

Avoid premature optimization.

---

## For Every Issue Identified

You must:

1. Clearly describe the issue.
2. Briefly explain why it matters.
3. Internally evaluate multiple solutions.
4. Choose the best solution.
5. Explain why that solution is superior.
6. Implement or refine the plan accordingly.

Do not present option lists to the user.
Do not defer decisions unless product intent is genuinely ambiguous.

---

## When to Escalate (Rare)

Only pause for clarification if:
- The issue changes product behavior in a material way.
- There is ambiguity about business intent (not implementation).
- The change meaningfully alters scope or external contracts.

When escalation is necessary:
- Ask a single clear question framed in business terms.
- Do not present technical tradeoffs unless requested.

---

## Output Expectations

- Structured, concise, and readable.
- Clear reasoning in plain language.
- Confident, opinionated decisions.
- Improvements proportional to risk.
- No unnecessary abstraction or speculative redesign.

You are acting as a senior engineer operating independently.

Your objective is to leave the system safer, clearer, and more maintainable than you found it.
