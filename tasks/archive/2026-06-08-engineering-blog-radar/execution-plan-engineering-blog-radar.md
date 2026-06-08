# Engineering Blog Radar Automation

Goal: Create a standalone automation that watches selected engineering blogs, records what it has seen, and surfaces only rare, high-confidence repo improvement recommendations.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The automation should live under `/Users/fromdarkness/.codex/automations/engineering-blog-radar/`.
- Prime Directive should not own this automation unless repeated runs reveal a durable workflow rule worth promoting later.
- Every enabled source should be checked daily. There should be no global source cap and no priority-based rotation.
- The first pass should be capped so old archive history does not become a backlog project.
- The default decision is reject.
- Initial sources are Jane Street, Netflix, LinkedIn Engineering, Meta Engineering, Pinterest Engineering, Uber Engineering, Slack Engineering, AWS Architecture, Microsoft DevBlogs, Airbnb Engineering, GitHub Engineering, Discord, Spotify Engineering, and Figma Engineering.
- Initial target repos are `/Volumes/Code/autoprophet`, `/Volumes/Code/primedirective`, `/Volumes/Code/sortinghat`, `/Volumes/Code/tradinginsight`, `/Volumes/Code/woostats`, `/Volumes/Code/uttr`, `/Volumes/Code/markdown-mode`, `/Volumes/Code/bop-poc`, and `/Volumes/Code/bop-autoresearch`.

## Steps

### 1. Create the automation files

- [x] Create `/Users/fromdarkness/.codex/automations/engineering-blog-radar/` with `automation.toml`, `prompt.md`, `sources.json`, `target-repos.json`, `source-events.jsonl`, `seen-posts.jsonl`, `evaluations.jsonl`, and `outputs/`.
- [x] Shape `automation.toml` from the existing saved automation patterns so the run is attached to the intended workspace and uses `prompt.md` as its operating prompt.
- [x] Write `sources.json` with the initial engineering blog list and per-source metadata: stable `id`, name, site URL, feed URL when available, enabled flag, tags, first-pass limit, daily limit, optional filters, and notes.
- [x] Write `target-repos.json` with the initial repo list and per-repo metadata: stable `id`, path, enabled flag, tags, scan notes, and any repo-specific recommendation constraints.
- [x] Record one source initialization event for each initial blog in `source-events.jsonl`.

### 2. Encode the skeptical review prompt

- [x] Write `prompt.md` so each post is rejected unless it maps to a real local repo condition: a problem, bottleneck, repeated workflow cost, missing safeguard, quality gap, or clear optimization opportunity.
- [x] Require the automation to compare articles only against enabled repos in `target-repos.json`, and to record when a repo path is missing or unavailable instead of pretending it was checked.
- [x] Require every surviving recommendation to include the article claim, matching local repo condition, why it is obviously better than current behavior, implementation sketch, validation check, and counterargument.
- [x] Require the automation to write no daily output when every evaluated post is rejected.

### 3. Define first-pass and daily behavior

- [x] Set the first-pass behavior to check every enabled source, evaluate at most 3 recent posts per source, prefer posts from the last 90 days, and mark older unseen posts as `not-backfilled`.
- [x] Set daily behavior to check every enabled source, skip already seen canonical URLs, and evaluate up to each source's `daily_limit`.
- [x] Use decision statuses `reject`, `watch`, `consider`, `strong-candidate`, `not-backfilled`, and `skipped-source-limit`.
- [x] Document the add-a-blog path: add the source to `sources.json`, append a `source-added` event, run its first pass with the configured limit, then include it in daily checks.

### 4. Validate the configuration

- [x] Resolve or verify canonical URLs for the initial sources and keep shortlinks out of the source IDs.
- [x] Verify that every enabled target repo path exists before the first run, or mark the missing repo as unavailable in the evaluation ledger.
- [x] Check that the JSON files parse cleanly.
- [x] Check that broad sources such as Microsoft DevBlogs and Discord have include or exclude filters when needed.
- [x] Check that the automation prompt, source registry, target-repo registry, and ledgers match the plan and do not reference Prime Directive as the owner.

### 5. Prepare for review

- [x] Leave implementation changes unstarted until this plan is approved.
- [x] After implementation, run the focused validation checks, final review, archive this execution plan, commit created changes without touching unrelated user changes, and run the finalization gate.
