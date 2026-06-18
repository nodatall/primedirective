# Deep Research Memo: Page Speed Optimizer Skill

web_research_status: completed
current_date_used: 2026-06-18
timezone: America/Los_Angeles

## Project Context Snapshot

Prime Directive is a Codex plugin source repo. The change under planning is a new `$page-speed-optimizer` skill, modeled after `$backend-optimizer` but owning frontend/browser performance. The intended default invocation is `/goal $page-speed-optimizer` with no required mode flags.

Known repo stack: Markdown skill contracts, YAML UI metadata, Python validation script, shell install script. Target skill users may run against many web stacks, so the skill must discover framework, routes, build/dev/prod commands, auth/data needs, and validation commands per repo.

Priority qualities: user-perceived speed, visual stability, route-transition quality, accessibility, measurement integrity, safe edits, maintainability, and low user invocation burden.

Privacy notes: External queries used generic stack and web-performance terms. No private source snippets, secrets, customer data, or repo-specific proprietary content were sent.

## Draft-Linked Research Agenda

| question_id | draft link | research bucket | question | possible artifact impact |
| --- | --- | --- | --- | --- |
| RQ1 | Step 2 default workflow | performance metrics | Should the skill measure only page load metrics, or also interaction and route-transition metrics? | Add INP, TBT proxy, soft navigation, and route-transition evidence requirements. |
| RQ2 | Step 2 verification | testing and observability | What evidence should prove a page or transition optimization? | Require production-like lab runs, Playwright traces/video/screenshots, field/RUM/CrUX when available, and before/after comparison. |
| RQ3 | Step 2 safety | accessibility and UX | What should prevent visual-transition fixes from harming users? | Add reduced-motion, focus/scroll, accessibility, SEO, analytics, and design-intent gates. |
| RQ4 | Step 3 public contract | maintainability | How much detail belongs in `SKILL.md` versus a reference file? | Keep activation and scope in `SKILL.md`; put loop, ledger, measurement, and stop gates in `references/optimization-loop.md`. |
| RQ5 | Step 4 validation | regression protection | Should the skill add CI performance budgets by default? | Make budgets optional and evidence-gated; avoid noisy budgets unless a stable command and target exist. |

## Improvement Backlog Tested

- Add INP and interaction latency as first-class, not secondary.
- Add soft-navigation and SPA route-transition measurement.
- Add bfcache and browser back/forward behavior.
- Require visual evidence for flashes and transition weirdness.
- Require field-vs-lab caveats and production-like builds.
- Add reduced-motion/accessibility checks for transition fixes.
- Avoid Lighthouse-score-only optimization.
- Avoid automatic removal of analytics, ads, scripts, CDN/cache headers, or deployment behavior.

## Evidence Ledger

| source_id | source_type | source_family | url | publication_date | last_updated_date | accessed_date | version_or_scope | supported_claims | counts_toward_external_primary_minimum | current_enough_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | primary official docs | Google web.dev | https://web.dev/articles/vitals | 2020-05-04 | 2024-10-31 | 2026-06-18 | Core Web Vitals | Core metrics are LCP, INP, CLS; field data matters; lab data is useful but not a substitute; TTFB/FCP/TBT are supporting metrics. | yes | Official Chrome/web.dev metric guidance; last updated after INP became stable. |
| S2 | primary official docs | Google web.dev | https://web.dev/articles/optimize-lcp | 2020-04-30 | 2025-03-31 | 2026-06-18 | LCP optimization | LCP work should separate server/TTFB, resource load delay, resource duration, and render delay instead of blindly preloading assets. | yes | Official Chrome/web.dev optimization guide updated in 2025. |
| S3 | primary official docs | Google web.dev | https://web.dev/articles/inp | unknown | unknown | 2026-06-18 | INP | INP measures interaction responsiveness across the page lifecycle and should be included in perceived performance work. | yes | Official metric definition for current Core Web Vitals. |
| S4 | primary official docs | Google web.dev | https://web.dev/articles/optimize-cls | unknown | unknown | 2026-06-18 | CLS optimization | CLS work should check images/media dimensions, embeds, injected content, fonts, and late layout changes. | yes | Official Chrome/web.dev CLS guidance. |
| S5 | primary official docs | Chrome for Developers | https://developer.chrome.com/docs/web-platform/soft-navigations | 2026-05 | unknown | 2026-06-18 | Soft Navigation API | SPA/soft navigation work needs special handling to measure page-like transitions and reset Web Vitals per soft navigation. | yes | Chrome docs published last month; directly current for route transitions. |
| S6 | primary official docs | Google web.dev | https://web.dev/articles/bfcache | 2023-05-25 | 2025-03-25 | 2026-06-18 | bfcache | Back/forward cache can make browser back/forward navigation instant and should be checked for navigation quality. | yes | Official guidance updated in 2025. |
| S7 | primary official docs | GoogleChrome Lighthouse | https://github.com/GoogleChrome/lighthouse/blob/main/docs/user-flows.md | unknown | active main branch | 2026-06-18 | Lighthouse user flows | User-flow audits combine navigation, timespan, and snapshot modes, and transitions/interactions should finish before ending timespans. | yes | Official Lighthouse repo docs on main branch. |
| S8 | primary official docs | Chrome DevTools | https://developer.chrome.com/docs/devtools/performance/reference | unknown | unknown | 2026-06-18 | DevTools Performance panel | Chrome Performance panel is appropriate for profiling runtime, layout shifts, long tasks, and Web Vitals signals. | yes | Official Chrome DevTools reference. |
| S9 | primary official docs | Chrome UX Report | https://developer.chrome.com/docs/crux/api | unknown | unknown | 2026-06-18 | CrUX API | Field data can be queried at URL/origin granularity when available; it complements lab measurements. | yes | Official CrUX API docs. |
| S10 | primary official repo | GoogleChrome web-vitals | https://github.com/GoogleChrome/web-vitals | active repo | active main branch | 2026-06-18 | web-vitals library | The web-vitals library measures Core Web Vitals and supports diagnostic attribution. | yes | Official GoogleChrome repository. |
| S11 | primary reference docs | MDN/Mozilla | https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion | unknown | 2026-06 | 2026-06-18 | prefers-reduced-motion | Visual transition work should respect users who request reduced non-essential motion. | yes | MDN browser reference updated recently. |
| S12 | primary standard guidance | W3C WAI | https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html | unknown | unknown | 2026-06-18 | WCAG 2.1 SC 2.3.3 | Motion triggered by interactions can distract or cause vestibular symptoms; users need a way to disable non-essential animation. | yes | Authoritative WAI/WCAG understanding doc. |
| S13 | primary framework docs | Next.js/Vercel | https://nextjs.org/docs/app/getting-started/linking-and-navigating | unknown | 2026-03-31 | 2026-06-18 | Next.js 16.2.2 navigation | Framework-specific navigation behavior can involve prefetching, streaming, loading UI, dynamic route waits, scroll handling, and hydration readiness. | yes | Current official docs with current version shown. |
| S14 | primary tool docs | Playwright | https://playwright.dev/docs/trace-viewer and https://playwright.dev/docs/videos | unknown | unknown | 2026-06-18 | Playwright traces and videos | Playwright traces/videos provide concrete evidence for route-transition state, screenshots, network, and action timing. | yes | Official Playwright docs. |
| S15 | primary framework docs | Vite | https://vite.dev/guide/build | unknown | unknown | 2026-06-18 | Vite production build | Vite performance checks should use production build output for production-serving claims. | yes | Official Vite docs. |
| O1 | operator practice | Shopify Performance | https://performance.shopify.com/blogs/blog/web-performance-tools-for-2026 | 2026-01-13 | unknown | 2026-06-18 | 2026 web performance workflow | Start from RUM/real problem areas, then validate root causes with DevTools traces and before/after local traces. | no | Current 2026 practitioner workflow from a large commerce platform. |
| O2 | operator practice | DebugBear | https://www.debugbear.com/blog/lighthouse-user-flows | 2021-11-08 | 2025-01-20 | 2026-06-18 | Lighthouse user flows | Cold-load Lighthouse misses interactive journeys; user flows can expose layout shifts and post-load accessibility/performance issues. | no | Updated 2025 practitioner guide aligned with official Lighthouse flow APIs. |
| O3 | operator practice | Performance Calendar | https://calendar.perfplanet.com/2025/chrome-devtools-for-debugging-web-performance/ | 2025 | unknown | 2026-06-18 | DevTools debugging workflow | Practical DevTools debugging should identify bottleneck type before patching. | no | Recent practitioner article from web performance community. |
| O4 | operator practice | DebugBear | https://www.debugbear.com/blog/fix-web-performance-devtools | 2024-08-15 | 2025-08-29 | 2026-06-18 | DevTools features | Modern DevTools traces and Web Vitals views help root-cause LCP, CLS, and runtime problems. | no | Updated 2025 practitioner guide. |
| O5 | operator practice | Shopify Performance | https://performance.shopify.com/blogs/blog/how-to-test-with-webpagetest | 2022-08-03 | unknown | 2026-06-18 | WebPageTest workflow | Filmstrip/waterfall comparison is useful for visual progress and before/after page-load evidence. | no | Older but still tool-specific practitioner workflow; used as supporting, not primary, evidence. |

## Findings By Bucket

### Standards and Adopt-Now Guidance

- F1: The skill must include INP and interaction latency. LCP/FCP/CLS alone would miss a major part of perceived speed. Adopted from S1, S3, S8, S10.
- F2: The skill must distinguish field, lab, and local evidence. Lab results can catch regressions and debug issues, but field data or RUM is the stronger priority signal when available. Adopted from S1, S9, O1.
- F3: SPA and client-route transitions need explicit soft-navigation or user-flow handling. Route changes can be user-perceived navigations even when the browser does not do a full page load. Adopted from S5, S7, O2.
- F4: Visual weirdness is not just subjective. Use screenshots/video/traces/filmstrips for flashes, blank gaps, stale content, layout jumps, and loading mismatches. Adopted from S7, S14, O2, O5.
- F5: The skill should inspect bfcache/back-forward behavior when navigation quality matters. Adopted from S6.
- F6: Transition fixes need accessibility constraints. Respect reduced motion and avoid focus/scroll regressions. Adopted from S11, S12, S13.
- F7: Production-like builds and mobile/CPU/network profiles are required before claiming user-facing speed wins. Adopted from S1, S8, S15, O1.

### Rejected or Deferred Ideas

- R1: Reject a Lighthouse-score-only workflow. It misses INP, soft navigations, visual transition quality, field variance, and auth/user-flow specifics.
- R2: Reject automatic removal or deferral of third-party scripts. The skill may measure impact and propose options, but analytics, ads, payment, support, auth, and compliance scripts need human approval.
- R3: Defer adding CI budgets by default. Budgets are useful after stable routes and commands exist, but noisy budgets can waste time or block unrelated work. The skill should add budget/regression checks only when it can define a credible baseline and command.
- R4: Defer broad cross-browser matrices by default. Use them when the issue is browser-specific, motion/accessibility-related, or when product support policy requires it.

### Emerging or Watchlist

- W1: Soft Navigation API support is current and relevant, but the skill should not require it to exist in every browser or stack. It should use it when available and otherwise rely on scripted user-flow evidence.
- W2: Chrome DevTools MCP and AI-assisted trace analysis are promising. The skill should prefer available browser automation and traces, but not make this tooling mandatory for every repo.

## Finding-to-Artifact Delta

| finding_id | research_question_id | bucket | disposition | recommendation | recommendation_level | support_type | source_ids | prd_tdd_sections_changed | execution_plan_sections_changed | task_plan_inputs_created | disposition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | RQ1 | performance | adopted | Add INP, interaction latency, and TBT proxy language to the skill loop. | adopt now | primary docs | S1,S3,S8,S10 | n/a | Step 2 default workflow | Skill reference checklist. | Missing this would make the skill obsolete for current Web Vitals. |
| F2 | RQ2 | verification | adopted | Require field/RUM/CrUX when available and lab runs for before/after debugging. | adopt now | primary + operator | S1,S9,O1 | n/a | Step 2 and Step 4 | Measurement rules. | Prevents overclaiming from local Lighthouse only. |
| F3 | RQ1 | route transitions | adopted | Treat soft navigation and user flows as first-class. | adopt now | primary + operator | S5,S7,O2 | n/a | Step 2 default workflow | Route-transition inventory and ledger rows. | Directly matches the user's flash/transition concern. |
| F4 | RQ2 | visual verification | adopted | Require Playwright trace/video/screenshots or equivalent visual evidence for transition quality. | adopt now | primary + operator | S7,S14,O2,O5 | n/a | Step 2 and Step 4 | Validation expectations. | Makes "weird flash" verifiable and reviewable. |
| F5 | RQ1 | navigation | adopted | Include bfcache/back-forward checks when relevant. | consider/adopt when applicable | primary docs | S6 | n/a | Step 2 default workflow | Navigation quality checklist. | Often high leverage but not always applicable. |
| F6 | RQ3 | accessibility | adopted | Add reduced-motion, focus, scroll, and accessibility safety gates. | adopt now | primary docs | S11,S12,S13 | n/a | Step 2 safety | Safety rules. | Prevents visual smoothness work from becoming inaccessible. |
| F7 | RQ2 | measurement | adopted | Require closest practical production mode before speed claims. | adopt now | primary + operator | S1,S8,S15,O1 | n/a | Step 2 default workflow | Measurement rules. | Dev mode measurements are misleading for user-facing wins. |
| F8 | RQ5 | regression protection | adopted with constraint | Add budgets/regression checks only when stable and low-noise. | consider | primary + operator | S7,O1 | n/a | Step 4 validation | Optional validation checklist. | Avoids fragile CI churn from noisy lab metrics. |

## Load-Bearing Falsification Pass

| claim_id | claim | why_load_bearing | current_support_source_ids | strongest_counterevidence_or_gap | falsification_searches_or_sources | outcome | artifact_or_conclusion_change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | INP must be first-class. | Without it, the skill would optimize only page load and miss interaction lag. | S1,S3,S10 | Lighthouse cannot measure INP directly in no-user lab runs. | S1 notes Lighthouse uses TBT proxy; S3 defines INP. | survived | Add INP plus TBT proxy and actual interaction testing. |
| C2 | Route transitions need visual evidence. | The user's main extra requirement is weird flashes between pages. | S7,S14,O2,O5 | Some flashes may be design intent or data-dependent. | Playwright trace/video docs and Lighthouse user-flow docs. | survived | Add screenshots/video/trace evidence and design-intent gates. |
| C3 | Soft navigation should be included but not mandatory. | SPA apps need it, but requiring it everywhere could block simple sites. | S5,S7,O2 | Soft Navigation API support is current but not universal. | Chrome soft navigation docs and Lighthouse user-flow docs. | revised | Use soft-navigation measurement when available; otherwise use scripted user flows. |
| C4 | Production-like builds are required for speed claims. | Dev mode can distort bundles, hydration, caching, and framework behavior. | S1,S8,S15,O1 | Some local apps cannot run production mode because of missing env/auth/data. | Vite production docs, Chrome DevTools, Shopify workflow. | survived | Add blocked/gated disposition for missing production-like target. |
| C5 | CI performance budgets should not be automatic. | Budgets can preserve wins, but noisy metrics can create false failures. | S7,O1 | Performance budgets are useful when stable commands and thresholds exist. | Lighthouse user-flow docs and operator practice. | revised | Make budgets optional, evidence-gated, and scoped to stable pages/transitions. |
| C6 | Transition fixes must respect reduced motion. | A smoother transition for most users can harm users with vestibular disorders. | S11,S12 | WCAG SC 2.3.3 is AAA, not necessarily a repo's existing compliance gate. | MDN and W3C guidance. | survived | Add safety rule regardless of formal compliance level. |

## Adopt-Now Checklist For Implementation

- Add one public skill with no required mode flags.
- Keep `SKILL.md` concise; put loop details in `references/optimization-loop.md`.
- Include page-load, interaction, route-transition, visual-stability, asset, third-party, and deployment/header candidates in one ledger.
- Require closest practical production mode before speed claims; gate missing env/auth/data.
- Use field/RUM/CrUX when available, but allow local lab evidence for before/after validation.
- Require screenshot/video/trace evidence for visual transition claims.
- Treat INP, long tasks, TBT proxy, hydration, and expensive render work as default inspection surfaces.
- Include soft-navigation and bfcache checks when the app has SPA-style navigation or meaningful browser back/forward flows.
- Add accessibility and reduced-motion gates for loading and transition changes.
- Gate analytics/third-party/CDN/cache/deployment changes when product or operator policy matters.

## Risks Or Unknowns That Remain

- The skill must work across Next.js, Vite, static sites, Rails/Laravel server-rendered apps, mobile webviews, and unknown stacks. The contract should specify discovery and evidence expectations rather than framework-specific implementation instructions.
- Soft Navigation API support and tooling will keep changing. Treat it as an optional measurement layer, not a mandatory path.
- Auth-gated flows and seeded data may block realistic measurements. The skill should record those as gated, not invent fake wins.
- Visual transition quality has subjective edges. The skill should capture evidence and fix obvious incoherent flashes/jumps, but design-intent decisions remain gated.

## User-Provided Deep Research Feedback Disposition

The user provided an additional deep-research critique after the initial memo. It was treated as supplemental planning evidence, not as a completed Pro analysis pass.

Adopted:

- Reframe the skill as journey-speed and visual-continuity optimization, not a page-load auditor.
- Make production build/start the default measurement target; dev-mode fallback must be marked degraded.
- Make INP, long tasks, interactions after load, and same-session navigation equal-status surfaces with initial page load.
- Add an explicit SPA branch: measure route-transition UX unconditionally, use soft-navigation metrics when supported, and do not require experimental soft-navigation APIs everywhere.
- Add bfcache/back-forward behavior as a default navigation-quality check, with API-level restored-reason diagnostics only when available.
- Add field-data assimilation from CrUX, PageSpeed Insights, app RUM, or `web-vitals` attribution when available, and label lab-only runs honestly.
- Make third-party cost, image cost, font cost, and cache/CDN/header behavior ledgerable surfaces.
- Add accessibility checks to the definition of safe when loading states, transitions, focus, live-region behavior, or reduced-motion behavior are affected.
- Add performance-budget and regression-hook guidance early when stable routes and low-noise thresholds exist.

Rejected or constrained:

- Do not make Lighthouse score improvement the primary success condition.
- Do not auto-remove or defer analytics, consent, auth, billing, security, or compliance-related third-party scripts.
- Do not auto-introduce framework-experimental transition systems as a generic fix.
- Do not require soft-navigation or bfcache diagnostic APIs as universal pass/fail gates when browser support is limited.

## Goal-Run State Addendum

The user pointed out that `/goal $page-speed-optimizer` also needs the operational discipline normally found in `$plan-to-goal` artifacts. This is adopted as a skill requirement.

The skill should not require the user to run `$plan-to-goal` first. Instead, a `/goal $page-speed-optimizer` run should create and maintain:

- `tasks/tmp/page-speed-optimizer-goal-state.md`: a readable state document for the current goal run.
- `tasks/tmp/page-speed-optimizer-ledger.jsonl`: the candidate inventory and disposition ledger.

The goal state document should include:

- `started_at`, `last_checkpoint_at`, elapsed wall-clock time, and any user-provided time or token budget.
- Current phase, last completed step, active step, and next exact action.
- Primary verifier and supporting checks for the current app.
- Inventory coverage for pages, transitions, interactions, assets, third parties, and deployment/cache surfaces.
- Active candidate, candidate ledger path, evidence paths, and latest validation result.
- Stop-condition status: success, blocked, incomplete, or interrupted.
- Blockers and protected boundaries.

The goal agent should update this document at start, after each meaningful checkpoint, after each candidate disposition, before compaction/interruption handoff, and before final closeout. A goal run should not be marked complete when this state document is missing or stale.

## Deep Research Completion Stamp

research_started_at: 2026-06-18T14:18:00-07:00
research_completed_at: 2026-06-18T14:40:00-07:00
elapsed_minutes: 22
duration_expectation_met: yes
under_20_minutes_explanation: n/a
external_primary_sources_count: 15
operator_practice_sources_count: 5
source_family_count: 10
research_questions_answered: 5
buckets_reviewed: core technical approach and architecture patterns; APIs and browser/framework constraints; performance and cost constraints; rollout and recovery behavior; accessibility and operational readiness; testing, verification, observability, and failure handling
follow_up_passes_completed: 3
load_bearing_claims_checked: 6
falsification_follow_up_passes_completed: 3
conclusions_changed_by_falsification: 2
adopted_findings_count: 8
rejected_or_deferred_findings_count: 4
prd_tdd_sections_changed: n/a
execution_plan_sections_changed: Step 2 default workflow; Step 2 safety; Step 4 validation
task_plan_inputs_created: n/a
supplemental_user_research_feedback_applied: yes
evidence_bar_met: yes
