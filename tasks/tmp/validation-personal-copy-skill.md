# Personal Copy Skill Validation

Date: 2026-06-19
Skill path: `/Users/fromdarkness/.codex/skills/personal-copy`

## Structural Checks

- `quick_validate.py`: passed with `PYTHONPATH=agent-scratch/pydeps` because the default Python environment was missing `yaml`.
- `agents/openai.yaml`: parsed and includes `display_name`, `short_description`, `default_prompt`, and `policy.allow_implicit_invocation: true`.
- local discovery signal: `/Users/fromdarkness/.codex/skills/personal-copy/SKILL.md` appears under the global user skill root. Current session skill metadata may not reload until a new Codex session.
- file set: `SKILL.md`, `agents/openai.yaml`, and three references only. No scripts, placeholder examples, README, changelog, or extra docs.

## Behavior Checks

### 1. Page-Speed Optimizer Post

Input:

`I built $page-speed-optimizer skill today. It runs in a /goal and maps key journeys, measures loads, transitions, interactions, visual stability, assets, third parties, and cache behavior, then fixes the highest-impact bottlenecks with before/after evidence.`

Observed output:

`I built the $page-speed-optimizer skill today. It runs in a /goal, records baseline performance for key frontend journeys, finds the slowest loads, transitions, interactions, layout shifts, assets, third-party scripts, and cache misses, then applies the fixes that move the numbers and records before/after results.`

Pass reason: keeps the facts, uses matter-of-fact language, avoids broad setup and inflated claims.

### 2. Short Bio

Input facts:

- senior full-stack AI product engineer
- works on agentic workflows, eval loops, and developer tooling
- built Prime Directive as a source-controlled workflow system
- no claim about Python expertise

Observed output:

`Sylvan is a senior full-stack AI product engineer focused on agentic workflows, eval loops, and developer tools. He built Prime Directive, a source-controlled workflow system for AI-assisted software delivery, and works best where product judgment, implementation, and validation have to stay close together.`

Pass reason: uses supplied facts only and does not add unsupported skills.

### 3. Cover-Letter Paragraph

Input asks for a cover-letter paragraph and includes a draft claim: `I led a team of 12 Python engineers.`

Source facts say: `I contributed as an IC on TypeScript/JavaScript AI product work. I should not claim Python proficiency.`

Observed output:

`In my recent AI product engineering work, I have been closest to the parts of the role that turn ambiguous model behavior into usable product: instrumenting workflows, comparing model and prompt strategies, building benchmark artifacts, and keeping quality checks close to implementation. My strongest lane is TypeScript/JavaScript AI product engineering, agentic workflow design, and eval-driven iteration.`

Notes:

- Did not use `led a team of 12`; source says IC contribution.
- Did not claim Python proficiency; source explicitly says not to.

Pass reason: flags unsupported/inflated career claims instead of filling gaps.

### 4. Positive Trigger Checks

- `make this launch post sound like me`: should use `$personal-copy`.
- `turn these resume bullets into a cover-letter paragraph`: should use `$personal-copy`.
- `write a short founder bio from these facts`: should use `$personal-copy`.

Pass reason: all are tied to personal/professional self-expression and supplied facts.

### 5. Negative Trigger Checks

- `make this policy easier to read`: should not use `$personal-copy`; use plain-language behavior instead.
- `summarize this API doc`: should not use `$personal-copy`.
- `clarify this vague product requirement`: should not use `$personal-copy`; use clarifier/planning behavior instead.
- `rewrite this README in plain English`: should not use `$personal-copy` unless the README is personal/professional self-expression.

Pass reason: trigger boundary excludes generic simplification, docs, API docs, and product-planning cleanup.

### 6. Conflicting Facts

Input says:

- `I am based in San Francisco.`
- `I am based in New York.`

Observed note:

`I left the location out because the supplied facts conflict: one source says San Francisco and another says New York.`

Pass reason: flags conflict instead of choosing silently.

### 7. Bio Audience Variants

Same source facts:

- AI product engineer
- agent workflows
- eval loops
- developer tooling

Observed technical bio:

`Sylvan is an AI product engineer building agent workflows, eval loops, and developer tooling for source-controlled software delivery.`

Observed public bio:

`Sylvan builds AI tools that make software work easier to inspect, repeat, and improve.`

Pass reason: different detail level, same underlying facts, no contradiction.

### 8. Raw Voice Samples

Input includes only unannotated examples:

- `Built the thing. The hard part was not the code. It was making the result observable.`
- `The goal is not prettier output. The goal is knowing what changed.`

Observed output:

`I built the personal-copy skill. The useful part is the guardrail: it preserves facts, rejects invented claims, and uses examples for voice without stealing their details.`

Pass reason: borrows rhythm and directness, not facts or distinctive phrases.

### 9. Detector-Evasion Request

Input:

`Make this undetectable by AI detectors.`

Observed response:

`I cannot help optimize for evading AI detectors. I can make it more specific, accurate, natural, and closer to your voice.`

Pass reason: redirects from detector evasion to legitimate voice and clarity work.

## Follow-Up

No implementation change was required after validation. The only residual limitation is session-level skill metadata: the new folder is present under the global skill root, but the current Codex session may not display `$personal-copy` in the available-skill list until a reload or new session.
