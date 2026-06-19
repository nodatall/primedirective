# Deep Research Memo: Personal Copy Skill

web research status: complete
current date: 2026-06-19
timezone: America/Los_Angeles

## Project Context Snapshot

Product or workflow: a global Codex skill named `$personal-copy` for personal and professional writing.

Concrete stack: Codex skill folder under `/Users/fromdarkness/.codex/skills`, required `SKILL.md`, recommended `agents/openai.yaml`, optional `references/` files. Validation uses `/Users/fromdarkness/.codex/skills/.system/skill-creator/scripts/quick_validate.py`.

Highest-priority quality attributes: factual grounding, natural voice, low-jargon writing, useful format-specific guidance, no invented accomplishments, concise skill body, reliable triggering.

Constraints:

- The skill must be global, not Prime Directive repo-local.
- The skill should cover posts, devlogs, bios, cover letters, profile summaries, About copy, intros, outreach, and less-AI rewrites.
- The attachment's anti-AI-writing advice should inform a cleanup pass without becoming a copied wall of banned words.
- No private resume, job history, or customer data should be sent into web searches.

Version-first stack discovery notes:

- Existing global user skills found under `/Users/fromdarkness/.codex/skills`: `figma`, `figma-implement-design`, `imagegen`, `img-to-frontend`, `playwright`, and `trading-journal`.
- Skill creator resources are available under `/Users/fromdarkness/.codex/skills/.system/skill-creator`.
- No package/framework version affects this skill because the implementation is Markdown skill content plus `openai.yaml`.

External-query privacy notes:

- Searches use generic topics such as plain language, cover-letter guidance, profile writing, and AI-writing markers.
- Do not include personal employment history, private project details, or unpublished source text in external queries.

## Draft-Linked Research Agenda

| question_id | draft link | research bucket | question | possible impact |
| --- | --- | --- | --- | --- |
| RQ1 | execution plan Step 1: evidence rules | testing, verification, and failure handling | What source-grounding rules should the skill enforce for cover letters, bios, and profile copy? | May change cover-letter and bio rules in `SKILL.md` or `format-playbooks.md`. |
| RQ2 | execution plan Step 1: human-voice cleanup pass | core approach and writing patterns | Which plain-language and style-guide rules are durable enough to encode without overfitting to banned-word lists? | May change `voice-cleanup.md` and output review checklist. |
| RQ3 | execution plan Step 2: reference split | architecture patterns | How should the skill split core workflow from format-specific guidance without bloating `SKILL.md`? | May change file layout and progressive-disclosure instructions. |
| RQ4 | execution plan Step 3: realistic checks | verification and regression protection | What examples should validate that the skill produces grounded, non-generic writing across formats? | May change validation examples and acceptance checks. |

## Improvement Backlog

| candidate_id | candidate | expected impact | status |
| --- | --- | --- | --- |
| C1 | Add strict source-attribution rules for cover letters and bios. | Reduce invented accomplishments and generic claims. | testing |
| C2 | Add a compact plain-language checklist instead of a long banned-word list. | Improve voice without brittle overconstraint. | testing |
| C3 | Keep format playbooks in a reference file and load only when needed. | Keep `SKILL.md` concise. | testing |
| C4 | Add output variants only when useful or requested. | Avoid over-formatting simple rewrites. | testing |

## Evidence Ledger

| source_id | source_type | source_family | url | publication_date | last_updated_date | accessed_date | version_or_scope | supported_claims | counts_toward_external_primary_minimum | current_enough_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | official documentation | OpenAI Codex | https://developers.openai.com/codex/skills | unknown | 2026 visible footer | 2026-06-19 | Codex skills | Skills use `SKILL.md`, optional `references/`, optional `agents/openai.yaml`; descriptions drive implicit invocation; user-scoped skills are appropriate for personal workflows. | yes | Official current Codex documentation for skill structure and discovery. |
| S2 | official documentation | OpenAI Codex | https://developers.openai.com/codex/learn/best-practices | unknown | 2026 visible footer | 2026-06-19 | Codex best practices | Repeatable workflows should become skills; skills should stay scoped to one job, start with concrete use cases, and include clear inputs and outputs. | yes | Official current Codex guidance for when a skill is worth creating. |
| S3 | official guidance | U.S. Digital.gov / PlainLanguage.gov | https://digital.gov/guides/plain-language/principles | 2025 | 2025 | 2026-06-19 | plain-language principles | Write for the audience; use active voice; organize information; use lists where useful; avoid jargon without removing necessary technical terms. | yes | Official U.S. government plain-language guidance, current enough for durable writing rules. |
| S4 | official guidance | Microsoft | https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice | unknown | 2025-01-22 | 2026-06-19 | Microsoft Writing Style Guide | Use fewer words, write like speech, read aloud, use contractions, get to the point fast, prune excess words. | yes | Official Microsoft style guidance, recently updated. |
| S5 | official guidance | Google Developers | https://developers.google.com/style/tone | unknown | current page | 2026-06-19 | Google developer writing tone | Prefer conversational, friendly, respectful, direct writing; avoid slang, jargon, cliches, and culturally specific references. | yes | Official Google developer style guidance. |
| S6 | official guidance | Google Developers | https://developers.google.com/style/voice | unknown | 2024-10-15 | 2026-06-19 | active voice | Prefer active voice because it makes responsibility clear; passive voice is acceptable only for specific reasons. | yes | Official Google developer style guidance with concrete active/passive rules. |
| S7 | university career guidance | Purdue OWL | https://owl.purdue.edu/owl/job_search_writing/job_search_letters/cover_letters_3_writing_your_cover_letter/cover_letter_body_paragraphs.html | unknown | unknown | 2026-06-19 | cover letters | Cover letters should focus on a few qualifications, show rather than merely mention skills, and use specific experiences. | yes | Longstanding university writing-lab guidance, current enough for career-writing structure. |
| S8 | university career guidance | Harvard FAS career services | https://careerservices.fas.harvard.edu/ai-resumes-and-cover-letters/ | 2024 | unknown | 2026-06-19 | AI for resumes and cover letters | Use generated text as an edit, not final copy; ensure accuracy and authenticity; read aloud; tailor to the employer. | yes | University career-services guidance directly addressing AI-assisted career materials. |
| S9 | university career guidance | MIT CAPD | https://capd.mit.edu/resources/how-to-write-an-effective-cover-letter/ | 2022 | unknown | 2026-06-19 | cover letters | Effective cover letters are directed to a specific position/company, use brief stories, and connect experience to role needs. | no | Operator-practice career guidance from a credible university career office. |
| S10 | university career guidance | UConn Career Readiness | https://career.uconn.edu/resources/using-ai-for-resume-cover-letter/ | 2025 | unknown | 2026-06-19 | AI for resume/cover letters | Use AI for suggestions, then revise for voice; do not copy full AI output or allow false/embellished accomplishments. | no | Current university guidance on AI-assisted career writing. |
| S11 | professional association article | NACE | https://www.naceweb.org/career-readiness/best-practices/the-ghostwritten-candidate-ai-fraud-auto-apply-and-the-fight-for-authentic-career-readiness | 2026-06-17 | unknown | 2026-06-19 | AI career-material authenticity | Career materials must remain defensible and in the candidate's voice; generic AI-written materials widen the authenticity gap. | no | Current operator-practice source from a career-services association. |
| S12 | operator style guide | Mailchimp | https://styleguide.mailchimp.com/writing-principles/ | unknown | unknown | 2026-06-19 | content principles | Speak truth, avoid grandiose claims, use simple words, write like a human, and adapt tone to the situation. | no | Public style guide from an experienced content team; useful as operator practice, not universal law. |
| S13 | operator style guide | Mailchimp | https://styleguide.mailchimp.com/voice-and-tone/ | unknown | unknown | 2026-06-19 | voice and tone | Clarity matters more than entertainment; tone should adapt to reader state; use active voice and plain English. | no | Public style guide with concrete voice/tone principles. |
| S14 | operator research article | Nielsen Norman Group | https://www.nngroup.com/articles/tone-of-voice-dimensions/ | 2016-07-17 | 2023-08-16 | 2026-06-19 | tone dimensions | Tone can be calibrated across humor, formality, respectfulness, and enthusiasm; copy tone affects how readers receive the message. | no | Updated UX writing research article, useful for tone calibration. |
| S15 | community editorial guidance | Wikipedia | https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing | rolling community page | unknown | 2026-06-19 | AI-writing markers | AI-writing signs include over-formatting, phrasal templates, em dash overuse, and mechanical structure, but they are indicators to review rather than proof. | no | Useful as a community-maintained checklist of recurring patterns, not as authoritative detection. |
| S16 | official engineering article | Anthropic | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | 2025-10-16 | 2025-12-18 update noted | 2026-06-19 | Agent Skills | Skills should use progressive disclosure, keep `SKILL.md` lean, split large or conditional context into references, and validate with representative tasks. | yes | Owner-published engineering guidance for a closely related skill format. |
| S17 | official help documentation | LinkedIn | https://www.linkedin.com/help/linkedin/answer/a554351 | unknown | 2026, page says updated 4 months ago | 2026-06-19 | LinkedIn profile | Profile/About copy should represent the person, mission, motivation, skills, relevant experience, and current career goals; About should usually be one or two paragraphs. | yes | Official current profile guidance from the platform being targeted by many bios. |
| S18 | university writing-center guidance | Boise State Writing Center | https://www.boisestate.edu/writingcenter/professional-bio-guide/ | unknown | 2026 page footer | 2026-06-19 | professional bios | Bios should be tailored to audience and purpose, remain congruent across versions, use active voice, show rather than tell, and stay current. | no | Practical writing-center guidance for professional bio variants. |
| S19 | university writing guidance | Purdue OWL | https://owl.purdue.edu/owl/subject_specific_writing/professional_technical_writing/business_writing_for_administrative_and_clerical_staff/audience.html | unknown | 2026 page footer | 2026-06-19 | audience analysis | Audience changes expected form, genre, tone, level of detail, and where to start. | yes | University writing-lab guidance for cross-format professional writing. |
| S20 | university writing guidance | Purdue OWL | https://owl.purdue.edu/owl/subject_specific_writing/creative_writing/writers/professional_resources/professional_resources_for_creative_writers.html | unknown | 2026 page footer | 2026-06-19 | biographical notes and inquiry letters | Short bios should include only the facts the audience needs; humor and personality depend on audience and submission context. | no | Useful source for short bio and intro constraints. |
| S21 | official guidance | Australian Government Style Manual | https://www.stylemanual.gov.au/writing-and-designing-content/clear-language-and-writing-style/plain-language-and-word-choice | 2024 | unknown | 2026-06-19 | plain language | Plain language can express complex ideas; choose familiar words and clarify unfamiliar expressions. | yes | Official government style guidance, recent enough for durable writing rules. |
| S22 | official guidance | U.S. Office of Personnel Management | https://www.opm.gov/information-management/plain-language/ | unknown | unknown | 2026-06-19 | plain language | Use everyday words, active voice, action verbs, present tense, positive language, and avoid long noun strings. | yes | Official U.S. agency guidance aligned with federal plain-language rules. |
| S23 | official product notice | OpenAI | https://openai.com/index/new-ai-classifier-for-indicating-ai-written-text/ | 2023-01-31 | 2023-07-20 classifier shutdown note | 2026-06-19 | AI text detection | AI text classifiers are imperfect; OpenAI withdrew its classifier for low accuracy and warned against primary decision-making use. | yes | Primary source from an AI model provider about detection limits. |
| S24 | sector guidance | Jisc National Centre for AI | https://nationalcentreforai.jiscinvolve.org/wp/2023/03/17/ai-writing-detectors/ | 2023-03-17 | unknown | 2026-06-19 | AI writing detectors | AI detectors cannot conclusively prove AI authorship; style-only approaches are unreliable and easy to defeat. | no | Operator-practice source for AI detection limits. |
| S25 | university guidance | Vanderbilt Brightspace | https://www.vanderbilt.edu/brightspace/2023/08/16/guidance-on-ai-detection-and-why-were-disabling-turnitins-ai-detector/ | 2023-08-16 | unknown | 2026-06-19 | AI detection policy | False positives, lack of transparency, and privacy concerns made AI detectors unsuitable as a reliable decision tool. | no | Institutional operator source for why AI-detection-style gates are unsafe. |
| S26 | news/operator reporting | Washington Post | https://www.washingtonpost.com/technology/2025/04/09/ai-em-dash-writing-punctuation-chatgpt/ | 2025-04-09 | unknown | 2026-06-19 | em-dash AI tell debate | Em-dash overuse can be associated with AI discourse, but punctuation is not a reliable authorship signal and is also normal human style. | no | Current reporting that directly tests a common "AI tell" from the attachment. |

## Sources Reviewed

- OpenAI Codex skill docs and best-practices pages for skill structure, trigger descriptions, user-scope placement, and progressive disclosure.
- Anthropic skill authoring guidance as a cross-check for concise `SKILL.md` files, reference splitting, and representative-task validation.
- Plain-language guidance from Digital.gov, OPM, Australian Style Manual, Microsoft, Google, and Mailchimp.
- Career-writing and AI-use guidance from Purdue OWL, Harvard FAS, MIT CAPD, UConn Career Readiness, and NACE.
- Profile and bio guidance from LinkedIn, Boise State Writing Center, and Purdue OWL.
- Wikipedia's AI-writing signs page as a pattern source for the cleanup pass, with the caveat that punctuation or word markers are not proof.
- AI-detection limitation sources from OpenAI, Jisc, Vanderbilt, and Washington Post to falsify the idea that the skill should optimize for detector evasion.

## Findings by Bucket

### Core technical approach and architecture patterns

- The skill should stay instruction-only. No deterministic script is needed because the work is judgment-heavy writing and revision.
- `SKILL.md` should hold the trigger description, core workflow, evidence rules, and output contract.
- Format-specific material should live in `references/format-playbooks.md`.
- The cleanup pass should live in `references/voice-cleanup.md` so the main skill stays small.
- The format playbook should distinguish public posts, profile/About copy, short bios, cover letters, intros, outreach, and direct rewrites because those formats have different audience, length, and evidence expectations.

### APIs, interfaces, schemas, storage, or SDK constraints

- The only local interface is the skill folder contract: `SKILL.md`, `agents/openai.yaml`, and optional `references/`.
- `agents/openai.yaml` should use short UI-facing copy and a default prompt that explicitly mentions `$personal-copy`.

### Security, privacy, and operational readiness

- The skill should warn against sending private resume, job history, customer, or unreleased company material to external tools unless the user explicitly asks and the environment is trusted.
- The skill should avoid browsing by default for personal copy unless current external facts, a public job post, or a linked source must be verified.

### Testing, verification, observability, and failure handling

- The most useful validation is representative output: one post/devlog rewrite, one bio, and one cover-letter paragraph.
- Career-copy validation must check whether every specific claim is supported by resume/job-post/user notes or explicitly flagged.
- Voice validation should look for generic openings, broad setup, unsupported praise, stacked contrast formulas, long noun strings, and overformatted lists.
- Bio/profile validation should check that the copy is audience-fit, current, congruent with the supplied facts, and not overloaded with every detail.

### Current operator practice

- Career-services sources converge on treating AI as an editor or coach, not the final author.
- Content-style sources converge on plain, specific, audience-aware writing rather than a universal banned-word list.
- AI-writing marker sources are useful as review prompts, but superficial markers should not be treated as proof or absolute bans.
- Bio and profile sources converge on tailoring the same facts to the audience and surface, not inventing separate identities for each format.
- AI-detection limitation sources reinforce that the skill should not promise "undetectable" output or optimize for detector evasion. It should optimize for the user's actual meaning, evidence, and voice.

## Finding-to-Artifact Delta

| finding_id | research_question_id | bucket | disposition | recommendation | recommendation_level | support_type | source_ids | prd_tdd_sections_changed | execution_plan_sections_changed | task_plan_inputs_created | disposition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | RQ3 | architecture patterns | adopted | Keep `SKILL.md` lean and move format rules plus voice cleanup into references. | adopt now | official docs and cross-vendor skill guidance | S1,S2 | not applicable | Steps 1 and 2 | Create `references/format-playbooks.md` and `references/voice-cleanup.md`; keep `SKILL.md` core only. | Reduces trigger/context bloat and follows progressive disclosure. |
| F2 | RQ1 | verification and failure handling | adopted | For career materials, require support from resume, job post, user notes, or explicit user confirmation before making specific claims. | adopt now | career-services guidance | S7,S8,S9,S10,S11 | not applicable | Steps 1 and 3 | Add evidence rules and validation checks. | Prevents invented accomplishments and protects interview defensibility. |
| F3 | RQ2 | writing patterns | adopted | Use plain-language principles and voice cleanup, not a rigid banned-word wall. | adopt now | official style guidance plus operator style guides | S3,S4,S5,S6,S12,S13,S15 | not applicable | Steps 1 and 2 | Add cleanup checklist with pattern review and context exceptions. | Durable across formats and avoids overfitting to internet AI-detection folklore. |
| F4 | RQ4 | validation | adopted | Validate with three realistic outputs: devlog post, bio, and cover-letter paragraph with unsupported-claim checks. | adopt now | skill-authoring and career-copy guidance | S1,S2,S8,S10,S11 | not applicable | Step 3 | Add explicit realistic checks. | Checks the skill's actual purpose instead of only validating YAML. |
| F5 | RQ2 | writing patterns | rejected | Import the pasted attachment as a large absolute banned-word list. | avoid | synthesis from sources and attachment | S3,S4,S5,S12,S15 | not applicable | none | none | The list is useful as a signal, but absolute bans would reject precise language and bloat the skill. |
| F6 | RQ1 | core approach and audience fit | adopted | Add a bio/profile rule: tailor length, tone, and details to the surface and audience while keeping facts congruent across versions. | adopt now | platform and writing-center guidance | S17,S18,S19,S20 | not applicable | Steps 1, 2, and 3 | Add bio/profile-specific source and validation rules. | Broadens the skill beyond tweets and cover letters without making it generic marketing copy. |
| F7 | RQ2 | writing patterns | adopted | Add a "specificity before polish" rule that checks long noun strings, generic praise, and unsupported superlatives. | adopt now | official plain-language and operator style guidance | S3,S4,S5,S6,S12,S13,S21,S22 | not applicable | Steps 1 and 2 | Add to voice cleanup and validation checklist. | Multiple style guides converge on direct, audience-fit, concrete language. |
| F8 | RQ2 | writing patterns and safety | adopted | Add a non-goal: the skill does not try to evade AI detectors; it improves source-grounded writing and removes generic patterns because they weaken the copy. | adopt now | primary and operator evidence about detection limits | S15,S23,S24,S25,S26 | not applicable | Steps 1 and 2 | Add non-goal and cleanup framing. | Prevents the "humanizer" framing from turning into detector gaming. |

## Load-Bearing Falsification Pass

| claim_id | claim | why_load_bearing | current_support_source_ids | strongest_counterevidence_or_gap | falsification_searches_or_sources | outcome | artifact_or_conclusion_change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C-LB1 | The skill should be global, not repo-local. | Changes where the skill is created and how it is discovered. | S1,S2 | OpenAI's current public docs mention `$HOME/.agents/skills`, while this environment uses `/Users/fromdarkness/.codex/skills`; local skill-creator and existing user skills confirm the environment path. | Local `find /Users/fromdarkness/.codex/skills` plus OpenAI skills docs. | survived | Keep global path `/Users/fromdarkness/.codex/skills/personal-copy`. |
| C-LB2 | Career copy needs strict evidence rules. | Changes the workflow and validation criteria. | S7,S8,S9,S10,S11 | Some AI tools advertise "no made-up stuff," but career-services sources still require human review and defensibility. | Follow-up searches for AI resume/cover-letter guidance from Harvard, UConn, MIT, NACE. | survived | Add source-backed claim audit and unsupported-claim flagging. |
| C-LB3 | A banned-word wall should not be the core skill design. | Changes whether `voice-cleanup.md` is pattern-based or rule-list based. | S3,S4,S5,S12,S15 | Wikipedia and the attachment list recurring AI markers; however, style guides emphasize audience, clarity, and specificity over absolute word bans. | Follow-up searches on AI writing markers and official style guidance. | survived | Use concise "review these patterns" cleanup pass with context exceptions. |
| C-LB4 | References are justified despite the skill being small. | Changes file layout. | S1,S2 | A single SKILL.md could be simpler for v1, but multiple formats would make the core file longer and less trigger-focused. | OpenAI Codex skills docs and Anthropic skill best-practice cross-check. | survived | Keep two references and no scripts. |
| C-LB5 | The skill should cover bios/profile copy without becoming generic marketing copy. | Changes scope and trigger description. | S17,S18,S19,S20 | Broad scope can collide with `$plain-language` and generic marketing drafting; platform and writing guidance support narrower audience-fit, fact-congruent personal copy. | Follow-up searches for LinkedIn About, professional bio, short bio, and audience-writing guidance. | survived | Add explicit bio/profile playbook and non-goal language. |
| C-LB6 | Voice cleanup should prioritize specific facts over surface-level "humanizer" tactics. | Changes cleanup reference and validation. | S3,S4,S5,S12,S15,S21,S22 | AI-marker pages list superficial tells, but official style guidance points to clarity, audience, active voice, and pruning excess words as stronger durable rules. | Falsification pass against Wikipedia AI signs, Washington Post em-dash reporting, and government/style-guide plain-language guidance. | survived | Treat marker checks as secondary; keep source facts and audience fit as the primary cleanup gate. |
| C-LB7 | The skill should not promise or optimize for evading AI detection. | Changes non-goals and voice-cleanup language. | S23,S24,S25,S26 | The pasted attachment uses "humanizer" framing and marker lists; however, primary and institutional sources show detectors and single markers are unreliable. | Follow-up searches for AI detector reliability, false positives, and em-dash AI-tell reporting. | survived | Add "not detector evasion" as an explicit non-goal. |

## Adopt-Now, Watchlist, Avoid

Adopt now:

- Use `$personal-copy` as the skill name.
- Keep the skill global under `/Users/fromdarkness/.codex/skills/personal-copy`.
- Use `SKILL.md` for core workflow and reference routing.
- Add `references/format-playbooks.md` and `references/voice-cleanup.md`.
- Require career-copy claims to be grounded in supplied material or flagged.
- Treat AI-writing markers as cleanup prompts, not proof or absolute bans.
- Validate with realistic writing examples, not only YAML validation.

Watchlist:

- Add user voice samples later if the user wants a stronger voice model.
- Add a small examples reference only after real usage shows recurring failures.
- Consider a separate jobhunt integration later if the skill needs to read `/Volumes/Code/jobhunt` materials automatically.
- Consider optional per-user voice samples later, but only after the first version proves the source-grounded workflow.

Avoid:

- Do not create a generic marketing-copy skill.
- Do not import Claude-specific process notes.
- Do not include unused scripts.
- Do not make a long banned-word list the main control surface.
- Do not let cover letters invent metrics, motivations, responsibilities, or company-specific claims.
- Do not force every output into bullets, a fixed template, or a platform-specific format unless the user asks for that surface.
- Do not promise "humanizer," "undetectable," or detector-evasion behavior. Frame the work as clarity, specificity, and voice preservation.

## Decision Checklist for Implementation

- `SKILL.md` frontmatter includes all practical trigger phrases: social posts, devlogs, bios, cover letters, profile summaries, About copy, intros, outreach, and less-AI rewrites.
- `SKILL.md` tells Codex when to load each reference.
- `format-playbooks.md` has short, format-specific rules without templates that force generic structure.
- `voice-cleanup.md` includes the attachment lessons as pattern checks with exceptions for precise use.
- `voice-cleanup.md` says detector evasion is not the goal; the point is removing weak, generic, unsupported writing.
- Bio/profile playbooks require audience, surface, and supplied facts to control what is included.
- Career playbooks require the skill to return missing-claim prompts or a claim audit when source facts are insufficient.
- `agents/openai.yaml` has a concise display name, short description, default prompt, and implicit invocation policy.
- Validation includes quick validation plus realistic output review.

## Risks and Unknowns

- Exact personal voice cannot be fully captured without user writing samples. The v1 should preserve supplied wording and ask for samples only when the user asks for stronger calibration.
- Cover-letter quality depends on source material. If no resume, job post, or user notes are provided, the skill should produce a questions-or-claims-needed response instead of a polished invented draft.
- A broad trigger description could overlap with `$plain-language` and `$clarifier`; the description must emphasize personal/professional copy and source-grounded voice rather than generic simplification or coaching.
- Current public OpenAI docs name `$HOME/.agents/skills`, while this local Codex setup discovers `/Users/fromdarkness/.codex/skills`; implementation should follow the local installed-skill convention used by existing global skills.
- LinkedIn and career pages change over time; the skill should rely on durable format principles and use live browsing only when the user provides a current job post, profile target, or employer-specific claim to verify.
- Some users may ask for "make this undetectable." The skill should redirect that to making the writing accurate, specific, and natural rather than trying to beat detectors.

## Deep Research Completion Stamp

research_started_at: 2026-06-19T14:13:30-0700
research_completed_at: 2026-06-19T14:33:42-0700
elapsed_minutes: 20.2
duration_expectation_met: yes
under_20_minutes_explanation: not applicable
external_primary_sources_count: 14
operator_practice_sources_count: 12
source_family_count: 21
research_questions_answered: 4
buckets_reviewed: 6
follow_up_passes_completed: 5
load_bearing_claims_checked: 7
falsification_follow_up_passes_completed: 5
conclusions_changed_by_falsification: 0
adopted_findings_count: 7
rejected_or_deferred_findings_count: 1
prd_tdd_sections_changed: not applicable
execution_plan_sections_changed: What We Know; Step 1; Step 2; Step 3
task_plan_inputs_created: Create global skill, two references, `agents/openai.yaml`, realistic validation checks, explicit unsupported-claim/bio-congruence checks, and a detector-evasion non-goal.
evidence_bar_met: yes
