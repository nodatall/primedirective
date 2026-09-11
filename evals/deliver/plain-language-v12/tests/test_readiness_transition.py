from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import importlib.util


MODULE_PATH = Path(__file__).resolve().parents[1] / "readiness_transition.py"
SPEC = importlib.util.spec_from_file_location("deliver_v127_readiness_transition", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
transition = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transition)


class ReadinessTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp(prefix="deliver-v127-readiness-", dir="/private/tmp"))
        self.git("init", "-q")
        self.git("config", "user.email", "evaluator-test@example.invalid")
        self.git("config", "user.name", "Evaluator Test")
        self.frozen_path = "evals/deliver/plain-language-v12/adapter.py"
        frozen = self.repo / self.frozen_path
        frozen.parent.mkdir(parents=True)
        frozen.write_text("frozen controller\n", encoding="utf-8")
        self.git("add", self.frozen_path)
        self.git("commit", "-q", "-m", "controller")
        self.controller_commit = self.git("rev-parse", "HEAD")
        self.document = self.author_document()
        self.write_json(transition.READINESS_RELATIVE_PATH, self.document)
        self.git("add", transition.READINESS_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "author ready")
        self.author_commit = self.git("rev-parse", "HEAD")

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)

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
        document: dict[str, object] = {
            "schema_version": transition.SCHEMA_VERSION,
            "oracle_version": transition.ORACLE_VERSION,
            "status": "author_ready",
            "private_evaluator_source_commit": "1" * 40,
            "private_evaluator_commit": "2" * 40,
            "public_adapter_introducing_commit": self.controller_commit,
            "frozen_public_file_digests": {
                self.frozen_path: transition.sha256_bytes(
                    (self.repo / self.frozen_path).read_bytes()
                ),
            },
            "frozen_public_file_commits": {self.frozen_path: self.controller_commit},
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
            "reviewer_allocation_id": "fresh-reviewer-allocation-v127",
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

    def isolation_receipt(self, **updates: object) -> dict[str, object]:
        review = transition.verify_independent_review_pass(self.repo)
        receipt: dict[str, object] = {
            "schema_version": 1,
            "oracle_version": transition.ORACLE_VERSION,
            "record_kind": "trusted_host_isolation",
            "result": "pass",
            "root_observed": True,
            "isolation_nonce": "4" * 64,
            "private_evaluator_source_commit": self.document["private_evaluator_source_commit"],
            "private_evaluator_final_commit": self.document["private_evaluator_commit"],
            "public_controller_commit": self.controller_commit,
            "predecessor_readiness_commit": review["commit"],
            "predecessor_readiness_sha256": review["sha256"],
            "independent_review_record_sha256": review["review_record_sha256"],
            "independent_review_transition_commit": review["commit"],
            "immutable_readiness_sha256": self.document["immutable_readiness_sha256"],
            "checks": {name: "pass" for name in transition.ISOLATION_CHECKS},
        }
        receipt.update(updates)
        return receipt

    def prepare_ready(self) -> dict[str, str]:
        receipt_path = self.write_json("isolation-input.json", self.isolation_receipt())
        transition.prepare_ready(self.repo, receipt_path)
        self.git("add", transition.READINESS_RELATIVE_PATH, transition.ISOLATION_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "ready")
        return transition.verify_ready(self.repo)

    def test_full_committed_monotonic_lifecycle_and_unrelated_descendant(self) -> None:
        self.assertEqual(transition.verify_author_ready(self.repo)["status"], "author_ready")
        (self.repo / "unrelated-author.txt").write_text("later author work\n", encoding="utf-8")
        self.git("add", "unrelated-author.txt")
        self.git("commit", "-q", "-m", "unrelated author descendant")
        self.assertEqual(transition.verify_author_ready(self.repo)["commit"], self.author_commit)
        self.assertEqual(self.prepare_review()["status"], "independent_review_pass")
        (self.repo / "unrelated-review.txt").write_text("later review work\n", encoding="utf-8")
        self.git("add", "unrelated-review.txt")
        self.git("commit", "-q", "-m", "unrelated review descendant")
        self.assertEqual(
            transition.verify_independent_review_pass(self.repo)["status"],
            "independent_review_pass",
        )
        ready = self.prepare_ready()
        self.assertEqual(ready["status"], "ready")
        unrelated = self.repo / "unrelated.txt"
        unrelated.write_text("later work\n", encoding="utf-8")
        self.git("add", "unrelated.txt")
        self.git("commit", "-q", "-m", "unrelated descendant")
        self.assertEqual(transition.verify_ready(self.repo)["commit"], ready["commit"])

    def test_ready_cannot_skip_independent_review(self) -> None:
        receipt = self.write_json("isolation-input.json", {"invalid": True})
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.prepare_ready(self.repo, receipt)

    def test_forged_reviewer_record_is_rejected(self) -> None:
        record = self.review_record(private_evaluator_final_commit="9" * 40)
        path = self.write_json("review-input.json", record)
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.prepare_independent_review(self.repo, path)

    def test_review_transition_rejects_extra_changed_file(self) -> None:
        record_path = self.write_json("review-input.json", self.review_record())
        transition.prepare_independent_review(self.repo, record_path)
        (self.repo / "unexpected.txt").write_text("not allowlisted\n", encoding="utf-8")
        self.git("add", transition.READINESS_RELATIVE_PATH, transition.REVIEW_RELATIVE_PATH, "unexpected.txt")
        self.git("commit", "-q", "-m", "invalid review transition")
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.verify_independent_review_pass(self.repo)

    def test_review_transition_rejects_immutable_field_change(self) -> None:
        record_path = self.write_json("review-input.json", self.review_record())
        transition.prepare_independent_review(self.repo, record_path)
        document = json.loads((self.repo / transition.READINESS_RELATIVE_PATH).read_text())
        document["private_evaluator_commit"] = "9" * 40
        document["immutable_readiness_sha256"] = transition.immutable_digest(document)
        self.write_json(transition.READINESS_RELATIVE_PATH, document)
        self.git("add", transition.READINESS_RELATIVE_PATH, transition.REVIEW_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "invalid immutable mutation")
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.verify_independent_review_pass(self.repo)

    def test_forged_isolation_receipt_is_rejected(self) -> None:
        self.prepare_review()
        receipt = self.isolation_receipt(root_observed=False)
        path = self.write_json("isolation-input.json", receipt)
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.prepare_ready(self.repo, path)

    def test_ready_rejects_rollback_or_overwrite(self) -> None:
        self.prepare_review()
        self.prepare_ready()
        document = copy.deepcopy(self.document)
        self.write_json(transition.READINESS_RELATIVE_PATH, document)
        self.git("add", transition.READINESS_RELATIVE_PATH)
        self.git("commit", "-q", "-m", "rollback")
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.verify_ready(self.repo)

    def test_ready_rejects_frozen_file_touch_even_if_bytes_are_restored(self) -> None:
        self.prepare_review()
        self.prepare_ready()
        path = self.repo / self.frozen_path
        original = path.read_bytes()
        path.write_bytes(original + b"temporary change\n")
        self.git("add", self.frozen_path)
        self.git("commit", "-q", "-m", "touch frozen file")
        path.write_bytes(original)
        self.git("add", self.frozen_path)
        self.git("commit", "-q", "-m", "restore frozen bytes")
        with self.assertRaises(transition.ReadinessTransitionError):
            transition.verify_ready(self.repo)


if __name__ == "__main__":
    unittest.main()
