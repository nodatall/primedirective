# Page Speed Optimizer Skill

Goal: Create a `$page-speed-optimizer` Prime Directive skill that improves real user-perceived journey speed, visual continuity, and navigation quality through one default workflow with no required mode flags.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The user wants `/goal $page-speed-optimizer` to be enough; the skill should not require remembered mode flags.
- The skill should optimize page load speed and also inspect page-to-page navigation for flashes, blank gaps, stale content, layout jumps, scroll/focus problems, loading-state mismatch, and transition jank.
- The closest local pattern is `$backend-optimizer`: a small public skill file, one detailed loop reference, UI metadata, README mirror, and contract ownership entry.
- `$backend-optimizer` explicitly routes frontend rendering and browser performance out of scope, so this new skill should own that surface.
- Deep research adopted these additions: INP/interaction latency, field-vs-lab caveats, soft-navigation and user-flow checks, bfcache/back-forward behavior, visual trace/video evidence, mobile/CPU/network profiles, reduced-motion/accessibility safeguards, and optional performance-budget/regression checks.
- User-provided deep research feedback sharpened the contract around journey speed, production-build evidence, SPA route-transition measurement, field-data assimilation, bfcache smoke checks, third-party cost, cache/CDN/header awareness, and ledger-driven completion.
- Goal-run behavior should borrow the useful `$plan-to-goal` discipline without requiring a separate user invocation: `/goal $page-speed-optimizer` should create and maintain a run state document with wall-clock tracking, resume state, primary verifier, stop-condition status, and evidence paths.

## Steps

### 1. Research and tighten the skill contract

- [x] Run the requested web-backed deep research pass against the current plan and record the working memo at `tasks/tmp/research-plan-page-speed-optimizer.md`.
- [x] Apply adopted deep-research findings to this execution plan before Pro analysis.
- [x] Incorporate the user-provided deep research critique into this execution plan and the research memo.
- [x] Dropped the requested ChatGPT Pro analysis pass after the Pro browser gate remained unavailable and the user approved implementation.
- [x] Recorded the blocked Pro gate at `tasks/tmp/pro-analysis-page-speed-optimizer.md`; no Pro findings were available to apply.
- [x] Refine this plan until the checklist is ordered, concrete, and free of material gaps.

### 2. Add the new skill

- [x] Create `skills/page-speed-optimizer/` with `SKILL.md`, `references/optimization-loop.md`, and `agents/openai.yaml`.
- [x] Make `$page-speed-optimizer` and `/goal $page-speed-optimizer` the only normal invocations; do not add user-facing mode flags.
- [x] Define the default workflow as journey-speed work: discover app stack and routes, run the closest practical production mode, inventory page loads, in-session navigations, interactions, and back/forward paths, inspect transition quality, fix the highest-impact safe issue, verify, and resweep.
- [x] Make production build/start the default measurement target. If only dev mode is available, mark the run degraded and prevent claims of representative production speed.
- [x] Include Core Web Vitals and supporting signals: LCP, INP, CLS, TTFB, FCP, TBT as an INP proxy in lab runs, long tasks, bundle/network cost, images, fonts, hydration, and expensive render work.
- [x] Include navigation-quality checks: scripted route transitions, SPA soft-navigation measurement when available, bfcache/back-forward behavior, scroll/focus behavior, stale-content flashes, blank gaps, skeleton mismatch, and layout jumps.
- [x] Include field-data assimilation: use CrUX, PageSpeed Insights, app RUM, or `web-vitals` attribution when a public or instrumented target exists; otherwise clearly label the run lab-only.
- [x] Define the candidate ledger at `tasks/tmp/page-speed-optimizer-ledger.jsonl` with rows for pages, transitions, interactions, assets, image/font costs, render bottlenecks, layout shifts, soft-navigation/bfcache issues, third-party scripts, and deployment/cache/CDN/header issues.
- [x] Define a required goal-run state document at `tasks/tmp/page-speed-optimizer-goal-state.md` for `/goal` runs. It should track `started_at`, `last_checkpoint_at`, elapsed wall-clock time, current phase, inventory coverage, primary verifier, supporting checks, active candidate, ledger path, evidence paths, stop-condition status, blockers, protected boundaries, and next exact action.
- [x] Require `/goal` runs to update the goal-run state document at start, after each meaningful checkpoint or candidate disposition, before interruption/compaction handoff, and before final closeout.
- [x] Define stop conditions so the goal cannot end after one Lighthouse win while high-impact page or transition issues remain unclassified.
- [x] Define safety rules for product behavior, visual design intent, reduced-motion preferences, accessibility, analytics, SEO, auth, third-party scripts, deployment/CDN/cache/header changes, framework-experimental transition APIs, and production-like measurements.

### 3. Wire the public contract

- [x] Add `$page-speed-optimizer` to the README quick reference and skill details.
- [x] Add a contract ownership row for the new skill and its reference files.
- [x] Keep README summaries short and leave detailed loop behavior in the new skill reference.

### 4. Validate and review

- [x] Run skill validation for `skills/page-speed-optimizer`.
- [x] Run `python3 scripts/validate-skill-contracts.py`.
- [x] Run `git diff --check`.
- [x] Run `./scripts/install-codex-plugin.sh`.
- [x] Add performance-budget or regression-check guidance early when stable routes, commands, and thresholds make the check low-noise; otherwise gate it instead of adding flaky CI.
- [x] Run a final branch review against this plan and fix material findings before closeout.
