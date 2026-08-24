#!/usr/bin/env python3
"""Validate Prime Directive skill metadata and owned workflow contracts."""

from __future__ import annotations

import argparse
import glob
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CONTRACTS = {
    "public-skill-metadata": "README.md; skills/*/SKILL.md",
    "architecture-guidance": "skills/shared/references/architecture/architecture-guidance.md",
    "plan-improvement": "skills/shared/references/planning/improve-plan.md",
    "deep-research": "skills/shared/references/planning/deep-research.md",
    "pro-analysis": "skills/shared/references/analysis/pro-browser-analysis.md",
    "task-file-contract": "skills/shared/references/execution/task-file-contract.md",
    "finalization-gate": "skills/shared/references/execution/finalization-gate.md",
    "review-protocol": "skills/shared/references/review/review-protocol.md",
    "review-calibration": "skills/shared/references/review/review-calibration.md",
    "finding-disposition": "skills/shared/references/review/finding-disposition.md",
    "dep-audit-checklist": "skills/shared/references/review/dep-audit-checklist.md",
    "swarm-lanes": "skills/shared/references/review/swarm-lanes.md",
    "plan-refine": "skills/plan-refine/SKILL.md",
    "plan-to-goal": "skills/plan-to-goal/SKILL.md",
    "review-plan": "skills/review-plan/SKILL.md",
    "skill-review": "skills/skill-review/SKILL.md",
    "reasoning-budget": "skills/shared/references/reasoning-budget.md",
}

MIRROR_CHECKS = [
    {
        "key": "plan-refine-challenge-schema",
        "error": "PD-CONTRACT-MIRROR-PLAN-REFINE",
        "owner": {"skills/plan-refine/SKILL.md"},
        "allowed": {"skills/shared/references/contract-ownership.md"},
        "single": ["previous_reviewer_round_had_blocker_or_material", "reviewer_dispositions"],
        "together": ["challenge_id", "pressure_type"],
    },
    {
        "key": "plan-refine-completion-stamp",
        "error": "PD-CONTRACT-MIRROR-PLAN-REFINE-STAMP",
        "owner": {"skills/plan-refine/SKILL.md"},
        "allowed": {
            "skills/shared/references/contract-ownership.md",
            "skills/shared/references/execution/task-file-contract.md",
        },
        "single": ["plan_refine_complete: yes", "ready_for_execution: yes"],
        "together": ["Refinement Completion Stamp", "fresh_reviewer_rounds"],
    },
    {
        "key": "deep-research-stamp-detail",
        "error": "PD-CONTRACT-MIRROR-DEEP-RESEARCH",
        "owner": {"skills/shared/references/planning/deep-research.md"},
        "allowed": {
            "skills/shared/references/analysis/pro-browser-analysis.md",
            "skills/shared/references/contract-ownership.md",
            "skills/first-principles-mode/SKILL.md",
            "skills/deliver/SKILL.md",
            "skills/shared/references/planning/generate-tasks.md",
            "skills/shared/references/planning/improve-plan.md",
            "skills/plan-refine/SKILL.md",
        },
        "single": ["evidence_bar_met: yes"],
        "together": ["Deep Research Completion Stamp", "evidence_bar_met"],
    },
    {
        "key": "pro-synthesis-stamp-detail",
        "error": "PD-CONTRACT-MIRROR-PRO",
        "owner": {"skills/shared/references/analysis/pro-browser-analysis.md"},
        "allowed": {
            "skills/shared/references/contract-ownership.md",
            "skills/deliver/SKILL.md",
            "skills/shared/references/planning/generate-tasks.md",
            "skills/shared/references/planning/improve-plan.md",
            "skills/plan-refine/SKILL.md",
        },
        "single": ["pro_synthesis_complete: yes"],
        "together": ["pro_result_read", "findings_reconciled"],
    },
    {
        "key": "finalization-baseline-detail",
        "error": "PD-CONTRACT-MIRROR-FINALIZATION",
        "owner": {"skills/shared/references/execution/finalization-gate.md"},
        "allowed": {
            "skills/shared/references/execution/task-file-contract.md",
            "skills/shared/references/contract-ownership.md",
            "skills/shared/references/review/review-protocol.md",
        },
        "single": [
            "finalization-baseline-<plan-key>",
            'git status --porcelain=v1 > "$baseline_tmp"',
        ],
        "together": [],
    },
]

INVOCATION_OVERRIDES = {
    "cleanup-merged-branches": "$cleanup-merged-branches",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(errors: list[str], code: str, message: str) -> None:
    errors.append(f"{code}: {message}")


def parse_front_matter_name(text: str) -> str | None:
    match = re.search(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        return None
    name = re.search(r"^name:\s*(.+)$", match.group(1), re.M)
    return name.group(1).strip() if name else None


def public_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in re.findall(r"`([^`]+)`", text):
        for part in re.split(r"\s+", raw.strip()):
            cleaned = part.strip("[](),;:")
            if cleaned.startswith("--"):
                tokens.add(cleaned)
            elif re.fullmatch(r"[a-z][a-z-]*=<[^>]+>", cleaned):
                tokens.add(cleaned)
    return tokens


def declared_skill_tokens(text: str) -> set[str]:
    parts: list[str] = []
    found_supported = False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.fullmatch(r"Supported modifiers?:", line.strip()):
            found_supported = True
            for next_line in lines[i + 1 :]:
                stripped = next_line.strip()
                if not stripped:
                    continue
                if not stripped.startswith("- "):
                    break
                parts.append(stripped)
            break
    if not found_supported:
        front = re.search(r"^---\n(.*?)\n---", text, re.S)
        if front:
            description = re.search(r"^description:\s*(.+)$", front.group(1), re.M)
            if description:
                parts.append(description.group(1))
    tokens = public_tokens("\n".join(parts))
    # Non-flag request options such as plan-key=<plan-key> should be public only
    # when they appear in activation/request-context sections.
    scoped_parts: list[str] = []
    scoped = re.search(r"^(?:Required request context|Activation examples):\n(.*?)(?:\n## |\Z)", text, re.S | re.M)
    if scoped:
        scoped_parts.append(scoped.group(1))
    tokens.update(token for token in public_tokens("\n".join(scoped_parts)) if not token.startswith("--"))
    return tokens


def readme_rows() -> dict[str, str]:
    readme = (ROOT / "README.md").read_text()
    rows: dict[str, str] = {}
    in_table = False
    for line in readme.splitlines():
        if line.startswith("| Skill |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("| ---"):
            continue
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        match = re.fullmatch(r"`([^`]+)`", cells[0])
        if match:
            rows[match.group(1)] = " ".join(cells[1:])
    return rows


def validate_skill_metadata(errors: list[str]) -> None:
    skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    skills: dict[str, set[str]] = {}
    for skill_file in skill_files:
        text = skill_file.read_text()
        name = parse_front_matter_name(text)
        if not name:
            fail(errors, "PD-SKILL-FRONTMATTER", f"{rel(skill_file)} missing front matter name")
            continue
        if name != skill_file.parent.name:
            fail(errors, "PD-SKILL-NAME", f"{rel(skill_file)} name {name!r} does not match directory {skill_file.parent.name!r}")
        skills[name] = declared_skill_tokens(text)

    rows = readme_rows()
    if set(rows) != set(skills):
        missing = sorted(set(skills) - set(rows))
        extra = sorted(set(rows) - set(skills))
        if missing:
            fail(errors, "PD-README-SKILL-MISSING", f"README missing skill rows: {', '.join(missing)}")
        if extra:
            fail(errors, "PD-README-SKILL-EXTRA", f"README has unknown skill rows: {', '.join(extra)}")

    for name, expected in sorted(skills.items()):
        readme_cell = rows.get(name, "")
        actual = public_tokens(readme_cell)
        if actual != expected:
            fail(
                errors,
                "PD-README-MODIFIERS",
                f"{name}: README tokens {sorted(actual)} do not match skill tokens {sorted(expected)}",
            )


def parse_owner_table(errors: list[str]) -> dict[str, str]:
    path = ROOT / "skills/shared/references/contract-ownership.md"
    if not path.exists():
        fail(errors, "PD-CONTRACT-OWNERSHIP-MISSING", f"{rel(path)} missing")
        return {}
    rows: dict[str, str] = {}
    in_owner_inventory = False
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            in_owner_inventory = line.strip() == "## Owner Inventory"
            continue
        if not in_owner_inventory:
            continue
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        key = cells[0].strip("`")
        if key in rows:
            fail(errors, "PD-CONTRACT-DUPLICATE-KEY", f"contract_key {key!r} appears more than once in contract ownership table")
        owner = cells[1].replace("`", "")
        rows[key] = owner
    return rows


def validate_owner_paths(errors: list[str]) -> None:
    rows = parse_owner_table(errors)
    for key, expected_owner in REQUIRED_CONTRACTS.items():
        actual_owner = rows.get(key)
        if actual_owner is None:
            fail(errors, "PD-CONTRACT-KEY-MISSING", f"contract_key {key!r} missing from contract ownership table")
            continue
        if actual_owner != expected_owner:
            fail(errors, "PD-CONTRACT-OWNER-MISMATCH", f"{key}: owner_path {actual_owner!r} should be {expected_owner!r}")
        for part in [p.strip() for p in actual_owner.split(";")]:
            if not part:
                fail(errors, "PD-CONTRACT-OWNER-PARSE", f"{key}: empty owner_path segment")
                continue
            if any(ch in part for ch in "*?["):
                if not glob.glob(str(ROOT / part)):
                    fail(errors, "PD-CONTRACT-OWNER-GLOB", f"{key}: owner_path glob {part!r} matched no files")
            elif not (ROOT / part).exists():
                fail(errors, "PD-CONTRACT-OWNER-PATH", f"{key}: owner_path {part!r} does not exist")
    for key, owner in sorted(rows.items()):
        for part in [p.strip() for p in owner.split(";")]:
            if not part:
                fail(errors, "PD-CONTRACT-OWNER-PARSE", f"{key}: empty owner_path segment")
                continue
            if any(ch in part for ch in "*?["):
                if not glob.glob(str(ROOT / part)):
                    fail(errors, "PD-CONTRACT-OWNER-GLOB", f"{key}: owner_path glob {part!r} matched no files")
            elif not (ROOT / part).exists():
                fail(errors, "PD-CONTRACT-OWNER-PATH", f"{key}: owner_path {part!r} does not exist")


def scan_mirrors(include_allowed: bool = False) -> list[tuple[str, str, str, str, str]]:
    hits: list[tuple[str, str, str, str, str]] = []
    for file_path in sorted((ROOT / "skills").glob("**/*.md")):
        rel_path = rel(file_path)
        text = file_path.read_text()
        for check in MIRROR_CHECKS:
            if rel_path in check["owner"]:
                disposition = "owner"
            elif rel_path in check["allowed"]:
                disposition = "allowed_summary" if rel_path == "skills/shared/references/contract-ownership.md" else "allowed_gate/check"
            else:
                disposition = "refactor/remove"
            reasons: list[str] = []
            for token in check["single"]:
                if token in text:
                    reasons.append(token)
            together = check["together"]
            if together and all(token in text for token in together):
                reasons.append(" + ".join(together))
            for reason in reasons:
                if include_allowed or disposition == "refactor/remove":
                    hits.append((check["error"], check["key"], rel_path, reason, disposition))
    return hits


def print_inventory() -> None:
    print("# Stale Mirror Inventory")
    print()
    current_hits = scan_mirrors(include_allowed=True)
    if not current_hits:
        print("No stale-mirror hits found by the final scanner.")
        return
    print("| error_id | pattern_key | path | matched | disposition |")
    print("| --- | --- | --- | --- | --- |")
    for error_id, key, path, reason, disposition in current_hits:
        print(f"| `{error_id}` | `{key}` | `{path}` | `{reason}` | `{disposition}` |")


def validate_mirrors(errors: list[str]) -> None:
    for error_id, key, path, reason, _disposition in scan_mirrors(include_allowed=False):
        fail(errors, error_id, f"{path} matches {key} outside owner/allowlist: {reason}")


def validate_plan_refine_completion_gate(errors: list[str]) -> None:
    plan_refine = (ROOT / "skills/plan-refine/SKILL.md").read_text()
    task_file_contract = (ROOT / "skills/shared/references/execution/task-file-contract.md").read_text()

    owner_tokens = [
        "## Refinement Completion Stamp",
        "plan_refine_complete",
        "fresh_reviewer_rounds",
        "reviewer_stop_gate",
        "ready_for_execution",
        "Do not write a successful stamp until at least one fresh reviewer subagent round has completed.",
    ]
    for token in owner_tokens:
        if token not in plan_refine:
            fail(errors, "PD-PLAN-REFINE-STAMP-OWNER", f"skills/plan-refine/SKILL.md missing completion-stamp token: {token}")

    shared_gate_tokens = [
        "Refinement Completion Stamp",
        "plan_refine_complete: yes",
        "ready_for_execution: yes",
        "A short risk checklist or ad-hoc note is not a valid refinement handoff.",
    ]
    for token in shared_gate_tokens:
        if token not in task_file_contract:
            fail(errors, "PD-TASK-FILE-REFINE-GATE", f"skills/shared/references/execution/task-file-contract.md missing refine gate token: {token}")


def validate_deep_research_completion_stamp(errors: list[str]) -> None:
    deep_research = (ROOT / "skills/shared/references/planning/deep-research.md").read_text()

    owner_tokens = [
        "## Deep Research Completion Stamp",
        "research_started_at",
        "research_completed_at",
        "elapsed_minutes",
        "duration_expectation_met",
        "under_20_minutes_explanation",
        "duration_expectation_met: yes",
        "Load-Bearing Falsification Pass",
        "load_bearing_claims_checked",
        "falsification_follow_up_passes_completed",
        "conclusions_changed_by_falsification",
        "evidence_bar_met: yes",
    ]
    for token in owner_tokens:
        if token not in deep_research:
            fail(errors, "PD-DEEP-RESEARCH-STAMP-OWNER", f"skills/shared/references/planning/deep-research.md missing completion-stamp token: {token}")


def validate_deep_research_prompt_contract(errors: list[str]) -> None:
    skill = (ROOT / "skills/deep-research-prompt/SKILL.md").read_text()
    readme = (ROOT / "README.md").read_text()

    skill_tokens = [
        "load-bearing falsification pass",
        "identify which claims would change the recommendation if wrong",
        "search for counterevidence when needed",
        "revise the conclusion if the evidence breaks",
        "avoid over-researching non-load-bearing claims",
    ]
    for token in skill_tokens:
        if token not in skill:
            fail(errors, "PD-DEEP-RESEARCH-PROMPT-FALSIFICATION", f"skills/deep-research-prompt/SKILL.md missing token: {token}")

    readme_tokens = [
        "load-bearing falsification pass",
        "revise the conclusion when the evidence breaks",
    ]
    for token in readme_tokens:
        if token not in readme:
            fail(errors, "PD-DEEP-RESEARCH-PROMPT-README", f"README.md missing deep-research-prompt token: {token}")


def validate_clarifier_editorial_review(errors: list[str]) -> None:
    skill = (ROOT / "skills/clarifier/SKILL.md").read_text()
    readme = (ROOT / "README.md").read_text()

    skill_tokens = [
        "Return concise feedback and ideas by default.",
        "Do not produce a complete rewritten draft unless the user explicitly asks for one.",
        "When the user explicitly asks for a rewrite, return one best revision.",
        "Never produce two versions merely to satisfy a quota.",
        "## Source Material",
        "Relevant repository or filesystem material retrieved for this task.",
        "### Semantic scope lock",
        "Treat the immediate draft as the default semantic boundary for any visible rewrite.",
        "Relevance and truth are not sufficient permission.",
        "## Choose the Task Mode",
        "Use only when the user explicitly limits the request to a phrase, sentence, typo, repeated word, grammar point, or punctuation choice.",
        "Do not infer this mode merely because the source is short or appears easy.",
        "## Context Reconstruction",
        "Search only the most likely relevant files and passages.",
        "Do not claim to have searched the conversation or filesystem unless that context was actually available and inspected.",
        "## Full-Pass Dispatch Gate",
        "The parent launches two independent fresh direction workers, `faithful-thesis` and `buried-tension`",
        "Do not put the two workers behind a nested orchestrator",
        "For every Clarifier request outside Explicit local edit, including a one-line resume bullet or professional statement, dispatch the work",
        "returns concise ideas by default or one selected revision when explicitly requested",
        "The runtime gate for every explicit `$clarifier` request outside Explicit local edit requires the two parent-launched named workers and one complete visible response.",
        "It has no minimum draft length.",
        "## Bounded private direction search",
        "Require every direction to anchor itself in a source quote or source-specific fact.",
        "Wait no more than 25 seconds for the parallel wave",
        "The timebox limits waiting, not quality: never return the first synthesized draft merely because the worker wave timed out.",
        "Use only one delegated wave.",
        "Select two to four private finalists when useful, but expose only the winner unless another direction creates a material user decision.",
        "If subagents are unavailable, run the two role-separated passes privately and sequentially; do not claim that they ran in parallel.",
        "## Job-Search Context",
        "Distinguish what the project or team did from what the user personally did.",
        "## Editing Order",
        "**Fidelity:** Preserve supported facts, intended certainty, voice, and ownership.",
        "**Compression:** Remove words and clauses that add no information.",
        "## Private Refinement Gate",
        "Do not launch critic subagents.",
        "### Fidelity veto",
        "adds a proper name, metric, achievement, technology, credential, product feature, or resume keyword",
        "translates live language into networking, consulting, marketing, or resume language",
        "Do not turn language such as `my agent found this`, `kind of rabbit-holing`, or `this could be fun` into a resume pitch",
        "create a compressed challenger to the leading candidate",
        "Replace framing phrases such as `took ownership of`, `was responsible for`, `worked to`, and `made improvements to` with the main action verb",
        "reject the longer version unless it adds a distinct fact, necessary attribution, or important qualification.",
        "`Took ownership of turning` -> `Turned`",
        "Treat clauses as semantic duplicates when they describe the same work under different labels.",
        "Treat research, observations, discovery, evaluation, and product testing as one overlapping activity family",
        "Labels alone never establish that the work was distinct; the source's use of both labels is not evidence.",
        "do not preserve `user research and end-to-end product testing` as two contributions unless inspected context distinguishes them concretely.",
        "replace the pair with one umbrella activity such as product validation or keep the more informative concrete method.",
        "Require every remaining clause to add a distinct supported fact, action, method, scope detail, constraint, or result.",
        "`Faster` describes an improvement; `fast` describes the resulting quality.",
        "prefer parallel end-state adjectives such as `turned an early proof of concept into a fast, polished experience` over mixed comparative phrasing such as `faster, more polished`",
        "Preserve the comparative when the baseline or measured improvement matters.",
        "## Core Writing Rules",
        "private reverse outline",
        "Treat topic sentences, passive voice, adverbs, transitions, paragraph formulas, and thesis placement as contextual choices rather than universal rules.",
        "### Clarity and evidence checks",
        "Treat a sentence over 30 words as a prompt to check whether it should be tightened or split, not as an automatic error.",
        "`due to the fact that` -> `because`",
        "Prefer relevant, supported data to subjective adjectives, adverbs, buzzwords, or ungrounded comparisons",
        "Never invent a number to make a claim sound objective.",
        "Flag weasel words such as `nearly all`, `significantly`, `arguably`, `best`, `would help`, `might bring clarity`, or `should result in benefits`",
        "Do not remove modal language that accurately represents real uncertainty, risk, or a conditional prediction.",
        "Apply the `so what?` test",
        "Avoid unexplained jargon, acronyms, and abbreviations when they would exclude the intended reader.",
        "lead with the shortest truthful answer that fits: `yes`, `no`, a number, or `I don't know` plus what would resolve the uncertainty.",
        "## Final Quality Gate",
        "For an explicit rewrite, a direct compressed challenger cannot improve it without losing meaning.",
        "## Response Format",
        "### Default coaching or thought-development request",
        "**Ideas:** The two to five most useful decisions, directions, questions, cuts, or emphasis changes.",
        "### Explicit rewrite request",
        "**Revision:** The one best supported version within the immediate draft's semantic scope.",
        "Do not append a diagnosis of weaknesses the revision already fixed.",
        "### Explicit feedback or critique request",
        "**Feedback:** The requested material critique of the original writing.",
        "If the user asks for both revision and feedback, lead with the revision and discuss only unresolved choices, factual uncertainty, or reusable patterns.",
    ]
    for token in skill_tokens:
        if token not in skill:
            fail(errors, "PD-CLARIFIER-EDITORIAL-REVIEW", f"skills/clarifier/SKILL.md missing token: {token}")

    readme_tokens = [
        "returns concise feedback and useful directions rather than ghostwriting a finished version",
        "a complete revision requires an explicit rewrite request",
        "the parent launches `faithful-thesis` and `buried-tension` directly",
        "treats the immediate draft as a semantic boundary",
        "do not enter rewritten prose without explicit permission",
        "turn casual curiosity into a resume pitch",
        "Worker timeouts never permit returning an unchecked first synthesis",
        "compares an explicitly requested revision with a compressed challenger",
        "prefers direct action verbs over framing such as `took ownership of turning`",
        "treats long sentences as a diagnostic",
        "prefers supported data to subjective qualifiers",
        "flags evidence-masking weasel words",
        "applies a `so what?` test",
        "defines necessary jargon",
        "does not invent metrics, erase honest uncertainty",
        "or impose business-writing rules on creative prose",
    ]
    for token in readme_tokens:
        if token not in readme:
            fail(errors, "PD-CLARIFIER-README", f"README.md missing Clarifier editorial-review token: {token}")

    hook_path = ROOT / "hooks/clarifier_dispatch_gate.py"
    spec = importlib.util.spec_from_file_location("clarifier_dispatch_gate", hook_path)
    if spec is None or spec.loader is None:
        fail(errors, "PD-CLARIFIER-DISPATCH", "unable to load hooks/clarifier_dispatch_gate.py")
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    short_resume_prompt = (
        "[$prime-directive:clarifier](/Volumes/Code/primedirective/skills/clarifier/SKILL.md) "
        "Drove user research and end-to-end product testing at an early-stage AI shopping startup."
    )
    if not module.explicit_request_needs_full_pass(short_resume_prompt):
        fail(errors, "PD-CLARIFIER-SHORT-DRAFT", "explicit one-line resume bullet did not enter the full pass")
    if module.explicit_request_needs_full_pass("$clarifier how does Clarifier choose directions?"):
        fail(errors, "PD-CLARIFIER-META", "meta question incorrectly entered the full pass")
    if module.LOCAL_ONLY.search("$clarifier rewrite just this phrase") is None:
        fail(errors, "PD-CLARIFIER-LOCAL", "explicit phrase-only request did not match Near-Done Mode")
    if module.requested_response_kind(short_resume_prompt) != "ideas":
        fail(errors, "PD-CLARIFIER-DEFAULT-IDEAS", "bare Clarifier draft did not select feedback-and-ideas output")
    if module.requested_response_kind("$clarifier feedback on this paragraph") != "feedback":
        fail(errors, "PD-CLARIFIER-FEEDBACK", "explicit critique did not select feedback output")
    if module.requested_response_kind("$clarifier rewrite this paragraph") != "rewrite":
        fail(errors, "PD-CLARIFIER-REWRITE", "rewrite request did not select revision output")
    if module.requested_response_kind("$clarifier feedback and rewrite this paragraph") != "rewrite":
        fail(errors, "PD-CLARIFIER-BOTH", "combined feedback and rewrite did not keep revision-first output")
    if not module.full_response_is_present("**Revision:** Turned the prototype into a fast, polished product."):
        fail(errors, "PD-CLARIFIER-ONE-REVISION", "one selected revision did not satisfy the dispatch gate")
    if not module.full_response_is_present(
        "**Ideas:** Keep the genuine curiosity and cut anything that turns it into a resume pitch.",
        "ideas",
    ):
        fail(errors, "PD-CLARIFIER-IDEAS-SHAPE", "default coaching output did not satisfy the dispatch gate")
    if module.full_response_is_present(
        "**Revision:** I built Prime Directive and reduced evaluation time from eight hours to one.",
        "ideas",
    ):
        fail(errors, "PD-CLARIFIER-SLOP-SHAPE", "unsolicited resume-style rewrite satisfied the default ideas gate")
    if module.full_response_is_present("**Plain version** A.\n\n**Alternative version** B."):
        fail(errors, "PD-CLARIFIER-OLD-SHAPE", "old two-version output incorrectly satisfied the new dispatch gate")
    if not module.full_response_is_present(
        "**Feedback:**\n\n**Reader effect:** Abstract.\n\n**Recommendation:** Use the direct verb.",
        "feedback",
    ):
        fail(errors, "PD-CLARIFIER-FEEDBACK-SHAPE", "explicit feedback output did not satisfy the dispatch gate")
    if module.agent_task_name("Agent", {"task_name": "faithful_thesis"}) != "faithful-thesis":
        fail(errors, "PD-CLARIFIER-DIRECT-WORKER", "direct faithful-thesis launch was not detected")
    exec_wrapped_worker = {
        "input": "await tools.multi_agent_v1__spawn_agent({task_name: 'buried-tension'})"
    }
    if module.agent_task_name("exec", exec_wrapped_worker) != "buried-tension":
        fail(errors, "PD-CLARIFIER-EXEC-WORKER", "exec-wrapped buried-tension launch was not detected")
    if not module.required_workers_present(
        {"faithful_thesis_launched": True, "buried_tension_launched": True}
    ):
        fail(errors, "PD-CLARIFIER-WORKER-GATE", "complete direct worker wave did not satisfy the gate")
    if module.required_workers_present({"faithful_thesis_launched": True}):
        fail(errors, "PD-CLARIFIER-MISSING-WORKER", "incomplete direct worker wave satisfied the gate")


def validate_first_principles_adversarial_council(errors: list[str]) -> None:
    first_principles = (ROOT / "skills/first-principles-mode/SKILL.md").read_text()
    rubric = (ROOT / "skills/first-principles-mode/references/analysis-rubric.md").read_text()
    readme = (ROOT / "README.md").read_text()

    skill_tokens = [
        "default adversarial council",
        "Start with independent lane memos",
        "Use 3-5 lanes",
        "claim, decisive evidence, strongest counterevidence",
        "Run two rebuttal rounds by default.",
        "Run a third rebuttal round only when",
        "leading explanation, confidence band, decisive evidence gap, or next verification step",
        "Preserve serious minority reports",
        "internal evidence matrix",
        "load-bearing claims",
        "compact Council Audit Summary only when",
        "Do not include a debate transcript.",
    ]
    for token in skill_tokens:
        if token not in first_principles:
            fail(errors, "PD-FIRST-PRINCIPLES-COUNCIL", f"skills/first-principles-mode/SKILL.md missing adversarial-council token: {token}")

    rubric_tokens = [
        "run the default adversarial council",
        "Start with independent lane memos",
        "Require rebuttal rounds.",
        "Use two rebuttal rounds by default",
        "Synthesize from an internal evidence matrix",
        "load-bearing claims",
        "Council Audit Summary only when",
        "parallel memos without rebuttal",
    ]
    for token in rubric_tokens:
        if token not in rubric:
            fail(errors, "PD-FIRST-PRINCIPLES-COUNCIL-RUBRIC", f"skills/first-principles-mode/references/analysis-rubric.md missing adversarial-council token: {token}")

    readme_tokens = [
        "default adversarial council",
        "independent lanes and rebuttal rounds",
        "load-bearing claims",
    ]
    for token in readme_tokens:
        if token not in readme:
            fail(errors, "PD-FIRST-PRINCIPLES-COUNCIL-README", f"README.md missing first-principles council token: {token}")


def validate_deliver_terminal_gate(errors: list[str]) -> None:
    deliver = (ROOT / "skills/deliver/SKILL.md").read_text()
    plan_to_goal = (ROOT / "skills/plan-to-goal/SKILL.md").read_text()
    finalization_gate = (ROOT / "skills/shared/references/execution/finalization-gate.md").read_text()
    readme = (ROOT / "README.md").read_text()
    deliver_agent = (ROOT / "skills/deliver/agents/openai.yaml").read_text()

    deliver_tokens = [
        "Execution scope is the entire unchecked remainder of `tasks/execution-plan-<plan-key>.md`",
        "`$deliver refine`, `$deliver plan`, `refine it`, `turn this into a deliver plan`, or equivalent keeps the same checklist file",
        "When the user later says `implement`, `implement the doc`, `implement this plan`, `go ahead`, or equivalent",
        "When a plan document contains the Deliver implementation instruction, that document is enough to route implementation back through this skill.",
        "plain-language deliver requests such as `deliver`, `refine it`, `implement deliver`, `deliver this`, `start deliver`, or `continue deliver`",
        "Later user messages such as `implement`, `implement deliver`, `go ahead`, `start`, `continue`, `finish it`, `do it`, or `ship it` are approval/resume signals",
        "Deliver implementation instruction:",
        "Include the exact Deliver implementation instruction near the top of every normal execution plan.",
        "Optional frontend mockup: `tasks/ui-mockup-<plan-key>.html`",
        "Frontend plan mockup rules:",
        "create a simple standalone HTML/CSS mockup at `tasks/ui-mockup-<plan-key>.html`",
        "Link the mockup from the execution plan with a short `Visual mockup:` note",
        "If `tasks/ui-mockup-<plan-key>.html` exists, move it to the same archive directory",
        "Normal mode: ask the user to say `implement the doc` when it looks right, or tell you what is wrong, missing, or out of order.",
        "Non-canonical plan-like files such as `tasks/tasks-plan-<plan-key>.md`, `tasks/*-spec.md`, pasted checklists, and review notes are source material only for `$deliver`.",
        "Do not continue into implementation with only a `tasks-plan`, spec, or notes file as the scope artifact.",
        "do not treat the absence of a canonical execution plan as permission to skip final review, archive movement, or the finalization gate.",
        "If the current turn starts from a generic approval or resume message while an active unarchived `$deliver` execution plan exists",
        "After every useful commit or plan update, immediately re-open the execution plan",
        "After the last checkbox is checked, implementation is still not terminal.",
        "review-deliver-final-<plan-key>.md",
        "Skipping final review is allowed only when a real blocker prevents it",
        "Commit the archive move and any final review, checklist, cleanup, implementation, or validation edits before the final handoff.",
        "Run the finalization gate before the final handoff.",
        "If any unchecked in-scope checkbox remains, continue execution instead of handing off",
        "Use a fresh reviewer subagent by default when subagents are available.",
        "Assign one worker agent by default when worker agents are available.",
        "Do not mention whether a subagent was or was not used in the user-facing review request",
        "Do not mention whether worker agents were or were not used",
        "Supported modifiers:",
        "`--deep-research`",
        "`--pro-analysis`",
        "`--fast`",
        "Fast mode skips only the initial user plan-review pause after refinement; it does not skip the written plan, research, Pro analysis, refinement, validation, final review, archive, commit, or finalization.",
        "$deliver --fast` creates or resumes the same readable execution plan, runs the same research/Pro/refinement gates, treats the refined plan as approved scope, and continues directly to step 7 without the initial user plan-review pause.",
        "Stop for user review of the Markdown plan file unless `--fast` is present.",
        "Do not launch a review app or external viewer.",
        "Normal mode: link `tasks/execution-plan-<plan-key>.md` and ask the user to review the Markdown file.",
        "`--fast` mode must still stop for destructive or data-loss actions",
        "When `--deep-research` is present, compose `skills/shared/references/planning/deep-research.md` after the readable execution plan exists and before any Pro analysis or refinement.",
        "tasks/tmp/research-plan-<plan-key>.md",
        "Deep Research Summary",
        "Hard-stop before Pro analysis or refinement if the Deep Research Completion Stamp is incomplete or `evidence_bar_met: yes` is missing.",
        "When `--pro-analysis` is present, compose `skills/shared/references/analysis/pro-browser-analysis.md` after the readable execution plan exists and before the refinement loop.",
        "tasks/tmp/pro-analysis-<plan-key>.md",
        "Pro Findings Summary",
        "Hard-stop before refinement if the Pro synthesis gate is incomplete.",
    ]
    for token in deliver_tokens:
        if token not in deliver:
            fail(errors, "PD-DELIVER-TERMINAL-GATE", f"skills/deliver/SKILL.md missing terminal-gate token: {token}")

    deliver_draft_tokens = [
        "$deliver` creates or resumes a readable execution plan at `tasks/execution-plan-<plan-key>.md`",
        "$deliver discuss` is a legacy alias for the draft-update behavior. Do not prefer it or introduce it as a separate workflow.",
        "Do not use this step for bare `$deliver`, `$deliver --deep-research`, `$deliver --pro-analysis`, `$deliver --fast`, `$deliver plan`, `$deliver refine`, `deliver this`, or equivalent requests",
        "Draft instruction:",
        "When asked to keep discussing or update this doc, load the `$deliver` skill and update this file as the current draft plan.",
        "When asked to refine this, turn this into a deliver plan, or make the plan, load the `$deliver` skill, keep this same checklist file, replace this instruction with the Deliver implementation instruction, refine the plan, and ask for review before implementation.",
        "The draft plan is for discussion. Keep it as plain as possible",
        "Please review this before I refine it.",
        "Use phases plus checkboxes from the start, even while the plan is still rough.",
        "Keep draft checkboxes concrete enough to discuss, but do not pretend every implementation detail is final.",
        "Do not add PRD, TDD, task-plan, status-log, audit-log, readiness, or topical section headers such as `The Problem`, `Current Best Plan`, `Decisions So Far`, or `Still Unclear`.",
        "Treat user removals as edits to the current plan, not as content to preserve.",
        "Do not turn removed scope into repeated `do not...` reminders.",
        "Do not carry rejected or removed scope into execution-plan work items.",
        "Write open questions as checkboxes, prefixed with `Open question:` when useful, so they are easy to resolve or remove during discussion.",
        "Do not refine, execute, or commit implementation work from the draft plan.",
        "If the user asks to refine the draft into a deliver plan, keep the same `tasks/execution-plan-<plan-key>.md`, replace the draft instruction with the Deliver implementation instruction, and continue with step 4.25 when `--deep-research` is present, step 4.5 when `--pro-analysis` is present, or step 5 otherwise.",
        "In-place refinement only prepares the execution plan; implementation still requires a separate approval such as `implement the doc` unless the current refinement request includes `--fast`.",
    ]
    for token in deliver_draft_tokens:
        if token not in deliver:
            fail(errors, "PD-DELIVER-DRAFT-MODE", f"skills/deliver/SKILL.md missing draft-mode token: {token}")

    deliver_refined_tokens = [
        "Do not put planning work inside a refined execution plan.",
        "The plan itself must already carry the chosen contract, shape, policy, acceptance criteria, or remaining explicit `Open question:` before implementation starts.",
        "Avoid placeholder work items such as `Define...`, `Decide...`, `Determine...`, `Plan...`, `Figure out...`, or `Clarify...` unless the requested deliverable is itself a planning artifact.",
        "If a decision is unresolved and would change implementation, write it as an `Open question:` checkbox and stop for user review; otherwise record the settled decision in `Context` or `Decision notes` and make the checkbox implement that decision.",
        "Open questions that would change implementation are implementation blockers, not normal backlog.",
        "The review handoff must list them under open questions and say they need to be resolved or explicitly deferred before implementation starts.",
        "if any implementation-changing `Open question:` checkboxes remain, list them as open questions and say they must be resolved or explicitly deferred before implementation starts",
        "if any implementation-changing `Open question:` checkboxes remain, stop and list them instead of starting implementation",
        "`--fast` mode must still stop for destructive or data-loss actions, missing credentials/env/service access, material scope ambiguity, billing/security/schema/API/product decisions, unresolved implementation-changing `Open question:` checkboxes",
        "The reviewer must reject refined plans that still contain meta-planning placeholders",
    ]
    for token in deliver_refined_tokens:
        if token not in deliver:
            fail(errors, "PD-DELIVER-REFINED-PLAN", f"skills/deliver/SKILL.md missing refined-plan token: {token}")

    plan_format = (ROOT / "skills/deliver/references/plan-format.md").read_text()
    plan_format_tokens = [
        "Do not put planning work inside a refined execution plan.",
        "The plan itself must already carry the chosen contract, shape, policy, acceptance criteria, or remaining explicit `Open question:` before implementation starts.",
        "Avoid placeholder work items such as `Define...`, `Decide...`, `Determine...`, `Plan...`, `Figure out...`, or `Clarify...` unless the requested deliverable is itself a planning artifact.",
        "If a decision is unresolved and would change implementation, write it as an `Open question:` checkbox and stop for user review; otherwise record the settled decision in `Context` or `Decision notes` and make the checkbox implement that decision.",
        "Open questions that would change implementation are implementation blockers, not normal backlog.",
        "The review handoff must list them under open questions and say they need to be resolved or explicitly deferred before implementation starts.",
    ]
    for token in plan_format_tokens:
        if token not in plan_format:
            fail(errors, "PD-DELIVER-PLAN-FORMAT", f"skills/deliver/references/plan-format.md missing refined-plan token: {token}")

    deliver_goal_tokens = [
        "skills/plan-to-goal/SKILL.md",
        "Durable goal plan: `tasks/goal-plan-<plan-key>.md`",
        "## Goal Plan Delegation",
        "slow, paid, approval-gated, nightly, or externally scheduled run",
        "$plan-to-goal` owns the `tasks/goal-plan-<plan-key>.md` format",
        "embedded `Start Prompt`",
        "goal-plan draft and `Start Prompt` are produced",
        "Do not execute a goal plan as a normal `$deliver` checklist.",
        "if `$deliver` chose a goal plan, say that it is a goal plan",
    ]
    for token in deliver_goal_tokens:
        if token not in deliver:
            fail(errors, "PD-DELIVER-GOAL-PLAN", f"skills/deliver/SKILL.md missing goal-plan token: {token}")

    pro_reference = (ROOT / "skills/shared/references/analysis/pro-browser-analysis.md").read_text()
    task_file_contract = (ROOT / "skills/shared/references/execution/task-file-contract.md").read_text()
    pro_deliver_reference_tokens = [
        "$deliver --pro-analysis",
        "$deliver --deep-research --pro-analysis",
        "The Pro browser gate requires a visible ChatGPT model label of `Pro Extended` or `Extended Pro` before submission.",
        "Treat `Thinking Extended`, `Extended Thinking`, ordinary thinking modes, or any non-Pro label as a failed Pro model-selection gate",
        "Chrome automation means the Chrome plugin/control-chrome path against the user's installed Chrome profile",
        "Do not use the in-app Browser plugin or standalone Playwright MCP surface as the Pro path",
        "If the first visible browser target is blank, `about:blank`, an empty new tab, or a non-ChatGPT page, do not treat that as an unavailable browser path.",
        "Set `pro_model_selected: yes` only when the visible selected label was `Pro Extended` or `Extended Pro`.",
        "For `$deliver --pro-analysis`, the readable execution plan must already exist as `tasks/execution-plan-<plan-key>.md`.",
        "When `$deliver --deep-research --pro-analysis` is active, the gate is hard:",
        "For `$deliver --pro-analysis`, write `tasks/tmp/pro-analysis-<plan-key>.md`",
        "For `$deliver --pro-analysis`, apply the synthesized findings into the readable execution plan before refinement and either user review or `--fast` implementation",
    ]
    for token in pro_deliver_reference_tokens:
        if token not in pro_reference:
            fail(errors, "PD-DELIVER-PRO-ANALYSIS", f"skills/shared/references/analysis/pro-browser-analysis.md missing deliver pro-analysis token: {token}")
    deliver_task_contract_tokens = [
        "`--deep-research` is valid with `$first-principles-mode`, `$deliver`, and legacy planning flows that explicitly support it",
        "`--pro-analysis` is valid with `$first-principles-mode`, `$deliver`, and `$repo-sweep`",
    ]
    for token in deliver_task_contract_tokens:
        if token not in task_file_contract:
            fail(errors, "PD-DELIVER-PRO-ANALYSIS", f"skills/shared/references/execution/task-file-contract.md missing deliver analysis token: {token}")

    plan_to_goal_tokens = [
        "name: plan-to-goal",
        "rough goal prompts",
        "starts with the goal, done-when criteria, not-done-yet criteria, and a copy-pasteable `/goal` start prompt",
        "tasks/goal-plan-<plan-key>.md",
        "## Weak Goal Gate",
        "## Goal Prompt Optimization",
        "## Goal",
        "## Done When",
        "## Not Done Yet If",
        "## Start Prompt",
        "## Plain Language Summary",
        "## Stop Conditions",
        "Before writing the goal plan, optimize the source into a goal contract",
        "Name the real objective in one sentence.",
        "This becomes the first-screen `Goal`.",
        "Extract or infer the baseline.",
        "Extract or infer the target, comparator, ceiling, or success signal.",
        "first-screen finish-line summary",
        "The goal plan itself must contain the compact paste-ready `/goal` prompt.",
        "Every goal plan must put the `Goal`, `Done When`, `Not Done Yet If`, and `Start Prompt` sections before rationale",
        "First-screen `Goal`, `Done When`, and `Not Done Yet If` entries that make the finish line obvious before process details.",
        "A copy-pasteable `Start Prompt` that starts with `/goal`, references the goal-plan file by absolute path, and does not duplicate the plan text.",
        "A reviewer should understand the completion condition without reading the later process sections.",
        "Derive the first-screen `Not Done Yet If` list from negative stop conditions and common fake wins.",
        "A failed validation, partial fix, confusing result, or completed sub-step is not a stop condition by itself.",
        "Do not stop early. Keep working until one of the Stop Conditions in the goal plan is met",
        "Fill `Resume State` so a new agent has one obvious next exact action",
        "Use a goal plan only when the source is open-ended enough that a stable checklist would be dishonest and the agent can run a real adaptive loop inside the goal.",
        "Goal mode also requires feedback cadence that fits autonomous iteration.",
        "slow, paid, approval-gated, nightly, or externally scheduled run",
        "2-4 hour decision run",
        "Not goal-ready yet.",
        "Done-when criteria that are measurable.",
        "Primary verifier that names the one strongest check that decides whether the goal succeeded.",
        "Supporting checks that do not prove success by themselves, but catch regressions, quality problems, or unsafe side effects.",
        "Anti-cheat criteria that name unacceptable shortcuts or fake wins.",
        "Verification command, artifact, or observable behavior.",
        "If the gate fails, stop with the missing items. Do not write a goal-plan file.",
        "Target and baseline:",
        "## Primary Verifier",
        "## Supporting Checks",
        "## Anti-Cheat Criteria",
        "Work backward from the target when choosing diagnostics and patches.",
        "Do not duplicate the plan text inside the slash prompt",
        "Write the same compact, file-referential `/goal` prompt in the first-screen `Start Prompt` section and in the chat response.",
        "reference the absolute path to `tasks/goal-plan-<plan-key>.md`",
        "Start prompt and chat prompt shape:",
        "Keep the `/goal` prompt compact.",
        "under 4,000 characters",
        "vague first-screen finish line",
        "source of truth for Goal, Done When, Not Done Yet If",
        "Resume State",
        "If validation results decide the next implementation step",
        "badness-prior training task",
        "calculate the plausible maximum",
    ]
    for token in plan_to_goal_tokens:
        if token not in plan_to_goal:
            fail(errors, "PD-PLAN-TO-GOAL", f"skills/plan-to-goal/SKILL.md missing token: {token}")

    plan_to_goal_template_start = plan_to_goal.find("````md\n# <Goal Name>")
    if plan_to_goal_template_start == -1:
        fail(errors, "PD-PLAN-TO-GOAL", "skills/plan-to-goal/SKILL.md missing goal-plan template start")
    else:
        plan_to_goal_template_order = [
            "## Goal",
            "## Done When",
            "## Not Done Yet If",
            "## Start Prompt",
            "/goal <one sentence objective>",
            "## Why This Is A Goal",
            "## Plain Language Summary",
            "## Starting Evidence",
            "## Work Loop",
            "## Primary Verifier",
            "## Stop Conditions",
        ]
        cursor = plan_to_goal_template_start
        for token in plan_to_goal_template_order:
            next_index = plan_to_goal.find(token, cursor)
            if next_index == -1:
                fail(errors, "PD-PLAN-TO-GOAL", f"skills/plan-to-goal/SKILL.md goal-plan template missing ordered token: {token}")
                break
            cursor = next_index + len(token)

    readme_tokens = [
        "goal-plan prompt for adaptive evidence loops",
        "rough goal prompts",
        "reviewable goal-plan doc with an embedded copy-pasteable `/goal` start prompt",
        "optimizes rough prose into a first-screen `Goal`, `Done When`, `Not Done Yet If`, and `Start Prompt` block",
        "finish-line-first review guidance",
        "no-early-stop guidance",
        "`deliver` | Use `$deliver` for the main planning, implementation, and review workflow.",
        "one readable execution plan refined right away",
        "runs web-backed deep research when requested",
        "asks the user to review the Markdown plan file unless `--fast` is present",
        "For frontend-facing plans, it creates a simple linked HTML mockup before approval",
        "Use `$deliver discuss` only when you want a draft checklist to stay current while you talk through it.",
        "Use bare `$deliver`, `refine`, or `plan`: keep the active checklist in `tasks/execution-plan-<plan-key>.md`, replace any draft instruction with the Deliver implementation instruction, refine it, and ask the user to review the Markdown file before approving implementation unless `--fast` is present.",
        "`--fast`: skip only the initial plan-review pause after refinement, then start implementation immediately",
        "`--deep-research`: run web-backed operator/current-practice research after the readable execution plan exists",
        "`--deep-research --pro-analysis`: run deep research first, apply adopted findings to the execution plan, then run ChatGPT Pro against the researched plan before refinement.",
        "Use `$deliver discuss` only when you want a draft checklist to stay current while you talk through it.",
        "`plan-to-goal` | Use `$plan-to-goal [plan-key=<plan-key>]`",
        "tasks/goal-plan-<plan-key>.md",
        "$deliver --pro-analysis",
        "$deliver --deep-research --pro-analysis",
    ]
    for token in readme_tokens:
        if token not in readme:
            fail(errors, "PD-DELIVER-README-GOAL-PLAN", f"README.md missing deliver goal-plan token: {token}")

    deliver_agent_tokens = [
        "wait for approval before execution unless I include --fast",
        "--fast skips only the initial plan-review pause",
        "validation, final review, archive, commit, and finalization",
    ]
    for token in deliver_agent_tokens:
        if token not in deliver_agent:
            fail(errors, "PD-DELIVER-AGENT-PROMPT", f"skills/deliver/agents/openai.yaml missing deliver prompt token: {token}")

    finalization_tokens = [
        "Portable hard gate for `$deliver` and legacy task-artifact execution.",
        "review-deliver-final-<plan-key>.md",
        "execution-plan-<plan-key>.md",
        "goal plan",
        "For `$deliver`, the scan covers the entire readable execution plan",
    ]
    for token in finalization_tokens:
        if token not in finalization_gate:
            fail(
                errors,
                "PD-DELIVER-FINALIZATION-GATE",
                f"skills/shared/references/execution/finalization-gate.md missing deliver gate token: {token}",
            )


def validate_review_plan_contract(errors: list[str]) -> None:
    review_plan_path = ROOT / "skills/review-plan/SKILL.md"
    if not review_plan_path.exists():
        fail(errors, "PD-REVIEW-PLAN", "skills/review-plan/SKILL.md missing")
        return

    review_plan = review_plan_path.read_text()
    readme = (ROOT / "README.md").read_text()
    deliver = (ROOT / "skills/deliver/SKILL.md").read_text()

    skill_tokens = [
        "name: review-plan",
        "Supports `--approval-gate`",
        "tasks/execution-plan-<plan-key>.md",
        "tasks/tmp/review-plan-<plan-key>.md",
        "first-principles adversarial council",
        "internal adversarial conversation",
        "Use 3-5 independent lanes",
        "Run two rebuttal rounds by default.",
        "Run a third rebuttal round only when",
        "Preserve serious minority risks",
        "auto-fix is the default",
        "`--approval-gate`",
        "apply the review-plan fixes",
        "Use an explicit user-provided path such as `tasks/execution-plan-<plan-key>.md` when present.",
        "Use the visible, attached, referenced, or current-thread `$deliver` execution plan when one is active.",
        "If the user is approving proposed fixes from a prior `--approval-gate` run",
        "apply still-valid proposed fixes or rerun against the current plan before editing",
        "## Retention And Cleanup",
        "After successful downstream `$deliver` final review and finalization, delete the completed review-plan log",
        "never edit implementation code",
        "must not start implementation",
        "Stop when a fresh reviewer round finds no `blocker` or `material` issues.",
        "8` is the hard maximum round count",
        "review_plan_complete",
        "fresh_council_rounds",
        "fresh_reviewer_rounds",
        "reviewer_stop_gate",
        "all_objections_dispositioned",
        "ready_for_implementation",
    ]
    for token in skill_tokens:
        if token not in review_plan:
            fail(errors, "PD-REVIEW-PLAN", f"skills/review-plan/SKILL.md missing token: {token}")

    def section(heading: str) -> str:
        match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?:\n## |\Z)", review_plan, re.S | re.M)
        return match.group(1) if match else ""

    plan_resolution = section("Plan Resolution")
    resolution_order = [
        "Use an explicit user-provided path such as `tasks/execution-plan-<plan-key>.md` when present.",
        "Use `plan-key=<plan-key>` when provided.",
        "Use the visible, attached, referenced, or current-thread `$deliver` execution plan when one is active.",
        "If exactly one active execution plan exists, infer its `plan-key`.",
        "If more than one active execution plan exists, stop and ask for `plan-key=<plan-key>`.",
    ]
    resolution_positions = [plan_resolution.find(token) for token in resolution_order]
    if any(position < 0 for position in resolution_positions) or resolution_positions != sorted(resolution_positions):
        fail(errors, "PD-REVIEW-PLAN-RESOLUTION", "skills/review-plan/SKILL.md must resolve explicit path, then plan-key, then current-thread plan, then inference/ambiguity")

    approval_gate_match = re.search(r"^9\. In `--approval-gate` mode.*?(?:\n10\. |\n## )", review_plan, re.S | re.M)
    approval_gate = approval_gate_match.group(0) if approval_gate_match else ""
    approval_gate_tokens = [
        "Do not edit `tasks/execution-plan-<plan-key>.md`.",
        "Write proposed fixes to `tasks/tmp/review-plan-<plan-key>.md`.",
        "Ask the user to approve the proposed fixes or request changes.",
        "When the user approves, apply still-valid proposed fixes or rerun against the current plan before editing.",
    ]
    for token in approval_gate_tokens:
        if token not in approval_gate:
            fail(errors, "PD-REVIEW-PLAN-APPROVAL-GATE", f"skills/review-plan/SKILL.md approval gate missing behavior token: {token}")

    workflow_text = section("Workflow")
    scope_text = section("Scope Boundaries")
    retention_text = section("Retention And Cleanup")
    for token in ["implementation source code", "tests", "migrations", "README or shared contract references"]:
        if token not in scope_text:
            fail(errors, "PD-REVIEW-PLAN-NO-IMPLEMENTATION", f"skills/review-plan/SKILL.md scope boundary missing forbidden edit target: {token}")
    if "start implementation" in workflow_text and "must not start implementation" not in workflow_text:
        fail(errors, "PD-REVIEW-PLAN-NO-IMPLEMENTATION", "skills/review-plan/SKILL.md workflow may allow implementation start")
    for token in [
        "the run stopped with unresolved blocker or material findings",
        "`--approval-gate` wrote proposed fixes that have not been applied or rejected",
        "After successful downstream `$deliver` final review and finalization, delete the completed review-plan log",
    ]:
        if token not in retention_text:
            fail(errors, "PD-REVIEW-PLAN-RETENTION", f"skills/review-plan/SKILL.md retention section missing behavior token: {token}")

    readme_tokens = [
        "`review-plan` | Use `$review-plan [plan-key=<plan-key>]`",
        "Use `$review-plan` when an active `$deliver` execution plan should get an adversarial first-principles council pass before implementation.",
        "### `$review-plan`",
        "Runs an adversarial first-principles council loop over one active `$deliver` execution plan.",
        "it may edit `tasks/execution-plan-<plan-key>.md`, but it must not edit implementation code or start implementation",
        "`--approval-gate`: run the same review loop read-only",
    ]
    for token in readme_tokens:
        if token not in readme:
            fail(errors, "PD-REVIEW-PLAN-README", f"README.md missing review-plan token: {token}")

    deliver_tokens = [
        "skills/review-plan/SKILL.md",
        "route that request through `$review-plan`",
        "Remove `tasks/tmp/review-plan-<plan-key>.md` when it records a completed `$review-plan` pass with no unresolved risk",
    ]
    for token in deliver_tokens:
        if token not in deliver:
            fail(errors, "PD-REVIEW-PLAN-DELIVER", f"skills/deliver/SKILL.md missing review-plan token: {token}")

    forbidden_skill_patterns = [
        "continue directly into implementation",
        "start implementation after review",
        "invoke `$deliver` implementation",
    ]
    for token in forbidden_skill_patterns:
        if token in review_plan:
            fail(errors, "PD-REVIEW-PLAN-NO-IMPLEMENTATION", f"skills/review-plan/SKILL.md contains implementation-start wording: {token}")


def validate_bounded_adversarial_priors(errors: list[str]) -> None:
    review_protocol = (ROOT / "skills/shared/references/review/review-protocol.md").read_text()
    review_chain = (ROOT / "skills/review-chain/SKILL.md").read_text()
    merge_review = (ROOT / "skills/merge-review/SKILL.md").read_text()
    merge_rubric = (ROOT / "skills/merge-review/references/merge-readiness-rubric.md").read_text()
    review_plan = (ROOT / "skills/review-plan/SKILL.md").read_text()
    contract_ownership = (ROOT / "skills/shared/references/contract-ownership.md").read_text()
    readme = (ROOT / "README.md").read_text()

    review_protocol_tokens = [
        "## Bounded adversarial priors",
        "bug_prior",
        "smaller_delta",
        "skeptic_falsifier",
        "must end in one of these outcomes",
        "a concrete verification pivot naming the smallest useful probe",
        "`no action` with the falsifying evidence",
        "Do not run unbounded \"keep looking until you find a bug\" loops.",
        "Do not invent findings to satisfy an adversarial prompt.",
        "run the bounded adversarial-prior checks: bug_prior, smaller_delta, and skeptic_falsifier",
        "## Final Review-Quality Check",
        "incorrect_or_overstated_findings",
        "missed_material_issues",
        "severity_or_disposition_adjustments",
        "the closing audit must attack the review itself",
        "Final review-quality check recorded when required",
    ]
    for token in review_protocol_tokens:
        if token not in review_protocol:
            fail(errors, "PD-BOUNDED-ADVERSARIAL-PRIORS", f"skills/shared/references/review/review-protocol.md missing token: {token}")

    consumer_tokens = [
        (
            "skills/review-chain/SKILL.md",
            review_chain,
            "Include the bounded adversarial-prior checks from `review-protocol.md` during Prompt A",
        ),
        (
            "skills/merge-review/SKILL.md",
            merge_review,
            "Include the rubric's bounded adversarial-prior checks before declaring a branch merge-ready.",
        ),
        (
            "skills/merge-review/references/merge-readiness-rubric.md",
            merge_rubric,
            "## Bounded Adversarial Priors",
        ),
        (
            "skills/merge-review/references/merge-readiness-rubric.md",
            merge_rubric,
            "Do not keep searching until a bug is found.",
        ),
        (
            "skills/review-plan/SKILL.md",
            review_plan,
            "Include a smaller-delta challenge and a skeptic/falsifier check",
        ),
        (
            "skills/shared/references/contract-ownership.md",
            contract_ownership,
            "bounded adversarial-prior checks",
        ),
        (
            "README.md",
            readme,
            "It includes bounded adversarial-prior checks, but remains report-first by default.",
        ),
        (
            "README.md",
            readme,
            "require evidence, a verification pivot, or `no action` with falsifying evidence instead of inventing a finding",
        ),
    ]
    for path, text, token in consumer_tokens:
        if token not in text:
            fail(errors, "PD-BOUNDED-ADVERSARIAL-PRIORS-CONSUMER", f"{path} missing token: {token}")


def validate_deliver_review_proportionality(errors: list[str]) -> None:
    disposition_path = "skills/shared/references/review/finding-disposition.md"
    protocol_path = "skills/shared/references/review/review-protocol.md"
    ownership_path = "skills/shared/references/contract-ownership.md"
    deliver_path = "skills/deliver/SKILL.md"
    worker_packet_path = "skills/deliver/references/worker-packet.md"
    rereview_reference_path = "skills/deliver/references/rereview-scope-record.md"
    rereview_script_path = "skills/deliver/scripts/validate_rereview_scope.py"
    disposition = (ROOT / disposition_path).read_text()
    protocol = (ROOT / protocol_path).read_text()
    ownership = (ROOT / ownership_path).read_text()
    deliver = (ROOT / deliver_path).read_text()
    worker_packet = (ROOT / worker_packet_path).read_text()
    rereview_reference = (ROOT / rereview_reference_path).read_text()
    rereview_script = (ROOT / rereview_script_path).read_text()

    disposition_tokens = [
        "## Deliver Test Value",
        "test_disposition: permanent | table_case | probe_only | no_test",
        "Before any new or changed Deliver test is kept as permanent coverage",
        "concise evidence-backed rationale",
        "supported path that is reachable",
        "explicit contract or credible harm",
        "uniquely uncovered",
        "stable across supported environments",
        "economical to understand and maintain",
        "smallest coherent table-driven test",
        "do not keep duplicate permanent coverage",
        "resource-limit-dependent behavior defaults to `probe_only`",
        "explicit supported contract",
        "agent-scratch/",
        "stronger coverage already proves the boundary",
        "Every implementation change and repaired finding still requires recorded verification evidence",
        "A fix may proceed without a permanent test.",
        "test_disposition` is independent of `Disposition",
        "never weakens `Disposition: fix`",
        "`$review-chain`, `$merge-review`, `$repo-sweep`",
        "or any other consumer",
    ]
    for token in disposition_tokens:
        if token not in disposition:
            fail(errors, "PD-DELIVER-REVIEW-PROPORTIONALITY", f"{disposition_path} missing token: {token}")

    protocol_tokens = [
        "## Deliver final-review remediation rereviews",
        "The initial `$deliver` final review is always one fresh `full-branch` round",
        "rereview_scope: targeted | full",
        "Default to one fresh `targeted` rereview",
        "the repaired finding IDs",
        "the exact pre-repair base state",
        "the repair boundary and exact repair diff",
        "the adjacent callers and relevant tests inspected",
        "the originating review prompt and the testing prompt",
        "Prompt H when the repaired boundary affects",
        "the relevant validation reruns",
        "evidence from one fresh reviewer",
        "crosses an architecture or trust boundary",
        "changes cross-process coordination or lifecycle/completion semantics across concurrent or asynchronous boundaries",
        "changes or protects a failure boundary where a fallible user-visible output or diagnostic step runs after irreversible mutation",
        "Mere mutation plus reporting remains `targeted` when the repair leaves their ordering and failure boundary unchanged",
        "changes a public contract",
        "broadly affects security or data integrity",
        "cannot be shown to be isolated",
        "targeted rereview discovers a new material defect",
        "Each repair action records its own required `rereview_scope`",
        "use the widest scope required by any repair",
        "the executed rereview round",
        "an isolated action can remain `targeted` in its own record",
        "bundled rereview-scope validator",
        "complete fixed Boolean risk-flag set",
        "from `fallible_output_after_irreversible_mutation`",
        "requires both `irreversible_mutation` and `user_visible_output_or_diagnostics`",
        "the two prerequisite flags without ordered failure remain `targeted`",
        "passing plan-phase validation",
        "passing complete-phase validation",
        "no unresolved verified `fix` findings",
        "does not change `$review-chain`, `$merge-review`, `$repo-sweep`",
        "All non-Deliver consumers retain their existing full resweep or rereview behavior unchanged.",
    ]
    for token in protocol_tokens:
        if token not in protocol:
            fail(errors, "PD-DELIVER-REVIEW-PROPORTIONALITY", f"{protocol_path} missing token: {token}")

    deliver_tokens = [
        disposition_path,
        protocol_path,
        "before step 7 when implementation may add or change tests",
        "Deliver-only `test_disposition` and final-review `rereview_scope`",
        "without copying their rubrics or applying them to other review workflows",
        "already-approved Deliver execution plan",
        "approved fixed remediation packet",
        "import the packet as execution tracking without changing its approved scope",
        "do not rerun plan refinement",
        "begin or resume implementation at step 7",
        "does not weaken the initial refinement",
        "Before keeping any new or changed test as permanent coverage",
        "one initial fresh full-branch review",
        "do not add another full review only as closeout ceremony",
        "trusted fixed remediation packet from the active workflow",
        "count that review as the initial full round",
        "Do not repeat it before repair",
        rereview_reference_path,
        "review-deliver-final-<plan-key>.rereview.json",
        "validate_rereview_scope.py <record> --phase plan",
        "validate_rereview_scope.py <record> --phase complete",
        "validator-derived action scope and grouped widest scope are authoritative",
    ]
    for token in deliver_tokens:
        if token not in deliver:
            fail(errors, "PD-DELIVER-REVIEW-PROPORTIONALITY", f"{deliver_path} missing token: {token}")

    worker_packet_tokens = [
        "Test value when this step adds or changes tests:",
        "test_disposition: permanent | table_case | probe_only | no_test",
        "the orchestrator must decide and include `test_disposition` plus its rationale before assigning permanent-test work",
        "assign only reproduction or repair",
        "keep permanent-test work out of the packet",
    ]
    for token in worker_packet_tokens:
        if token not in worker_packet:
            fail(errors, "PD-DELIVER-REVIEW-PROPORTIONALITY", f"{worker_packet_path} missing token: {token}")

    rereview_reference_tokens = [
        "review-deliver-final-<plan-key>.rereview.json",
        "`schema_version: 2`",
        "all nine Boolean `risk_flags`",
        "architecture_or_trust_boundary",
        "cross_process_or_async_completion",
        "irreversible_mutation",
        "user_visible_output_or_diagnostics",
        "fallible_output_after_irreversible_mutation",
        "changes or protects a failure boundary",
        "Mere mutation plus reporting does not require the flag when their ordering and failure boundary are unchanged",
        "public_contract",
        "broad_security_or_data_integrity",
        "isolation_unproven",
        "new_material_finding",
        "--phase plan",
        "--phase complete",
        "widest scope derived for its listed actions",
    ]
    for token in rereview_reference_tokens:
        if token not in rereview_reference:
            fail(errors, "PD-DELIVER-REREVIEW-SCOPE-GATE", f"{rereview_reference_path} missing token: {token}")

    rereview_script_tokens = [
        "RISK_FLAGS",
        "DIRECT_FULL_FLAGS",
        "def derived_scope",
        "irreversible_mutation",
        "user_visible_output_or_diagnostics",
        "fallible_output_after_irreversible_mutation",
        "schema_version must be 2",
        "requires both",
        "plan-phase record must have an empty rounds array",
        "complete-phase record must include at least one executed round",
        "requires {expected_scope} rereview from its widest action",
        "actions missing executed rereview evidence",
    ]
    for token in rereview_script_tokens:
        if token not in rereview_script:
            fail(errors, "PD-DELIVER-REREVIEW-SCOPE-GATE", f"{rereview_script_path} missing token: {token}")

    try:
        spec = importlib.util.spec_from_file_location("deliver_rereview_scope_validator", ROOT / rereview_script_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load validator module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        isolated = {name: False for name in module.RISK_FLAGS}
        mutation_output = dict(isolated)
        mutation_output["irreversible_mutation"] = True
        mutation_output["user_visible_output_or_diagnostics"] = True
        ordered_failure = dict(mutation_output)
        ordered_failure["fallible_output_after_irreversible_mutation"] = True
        inconsistent = dict(isolated)
        inconsistent["fallible_output_after_irreversible_mutation"] = True
        if module.derived_scope(isolated) != "targeted":
            raise RuntimeError("isolated scope was not targeted")
        if module.derived_scope(mutation_output) != "targeted":
            raise RuntimeError("mutation/output scope was not targeted")
        if module.derived_scope(ordered_failure) != "full":
            raise RuntimeError("ordered-failure scope was not full")
        try:
            module.derived_scope(inconsistent)
        except module.RecordError:
            pass
        else:
            raise RuntimeError("inconsistent ordered-failure flags were accepted")
    except Exception as exc:
        fail(errors, "PD-DELIVER-REREVIEW-SCOPE-GATE", f"{rereview_script_path} functional check failed: {exc}")

    ownership_tokens = [
        "Deliver-final-review-only targeted/full rereview topology",
        "cross-process or concurrent/asynchronous lifecycle/completion, irreversible-mutation ordering, grouped-round scope rules",
        "requirement for deterministic Deliver scope validation",
        "Deliver skill owns the concrete scope-record schema and bundled validator",
        "The Deliver-only topology does not apply to other consumers.",
        "Deliver-only implementation-and-final-review test-persistence vocabulary",
        "The Deliver-only vocabulary does not apply to other consumers.",
    ]
    for token in ownership_tokens:
        if token not in ownership:
            fail(errors, "PD-DELIVER-REVIEW-PROPORTIONALITY", f"{ownership_path} missing token: {token}")


def validate_architecture_guidance(errors: list[str]) -> None:
    reference = (ROOT / "skills/shared/references/architecture/architecture-guidance.md").read_text()
    create_architecture = (ROOT / "skills/create-architecture/SKILL.md").read_text()
    bootstrap = (ROOT / "skills/bootstrap-repo-rules/SKILL.md").read_text()
    deliver = (ROOT / "skills/deliver/SKILL.md").read_text()
    review_chain = (ROOT / "skills/review-chain/SKILL.md").read_text()
    repo_sweep = (ROOT / "skills/repo-sweep/SKILL.md").read_text()
    contract_ownership = (ROOT / "skills/shared/references/contract-ownership.md").read_text()
    readme = (ROOT / "README.md").read_text()
    agents = (ROOT / "AGENTS.md").read_text()

    reference_tokens = [
        "## Boundary-Affecting Work",
        "Small local edits inside one existing boundary are not boundary-affecting.",
        "## Non-Trivial Repo Signal",
        "## Architecture Doctrine",
        "## Architecture Document Template",
        "docs/ARCHITECTURE.md",
        "Accepted Deviations",
        "Do not build or require a universal cross-stack architecture validator from this reference.",
    ]
    for token in reference_tokens:
        if token not in reference:
            fail(errors, "PD-ARCHITECTURE-REFERENCE", f"skills/shared/references/architecture/architecture-guidance.md missing token: {token}")

    create_architecture_tokens = [
        "name: create-architecture",
        "Invoke explicitly with `$create-architecture`.",
        "skills/shared/references/architecture/architecture-guidance.md",
        "Existing repo mode",
        "Greenfield mode",
        "docs/ARCHITECTURE.md",
        "Do not create a second document unless the repo already has its own convention.",
    ]
    for token in create_architecture_tokens:
        if token not in create_architecture:
            fail(errors, "PD-CREATE-ARCHITECTURE-SKILL", f"skills/create-architecture/SKILL.md missing token: {token}")

    consumer_checks = [
        ("skills/bootstrap-repo-rules/SKILL.md", bootstrap, "suggest or invoke `$create-architecture`"),
        ("skills/deliver/SKILL.md", deliver, "For boundary-affecting implementation work"),
        ("skills/review-chain/SKILL.md", review_chain, "forbidden dependency edges"),
        ("skills/repo-sweep/SKILL.md", repo_sweep, "label those findings as inferred rather than contract drift"),
    ]
    for path, text, local_token in consumer_checks:
        for token in ["skills/shared/references/architecture/architecture-guidance.md", "docs/ARCHITECTURE.md", local_token]:
            if token not in text:
                fail(errors, "PD-ARCHITECTURE-CONSUMER", f"{path} missing architecture token: {token}")

    metadata_tokens = [
        "`create-architecture` | Use `$create-architecture` when a non-trivial repo needs a concrete `docs/ARCHITECTURE.md`",
        "Use `$create-architecture` when a non-trivial repo needs a concrete `docs/ARCHITECTURE.md`",
        "Creates or updates a repo-specific `docs/ARCHITECTURE.md`.",
    ]
    for token in metadata_tokens:
        if token not in readme:
            fail(errors, "PD-CREATE-ARCHITECTURE-README", f"README.md missing create-architecture token: {token}")

    ownership_token = "`architecture-guidance` | `skills/shared/references/architecture/architecture-guidance.md`"
    if ownership_token not in contract_ownership:
        fail(errors, "PD-ARCHITECTURE-OWNERSHIP", f"skills/shared/references/contract-ownership.md missing token: {ownership_token}")

    agents_token = "Before boundary-affecting work, read `docs/ARCHITECTURE.md` when it exists."
    if agents_token not in agents:
        fail(errors, "PD-ARCHITECTURE-AGENTS", f"AGENTS.md missing architecture token: {agents_token}")


def validate_ship_branch(errors: list[str]) -> None:
    skill = (ROOT / "skills/ship-branch/SKILL.md").read_text()
    readme = (ROOT / "README.md").read_text()

    skill_tokens = [
        "name: ship-branch",
        "Invoke explicitly with `$ship-branch`",
        "Use `$cleanup-merged-branches` for broad cleanup scans.",
        "If there are unstaged, staged, or untracked changes, print a compact summary before doing anything",
        "Ask the user whether to commit the changes or stash them.",
        "Do not auto-commit, auto-stage, or auto-stash dirty work.",
        "Compare the branch to the resolved base with `git log --oneline <base>..HEAD`.",
        "Use `git push -u origin <current-branch>`.",
        "Use `gh pr view --head <current-branch>` to find an existing PR.",
        "Use a normal ready PR by default because this skill's purpose is to merge.",
        "If required checks are pending or queued, keep checking until all required checks pass or any check fails.",
        "If required checks fail, inspect the failed check output with `gh pr checks`, `gh run view --log-failed`, or the check URL.",
        "During the failed-check repair loop, commit only agent-made fixes for failed PR checks after verifying the branch was clean before the fix",
        "Merge with the repo's normal merge path.",
        "Delete the local shipped branch with `git branch -d <branch>`.",
        "Never use `git branch -D`.",
        "Never run `git reset --hard`.",
        "Never delete local or remote branches until the PR merge is confirmed.",
    ]
    for token in skill_tokens:
        if token not in skill:
            fail(errors, "PD-SHIP-BRANCH", f"skills/ship-branch/SKILL.md missing token: {token}")

    readme_tokens = [
        "`ship-branch` | Use `$ship-branch` when the current feature branch should be pushed",
        "Use `$ship-branch` when the current feature branch should be pushed, PR'd, merged, deleted locally/remotely, and the checkout returned to the base branch.",
        "Finishes the current feature branch.",
    ]
    for token in readme_tokens:
        if token not in readme:
            fail(errors, "PD-SHIP-BRANCH-README", f"README.md missing ship-branch token: {token}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-only", action="store_true", help="print stale-mirror inventory and exit")
    args = parser.parse_args()

    if args.inventory_only:
        print_inventory()
        return 0

    errors: list[str] = []
    validate_skill_metadata(errors)
    validate_owner_paths(errors)
    validate_plan_refine_completion_gate(errors)
    validate_deep_research_completion_stamp(errors)
    validate_deep_research_prompt_contract(errors)
    validate_clarifier_editorial_review(errors)
    validate_first_principles_adversarial_council(errors)
    validate_deliver_terminal_gate(errors)
    validate_review_plan_contract(errors)
    validate_bounded_adversarial_priors(errors)
    validate_deliver_review_proportionality(errors)
    validate_architecture_guidance(errors)
    validate_ship_branch(errors)
    validate_mirrors(errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("skill contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
