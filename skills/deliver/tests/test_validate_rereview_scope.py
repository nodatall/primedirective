from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_rereview_scope.py"
SPEC = importlib.util.spec_from_file_location("validate_rereview_scope", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def action(
    finding_id: str,
    *,
    contract_effect: str = "none",
    contract_source: str | None = None,
    **enabled_flags: bool,
) -> dict:
    flags = {name: False for name in MODULE.RISK_FLAGS}
    flags["changes_approved_public_contract"] = contract_effect == "change"
    flags["isolation_unproven"] = contract_effect == "uncertain"
    flags.update(enabled_flags)
    required_scope = MODULE.derived_scope(flags)
    return {
        "finding_id": finding_id,
        "repair_boundary": f"repair boundary for {finding_id}",
        "approved_contract_basis": {
            "effect": contract_effect,
            "source": contract_source or f"approved contract evidence for {finding_id}",
        },
        "risk_flags": flags,
        "required_scope": required_scope,
        "scope_rationale": f"derived scope for {finding_id}",
    }


def record(*actions: dict, rounds: list[dict] | None = None) -> dict:
    return {
        "schema_version": 3,
        "actions": list(actions),
        "rounds": [] if rounds is None else rounds,
    }


class RereviewScopeValidatorTests(unittest.TestCase):
    def test_isolated_repair_is_targeted(self) -> None:
        value = record(action("F-1"))
        self.assertEqual(MODULE.validate_record(value, "plan"), {"F-1": "targeted"})

    def test_pf_002_cross_process_completion_requires_full(self) -> None:
        value = record(action("PF-002", cross_process_or_async_completion=True))
        self.assertEqual(MODULE.validate_record(value, "plan"), {"PF-002": "full"})

    def test_supported_restoration_is_targeted_for_rf_001_and_rf_003(self) -> None:
        cases = (
            (
                "RF-001",
                {
                    "irreversible_mutation": True,
                    "user_visible_output_or_diagnostics": True,
                },
            ),
            ("RF-003", {}),
        )
        for finding_id, flags in cases:
            with self.subTest(finding_id=finding_id):
                value = record(
                    action(
                        finding_id,
                        contract_effect="restore",
                        contract_source=f"approval record for {finding_id}",
                        **flags,
                    )
                )
                self.assertEqual(
                    MODULE.validate_record(value, "plan"),
                    {finding_id: "targeted"},
                )

                value["actions"][0]["required_scope"] = "full"
                with self.assertRaisesRegex(
                    MODULE.RecordError, "requires targeted rereview"
                ):
                    MODULE.validate_record(value, "plan")

    def test_rf_002_fallible_output_after_mutation_requires_full(self) -> None:
        value = record(
            action(
                "RF-002",
                irreversible_mutation=True,
                user_visible_output_or_diagnostics=True,
                fallible_output_after_irreversible_mutation=True,
            )
        )
        self.assertEqual(MODULE.validate_record(value, "plan"), {"RF-002": "full"})

        value["actions"][0]["required_scope"] = "targeted"
        with self.assertRaisesRegex(MODULE.RecordError, "requires full rereview"):
            MODULE.validate_record(value, "plan")

    def test_ordered_failure_requires_mutation_and_output_flags(self) -> None:
        inconsistent_flags = (
            {"user_visible_output_or_diagnostics": True},
            {"irreversible_mutation": True},
        )
        for prerequisite_flags in inconsistent_flags:
            with self.subTest(prerequisite_flags=prerequisite_flags):
                value = record(action("F-1"))
                value["actions"][0]["risk_flags"].update(
                    prerequisite_flags,
                    fallible_output_after_irreversible_mutation=True,
                )
                with self.assertRaisesRegex(
                    MODULE.RecordError,
                    "fallible_output_after_irreversible_mutation requires both",
                ):
                    MODULE.validate_record(value, "plan")

    def test_contract_effect_and_boolean_combinations(self) -> None:
        for effect in sorted(MODULE.APPROVED_CONTRACT_EFFECTS):
            for changes_contract in (False, True):
                with self.subTest(effect=effect, changes_contract=changes_contract):
                    value = record(
                        action(
                            "F-contract",
                            contract_effect=effect,
                            changes_approved_public_contract=changes_contract,
                        )
                    )
                    if changes_contract == (effect == "change"):
                        expected_scope = (
                            "full" if effect in {"change", "uncertain"} else "targeted"
                        )
                        self.assertEqual(
                            MODULE.validate_record(value, "plan"),
                            {"F-contract": expected_scope},
                        )
                    else:
                        with self.assertRaisesRegex(
                            MODULE.RecordError,
                            "changes_approved_public_contract must be true iff",
                        ):
                            MODULE.validate_record(value, "plan")

    def test_uncertain_contract_effect_requires_isolation_unproven(self) -> None:
        value = record(
            action(
                "F-uncertain",
                contract_effect="uncertain",
                isolation_unproven=False,
            )
        )
        with self.assertRaisesRegex(
            MODULE.RecordError,
            "effect uncertain requires isolation_unproven",
        ):
            MODULE.validate_record(value, "plan")

    def test_contract_basis_schema_and_source_fail_closed(self) -> None:
        missing_effect = record(action("F-missing", contract_effect="restore"))
        del missing_effect["actions"][0]["approved_contract_basis"]["effect"]
        extra_key = record(action("F-extra"))
        extra_key["actions"][0]["approved_contract_basis"]["citation"] = "extra"
        unsupported_restore = record(
            action("F-restore", contract_effect="restore", contract_source=" ")
        )
        invalid_effect = record(action("F-invalid", contract_effect="revision"))

        cases = (
            ("missing effect", missing_effect, "keys mismatch"),
            ("extra key", extra_key, "keys mismatch"),
            ("unsupported restore", unsupported_restore, "must be a non-empty string"),
            ("invalid effect", invalid_effect, "must be one of"),
        )
        for label, value, error in cases:
            with self.subTest(case=label):
                with self.assertRaisesRegex(MODULE.RecordError, error):
                    MODULE.validate_record(value, "plan")

    def test_v2_and_old_new_schema_mixtures_fail_closed(self) -> None:
        v2 = record(action("F-v2"))
        v2["schema_version"] = 2
        old_only = record(action("F-old"))
        old_flags = old_only["actions"][0]["risk_flags"]
        old_flags["public_contract"] = old_flags.pop(
            "changes_approved_public_contract"
        )
        old_and_new = record(action("F-mixed"))
        old_and_new["actions"][0]["risk_flags"]["public_contract"] = False
        missing_basis = record(action("F-no-basis"))
        del missing_basis["actions"][0]["approved_contract_basis"]

        cases = (
            ("schema v2", v2, "schema_version must be 3"),
            ("old flag only", old_only, "keys mismatch"),
            ("old and new flags", old_and_new, "keys mismatch"),
            ("missing basis", missing_basis, "keys mismatch"),
        )
        for label, value, error in cases:
            with self.subTest(case=label):
                with self.assertRaisesRegex(MODULE.RecordError, error):
                    MODULE.validate_record(value, "plan")

    def test_grouped_round_uses_widest_action_scope(self) -> None:
        value = record(
            action("F-targeted"),
            action("F-full", contract_effect="change"),
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
        del missing["actions"][0]["risk_flags"][
            "fallible_output_after_irreversible_mutation"
        ]
        with self.assertRaisesRegex(MODULE.RecordError, "keys mismatch"):
            MODULE.validate_record(missing, "plan")

        malformed = record(action("F-1"))
        malformed["actions"][0]["risk_flags"][
            "fallible_output_after_irreversible_mutation"
        ] = "no"
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
