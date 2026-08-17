from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from evals.deliver import harness


class DeliverEvalHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.contract = self.root / "SKILL.md"
        self.contract.write_text("# Extracted Deliver contract\n", encoding="utf-8")

    def prepare_retry(self, name: str = "stage") -> Path:
        stage = self.root / name
        harness.prepare_scenario("retry-failed", self.contract, stage)
        return stage

    def test_eof_normalized_fixture_and_evaluator_files_are_frozen(self) -> None:
        expected = {
            "fixture/.gitignore": "c356d3f244c58f189b455e791d2827bab893da16bc33a696acf7284701299ad5",
            "fixture/AGENTS.md": "fec5a1f1a9de2e118261646bbf72cc6090ef013ba7bec20c3d14a0ee94e7f829",
            "fixture/README.md": "eac9bf49a2ba578c596545f98817ad35ba4e3498e706a42587dc22f564c991f9",
            "fixture/pyproject.toml": "61c6a391de0a2ee6d778df2e6d4825db53ec27f7b998f08c2baa55767b940659",
            "fixture/queuectl/__init__.py": "f3ce23d1607dd7f0c31c73e37bb65081df9f2ffc5fd08d270ac5a432435852a6",
            "fixture/queuectl/cli.py": "0900d4fce33aa4d75bf60d65b74330b51fe0e768b38a439e0fe52e1a4174cd62",
            "fixture/queuectl/store.py": "dff6161afb58ba0b0bff488d3d02a458f46ee8a22c9b134ddd276aae8a9e7275",
            "fixture/tests/test_cli.py": "da29be1743de74923dc6ae45baca1b12950eb8e37aa33dc06a24be5889a54187",
            "evaluator/hidden_tests.py": "b08f492221194bdaf2100756d89615b07106893db3e6a260c294ba8bebc8e5bc",
            "evaluator/posthoc_review_tests.py": "a0e0699994e0ee3ebc87555514f0488c77f40cdba720e86595ba1239a19dab9f",
        }
        scenario = harness.SUITE_ROOT / "retry-failed"
        for relative, digest in expected.items():
            self.assertEqual(harness.sha256_file(scenario / relative), digest, relative)
        hidden_source = (scenario / "evaluator/hidden_tests.py").read_text(encoding="utf-8")
        self.assertEqual(hidden_source.count("    def test_"), 7)

    def test_preparation_is_identical_allowlisted_and_packet_is_staged_late(self) -> None:
        first = self.prepare_retry("first")
        second = self.prepare_retry("second")
        first_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=first / "repo", text=True).strip()
        second_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=second / "repo", text=True).strip()
        self.assertEqual(first_head, second_head)
        harness.verify_manifest(first)
        manifest = json.loads((first / "runner-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["scenario_stage"], "pre_packet")
        self.assertFalse(any("evaluator" in entry["path"] for entry in manifest["files"]))
        self.assertFalse((first / "scenario/review-packet").exists())

        with self.assertRaises(harness.HarnessError):
            harness.stage_review_packet(first)
        validation = self.root / "public-validation.txt"
        validation.write_text("3 tests passed\n", encoding="utf-8")
        harness.freeze_pre_packet(first, validation)
        harness.stage_review_packet(first)
        self.assertTrue((first / "scenario/review-packet/findings.md").is_file())
        harness.verify_manifest(first)

    def test_nested_contract_package_references_are_staged_and_hashed(self) -> None:
        package = self.root / "contract-package"
        reference = package / "references/review/review-protocol.md"
        reference.parent.mkdir(parents=True)
        (package / "SKILL.md").write_text("# Deliver\n", encoding="utf-8")
        reference.write_text("# Review protocol\n", encoding="utf-8")

        stage = self.root / "package-stage"
        harness.prepare_scenario("retry-failed", package, stage)
        staged_reference = stage / "contract/references/review/review-protocol.md"
        self.assertEqual(staged_reference.read_text(encoding="utf-8"), "# Review protocol\n")
        manifest = json.loads((stage / "runner-manifest.json").read_text(encoding="utf-8"))
        entries = {entry["path"]: entry for entry in manifest["files"]}
        relative = "contract/references/review/review-protocol.md"
        self.assertEqual(entries[relative]["category"], "contract")
        self.assertEqual(entries[relative]["sha256"], harness.sha256_file(staged_reference))
        harness.verify_manifest(stage)

    def test_historical_fixture_is_exactly_pinned(self) -> None:
        stage = self.root / "holdout"
        result = harness.prepare_scenario(
            "preflight-remediation-holdout", self.contract, stage
        )
        self.assertEqual(
            result["fixture_source"],
            "git:27103d3a05eb20072d29917532326a5cbd59dc8f:e82fcd1e96b04cea2b9ed730a20c4d027b9e3049",
        )
        tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=stage / "repo", text=True).strip()
        self.assertEqual(tree, "e82fcd1e96b04cea2b9ed730a20c4d027b9e3049")
        self.assertFalse((stage / "scenario/review-packet").exists())

    def test_manifest_rejects_symlink_path_escape_and_evaluator_input(self) -> None:
        root = self.root / "paths"
        root.mkdir()
        outside = self.root / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        (root / "link").symlink_to(outside)
        with self.assertRaises(harness.HarnessError):
            harness.safe_path(root, "link")
        with self.assertRaises(harness.HarnessError):
            harness.safe_path(root, "../outside.txt")
        with self.assertRaises(harness.HarnessError):
            harness.reject_evaluator_path(Path("scenario/evaluator/ledger.json"))

    def test_trace_audit_is_pre_freeze_only_and_fails_closed(self) -> None:
        clean = self.root / "clean.jsonl"
        clean.write_text(
            '{"event":"tool","path":"repo/queuectl/cli.py"}\n'
            '{"event":"output_freeze"}\n'
            '{"event":"tool","path":"evals/deliver/evaluator/outcome-ledger.json"}\n',
            encoding="utf-8",
        )
        harness.audit_trace(clean)
        contaminated = self.root / "contaminated.jsonl"
        contaminated.write_text(
            '{"event":"tool","path":"retry-failed/evaluator/hidden_tests.py"}\n'
            '{"event":"output_freeze"}\n',
            encoding="utf-8",
        )
        with self.assertRaises(harness.HarnessError):
            harness.audit_trace(contaminated)
        missing_freeze = self.root / "missing-freeze.jsonl"
        missing_freeze.write_text('{"event":"tool","path":"repo/README.md"}\n', encoding="utf-8")
        with self.assertRaises(harness.HarnessError):
            harness.audit_trace(missing_freeze)

    def make_run_record(self, name: str, identity_text: str) -> Path:
        run_root = self.root / name
        evidence = run_root / "evidence"
        evidence.mkdir(parents=True)
        (evidence / "implementation.diff").write_text(
            f"--- /tmp/{identity_text}/old.py\n+++ /tmp/{identity_text}/new.py\n+fixed\n",
            encoding="utf-8",
        )
        (evidence / "tests.diff").write_text("--- tests/test_old.py\n+++ tests/test_new.py\n+covered\n", encoding="utf-8")
        (evidence / "probes.json").write_text('[{"id":"RF-001","passed":true}]\n', encoding="utf-8")
        (evidence / "reviews.json").write_text('[{"finding_id":"RF-001","scope":"targeted"}]\n', encoding="utf-8")
        record = {
            "scenario_id": "retry-failed",
            "snapshots": {"pre_packet": "1" * 64, "post_remediation": "2" * 64},
            "evidence": {
                "implementation_diff": "evidence/implementation.diff",
                "test_diff": "evidence/tests.diff",
                "probe_results": "evidence/probes.json",
                "review_log": "evidence/reviews.json",
            },
            "measurements": {
                "test_count": 1,
                "test_size_lines": 4,
                "full_review_rounds": 0,
                "targeted_rereviews": 1,
                "wall_time_seconds": 2,
            },
            "identity_clues": [identity_text],
        }
        path = run_root / "run-record.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def test_normalization_redacts_identity_and_blind_labels_are_swap_invariant(self) -> None:
        first_record = self.make_run_record("first-run", "baseline-arm-a")
        second_record = self.make_run_record("second-run", "candidate-arm-b")
        first = harness.normalize_run(first_record)
        second = harness.normalize_run(second_record)
        serialized = json.dumps([first, second]).lower()
        self.assertNotIn("baseline", serialized)
        self.assertNotIn("candidate", serialized)
        self.assertNotIn("/tmp/", serialized)
        first_path = self.root / "normalized-first.json"
        second_path = self.root / "normalized-second.json"
        harness.write_json(first_path, first)
        harness.write_json(second_path, second)
        forward = harness.build_blind_packet([first_path, second_path])
        swapped = harness.build_blind_packet([second_path, first_path])
        self.assertEqual(harness.canonical_json(forward), harness.canonical_json(swapped))

    def test_candidate_compliance_is_separate_and_structured(self) -> None:
        record = self.make_run_record("compliance-run", "neutral-label")
        data = json.loads(record.read_text(encoding="utf-8"))
        data["candidate_compliance"] = []
        record.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(harness.HarnessError):
            harness.normalize_run(record)

        report = self.root / "candidate-fields.json"
        report.write_text(
            json.dumps(
                {
                    "revealed_identity": "candidate",
                    "records": [
                        {
                            "finding_id": "RF-001",
                            "test_disposition": "permanent",
                            "test_rationale": "Supported chronological selection boundary.",
                            "repair_authorized": True,
                            "rereview_scope": "targeted",
                            "rereview_rationale": "The repair is isolated to ordering and adjacent tests.",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(harness.check_candidate_compliance(report), {"compliant": True, "violations": []})

    def test_ledger_spans_every_frozen_disposition_and_scope(self) -> None:
        harness.validate_ledger()


if __name__ == "__main__":
    unittest.main()
