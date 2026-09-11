from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import importlib.util


MODULE_PATH = Path(__file__).resolve().parents[1] / "readiness_transition.py"
SPEC = importlib.util.spec_from_file_location("deliver_v1232_readiness_transition", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
transition = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transition)


class ReadinessTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp(prefix="deliver-v1232-readiness-", dir="/private/tmp"))
        self.addCleanup(shutil.rmtree, self.repo)
        self.public_patch = mock.patch.object(transition, "PUBLIC_REPOSITORY", self.repo)
        self.private_patch = mock.patch.object(
            transition, "PRIVATE_EVALUATOR_REPOSITORY", self.repo / "private-evaluator"
        )
        self.public_patch.start()
        self.private_patch.start()
        self.addCleanup(self.public_patch.stop)
        self.addCleanup(self.private_patch.stop)
        self.git("init", "-q")
        self.git("config", "user.email", "evaluator-test@example.invalid")
        self.git("config", "user.name", "Evaluator Test")
        self.frozen_path = "evals/deliver/plain-language-v12/adapter.py"
        source_root = MODULE_PATH.parents[3]
        for relative, content in (
            (self.frozen_path, b"frozen controller\n"),
            *(
                (relative, (source_root / relative).read_bytes())
                for relative in transition.DEPENDENCY_ROLES
            ),
        ):
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.write_json(
            transition.DEPENDENCY_MANIFEST_RELATIVE_PATH,
            transition.build_dependency_manifest(self.repo),
        )
        self.git("add", self.frozen_path, *transition.DEPENDENCY_OBSERVED_ROLES)
        self.git("commit", "-q", "-m", "controller")
        self.controller_commit = self.git("rev-parse", "HEAD")
        self.document = self.author_document()
        self.write_json(transition.READINESS_RELATIVE_PATH, self.document)
        self.git("add", transition.READINESS_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "author ready")
        self.author_commit = self.git("rev-parse", "HEAD")

    def git(self, *arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments], cwd=self.repo, check=True, capture_output=True, text=True,
        ).stdout.strip()

    def write_json(self, relative_path: str, value: object) -> Path:
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(transition.canonical_file_bytes(value))
        return path

    def author_document(self) -> dict[str, object]:
        frozen = (self.frozen_path, *transition.DEPENDENCY_OBSERVED_ROLES)
        document: dict[str, object] = {
            "schema_version": transition.SCHEMA_VERSION,
            "oracle_version": transition.ORACLE_VERSION,
            "status": "author_ready",
            "private_evaluator_source_commit": "1" * 40,
            "private_evaluator_commit": "2" * 40,
            "public_adapter_introducing_commit": self.controller_commit,
            "independent_case_bundle_interface_path": transition.BUNDLE_INTERFACE_RELATIVE_PATH,
            "independent_case_bundle_interface_sha256": transition.sha256_bytes(
                (self.repo / transition.BUNDLE_INTERFACE_RELATIVE_PATH).read_bytes()
            ),
            "independent_case_bundle_source_commit": "5" * 40,
            "independent_case_bundle_source_tree": "6" * 40,
            "independent_case_bundle_manifest_sha256": "7" * 64,
            "independent_case_bundle_validation_sha256": "8" * 64,
            "independent_case_bundle_complete_import_status": "pass",
            "frozen_public_file_digests": {
                path: transition.sha256_bytes((self.repo / path).read_bytes()) for path in frozen
            },
            "frozen_public_file_commits": {path: self.controller_commit for path in frozen},
            "root_isolation_contract": transition.root_isolation_contract(),
            "root_isolation_dependency_binding": transition.dependency_binding(
                self.repo, self.controller_commit
            ),
            "readiness_predecessor_commit": "pending_transition",
            "readiness_predecessor_sha256": "pending_transition",
            "independent_review_record_path": transition.REVIEW_RELATIVE_PATH,
            "independent_review_record_sha256": "pending_independent_review",
            "trusted_host_isolation_receipt_path": transition.ISOLATION_RELATIVE_PATH,
            "trusted_host_isolation_receipt_sha256": "pending_trusted_host_isolation",
            "independent_review_result_kind": "pending_independent_review",
            "private_independent_reviewed_source_commit": "pending_independent_review",
            "private_independent_reviewed_final_commit": "pending_independent_review",
            "trusted_host_isolation_result_kind": "pending_trusted_host_isolation",
            "private_trusted_host_isolation_tested_source_commit": "pending_trusted_host_isolation",
            "private_trusted_host_isolation_tested_final_commit": "pending_trusted_host_isolation",
            "independent_semantic_review_status": "pending_independent_review",
            "hidden_material_noninterference_independent_review_status": "pending_independent_review",
            "judge_packet_recursive_identity_scan_independent_review_status": "pending_independent_review",
            "content_control_plane_separation_independent_review_status": "pending_independent_review",
            "case_grouping_independent_review_status": "pending_independent_review",
            "zero_static_coverage_independent_review_status": "pending_independent_review",
            "comparison_runtime_review_status": "pending_independent_review",
            "durable_comparison_lifecycle_independent_review_status": "pending_independent_review",
            "trusted_root_independent_review_status": "pending_independent_review",
            "sealed_artifact_derivation_independent_review_status": "pending_independent_review",
            "isolation_probe_status": "pending_trusted_host_isolation",
            "proportionality": {"safe_grouping_review_status": "pending_independent_review"},
            "coverage_credit_policy": {"independent_review_status": "pending_independent_review"},
        }
        document["immutable_readiness_sha256"] = transition.immutable_digest(document)
        return document

    def review_record(self, **updates: object) -> dict[str, object]:
        author = transition.verify_author_ready(self.repo)
        record: dict[str, object] = {
            "schema_version": 1,
            "oracle_version": transition.ORACLE_VERSION,
            "record_kind": "independent_review",
            "result": "pass",
            "reviewer_allocation_id": "fresh-reviewer-allocation-v1232",
            "reviewer_nonce": "3" * 64,
            "private_evaluator_source_commit": self.document["private_evaluator_source_commit"],
            "private_evaluator_final_commit": self.document["private_evaluator_commit"],
            "public_controller_commit": self.controller_commit,
            "predecessor_readiness_commit": author["commit"],
            "predecessor_readiness_sha256": author["sha256"],
            "immutable_readiness_sha256": self.document["immutable_readiness_sha256"],
            "reviewed_public_file_digests_sha256": transition.sha256_bytes(
                transition.canonical_json(self.document["frozen_public_file_digests"])
            ),
            "checks": {name: "pass" for name in transition.REVIEW_CHECKS},
        }
        record.update(updates)
        return record

    def prepare_review(self) -> dict[str, str]:
        record_path = self.write_json("review-input.json", self.review_record())
        transition.prepare_independent_review(self.repo, record_path)
        self.git("add", transition.READINESS_RELATIVE_PATH, transition.REVIEW_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "independent review pass")
        return transition.verify_independent_review_pass(self.repo)

    def probe_evidence(self, operation: str, challenge: str) -> dict[str, object]:
        probe_id, claims = transition.PROBE_SPECS[operation]
        common: dict[str, object] = {
            "schema_version": 1,
            "oracle_version": transition.ORACLE_VERSION,
            "probe_id": probe_id,
            "challenge": challenge,
            "result": "pass",
            "claims": {name: True for name in claims},
        }
        if operation == "outer-sandbox":
            common["sandbox_profile_sha256"] = "4" * 64
        else:
            common.update({
                "bundled_codex_identity": {
                    "path": "/Applications/ChatGPT.app/Contents/Resources/codex",
                    "version": "codex-test",
                    "sha256": "5" * 64,
                },
                "runner_trace_sha256": "6" * 64,
                "runner_profile_sha256": "7" * 64,
            })
        common["dependency_manifest_sha256"] = self.document[
            "root_isolation_dependency_binding"
        ]["manifest_sha256"]
        closure_root = Path(".")
        common["staged_dependency_observations_sha256"] = "8" * 64
        return common

    def fake_probe(self, command: list[str], _repo: Path) -> subprocess.CompletedProcess[str]:
        operation = command[3]
        challenge = command[-1]
        evidence = self.probe_evidence(operation, challenge)
        closure_root = Path(command[command.index("--closure-root") + 1])
        staged = transition._stage_dependency_closure_observations(closure_root)
        evidence["staged_dependency_observations_sha256"] = transition.sha256_bytes(
            transition.canonical_json(staged)
        )
        evidence["dependency_manifest_sha256"] = command[
            command.index("--dependency-manifest-sha256") + 1
        ]
        return subprocess.CompletedProcess(
            command, 0, (transition.canonical_json(evidence) + b"\n").decode(), ""
        )

    def run_root(self, side_effect=None) -> None:
        with mock.patch.object(transition, "_verify_private_evaluator") as private_check, mock.patch.object(
            transition, "_execute_probe_command", side_effect=side_effect or self.fake_probe,
        ):
            transition.run_root_isolation(self.repo)
            self.assertEqual(private_check.call_count, 2)

    def dependency_manifest_inputs(self) -> tuple[dict[str, bytes], dict[str, str]]:
        blobs = {
            path: (self.repo / path).read_bytes() for path in transition.DEPENDENCY_ROLES
        }
        modes = {
            path: transition._file_mode(self.repo / path)
            for path in transition.DEPENDENCY_ROLES
        }
        return blobs, modes

    def prepare_ready(self) -> dict[str, str]:
        self.run_root()
        self.git("add", transition.READINESS_RELATIVE_PATH, transition.ISOLATION_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "ready")
        return transition.verify_ready(self.repo)

    def test_full_committed_monotonic_lifecycle_and_unrelated_descendant(self) -> None:
        self.assertEqual(transition.verify_author_ready(self.repo)["status"], "author_ready")
        (self.repo / "unrelated-author.txt").write_text("later author work\n", encoding="utf-8")
        self.git("add", "unrelated-author.txt")
        self.git("commit", "-q", "-m", "unrelated author descendant")
        self.prepare_review()
        (self.repo / "unrelated-review.txt").write_text("later review work\n", encoding="utf-8")
        self.git("add", "unrelated-review.txt")
        self.git("commit", "-q", "-m", "unrelated review descendant")
        ready = self.prepare_ready()
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(
            json.loads((self.repo / transition.ISOLATION_RELATIVE_PATH).read_text())["network_policy"],
            transition.NETWORK_POLICY,
        )

    def test_controller_frozen_scaffold_is_exact_and_non_ready(self) -> None:
        scaffold = {
            "schema_version": transition.SCHEMA_VERSION,
            "oracle_version": transition.ORACLE_VERSION,
            "status": "controller_frozen_awaiting_independent_bundle",
            "public_adapter_identifier": "deliver_plain_language_v12",
            "independent_case_bundle_interface_path": transition.BUNDLE_INTERFACE_RELATIVE_PATH,
            "independent_case_bundle_interface_sha256": transition.sha256_bytes(
                (self.repo / transition.BUNDLE_INTERFACE_RELATIVE_PATH).read_bytes()
            ),
            "hidden_case_authoring_performed": False,
            "private_evaluator_freeze_performed": False,
            "independent_review_performed": False,
            "trusted_host_isolation_performed": False,
            "official_arm_execution_performed": False,
            "official_judge_execution_performed": False,
        }
        self.write_json(transition.READINESS_RELATIVE_PATH, scaffold)
        self.git("add", transition.READINESS_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "controller frozen")
        result = transition.verify_controller_frozen(self.repo)
        self.assertEqual(result["status"], scaffold["status"])
        self.assertEqual(
            set(result["public_file_sha256"]),
            set(transition.DEPENDENCY_OBSERVED_ROLES),
        )
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.verify_author_ready(self.repo)

    def test_controller_frozen_scaffold_rejects_claims_or_unknown_fields(self) -> None:
        base = {
            "schema_version": transition.SCHEMA_VERSION,
            "oracle_version": transition.ORACLE_VERSION,
            "status": "controller_frozen_awaiting_independent_bundle",
            "public_adapter_identifier": "deliver_plain_language_v12",
            "independent_case_bundle_interface_path": transition.BUNDLE_INTERFACE_RELATIVE_PATH,
            "independent_case_bundle_interface_sha256": transition.sha256_bytes(
                (self.repo / transition.BUNDLE_INTERFACE_RELATIVE_PATH).read_bytes()
            ),
            "hidden_case_authoring_performed": False,
            "private_evaluator_freeze_performed": False,
            "independent_review_performed": False,
            "trusted_host_isolation_performed": False,
            "official_arm_execution_performed": False,
            "official_judge_execution_performed": False,
        }
        for field, value in (
            ("hidden_case_authoring_performed", True),
            ("private_evaluator_freeze_performed", True),
            ("unexpected", False),
        ):
            candidate = dict(base)
            candidate[field] = value
            self.write_json(transition.READINESS_RELATIVE_PATH, candidate)
            self.git("add", transition.READINESS_RELATIVE_PATH)
            self.git("commit", "-q", "-m", f"invalid scaffold {field}")
            with self.assertRaises(transition.ReadinessTransitionError):
                transition.verify_controller_frozen(self.repo)

    def test_ready_cannot_skip_independent_review(self) -> None:
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root()

    def test_forged_reviewer_record_is_rejected(self) -> None:
        path = self.write_json(
            "review-input.json", self.review_record(private_evaluator_final_commit="9" * 40)
        )
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.prepare_independent_review(self.repo, path)

    def test_caller_receipt_and_pass_flags_are_not_cli_inputs(self) -> None:
        for forbidden in ("--receipt", "--network-boundary-pass", "--checks"):
            with mock.patch.object(
                sys,
                "argv",
                [str(MODULE_PATH), "run-root-isolation", "--repo", str(self.repo), forbidden, "x"],
            ), self.assertRaises(SystemExit):
                transition.main()

    def test_caller_environment_pass_flags_do_not_enter_receipt(self) -> None:
        self.prepare_review()
        with mock.patch.dict(os.environ, {"NETWORK_BOUNDARY": "pass", "ROOT_OBSERVED": "true"}):
            self.run_root()
        receipt = (self.repo / transition.ISOLATION_RELATIVE_PATH).read_text()
        self.assertNotIn("NETWORK_BOUNDARY", receipt)
        self.assertNotIn("ROOT_OBSERVED", receipt)
        self.assertNotIn("network_boundary", receipt)

    def test_failed_or_skipped_probe_cannot_create_transition_files(self) -> None:
        self.prepare_review()
        def failed(command: list[str], _repo: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 2, "", "probe skipped\n")
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root(failed)
        self.assertFalse((self.repo / transition.ISOLATION_RELATIVE_PATH).exists())
        self.assertEqual(
            json.loads((self.repo / transition.READINESS_RELATIVE_PATH).read_text())["status"],
            "independent_review_pass",
        )

    def test_mocked_success_without_required_evidence_is_rejected(self) -> None:
        self.prepare_review()
        def empty(command: list[str], _repo: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, '{"result":"pass"}\n', "")
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root(empty)

    def test_probe_test_identity_and_output_format_drift_are_rejected(self) -> None:
        self.prepare_review()
        def drift(command: list[str], _repo: Path) -> subprocess.CompletedProcess[str]:
            evidence = self.probe_evidence(command[3], command[-1])
            evidence["probe_id"] = "wrong-test-identity"
            return subprocess.CompletedProcess(command, 0, json.dumps(evidence) + "\n", "")
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root(drift)

    def test_missing_single_observed_claim_is_rejected(self) -> None:
        self.prepare_review()
        def missing(command: list[str], _repo: Path) -> subprocess.CompletedProcess[str]:
            evidence = self.probe_evidence(command[3], command[-1])
            evidence["claims"].pop(next(iter(evidence["claims"])))
            return subprocess.CompletedProcess(
                command, 0, (transition.canonical_json(evidence) + b"\n").decode(), ""
            )
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root(missing)

    def test_frozen_probe_source_drift_is_rejected(self) -> None:
        self.prepare_review()
        path = self.repo / transition.PROBE_RELATIVE_PATH
        path.write_text("tampered probe\n", encoding="utf-8")
        self.git("add", transition.PROBE_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "touch frozen probe")
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root()

    def test_descendant_harness_replacement_cannot_emit_forged_pass(self) -> None:
        self.prepare_review()
        harness = self.repo / transition.HARNESS_RELATIVE_PATH
        harness.write_text("def preflight_runner(*args): return None\n", encoding="utf-8")
        self.git("add", transition.HARNESS_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "replace frozen harness")
        with mock.patch.object(transition, "_verify_private_evaluator"), mock.patch.object(
            transition, "_execute_probe_command"
        ) as execute, self.assertRaises(transition.ReadinessTransitionError):
            transition.run_root_isolation(self.repo)
            execute.assert_not_called()

    def test_touch_and_restore_dependency_history_is_rejected(self) -> None:
        self.prepare_review()
        harness = self.repo / transition.HARNESS_RELATIVE_PATH
        original = harness.read_bytes()
        harness.write_bytes(original + b"\n# touched\n")
        self.git("add", transition.HARNESS_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "touch harness")
        harness.write_bytes(original)
        self.git("add", transition.HARNESS_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "restore harness")
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root()

    def test_dependency_manifest_omission_and_extra_are_rejected(self) -> None:
        blobs, modes = self.dependency_manifest_inputs()
        manifest = transition.build_dependency_manifest(self.repo)
        for replacement in (
            manifest["entries"][:-1],
            [*manifest["entries"], {
                "path": "evals/deliver/forged.py", "role": "forged",
                "sha256": "9" * 64, "git_mode": "100644",
            }],
        ):
            candidate = copy.deepcopy(manifest)
            candidate["entries"] = replacement
            candidate["entry_count"] = len(replacement)
            candidate["entries_sha256"] = transition.sha256_bytes(
                transition.canonical_json(replacement)
            )
            candidate["manifest_sha256"] = transition.sha256_bytes(
                transition.canonical_json(transition._manifest_payload(candidate))
            )
            with self.assertRaises(transition.ReadinessTransitionError):
                transition._validate_dependency_manifest_document(candidate, blobs, modes)

    def test_dependency_symlink_is_rejected(self) -> None:
        harness = self.repo / transition.HARNESS_RELATIVE_PATH
        harness.unlink()
        harness.symlink_to(self.repo / transition.PROBE_RELATIVE_PATH)
        with self.assertRaises(transition.ReadinessTransitionError):
            transition._dependency_observations(self.repo, self.controller_commit)

    def test_pythonpath_shadowing_is_rejected_before_probe(self) -> None:
        self.prepare_review()
        shadowed = {**transition.PROBE_ENVIRONMENT, "PYTHONPATH": "/private/tmp/shadow"}
        with mock.patch.object(transition, "PROBE_ENVIRONMENT", shadowed), mock.patch.object(
            transition, "_verify_private_evaluator"
        ), mock.patch.object(transition, "_execute_probe_command") as execute, self.assertRaises(
            transition.ReadinessTransitionError
        ):
            transition.run_root_isolation(self.repo)
        execute.assert_not_called()

    def test_dependency_pre_post_drift_is_rejected(self) -> None:
        self.prepare_review()
        calls = 0

        def drift(command: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
            nonlocal calls
            result = self.fake_probe(command, repo)
            calls += 1
            if calls == 1:
                harness = self.repo / transition.HARNESS_RELATIVE_PATH
                harness.write_bytes(harness.read_bytes() + b"\n# drift during probes\n")
            return result

        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root(drift)
        self.assertFalse((self.repo / transition.ISOLATION_RELATIVE_PATH).exists())

    def test_staged_extra_file_and_symlink_are_rejected(self) -> None:
        observations = self.document["root_isolation_dependency_binding"]["entries"]
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            transition._stage_dependency_closure(
                self.repo, self.controller_commit, root, observations
            )
            (root / "unexpected.py").write_text("pass\n", encoding="utf-8")
            with self.assertRaises(transition.ReadinessTransitionError):
                transition._stage_dependency_closure_observations(root)
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            transition._stage_dependency_closure(
                self.repo, self.controller_commit, root, observations
            )
            harness = root / transition.HARNESS_RELATIVE_PATH
            harness.unlink()
            harness.symlink_to(root / transition.PROBE_RELATIVE_PATH)
            with self.assertRaises(transition.ReadinessTransitionError):
                transition._stage_dependency_closure_observations(root)

    def test_dirty_tracked_state_is_rejected_before_probe(self) -> None:
        self.prepare_review()
        (self.repo / self.frozen_path).write_text("dirty\n", encoding="utf-8")
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root()

    def test_receipt_is_write_once(self) -> None:
        self.prepare_review()
        self.run_root()
        with self.assertRaises(transition.ReadinessTransitionError):
            self.run_root()

    def test_ready_rejects_rollback_or_receipt_overwrite(self) -> None:
        self.prepare_review()
        self.prepare_ready()
        document = copy.deepcopy(self.document)
        self.write_json(transition.READINESS_RELATIVE_PATH, document)
        self.git("add", transition.READINESS_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "rollback")
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.verify_ready(self.repo)

    def test_ready_rejects_tampered_probe_evidence(self) -> None:
        self.prepare_review()
        self.prepare_ready()
        receipt = json.loads((self.repo / transition.ISOLATION_RELATIVE_PATH).read_text())
        receipt["probes"][0]["evidence"]["claims"]["stage_read_allowed"] = False
        self.write_json(transition.ISOLATION_RELATIVE_PATH, receipt)
        self.git("add", transition.ISOLATION_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "tamper receipt")
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.verify_ready(self.repo)

    def test_review_transition_rejects_immutable_contract_change(self) -> None:
        record_path = self.write_json("review-input.json", self.review_record())
        transition.prepare_independent_review(self.repo, record_path)
        document = json.loads((self.repo / transition.READINESS_RELATIVE_PATH).read_text())
        document["root_isolation_contract"]["network_policy"] = "network isolation passes"
        document["immutable_readiness_sha256"] = transition.immutable_digest(document)
        self.write_json(transition.READINESS_RELATIVE_PATH, document)
        self.git("add", transition.READINESS_RELATIVE_PATH, transition.REVIEW_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "mutate contract")
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.verify_independent_review_pass(self.repo)


if __name__ == "__main__":
    unittest.main()
