# Page Speed Optimizer Loop

Use this reference for `$page-speed-optimizer` runs.

This skill has no public mode flags. A user should be able to invoke `/goal $page-speed-optimizer` without adding a custom prompt. Apply the journey inventory, goal state, candidate ledger, measurement rules, safety gates, and completion gate automatically.

## Goal-Run State

For `/goal $page-speed-optimizer`, maintain a readable state document at:

```text
tasks/tmp/page-speed-optimizer-goal-state.md
```

Create it at the start of the goal run. Update it after every meaningful checkpoint, after every candidate disposition, before context compaction or interruption handoff when possible, and before final closeout.

The state document should contain:

- `started_at`: local timestamp with timezone when known
- `last_checkpoint_at`: local timestamp with timezone when known
- `elapsed_wall_clock`: current elapsed wall-clock time for the run
- `user_budget`: time, token, or scope budget if the user provided one; otherwise `none provided`
- `current_phase`: discovering, measuring, patching, validating, resweeping, blocked, or complete
- `last_completed_step`: concrete completed step or `none yet`
- `active_step`: current work or `none`
- `next_exact_action`: the next command, route, trace, file, or decision to inspect
- `primary_verifier`: the strongest check or evidence bundle for this app
- `supporting_checks`: non-decisive checks that catch regressions or safety issues
- `inventory_coverage`: pages, transitions, interactions, assets, third parties, deploy/cache surfaces
- `active_candidate`: current ledger candidate id or `none`
- `ledger_path`: path to the JSONL ledger
- `evidence_paths`: reports, traces, screenshots, videos, logs, or benchmark files
- `stop_condition_status`: incomplete, success, blocked, interrupted, or unsafe without approval
- `blockers`: exact blocker and required user/external action, or `none`
- `protected_boundaries`: behavior, policy, data, config, or files that must not change

Use this shape unless the repo has a stronger local convention:

```md
# Page Speed Optimizer Goal State

started_at: <timestamp>
last_checkpoint_at: <timestamp>
elapsed_wall_clock: <duration>
user_budget: <time/token/scope budget or none provided>

## Current State

- current_phase: <discovering|measuring|patching|validating|resweeping|blocked|complete>
- last_completed_step: <step or none yet>
- active_step: <step or none>
- next_exact_action: <command, route, trace, file, or decision>
- stop_condition_status: <incomplete|success|blocked|interrupted|unsafe without approval>

## Verification

- primary_verifier: <strongest check or evidence bundle for this app>
- supporting_checks: <regression, visual, accessibility, build, or safety checks>
- last_validation: <command, artifact, or observable result>

## Inventory Coverage

- pages: <covered/pending/gated>
- transitions: <covered/pending/gated>
- interactions: <covered/pending/gated>
- assets: <covered/pending/gated>
- third_parties: <covered/pending/gated>
- deploy_cache_surfaces: <covered/pending/gated>

## Active Candidate

- active_candidate: <ledger id or none>
- ledger_path: tasks/tmp/page-speed-optimizer-ledger.jsonl
- evidence_paths: <reports, traces, screenshots, videos, logs, or none yet>

## Boundaries And Blockers

- protected_boundaries: <behavior, policy, data, config, or files that must not change>
- blockers: <none or exact blocker and required user/external action>
```

Do not mark a `/goal` run complete if this state document is missing, stale, or inconsistent with the ledger.

## Candidate Ledger

Keep one row per candidate in:

```text
tasks/tmp/page-speed-optimizer-ledger.jsonl
```

Each row should be JSONL with these fields when known:

```json
{
  "id": "short-stable-id",
  "candidate": "what may be slow, unstable, or visually janky",
  "surface": "page-load|route-transition|interaction|asset|third-party|cache|deploy|bfcache|field-data|regression-check",
  "route_or_flow": "route, user flow, transition, interaction, or URL",
  "navigation_type": "hard-navigation|soft-navigation|same-page-interaction|back-forward|repeat-visit|unknown",
  "environment": "prod-build-local|preview-url|production-url|dev-degraded|static-review",
  "profile": "mobile-throttled|desktop|field-data|custom|unknown",
  "coverage_status": "inventoried|measured|visual-reviewed|fixed|gated|rejected",
  "baseline_metrics": "LCP, INP/proxy, CLS, TTFB, FCP, long tasks, transfer, request count, or field data",
  "visual_evidence": "trace, screenshot, video, filmstrip, or none",
  "root_cause_hypothesis": "why this candidate may matter",
  "proposed_fix": "smallest useful change",
  "experiment": "measurement or check to run",
  "result": "before/after or rejection evidence",
  "disposition": "improved|already acceptable|not worth cost|unsafe without approval|blocked by missing realistic data|requires product/design/deployment decision|failed experiment",
  "validation": "commands, reports, traces, screenshots, logs, or artifacts",
  "risk": "tradeoff or protected boundary",
  "next_action": "resume point or none"
}
```

Performance-specific fields can be added when useful:

- `lcp`
- `inp_or_proxy`
- `cls`
- `fcp`
- `ttfb`
- `long_tasks`
- `bundle_or_transfer_cost`
- `third_party_cost`
- `bfcache_status`
- `field_data_reference`

Update the ledger or goal state after every candidate is classified, fixed, rejected, or gated. After interruption or context compaction, resume from the first high-impact row whose disposition still requires action.

The ledger is also the inventory receipt. Every high-impact page, transition, interaction, asset family, third-party cost, or deploy/cache surface discovered during the run must have a row or be covered by a row with a clear scope, even when it is already acceptable, static-reviewed only, or gated by missing safe access.

## Dispositions

- `improved`: accepted fix has before/after evidence and required regression checks passed.
- `already acceptable`: baseline evidence shows the candidate is not a meaningful bottleneck or visual issue.
- `not worth cost`: improvement is too small, tradeoff is too high, or complexity outweighs gain.
- `unsafe without approval`: action could affect product behavior, visual intent, accessibility, SEO, analytics, auth, billing, security, consent, deployment, caching policy, or compliance.
- `blocked by missing realistic data`: current environment cannot produce credible measurements, auth, seeded data, field data, or production-like runtime.
- `requires product/design/deployment decision`: the right fix changes design intent, routing behavior, loading semantics, analytics policy, deployment/CDN/cache config, or framework strategy.
- `failed experiment`: a plausible low-risk experiment did not improve the measured bottleneck.

## Shared Stop Condition

Stop only when every high-impact candidate is one of:

- improved and verified
- already acceptable
- not worth cost with evidence
- unsafe without approval
- blocked by missing realistic data
- requires product/design/deployment decision
- failed experiment with evidence

Do not stop only because one phase is complete, one Lighthouse score improved, one route got faster, one visual issue was fixed, or one benchmark improved.

Do not decide that the high-impact set is exhausted until the journey inventory is exhausted. A safe local fix plus a few unmeasured routes is a partial pass, not a completed page-speed optimization, unless every discovered high-impact page, route transition, interaction, and relevant cost surface has a ledger disposition.

The final answer must distinguish `journey-speed optimization complete` from narrower outcomes such as `safe local pass complete`, `lab-only pass complete`, or `blocked before production-like measurement`.

## Discovery

Establish the app and measurement target:

- framework and rendering model: Next.js, Remix, Vite, CRA, Astro, static, Rails/Laravel/server-rendered, webview, or unknown
- package manager, build command, start command, preview/deploy command, and test commands
- route definitions, navigation links, sitemap, app router files, page files, or generated routes
- auth requirements, seeded data requirements, and safe test credentials when available
- production, preview, or local production-like URL
- existing RUM, `web-vitals`, analytics, Lighthouse CI, Playwright, WebPageTest, bundle analysis, or performance-budget setup
- browser support policy when discoverable

Prefer production build/start. If production mode cannot run locally, use the closest safe target and mark the environment as degraded in the state document and every affected ledger row.

## Journey Inventory

Inventory:

- initial hard navigations for important pages
- in-session route transitions for important flows
- meaningful interactions after load, such as menus, filters, tabs, searches, modals, command palettes, forms, and expensive controls
- back/forward paths and bfcache eligibility where relevant
- repeat visits and cache-hit behavior where relevant
- route chunks, JS/CSS bundles, images, fonts, preloads, resource hints, and hydration/client-work costs
- third-party scripts, analytics, tag managers, embeds, consent surfaces, ads, support widgets, experiments, and payment/auth scripts
- deployment/cache surfaces such as TTFB, cache headers, CDN/static asset delivery, compression, and stale-sensitive pages when a URL is safely inspectable

Inventory rules:

- Search static routes, navigation components, app shell, layout files, build config, scripts, and tests before fixing. Do not stop after the first measured bottleneck.
- Record every discovered high-impact surface in the ledger with `coverage_status`.
- For each important page or flow, record the environment and profile used for measurement.
- For SPAs and client-side routing, always inspect route-transition UX; use soft-navigation metrics when supported, but do not require experimental APIs as a universal pass/fail gate.
- For back/forward paths, test user-visible behavior by default and use restored-reason diagnostics only when supported.
- When no safe auth, seeded data, public URL, production build, or field data is available, still do static matching and safe local measurement where reasonable, then mark the missing evidence as gated.

## Measurement Rules

- A passing test is not a performance measurement unless it records the relevant timing, plan, trace, or resource signal.
- Production-like measurements are the default target. Dev-mode measurements can guide debugging, but cannot prove a production speed win.
- Field data, RUM, CrUX, PageSpeed Insights, or `web-vitals` attribution should guide priority when available. Lab data is diagnostic and useful for before/after comparison, but field data wins when there is a conflict.
- Use representative device, CPU, and network profiles. Default toward mobile-like throttling unless the app is explicitly desktop-only or internal-admin-only.
- Repeat enough to avoid obvious noise when comparing before/after results.
- Use TBT, long tasks, and traces as synthetic proxies for interaction responsiveness when direct INP cannot be produced locally; do not silently equate TBT with INP.
- For visual transition claims, collect trace-backed evidence when possible. Use screenshots for stable visual issues and video or trace evidence for timing-sensitive flashes, blank frames, and transition jank.
- Static code reading can rank candidates, but it cannot prove a speedup.
- If two plausible causes fit the evidence, use the verification pivot and add the smallest probe that separates them.
- Record positive and negative experiments so the loop does not repeat failed ideas.

## Ranking

Rank candidates by:

- field impact or evidence from real users
- importance of the page, route, or user journey
- LCP, INP or proxy, CLS, TTFB, FCP, long tasks, and main-thread pressure
- visible blank gaps, stale content flashes, skeleton mismatch, layout jumps, focus loss, or scroll discontinuity
- request count, transfer size, render-blocking resources, bundle or route-chunk cost
- image/font/CSS/JS cost and cacheability
- third-party cost, especially scripts that block rendering or interaction
- bfcache misses or slow back/forward paths
- implementation risk, policy risk, and validation cost

## Safe Fix Examples

Safe fixes can include:

- narrowing or delaying non-critical first-party work
- removing dead first-party code or unused route imports
- improving image dimensions, formats, responsive sizes, priority, lazy loading, or LCP image delivery
- improving font loading, fallback sizing, or layout-shift-causing font behavior
- reducing avoidable client hydration or expensive render work
- splitting or deferring first-party route chunks when the route shape supports it
- fixing loading state mismatch, stale content flashes, focus/scroll continuity, or skeleton layout stability without changing product semantics
- adding focused performance regression checks when stable and low-noise
- documenting gated third-party, CDN, or deployment recommendations when direct changes need approval

Accept only measured wins or clearly verified visual improvements.

## Human-Decision Gates

Gate these instead of auto-fixing:

- product behavior, routing semantics, visual redesign, or UX intent changes
- analytics, consent, auth, billing, security, payment, support, ads, experiments, or compliance-related third-party changes
- SEO, metadata, canonical URL, sitemap, or indexing behavior
- cache headers, CDN config, production deployment config, or sensitive-page caching when policy matters
- cross-browser support policy changes
- framework-experimental transition systems or architecture-level rendering changes
- auth-gated or data-dependent flows without safe credentials or seeded data

## Anti-Cheat Rules

Do not count any of these as success:

- improving a Lighthouse score while leaving discovered high-impact journeys unclassified
- measuring only dev mode and claiming production speed improved
- hiding or bypassing a slow route, interaction, third-party script, or loading state instead of fixing or gating it
- disabling analytics, consent, auth, billing, security, support, ads, or compliance scripts without approval
- cropping screenshots, omitting trace/video evidence, or ignoring visible flashes and layout jumps that remain reproducible
- weakening accessibility, focus behavior, reduced-motion handling, SEO, or routing semantics to make a metric look better
- adding a flaky budget or regression check that creates noise without protecting a real performance surface

## Budget and Regression Checks

Add or recommend performance budgets only when:

- the route or flow is stable enough to measure repeatably
- the command is deterministic enough for local or CI use
- the threshold is based on a baseline, product target, or clear comparator
- the check catches a real regression without high false-positive risk

Reasonable budget surfaces include route chunk size, image bytes, total transfer, critical request count, Lighthouse/user-flow thresholds, trace-derived long-task ceilings, or visual regression receipts. Gate budgets when they would be flaky, environment-specific, or unsupported by the repo's validation surface.

## Closeout Requirements

For report-first runs, lead with ranked findings and the evidence behind each finding.

For `/goal` runs, final output must include:

- goal state path and ledger path
- started time, end time, and elapsed wall-clock time
- inventory coverage
- candidates improved
- candidates rejected with evidence
- human-decision gates
- validation commands and artifact paths
- whether field data was used, lab-only, or unavailable
- whether production-like measurement was used or the run was degraded
- residual risks and next action when incomplete
