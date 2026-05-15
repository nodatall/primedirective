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
3. Write one paste-ready ChatGPT Deep Research prompt.
4. Assume the user will manually select the relevant GitHub repo, files, or project context in ChatGPT before starting Deep Research.
5. Do not run web research, Pro browser analysis, local repo analysis, or implementation.
6. Do not ask questions unless the thread has no usable plan or target at all.

## Prompt Requirements

The generated prompt must ask ChatGPT Deep Research to:

- restate the current plan in plain language before critiquing it
- reason from first principles about the actual goal, constraints, and failure modes
- take an adversarial view and identify hidden assumptions, weak spots, and likely ways the plan could fail
- search the internet for current best practices, operator lessons, alternatives, and relevant failure reports when they could change the plan
- compare the current plan against stronger alternatives instead of only improving the existing plan
- distinguish adopt-now recommendations from speculative or watchlist ideas
- cite sources and explain why each source is current enough for the claim it supports
- produce concrete changes to make before local planning or execution

## Output

Return only:

1. A one-sentence note telling the user to select the relevant repo or files in ChatGPT Deep Research before submitting.
2. A fenced `text` block containing the prompt.

Keep the prompt specific to the thread. Do not use a generic template when the thread already contains concrete plan details.
