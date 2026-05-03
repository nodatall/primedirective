# Verification Pivot

Use this reference when analysis or repair is no longer limited by reasoning effort. It is limited by missing evidence.

## Purpose

Hard problems often fail because the agent keeps improving theories, prompts, or patches without creating back-pressure from reality.

The verification pivot forces a change in behavior: stop guessing, name what cannot be known from the current evidence, and define the smallest probe that would separate the plausible explanations.

## Trigger

Use this pivot when any of these are true:

- Two or more materially different explanations still fit the available evidence.
- The answer depends on runtime state, logs, provider behavior, persisted state, generated artifacts, UI state, or message flow that has not been observed.
- The next proposed step is another variation, prompt tweak, local patch, or policy change without a concrete observation that would prove it helped.
- A previous analysis, patch, or run failed and the next pass would reuse the same evidence.
- The same fix hypothesis has failed twice.
- The system is producing polished outputs, but the outputs do not reveal why a choice, transition, gate, or failure happened.

Do not invoke the pivot just because a question is hard. Invoke it when current evidence cannot distinguish the leading explanations.

## Output Contract

When the pivot triggers, the answer or work log must state:

- what is unknown
- which plausible explanations the current evidence cannot separate
- the smallest useful verification step
- the exact signal that would support or weaken each explanation
- whether the current skill should stop after naming the probe or implement the probe itself

Prefer one concrete next check over a menu of possibilities.

## Good Verification Steps

A good verification step is small enough to run soon and specific enough to change the next decision.

Use one of these shapes when appropriate:

- Add a focused log at the decision point that records inputs, selected branch, rejected branch, and reason.
- Add a deterministic test that builds the needed state and triggers the behavior without relying on a long manual run.
- Add a replay or fixture that feeds known inputs through the path and captures the output contract.
- Add a narrow behavior probe under `/codex-scripts/` when the observation is temporary or exploratory.
- Inspect persisted artifacts, database rows, generated reports, provider responses, or UI/browser state that the current theory depends on.

Do not call broad test suites, long exploratory runs, or another generation batch a verification pivot unless they expose the missing decision signal.

## Skill Behavior

Read-only skills should stop after naming the pivot unless the user separately asks for implementation.

Execution skills may build the smallest probe, run it, inspect fresh evidence, and then continue. Temporary probes belong in `/codex-scripts/`; promote them into real tests only when the check should remain part of the repo.

## Anti-Patterns

- Do not hide material uncertainty inside a polished best-guess memo.
- Do not say "try again with better prompts" when no observation explains the current failure.
- Do not keep patching the same hypothesis after repeated failures.
- Do not add logging everywhere. Add the smallest observation that separates the explanations.
- Do not treat a passing adjacent check as proof when the actual missing signal was not observed.
