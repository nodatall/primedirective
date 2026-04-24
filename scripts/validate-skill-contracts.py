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
    "plan-refine": "skills/plan-refine/SKILL.md",
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
        "key": "deep-research-stamp-detail",
        "error": "PD-CONTRACT-MIRROR-DEEP-RESEARCH",
        "owner": {"skills/shared/references/planning/deep-research.md"},
        "allowed": {
            "skills/shared/references/analysis/pro-oracle-escalation.md",
            "skills/shared/references/contract-ownership.md",
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
        if len(cells) != 3:
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
        actual = public_tokens(rows.get(name, ""))
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
    for line in path.read_text().splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        key = cells[0].strip("`")
        owner = cells[1].replace("`", "")
        if key in REQUIRED_CONTRACTS:
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


def mirror_hits() -> list[tuple[str, str, str, str]]:
    hits: list[tuple[str, str, str, str]] = []
    for file_path in sorted((ROOT / "skills").glob("**/*.md")):
        rel_path = rel(file_path)
        text = file_path.read_text()
        for check in MIRROR_CHECKS:
            if rel_path in check["owner"] or rel_path in check["allowed"]:
                continue
            reasons: list[str] = []
            for token in check["single"]:
                if token in text:
                    reasons.append(token)
            together = check["together"]
            if together and all(token in text for token in together):
                reasons.append(" + ".join(together))
            for reason in reasons:
                hits.append((check["error"], check["key"], rel_path, reason))
    return hits


def print_inventory() -> None:
    print("# Stale Mirror Inventory")
    print()
    current_hits = mirror_hits()
    if not current_hits:
        print("No prohibited stale-mirror hits found by the final scanner.")
        return
    print("| error_id | pattern_key | path | matched | disposition |")
    print("| --- | --- | --- | --- | --- |")
    for error_id, key, path, reason in current_hits:
        print(f"| `{error_id}` | `{key}` | `{path}` | `{reason}` | `refactor/remove` |")


def validate_mirrors(errors: list[str]) -> None:
    for error_id, key, path, reason in mirror_hits():
        fail(errors, error_id, f"{path} matches {key} outside owner/allowlist: {reason}")


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
    validate_mirrors(errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("skill contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
