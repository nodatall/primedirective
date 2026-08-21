#!/usr/bin/env python3
"""Validate Deliver final-review repair scope records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


RISK_FLAGS = {
    "architecture_or_trust_boundary",
    "cross_process_or_async_completion",
    "irreversible_mutation",
    "user_visible_output_or_diagnostics",
    "public_contract",
    "broad_security_or_data_integrity",
    "isolation_unproven",
    "new_material_finding",
}

DIRECT_FULL_FLAGS = RISK_FLAGS - {
    "irreversible_mutation",
    "user_visible_output_or_diagnostics",
}


class RecordError(ValueError):
    pass


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RecordError(f"{label} keys mismatch; missing={missing}, extra={extra}")


def require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecordError(f"{label} must be a non-empty string")
    return value


def derived_scope(flags: dict[str, bool]) -> str:
    direct_full = any(flags[name] for name in DIRECT_FULL_FLAGS)
    mutation_output = (
        flags["irreversible_mutation"]
        and flags["user_visible_output_or_diagnostics"]
    )
    return "full" if direct_full or mutation_output else "targeted"


def validate_record(record: Any, phase: str) -> dict[str, str]:
    if phase not in {"plan", "complete"}:
        raise RecordError("phase must be plan or complete")
    if not isinstance(record, dict):
        raise RecordError("record must be a JSON object")
    require_exact_keys(record, {"schema_version", "actions", "rounds"}, "record")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise RecordError("schema_version must be 1")

    actions = record["actions"]
    if not isinstance(actions, list) or not actions:
        raise RecordError("actions must be a non-empty array")

    required_by_id: dict[str, str] = {}
    for index, action in enumerate(actions):
        label = f"actions[{index}]"
        if not isinstance(action, dict):
            raise RecordError(f"{label} must be an object")
        require_exact_keys(
            action,
            {
                "finding_id",
                "repair_boundary",
                "risk_flags",
                "required_scope",
                "scope_rationale",
            },
            label,
        )
        finding_id = require_nonempty_string(action["finding_id"], f"{label}.finding_id")
        if finding_id in required_by_id:
            raise RecordError(f"duplicate finding_id: {finding_id}")
        require_nonempty_string(action["repair_boundary"], f"{label}.repair_boundary")
        require_nonempty_string(action["scope_rationale"], f"{label}.scope_rationale")

        flags = action["risk_flags"]
        if not isinstance(flags, dict):
            raise RecordError(f"{label}.risk_flags must be an object")
        require_exact_keys(flags, RISK_FLAGS, f"{label}.risk_flags")
        for name, value in flags.items():
            if not isinstance(value, bool):
                raise RecordError(f"{label}.risk_flags.{name} must be a boolean")

        expected_scope = derived_scope(flags)
        if action["required_scope"] != expected_scope:
            raise RecordError(
                f"{finding_id} requires {expected_scope} rereview, "
                f"not {action['required_scope']!r}"
            )
        required_by_id[finding_id] = expected_scope

    rounds = record["rounds"]
    if not isinstance(rounds, list):
        raise RecordError("rounds must be an array")
    if phase == "plan":
        if rounds:
            raise RecordError("plan-phase record must have an empty rounds array")
        return required_by_id
    if not rounds:
        raise RecordError("complete-phase record must include at least one executed round")

    reviewed_ids: set[str] = set()
    round_ids: set[str] = set()
    for index, review_round in enumerate(rounds):
        label = f"rounds[{index}]"
        if not isinstance(review_round, dict):
            raise RecordError(f"{label} must be an object")
        require_exact_keys(
            review_round,
            {"round_id", "reviewed_finding_ids", "scope"},
            label,
        )
        round_id = require_nonempty_string(review_round["round_id"], f"{label}.round_id")
        if round_id in round_ids:
            raise RecordError(f"duplicate round_id: {round_id}")
        round_ids.add(round_id)

        finding_ids = review_round["reviewed_finding_ids"]
        if (
            not isinstance(finding_ids, list)
            or not finding_ids
            or any(not isinstance(item, str) or not item for item in finding_ids)
        ):
            raise RecordError(f"{label}.reviewed_finding_ids must be non-empty strings")
        if len(set(finding_ids)) != len(finding_ids):
            raise RecordError(f"{label}.reviewed_finding_ids contains duplicates")
        unknown = sorted(set(finding_ids) - set(required_by_id))
        if unknown:
            raise RecordError(f"{label} references unknown finding IDs: {unknown}")

        expected_scope = (
            "full"
            if any(required_by_id[finding_id] == "full" for finding_id in finding_ids)
            else "targeted"
        )
        if review_round["scope"] != expected_scope:
            raise RecordError(
                f"{round_id} requires {expected_scope} rereview from its widest action, "
                f"not {review_round['scope']!r}"
            )
        reviewed_ids.update(finding_ids)

    missing = sorted(set(required_by_id) - reviewed_ids)
    if missing:
        raise RecordError(f"actions missing executed rereview evidence: {missing}")
    return required_by_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("--phase", required=True, choices=("plan", "complete"))
    args = parser.parse_args(argv)

    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        required = validate_record(record, args.phase)
    except (OSError, json.JSONDecodeError, RecordError) as exc:
        print(f"deliver rereview scope validation failed: {exc}", file=sys.stderr)
        return 2

    counts = {"targeted": 0, "full": 0}
    for scope in required.values():
        counts[scope] += 1
    print(
        "deliver rereview scope validation passed: "
        f"phase={args.phase} actions={len(required)} "
        f"targeted={counts['targeted']} full={counts['full']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
