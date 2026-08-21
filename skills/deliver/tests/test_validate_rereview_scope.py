from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_rereview_scope.py"
SPEC = importlib.util.spec_from_file_location("validate_rereview_scope", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def action(finding_id: str, **enabled_flags: bool) -> dict:
    flags = {name: False for name in MODULE.RISK_FLAGS}
    flags.update(enabled_flags)
    required_scope = MODULE.derived_scope(flags)
    return {
        "finding_id": finding_id,
        "repair_boundary": f"repair boundary for {finding_id}",
        "risk_flags": flags,
        "required_scope": required_scope,
        "scope_rationale": f"derived scope for {finding_id}",
    }


def record(*actions: dict, rounds: list[dict] | None = None) -> dict:
    return {
        "schema_version": 1,
        "actions": list(actions),
        "rounds": [] if rounds is None else rounds,
    }


class RereviewScopeValidatorTests(unittest.TestCase):
    def test_isolated_repair_is_targeted(self) -> None:
        value = record(action("F-1"))
        self.assertEqual(MODULE.validate_record(value, "plan"), {"F-1": "targeted"})

    def test_cross_process_completion_requires_full(self) -> None:
        value = record(action("F-1", cross_process_or_async_completion=True))
        self.assertEqual(MODULE.validate_record(value, "plan"), {"F-1": "full"})

    def test_mutation_plus_output_requires_full(self) -> None:
        value = record(
            action(
                "RF-002",
                irreversible_mutation=True,
                user_visible_output_or_diagnostics=True,
            )
        )
        self.assertEqual(MODULE.validate_record(value, "plan"), {"RF-002": "full"})

        value["actions"][0]["required_scope"] = "targeted"
        with self.assertRaisesRegex(MODULE.RecordError, "requires full rereview"):
            MODULE.validate_record(value, "plan")

    def test_grouped_round_uses_widest_action_scope(self) -> None:
        value = record(
            action("F-targeted"),
            action("F-full", public_contract=True),
            rounds=[
                {
                    "round_id": "round-1",
                    "reviewed_finding_ids": ["F-targeted", "F-full"],
                    "scope": "full",
                }
            ],
        )
        MODULE.validate_record(value, "complete")

        value["rounds"][0]["scope"] = "targeted"
        with self.assertRaisesRegex(MODULE.RecordError, "widest action"):
            MODULE.validate_record(value, "complete")

    def test_missing_or_malformed_risk_flags_fail_closed(self) -> None:
        missing = record(action("F-1"))
        del missing["actions"][0]["risk_flags"]["public_contract"]
        with self.assertRaisesRegex(MODULE.RecordError, "keys mismatch"):
            MODULE.validate_record(missing, "plan")

        malformed = record(action("F-1"))
        malformed["actions"][0]["risk_flags"]["public_contract"] = "no"
        with self.assertRaisesRegex(MODULE.RecordError, "must be a boolean"):
            MODULE.validate_record(malformed, "plan")

    def test_complete_phase_requires_evidence_for_every_action(self) -> None:
        value = record(
            action("F-1"),
            action("F-2"),
            rounds=[
                {
                    "round_id": "round-1",
                    "reviewed_finding_ids": ["F-1"],
                    "scope": "targeted",
                }
            ],
        )
        with self.assertRaisesRegex(MODULE.RecordError, "missing executed rereview evidence"):
            MODULE.validate_record(value, "complete")

    def test_plan_phase_rejects_pretended_executed_rounds(self) -> None:
        value = record(action("F-1"))
        value["rounds"] = [
            {
                "round_id": "round-1",
                "reviewed_finding_ids": ["F-1"],
                "scope": "targeted",
            }
        ]
        with self.assertRaisesRegex(MODULE.RecordError, "empty rounds array"):
            MODULE.validate_record(value, "plan")


if __name__ == "__main__":
    unittest.main()
