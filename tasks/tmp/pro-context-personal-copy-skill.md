# Pro Context Bundle: Personal Copy Skill

Date: 2026-06-19
Target plan: `tasks/execution-plan-personal-copy-skill.md`
Research memo: `tasks/tmp/research-plan-personal-copy-skill.md`

## Request for Pro

Pressure-test this Deliver execution plan before implementation.

Focus on whether the plan is sufficient to create a global Codex skill named `$personal-copy` for grounded personal and professional writing. Identify missing guardrails, missing validation cases, scope overlap with `$plain-language` or `$clarifier`, weak sequencing, and any skill-authoring details that should change before implementation.

Do not implement. Return actionable findings only. For each finding, say whether it should be adopted, rejected, or deferred, and why.

## Current Goal

Create a global `$personal-copy` skill at `/Users/fromdarkness/.codex/skills/personal-copy`.

The skill should help with:

- social posts and devlogs
- bios, profile summaries, and About copy
- cover letters and career copy
- intros and outreach
- rewrites such as "make this sound like me" or "make this less AI"

Core intent: preserve source facts and the user's voice, avoid invented claims, and make the writing more specific, direct, and natural.

## Local Skill-Creator Constraints

The local `skill-creator` instructions say:

- Every skill needs `SKILL.md` with YAML frontmatter containing only `name` and `description`.
- The `description` is the trigger surface, so it must contain the practical "when to use" contexts.
- Use `agents/openai.yaml` for UI metadata, including a short `display_name`, `short_description`, `default_prompt`, and `policy.allow_implicit_invocation`.
- Use the initializer: `/Users/fromdarkness/.codex/skills/.system/skill-creator/scripts/init_skill.py`.
- Validate with `/Users/fromdarkness/.codex/skills/.system/skill-creator/scripts/quick_validate.py`.
- Keep `SKILL.md` lean and put conditional detail in direct `references/` files.
- Do not add README, changelog, placeholder examples, unused scripts, or extra docs.

Existing global user skills live under `/Users/fromdarkness/.codex/skills`, so this plan uses that local install convention rather than a repo-local Prime Directive skill path.

## Deep Research Findings Adopted Into The Plan

The research pass reviewed current Codex skill docs, skill-authoring guidance, plain-language/style guidance, career-services guidance, profile/bio guidance, AI-writing marker discussions, and AI-detection reliability sources.

Adopted findings:

- Keep `SKILL.md` focused on trigger, workflow, evidence rules, reference routing, and output contract.
- Add `references/format-playbooks.md` for format-specific guidance.
- Add `references/voice-cleanup.md` for the final pass.
- Require career-copy claims to be grounded in resume material, a job post, user notes, or explicit user confirmation.
- Have the skill flag unsupported career claims instead of filling gaps.
- Add bio/profile rules for audience, surface, length, currentness, and fact congruence across versions.
- Make the voice cleanup pattern-based: audience, specificity, rhythm, claim support, generic setup language, unsupported praise, long noun strings, signposting, overformatting.
- Treat AI-writing markers as review prompts with context exceptions, not absolute proof or banned-word rules.
- Add a non-goal: the skill does not optimize for AI-detector evasion or promise "undetectable" copy.
- Validate with realistic examples: `$page-speed-optimizer` post, short bio, cover-letter paragraph, unsupported career claim case, and same bio facts rewritten for different audiences without contradictions.

Rejected/deferred:

- Do not copy the attachment into the skill as a long banned-word list.
- Do not add scripts unless real repeated deterministic work appears later.
- Do not add voice-sample assets in v1 unless the user later asks for stronger calibration.

## Attachment Lessons To Integrate Carefully

The user attached a note listing common "AI writing" tells: grand openings, vague superlatives, uniform sentence blocks, signposting, bold-term list formatting, cliches, overuse of em dashes, stock contrast structures, and words such as "delve," "pivotal," "seamless," "robust," and "transformative."

The plan currently treats this as a cleanup checklist, not a hard ban. Exceptions should be allowed when a word is precise, technical, quoted, or part of the user's real voice.

## Current Execution Plan

```md
# Personal Copy Skill

Goal: Create a global `$personal-copy` skill for grounded personal and professional writing.

Please review this before I start.
Tell me what is wrong, missing, or out of order.

Deliver implementation instruction:
When asked to implement this doc, load the `$deliver` skill, use this file as the approved execution plan, scan every checkbox, and continue through final review, archive movement, commit, and finalization before the final handoff.

## What We Know

- The skill should live at `/Users/fromdarkness/.codex/skills/personal-copy`.
- It should support posts, devlogs, bios, cover letters, profile summaries, About copy, intros, outreach, and "make this sound like me / less AI" rewrites.
- It should preserve source facts and voice, avoid invented claims, and include a human-voice cleanup pass.
- The attachment about AI-writing markers should inform the cleanup pass, but not become a brittle copied banned-word wall.
- This is a global personal skill, not a Prime Directive repo-local workflow skill.
- Career materials should use AI as an editor or coach, not as the real author: claims must come from resume material, the job post, user notes, or explicit user confirmation.
- Voice cleanup should focus on audience, specificity, rhythm, and defensible claims rather than treating punctuation or individual words as proof of AI writing.
- Bio and profile copy should tailor the same facts to the target audience and surface while staying congruent with the user's real history across versions.

## Steps

### 1. Shape the skill contract

- [ ] Confirm the final trigger name, scope, and non-goals for `$personal-copy`.
- [ ] Define the evidence rules for lightweight posts, bios, cover letters, and outreach.
- [ ] Define bio/profile rules for audience, surface length, fact congruence, and currentness.
- [ ] Define the human-voice cleanup pass in concise, reusable instructions.
- [ ] Include a "specificity before polish" rule that cuts generic praise, unsupported superlatives, and long noun strings.
- [ ] Decide which details belong in `SKILL.md` versus reference files.
- [ ] Make the trigger description specific enough to avoid swallowing generic `$plain-language` or `$clarifier` requests.

### 2. Create the global skill

- [ ] Use the skill-creator initializer to create `/Users/fromdarkness/.codex/skills/personal-copy` with reference resources and `agents/openai.yaml`.
- [ ] Replace the generated `SKILL.md` with the final trigger description, workflow, safety rules, and output expectations.
- [ ] Add a `references/format-playbooks.md` file for posts, devlogs, bios, cover letters, profile summaries, intros, outreach, and rewrites.
- [ ] Add a `references/voice-cleanup.md` file that turns the attachment lessons into a compact final-pass checklist.
- [ ] In career-copy paths, instruct the skill to flag unsupported claims instead of filling gaps.
- [ ] In bio/profile paths, instruct the skill to tailor detail level to the audience and surface instead of stuffing every fact into every version.
- [ ] In voice-cleanup paths, treat AI-writing markers as review prompts with context exceptions, not absolute banned terms.
- [ ] Keep the skill free of unused scripts, placeholder examples, and extra documentation files.

### 3. Validate the skill

- [ ] Run the skill-creator `quick_validate.py` check against the new skill folder.
- [ ] Run realistic checks on the `$page-speed-optimizer` post, a short bio, and a cover-letter paragraph.
- [ ] Include one validation case where the draft tries to make an unsupported career claim and confirm the skill flags it.
- [ ] Include one validation case where the same bio facts are rewritten for different audiences without contradicting each other.
- [ ] Tighten the skill if the checks produce generic, inflated, unsupported, or obviously AI-styled copy.
- [ ] Inspect the generated `agents/openai.yaml` for accurate display text and default prompt.

### 4. Close out

- [ ] Report the created global skill path and validation results.
- [ ] Note any residual limitations, especially around cover letters requiring source material.
```

## Key Source Threads From Research

- OpenAI Codex skills docs and OpenAI Codex best practices: skill anatomy, trigger descriptions, progressive disclosure, and representative workflows.
- Anthropic Agent Skills article: keep the main skill lean, split conditional context into references, validate on representative tasks.
- Digital.gov, Microsoft Style Guide, Google Style Guide, Australian Style Manual, and OPM plain-language guidance: write for audience, use direct language, avoid jargon and long noun strings, read aloud, prune excess words.
- Purdue OWL, Harvard FAS, MIT CAPD, UConn, and NACE: career materials should be specific, defensible, tailored to the role, and not ghostwritten from invented AI claims.
- LinkedIn Help, Boise State Writing Center, and Purdue OWL audience guidance: profile and bio copy should match audience/surface while staying factually congruent.
- OpenAI classifier shutdown notice, Jisc, Vanderbilt, Wikipedia AI-writing signs, and Washington Post em-dash reporting: marker lists and detectors are unreliable as proof, but marker lists are useful as revision prompts.

## Questions For Pro

1. Is this scope too broad for one skill, or is "source-grounded personal/professional copy" a coherent boundary?
2. What guardrails are missing for cover letters, bios, outreach, or "less AI" rewrites?
3. Is the current reference split right, or should the plan use a different file layout?
4. Are the validation cases strong enough to catch generic, unsupported, or over-polished output?
5. What should change before implementation, if anything?
