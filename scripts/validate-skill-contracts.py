#!/usr/bin/env python3
"""Validate Prime Directive skill metadata and owned workflow contracts."""

from __future__ import annotations

import argparse
import glob
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


def readme_rows() -> dict[str, tuple[str, str]]:
    readme = (ROOT / "README.md").read_text()
    rows: dict[str, tuple[str, str]] = {}
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
        if len(cells) != 3:
            continue
        match = re.fullmatch(r"`([^`]+)`", cells[0])
        if match:
            rows[match.group(1)] = (cells[1], cells[2])
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
        invocation_cell, options_cell = rows.get(name, ("", ""))
        expected_invocation = INVOCATION_OVERRIDES.get(name, f"${name}")
        invocation_codes = re.findall(r"`([^`]+)`", invocation_cell)
        valid_invocations = bool(invocation_codes)
        for code in invocation_codes:
            first_token = code.split()[0] if code.split() else ""
            if first_token != expected_invocation:
                valid_invocations = False
        if not valid_invocations:
            fail(errors, "PD-README-INVOCATION", f"{name}: README invocation cell does not include `{expected_invocation}`")
        actual = public_tokens(" ".join([invocation_cell, options_cell]))
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
        "evidence_bar_met: yes",
    ]
    for token in owner_tokens:
        if token not in deep_research:
            fail(errors, "PD-DEEP-RESEARCH-STAMP-OWNER", f"skills/shared/references/planning/deep-research.md missing completion-stamp token: {token}")


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
        "Council Audit Summary only when",
        "parallel memos without rebuttal",
    ]
    for token in rubric_tokens:
        if token not in rubric:
            fail(errors, "PD-FIRST-PRINCIPLES-COUNCIL-RUBRIC", f"skills/first-principles-mode/references/analysis-rubric.md missing adversarial-council token: {token}")

    readme_tokens = [
        "default adversarial council",
        "independent lanes and rebuttal rounds",
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
        "`--pro-analysis`",
        "`--fast`",
        "Fast mode skips only the initial user plan-review pause after refinement; it does not skip the written plan, refinement, validation, final review, archive, commit, or finalization.",
        "$deliver --fast` creates or resumes the same readable execution plan, runs the same Pro/refinement gates, treats the refined plan as approved scope, and continues directly to step 7 without the initial user plan-review pause.",
        "Stop for user review of the Markdown plan file unless `--fast` is present.",
        "Do not launch a review app or external viewer.",
        "Normal mode: link `tasks/execution-plan-<plan-key>.md` and ask the user to review the Markdown file.",
        "`--fast` mode must still stop for destructive or data-loss actions",
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
        "Do not use this step for bare `$deliver`, `$deliver --pro-analysis`, `$deliver --fast`, `$deliver plan`, `$deliver refine`, `deliver this`, or equivalent requests",
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
        "If the user asks to refine the draft into a deliver plan, keep the same `tasks/execution-plan-<plan-key>.md`, replace the draft instruction with the Deliver implementation instruction, and continue with step 4.5 when `--pro-analysis` is present or step 5 otherwise.",
        "In-place refinement only prepares the execution plan; implementation still requires a separate approval such as `implement the doc` unless the current refinement request includes `--fast`.",
    ]
    for token in deliver_draft_tokens:
        if token not in deliver:
            fail(errors, "PD-DELIVER-DRAFT-MODE", f"skills/deliver/SKILL.md missing draft-mode token: {token}")

    deliver_goal_tokens = [
        "skills/plan-to-goal/SKILL.md",
        "Durable goal plan: `tasks/goal-plan-<plan-key>.md`",
        "## Goal Plan Delegation",
        "slow, paid, approval-gated, nightly, or externally scheduled run",
        "$plan-to-goal` owns the `tasks/goal-plan-<plan-key>.md` format",
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
        "The Pro browser gate requires a visible ChatGPT model label of `Pro Extended` or `Extended Pro` before submission.",
        "Treat `Thinking Extended`, `Extended Thinking`, ordinary thinking modes, or any non-Pro label as a failed Pro model-selection gate",
        "If the first visible browser target is blank, `about:blank`, an empty new tab, or a non-ChatGPT page, do not treat that as an unavailable browser path.",
        "Set `pro_model_selected: yes` only when the visible selected label was `Pro Extended` or `Extended Pro`.",
        "For `$deliver --pro-analysis`, the readable execution plan must already exist as `tasks/execution-plan-<plan-key>.md`.",
        "For `$deliver --pro-analysis`, write `tasks/tmp/pro-analysis-<plan-key>.md`",
        "For `$deliver --pro-analysis`, apply the synthesized findings into the readable execution plan before refinement and either user review or `--fast` implementation",
    ]
    for token in pro_deliver_reference_tokens:
        if token not in pro_reference:
            fail(errors, "PD-DELIVER-PRO-ANALYSIS", f"skills/shared/references/analysis/pro-browser-analysis.md missing deliver pro-analysis token: {token}")
    pro_deliver_task_contract_token = "`--pro-analysis` is valid with `$first-principles-mode`, `$deliver`, and `$repo-sweep`"
    if pro_deliver_task_contract_token not in task_file_contract:
        fail(errors, "PD-DELIVER-PRO-ANALYSIS", f"skills/shared/references/execution/task-file-contract.md missing deliver pro-analysis token: {pro_deliver_task_contract_token}")

    plan_to_goal_tokens = [
        "name: plan-to-goal",
        "tasks/goal-plan-<plan-key>.md",
        "## Weak Goal Gate",
        "Use a goal plan only when the source is open-ended enough that a stable checklist would be dishonest and the agent can run a real adaptive loop inside the goal.",
        "Goal mode also requires feedback cadence that fits autonomous iteration.",
        "slow, paid, approval-gated, nightly, or externally scheduled run",
        "2-4 hour decision run",
        "Not goal-ready yet.",
        "Done-when criteria that are measurable.",
        "Verification command, artifact, or observable behavior.",
        "If the gate fails, stop with the missing items. Do not write a goal-plan file.",
        "Target and baseline:",
        "Work backward from the target when choosing diagnostics and patches.",
        "must not embed the full `/goal` prompt.",
        "print the compact paste-ready `/goal` prompt separately",
        "reference the absolute path to `tasks/goal-plan-<plan-key>.md`",
        "Do not copy this Markdown file into `/goal`.",
        "Separate chat prompt shape:",
        "Keep the `/goal` prompt compact.",
        "under 4,000 characters",
        "Resume State",
        "If validation results decide the next implementation step",
        "badness-prior training task",
        "calculate the plausible maximum",
    ]
    for token in plan_to_goal_tokens:
        if token not in plan_to_goal:
            fail(errors, "PD-PLAN-TO-GOAL", f"skills/plan-to-goal/SKILL.md missing token: {token}")

    readme_tokens = [
        "goal-plan prompt for adaptive evidence loops",
        "`deliver` | `$deliver`, `$deliver refine`, or `$deliver plan` | `--pro-analysis`, `--fast`; legacy `$deliver discuss` is a draft-update alias",
        "one readable execution plan refined right away",
        "asks the user to review the Markdown plan file unless `--fast` is present",
        "Use `$deliver discuss` only when you want a draft checklist to stay current while you talk through it.",
        "bare `$deliver`, `refine`, or `plan`: keep the active checklist in `tasks/execution-plan-<plan-key>.md`, replace any draft instruction with the Deliver implementation instruction, refine it, and ask the user to review the Markdown file before approving implementation unless `--fast` is present.",
        "`--fast`: skip only the initial plan-review pause after refinement, then start implementation immediately",
        "`discuss`: legacy alias for creating or updating the same draft checklist plan. Do not treat it as a separate workflow.",
        "`plan-to-goal` | `$plan-to-goal [plan-key=<plan-key>]`",
        "tasks/goal-plan-<plan-key>.md",
        "$deliver --pro-analysis",
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
        "`review-plan` | `$review-plan [plan-key=<plan-key>]` | `plan-key=<plan-key>`, `--approval-gate`; reviews active `$deliver` execution plans",
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
        "`create-architecture` | `$create-architecture` | None",
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
        "`ship-branch` | `$ship-branch` | None",
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
    validate_first_principles_adversarial_council(errors)
    validate_deliver_terminal_gate(errors)
    validate_review_plan_contract(errors)
    validate_bounded_adversarial_priors(errors)
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
