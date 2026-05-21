---
name: deep-research-prompt
description: Create a paste-ready prompt for ChatGPT.com Deep Research from the current thread's plan or discussion. Use when the user wants to manually run ChatGPT Deep Research with a connected GitHub repo or files, especially to get first-principles adversarial critique, current best practices, alternatives, and external research before local planning or execution.
---

# Deep Research Prompt Skill

Create a prompt the user can paste into ChatGPT.com Deep Research.

## Activation

Invoke explicitly with `$deep-research-prompt`.

## Workflow

1. Treat the current conversation above the trigger as the source material.
2. Identify the plan, feature, architecture, or implementation direction being discussed.
3. Classify whether the request needs broad source discovery before evaluation.
4. Write one paste-ready ChatGPT Deep Research prompt.
5. Assume the user will manually select the relevant GitHub repo, files, or project context in ChatGPT before starting Deep Research.
6. Do not run web research, Pro browser analysis, local repo analysis, or implementation.
7. Do not ask questions unless the thread has no usable plan or target at all.

## Broad Source Discovery

Use broad source discovery when the request asks for best tools, APIs, providers, ways to do something, who does this, alternatives, a market map, people, companies, products, or what exists.

Also use it when the user names examples but says not to limit the search to them, or when the area may include niche, hidden, sales-led, startup, GitHub, community, marketplace, partner, or integration-only options.

When broad source discovery applies, the generated prompt must require this order:

1. Discovery phase.
2. Candidate inventory.
3. Evaluation and ranking.

Do not let the generated prompt start by ranking only the obvious named examples.

For broad source discovery prompts, require Deep Research to search across official docs, pricing pages, API references, SDKs, GitHub repos, integration docs, partner pages, API marketplaces, developer forums, comparison pages, startup directories, affiliate or partner networks, changelogs, demos, examples, and vendor pages that hide the real surface under words like developers, partners, platform, integrations, data, API, catalog, feed, or automation.

For broad source discovery prompts, require vocabulary expansion before searching. The prompt should ask Deep Research to search the user's exact words, synonyms, adjacent industry terms, workflow terms, buyer or user role terms, data-object terms, integration and API terms, commercial category terms, "alternative to X" terms, and "powered by", "integrates with", or "partner API" terms.

For broad source discovery prompts, require a missed-source check before finalizing. The check should ask what would be missed by official-docs-only searches, what providers use different language than the user, what adjacent industries solve the same workflow, what APIs are hidden behind affiliate, partner, enterprise, marketplace, SDK, or integration pages, what GitHub repos or unofficial SDKs point to real providers, and what a domain expert would search for that a generalist would not.

For broad source discovery prompts, require the final answer to include:

- discovery map: categories searched and why
- candidate inventory: all plausible sources found, including weak or uncertain ones
- shortlist: best options to test first
- comparison table
- recommended architecture or workflow
- concrete next tests
- dead ends
- search trail: representative queries and source paths used
- confidence notes: what may still be missing and where to search next

## Prompt Requirements

The generated prompt must ask ChatGPT Deep Research to:

- restate the current plan in plain language before critiquing it
- reason from first principles about the actual goal, constraints, and failure modes
- take an adversarial view and identify hidden assumptions, weak spots, and likely ways the plan could fail
- search the internet for current best practices, operator lessons, alternatives, and relevant failure reports when they could change the plan
- compare the current plan against stronger alternatives instead of only improving the existing plan
- when broad source discovery applies, actively search for unknown, niche, emerging, non-obvious, adjacent, and differently named solutions before ranking options
- when broad source discovery applies, warn against over-indexing on SEO-dominant, documentation-heavy, incumbent, or already-named providers
- distinguish adopt-now recommendations from speculative or watchlist ideas
- cite sources and explain why each source is current enough for the claim it supports
- produce concrete changes to make before local planning or execution

## Output

Return only:

1. A one-sentence note telling the user to select the relevant repo or files in ChatGPT Deep Research before submitting.
2. A fenced `text` block containing the prompt.

Keep the prompt specific to the thread. Do not use a generic template when the thread already contains concrete plan details.
