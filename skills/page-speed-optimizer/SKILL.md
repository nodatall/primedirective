---
name: page-speed-optimizer
description: Optimize frontend journey speed and visual continuity through report-first audits or bounded `/goal` fix loops. Use when the user asks to improve page load speed, Core Web Vitals, interaction responsiveness, frontend bundle or asset cost, route-to-route transitions, flashes, blank gaps, layout shifts, loading-state mismatch, bfcache/back-forward behavior, or other browser-perceived performance. Normal use has no mode flags.
---

# Page Speed Optimizer Skill

Improve real user-perceived frontend speed with measured evidence. This skill is the frontend/browser counterpart to `$backend-optimizer`: it focuses on page loads, in-session navigation, interactions, visual stability, assets, third-party scripts, and deployment/cache surfaces, not backend query optimization or broad repo audit work.

## Activation

Invoke explicitly with `$page-speed-optimizer`.

Invoke inside a Codex goal when the user wants the bounded measured fix loop:

```text
/goal $page-speed-optimizer
```

Do not add or require public mode flags. A bare invocation is enough; the skill decides what to inspect from the app, routes, available runtime, and evidence.

## References

Load `skills/page-speed-optimizer/references/optimization-loop.md` before substantive work. It owns the goal-run state document, candidate ledger, journey inventory, measurement rules, safety gates, and stop conditions.

Also load these when they materially affect the run:

- `skills/shared/references/analysis/verification-pivot.md` when current evidence cannot separate plausible bottlenecks.
- `skills/shared/references/reasoning-budget.md` for planning, loop, worker, and verification reasoning tiers.
- `skills/shared/references/architecture/architecture-guidance.md` when a proposed change would alter frontend/backend boundaries or when `docs/ARCHITECTURE.md` exists.

## Invocation Behavior

Bare `$page-speed-optimizer` is report-first:

- discover the app stack, routes, build/start commands, safe runtime target, and key user journeys
- inventory page loads, route transitions, interactions, assets, third-party scripts, and deployment/cache surfaces
- collect field, lab, trace, screenshot, or video evidence when practical
- rank candidates and recommend safe fixes
- stop before code, config, build, deploy, analytics, cache, or visual-behavior changes unless the user explicitly approves fixes

`/goal $page-speed-optimizer` is the bounded measured fix loop:

- create or update the goal-run state document and candidate ledger
- inventory and rank journey-speed candidates before fixing
- fix only safe high-impact candidates with before/after evidence
- update the state document and ledger after each meaningful checkpoint or candidate disposition
- resweep until every high-impact candidate is improved, rejected with evidence, or gated behind a clear decision
- do not mark the goal complete while the goal-run state document is missing, stale, or inconsistent with the ledger
- do not mark the goal complete after one Lighthouse win, one route fix, or one improved metric while high-impact pages, transitions, interactions, or assets remain unclassified

## Scope

In scope:

- initial page load speed and Core Web Vitals
- INP, interaction latency, long tasks, and main-thread pressure
- route transitions, SPA soft navigations when measurable, loading-state quality, stale-content flashes, and layout jumps
- bfcache and back/forward navigation behavior
- frontend bundles, route chunks, images, fonts, CSS, resource hints, and hydration/client-work cost
- third-party scripts, analytics, embeds, tag managers, and consent surfaces as measured cost candidates
- cache headers, CDN/static asset delivery, TTFB, and deployed/preview URL behavior when safely inspectable
- performance budgets and regression checks when routes, commands, and thresholds are stable enough to avoid noise

Out of scope:

- backend database/query optimization
- broad security review, dependency audit, architecture redesign, and whole-repo production-readiness review
- product redesign, visual redesign, SEO strategy, analytics policy, or business tradeoff decisions as auto-fixes
- automatic adoption of framework-experimental transition systems as a generic remedy

Route out-of-scope work:

- Use `$backend-optimizer` for backend/database performance.
- Use `$repo-sweep` for broad repository audit, production readiness, security/config/API-surface review, or larger redesign findings.
- Use normal planning or `$create-architecture` for product-level navigation redesign, routing ownership changes, or large rendering architecture shifts.

## Safety Rules

- Prefer production build/start or the closest practical production mode before claiming user-facing performance wins.
- If only dev mode is available, mark the run degraded and do not claim representative production speed.
- Do not change product behavior, visual design intent, accessibility semantics, routing semantics, SEO, auth, billing, security, consent, analytics policy, or data-retention behavior without human approval.
- Do not remove, defer, or alter third-party scripts when they may affect analytics, consent, auth, payments, support, ads, experiments, security, or compliance without explicit approval.
- Do not change CDN, cache headers, preview/production deployment config, or sensitive-page caching without target verification and approval when policy matters.
- Respect reduced-motion preferences and focus/scroll continuity when changing loading states, transitions, animations, or skeletons.
- Treat missing production-like runtime, missing auth, missing seeded data, missing public URL, or missing field data as a gated candidate, not as permission to invent a win.

## Workflow

1. Establish baseline and safety.
   - Inspect git status and preserve unrelated changes.
   - Identify framework, package manager, build/start commands, routes, auth/data needs, public or preview URLs, existing performance scripts, and test commands.
   - Prefer production build/start. Record any degraded runtime and why.
   - For `/goal`, create or update `tasks/tmp/page-speed-optimizer-goal-state.md` and `tasks/tmp/page-speed-optimizer-ledger.jsonl`.
2. Inventory journeys and candidates.
   - Map important page loads, in-session route transitions, interactions, back/forward paths, assets, third-party scripts, and deploy/cache surfaces.
   - Include field data such as CrUX, PageSpeed Insights, app RUM, or `web-vitals` attribution when available.
   - Include lab evidence such as Lighthouse navigation/user flows, DevTools traces, Playwright traces/screenshots/video, WebPageTest, or local production-mode measurements when practical.
3. Rank by user impact.
   - Prioritize field impact, route importance, LCP/INP/CLS severity, TTFB, interaction latency, long tasks, visible flashes, layout shifts, blank gaps, stale content, asset cost, third-party cost, and frequency.
4. Report or fix.
   - Bare `$page-speed-optimizer`: report ranked candidates and stop before changes unless fixes were explicitly approved.
   - `/goal $page-speed-optimizer`: fix safe high-impact candidates one at a time, verify, update state and ledger, and resweep.
5. Verify.
   - Capture before/after evidence for each accepted optimization.
   - Run focused regression checks and visual/navigation checks affected by the fix.
   - Add budget or regression checks only when the route, command, and threshold are stable enough to be useful.
6. Close out.
   - State why the loop stopped.
   - List improved candidates, rejected candidates, gated decisions, validation, and residual risks.
   - State whether the result is `journey-speed optimization complete` or a narrower result such as `safe local pass complete`.
   - For `/goal`, include the goal state path, ledger path, wall-clock elapsed time, inventory coverage, and stop-condition status.

## Output

For report-first runs, lead with ranked findings:

- candidate
- surface or route/flow
- evidence
- impact
- safe fix path
- risk or gate
- recommended next action

For `/goal` runs, include:

- rounds completed, wall-clock elapsed time, and stop reason
- goal state path and ledger path
- inventory coverage across pages, transitions, interactions, assets, third parties, and deploy/cache surfaces
- candidates improved
- candidates rejected with evidence
- human-decision gates
- validation commands, traces, screenshots, videos, reports, or artifacts
- residual risks and resume point when incomplete
