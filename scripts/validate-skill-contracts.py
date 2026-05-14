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
    "planning-intake": "skills/shared/references/planning/socratic-planning.md",
    "prd-generation": "skills/shared/references/planning/create-prd.md",
    "tdd-generation": "skills/shared/references/planning/create-tdd.md",
    "task-plan-generation": "skills/shared/references/planning/generate-tasks.md",
    "plan-improvement": "skills/shared/references/planning/improve-plan.md",
    "deep-research": "skills/shared/references/planning/deep-research.md",
    "pro-analysis": "skills/shared/references/analysis/pro-oracle-escalation.md",
    "task-file-contract": "skills/shared/references/execution/task-file-contract.md",
    "task-management": "skills/shared/references/execution/task-management.md",
    "finalization-gate": "skills/shared/references/execution/finalization-gate.md",
    "review-protocol": "skills/shared/references/review/review-protocol.md",
    "review-calibration": "skills/shared/references/review/review-calibration.md",
    "finding-disposition": "skills/shared/references/review/finding-disposition.md",
    "dep-audit-checklist": "skills/shared/references/review/dep-audit-checklist.md",
    "swarm-lanes": "skills/shared/references/review/swarm-lanes.md",
    "plan-refine": "skills/plan-refine/SKILL.md",
    "plan-to-goal": "skills/plan-to-goal/SKILL.md",
    "plan-and-execute": "skills/plan-and-execute/SKILL.md",
    "execute-task": "skills/execute-task/SKILL.md",
    "harness-drift": "skills/shared/references/harness-drift.md",
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
            "skills/plan-and-execute/SKILL.md",
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
            "skills/shared/references/analysis/pro-oracle-escalation.md",
            "skills/shared/references/contract-ownership.md",
            "skills/first-principles-mode/SKILL.md",
            "skills/plan-and-execute/SKILL.md",
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
        "owner": {"skills/shared/references/analysis/pro-oracle-escalation.md"},
        "allowed": {
            "skills/shared/references/contract-ownership.md",
            "skills/plan-and-execute/SKILL.md",
            "skills/shared/references/planning/generate-tasks.md",
            "skills/shared/references/planning/improve-plan.md",
            "skills/plan-refine/SKILL.md",
        },
        "single": ["pro_synthesis_complete: yes"],
        "together": ["oracle_result_read", "findings_reconciled"],
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
    plan_and_execute = (ROOT / "skills/plan-and-execute/SKILL.md").read_text()
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

    orchestrator_tokens = [
        "Refinement Completion Stamp",
        "plan_refine_complete: yes",
        "ready_for_execution: yes",
        "fresh_reviewer_rounds",
        "reviewer_stop_gate: no_unresolved_blocker_or_material",
        "before any implementation edit",
    ]
    for token in orchestrator_tokens:
        if token not in plan_and_execute:
            fail(errors, "PD-PLAN-EXECUTE-REFINE-GATE", f"skills/plan-and-execute/SKILL.md missing refine gate token: {token}")

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
    plan_and_execute = (ROOT / "skills/plan-and-execute/SKILL.md").read_text()
    execute_task = (ROOT / "skills/execute-task/SKILL.md").read_text()
    plan_to_goal = (ROOT / "skills/plan-to-goal/SKILL.md").read_text()
    finalization_gate = (ROOT / "skills/shared/references/execution/finalization-gate.md").read_text()
    readme = (ROOT / "README.md").read_text()

    deliver_tokens = [
        "Execution scope is the entire unchecked remainder of `tasks/execution-plan-<plan-key>.md`",
        "`$deliver plan` creates or refines `tasks/execution-plan-<plan-key>.md`, embeds the Deliver implementation instruction in the plan, then stops for review.",
        "When the user later says `implement`, `implement the doc`, `implement this plan`, `go ahead`, or equivalent",
        "When a plan document contains the Deliver implementation instruction, that document is enough to route implementation back through this skill.",
        "plain-language deliver requests such as `deliver`, `implement deliver`, `deliver this`, `start deliver`, or `continue deliver`",
        "Later user messages such as `implement`, `implement deliver`, `go ahead`, `start`, `continue`, `finish it`, `do it`, or `ship it` are approval/resume signals",
        "Deliver implementation instruction:",
        "Include the exact Deliver implementation instruction near the top of every normal execution plan.",
        "Tell the user they can say `implement the doc` when it looks right.",
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
    ]
    for token in deliver_tokens:
        if token not in deliver:
            fail(errors, "PD-DELIVER-TERMINAL-GATE", f"skills/deliver/SKILL.md missing terminal-gate token: {token}")

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
        "Keep the `/goal` prompt compact.",
        "under 4,000 characters",
        "State Recording",
        "If validation results decide the next implementation step",
        "badness-prior training task",
        "calculate the plausible maximum",
    ]
    for token in plan_to_goal_tokens:
        if token not in plan_to_goal:
            fail(errors, "PD-PLAN-TO-GOAL", f"skills/plan-to-goal/SKILL.md missing token: {token}")

    plan_and_execute_goal_tokens = [
        "skills/plan-to-goal/SKILL.md",
        "Before one-shot execution, check whether the generated or refined artifacts are goal-shaped",
        "decisive evidence depends on a slow, paid, approval-gated, nightly, or externally scheduled run",
        "Do not continue into `$execute-task --one-shot` after creating a goal plan.",
        "Do not add this preflight to `$execute-task`",
    ]
    for token in plan_and_execute_goal_tokens:
        if token not in plan_and_execute:
            fail(errors, "PD-PLAN-EXECUTE-GOAL-FORK", f"skills/plan-and-execute/SKILL.md missing goal-fork token: {token}")

    forbidden_execute_task_tokens = [
        "plan-to-goal",
        "goal-shaped",
        "goal plan",
    ]
    for token in forbidden_execute_task_tokens:
        if token in execute_task:
            fail(errors, "PD-EXECUTE-TASK-NO-GOAL-FORK", f"skills/execute-task/SKILL.md should not contain goal-fork token: {token}")

    readme_tokens = [
        "goal-plan prompt for adaptive evidence loops",
        "`plan-to-goal` | `$plan-to-goal [plan-key=<plan-key>]`",
        "tasks/goal-plan-<plan-key>.md",
    ]
    for token in readme_tokens:
        if token not in readme:
            fail(errors, "PD-DELIVER-README-GOAL-PLAN", f"README.md missing deliver goal-plan token: {token}")

    finalization_tokens = [
        "Portable hard gate for `$execute-task --one-shot`, `$plan-and-execute`, and `$deliver`.",
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
    validate_mirrors(errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("skill contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
