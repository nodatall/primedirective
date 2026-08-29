from __future__ import annotations

import contextlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[4]
ADAPTER_PATH = Path(__file__).resolve().parents[1] / "adapter.py"
SPEC = importlib.util.spec_from_file_location("deliver_plain_language_v12_adapter", ADAPTER_PATH)
assert SPEC is not None and SPEC.loader is not None
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scratch = Path(tempfile.mkdtemp(prefix="deliver-v12-adapter-tests-", dir="/private/tmp"))
        cls.authority = adapter.BASELINE_MANIFEST_PATH
        manifest = json.loads(cls.authority.read_text(encoding="utf-8"))
        cls.packages: list[Path] = []
        for label in ("baseline", "candidate"):
            root = cls.scratch / label
            for entry in manifest["files"]:
                path = root / entry["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                result = subprocess.run(
                    ["git", "show", f"{manifest['baseline_commit']}:{entry['path']}"],
                    cwd=REPO_ROOT, check=True, capture_output=True,
                )
                path.write_bytes(result.stdout)
                path.chmod(int(entry["git_mode"], 8) & 0o777)
            cls.packages.append(root)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.scratch.parent == Path("/private/tmp") and cls.scratch.name.startswith(
            "deliver-v12-adapter-tests-"
        ):
            shutil.rmtree(cls.scratch)

    def setUp(self) -> None:
        self.runtimes: list[Path] = []
        self.inputs = Path(tempfile.mkdtemp(prefix="deliver-v12-inputs-", dir="/private/tmp"))
        self.packet = self.inputs / "packet.txt"
        self.packet.write_text("answer-free projected packet\n", encoding="utf-8")
        self.schema = self.inputs / "schema.json"
        self.schema_document = {
            "schema_version": 1,
            "oracle_version": adapter.ORACLE_VERSION,
            "per_arm_response_schema": {
                "type": "array",
                "minItems": 1,
                "maxItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["workflow_record_code"],
                    "properties": {
                        "workflow_record_code": {"type": "string", "pattern": r"^R-[0-9]{4}$"}
                    },
                },
            },
        }
        self.schema.write_text(json.dumps(self.schema_document) + "\n", encoding="utf-8")
        self.labels = self.inputs / "labels.json"
        self.labels.write_text('{"opaque":"mapping"}\n', encoding="utf-8")
        self.readiness = self.inputs / "readiness.json"
        baseline_authority = json.loads(adapter.BASELINE_MANIFEST_PATH.read_text(encoding="utf-8"))
        inventory = json.loads(adapter.INVENTORY_PATH.read_text(encoding="utf-8"))
        behavior_ids = [item["behavior_id"] for item in inventory["behaviors"]]
        self.readiness_document = {
            "schema_version": adapter.READINESS_SCHEMA_VERSION,
            "oracle_version": adapter.ORACLE_VERSION,
            "status": "ready",
            "model": "gpt-5.6-sol",
            "reasoning": "xhigh",
            "public_adapter_identifier": adapter.ADAPTER_IDENTIFIER,
            "public_adapter_introducing_commit": "3" * 40,
            "public_adapter_path": adapter.ADAPTER_RELATIVE_PATH,
            "public_adapter_sha256": adapter.sha256_file(ADAPTER_PATH),
            "public_execution_policy_path": adapter.POLICY_RELATIVE_PATH,
            "public_execution_policy_sha256": adapter.sha256_file(adapter.POLICY_PATH),
            "private_evaluator_source_commit": "4" * 40,
            "private_evaluator_commit": "4" * 40,
            "private_independent_review_attested_source_commit": "4" * 40,
            "private_trusted_host_isolation_attested_source_commit": "4" * 40,
            "private_independent_review_attestation_sha256": "5" * 64,
            "private_trusted_host_isolation_attestation_sha256": "6" * 64,
            "public_contract_inventory_sha256": adapter.sha256_file(adapter.INVENTORY_PATH),
            "baseline_package_manifest_sha256": adapter.sha256_file(adapter.BASELINE_MANIFEST_PATH),
            "baseline_package_content_manifest_sha256": baseline_authority["manifest_sha256"],
            "baseline_commit": baseline_authority["baseline_commit"],
            "private_projected_packet_sha256": adapter.sha256_file(self.packet),
            "per_arm_response_schema_sha256": adapter.sha256_file(self.schema),
            "projected_packet_bytes": self.packet.stat().st_size,
            "projected_packet_lexical_word_count": adapter.lexical_word_count(
                self.packet.read_text(encoding="utf-8")
            ),
            "case_count": len(behavior_ids),
            "single_behavior_case_count": len(behavior_ids),
            "multi_behavior_case_count": 0,
            "previous_oracle_case_reuse_count": 0,
            "behavior_id_count": len(behavior_ids),
            "covered_behavior_ids": behavior_ids,
            "assertion_count": len(behavior_ids),
            "hard_scored_field_instance_count": len(behavior_ids) * 5,
            "hidden_comprehension_behavior_count": len(behavior_ids),
            "full_behavior_lane_gate_count": 0,
            "static_credit_behavior_count": 0,
            "proportionality": {"safe_grouping_review_status": "pass"},
            "coverage_credit_policy": {
                "hidden_deterministic_comprehension_assertions": len(behavior_ids),
                "full_behavior_lane_gates": 0,
                "static_owner_or_route_proofs": 0,
                "unchanged_owner_bytes_or_route_text_can_earn_credit": False,
                "caller_authored_coverage_can_earn_credit": False,
                "independent_review_status": "pass",
            },
            "author_validation_status": "pass",
            "independent_semantic_attestation_status": "pass",
            "case_grouping_independent_review_status": "pass",
            "zero_static_coverage_independent_review_status": "pass",
            "arm_projection_status": "pass",
            "byte_identical_arm_packet_status": "pass",
            "public_adapter_deterministic_integration_status": "pass",
            "comparison_runtime_author_validation_status": "pass",
            "comparison_runtime_review_status": "pass",
            "isolation_probe_status": "pass",
            "live_model_feasibility_status": "pending_official_execution",
            "live_model_execution_performed": False,
            "deterministic_controls_are_live_arm_execution": False,
            "deterministic_controls_are_judge_verdict_evidence": False,
            "execution_limits": dict(adapter.READINESS_EXECUTION_LIMITS),
        }
        self.write_readiness()
        self.identity = {
            "commit": "1" * 40,
            "evals_tree": "2" * 40,
            "adapter_sha256": adapter.sha256_file(ADAPTER_PATH),
        }

    def write_readiness(self) -> None:
        self.readiness.write_text(
            json.dumps(self.readiness_document) + "\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        for runtime in self.runtimes:
            if runtime.parent == Path("/private/tmp") and adapter.SAFE_RUNTIME.fullmatch(runtime.name):
                shutil.rmtree(runtime, ignore_errors=True)
        if self.inputs.parent == Path("/private/tmp") and self.inputs.name.startswith(
            "deliver-v12-inputs-"
        ):
            shutil.rmtree(self.inputs)

    def initialize(self) -> tuple[dict[str, object], Path]:
        with (
            mock.patch.object(adapter, "READINESS_PATH", self.readiness),
            mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
            mock.patch.object(adapter, "repository_identity", return_value=self.identity),
        ):
            result = adapter.initialize_runtime(
                Path("/private/tmp"), self.packet, self.schema,
                self.packages[0], self.packages[1], self.authority, self.labels,
                self.authority,
            )
        runtime = Path(result["runtime_root"])
        self.runtimes.append(runtime)
        return result, Path(result["state_path"])

    @contextlib.contextmanager
    def live_binding_patches(self):
        with mock.patch.object(adapter, "verify_live_bindings"):
            yield

    def mark_process_complete(
        self, state_path: Path, arm: str, *, started_at: float | None = None,
    ) -> Path:
        started_at = adapter.time.time() if started_at is None else started_at
        state = adapter.load_state(state_path)
        arm_root = adapter.control_root(Path(state["binding"]["runtime"]["real_path"])) / "arms" / arm
        attempt_root = arm_root / "comprehension" / "attempt-1"
        attempt_root.mkdir(parents=True)
        response = attempt_root / "response.json"
        response.write_text('[{"workflow_record_code":"R-0001"}]', encoding="utf-8")
        (attempt_root / "trace.jsonl").write_text('{"type":"turn.completed"}\n', encoding="utf-8")
        (attempt_root / "stderr.txt").write_text("", encoding="utf-8")
        (attempt_root / "metadata.json").write_text('{}\n', encoding="utf-8")
        (arm_root / "runner-preflight.json").write_text('{}\n', encoding="utf-8")
        result = arm_root / "controller" / "attempt-1" / "result.json"
        result.parent.mkdir(parents=True, exist_ok=True)
        result.write_text(json.dumps({
            "schema_version": 1, "attempt": 1, "exit_code": 0,
            "error_type": None, "error": None,
        }) + "\n", encoding="utf-8")
        state["arms"][arm].update({
            "status": "process_complete",
            "arm_started_at": started_at,
            "deadline_at": started_at + adapter.EXPECTED_POLICY["arm_total_seconds"],
            "attempts": [{
                "attempt": 1,
                "started_at": started_at,
                "process": {"pid": 999999, "ps_identity_sha256": "3" * 64, "command_sha256": "4" * 64},
                "result_path": str(result),
                "stdout_path": str(result.parent / "stdout.txt"),
                "stderr_path": str(result.parent / "stderr.txt"),
            }],
        })
        adapter.atomic_json(state_path, state)
        return response

    def fail_first_attempt_before_output(self, state_path: Path, *, started_at: float) -> None:
        evidence = {
            "pid": 43001,
            "ps_identity_sha256": "7" * 64,
            "command_sha256": "8" * 64,
        }
        with self.live_binding_patches():
            adapter.launch_arm(
                state_path,
                "baseline",
                now=started_at,
                launcher=lambda _command, _stdout, _stderr: SimpleNamespace(pid=43001),
                identity_reader=lambda _pid, _command: evidence,
            )
            state = adapter.load_state(state_path)
            attempt = state["arms"]["baseline"]["attempts"][-1]
            Path(attempt["result_path"]).write_text(json.dumps({
                "schema_version": 1,
                "attempt": 1,
                "exit_code": 1,
                "error_type": "OSError",
                "error": "pre-output infrastructure",
            }) + "\n", encoding="utf-8")
            with mock.patch.object(adapter, "same_process", return_value=False):
                adapter.poll_arm(state_path, "baseline", now=started_at + 15)

    def test_describe_reports_exact_public_interface_and_policy(self) -> None:
        description = adapter.describe()
        self.assertEqual(description["adapter_identifier"], "deliver_plain_language_v12")
        self.assertEqual(
            list(description["operations"]),
            ["describe", "initialize", "launch-arm", "poll-arm", "seal-arm", "freeze-handoff"],
        )
        self.assertEqual(description["process_policy"], adapter.EXPECTED_POLICY)
        self.assertEqual(set(description["required_arm_artifacts"]), set(adapter.REQUIRED_ARTIFACTS))

    def test_v11_manifest_reproduces_immutable_files(self) -> None:
        manifest = adapter.verify_v11_files()
        self.assertEqual(manifest["baseline_commit"], "021ac29eab5b28afc2222e16944c540dfd8362e9")
        self.assertEqual(len(manifest["files"]), 41)

    def test_initialize_creates_identity_and_binds_exact_packages(self) -> None:
        result, state_path = self.initialize()
        state = adapter.load_state(state_path)
        self.assertRegex(result["run_id"], r"^[0-9a-f]{32}$")
        self.assertRegex(result["nonce"], r"^[0-9a-f]{64}$")
        self.assertEqual(state["binding"]["arm_order"], ["baseline", "candidate"])
        self.assertEqual(state["binding"]["model"], "gpt-5.6-sol")
        self.assertNotEqual(state["run_id"], state["nonce"])
        self.assertIsNone(state["arms"]["baseline"]["arm_started_at"])
        self.assertIsNone(state["arms"]["baseline"]["deadline_at"])
        for arm in adapter.ARMS:
            manifest = state["binding"]["packages"][arm]["package_manifest"]
            self.assertTrue(manifest["files"])
            self.assertTrue(all(item["source_commit"] == manifest["source_commit"] for item in manifest["files"]))
            self.assertTrue(all(item["source_tree"] == manifest["source_tree"] for item in manifest["files"]))

    def test_readiness_requires_every_review_validation_and_isolation_gate(self) -> None:
        for field in adapter.REQUIRED_READINESS_PASS_FIELDS:
            with self.subTest(field=field):
                original = self.readiness_document[field]
                self.readiness_document[field] = "pending_independent_review"
                self.write_readiness()
                try:
                    with (
                        mock.patch.object(adapter, "READINESS_PATH", self.readiness),
                        mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
                        self.assertRaisesRegex(adapter.AdapterError, "gate is not passed"),
                    ):
                        adapter.validate_readiness(self.packet, self.schema)
                finally:
                    self.readiness_document[field] = original
                    self.write_readiness()

    def test_readiness_requires_bound_review_and_isolation_attestations(self) -> None:
        for field in adapter.REQUIRED_READINESS_ATTESTATION_DIGESTS:
            with self.subTest(field=field):
                original = self.readiness_document[field]
                self.readiness_document[field] = "missing"
                self.write_readiness()
                try:
                    with (
                        mock.patch.object(adapter, "READINESS_PATH", self.readiness),
                        mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
                        self.assertRaisesRegex(adapter.AdapterError, "attestation binding"),
                    ):
                        adapter.validate_readiness(self.packet, self.schema)
                finally:
                    self.readiness_document[field] = original
                    self.write_readiness()

    def test_readiness_binds_attestations_to_the_evaluator_source_commit(self) -> None:
        self.readiness_document["private_independent_review_attested_source_commit"] = "7" * 40
        self.write_readiness()
        with (
            mock.patch.object(adapter, "READINESS_PATH", self.readiness),
            mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
            self.assertRaisesRegex(adapter.AdapterError, "do not bind"),
        ):
            adapter.validate_readiness(self.packet, self.schema)

    def test_readiness_rejects_placeholder_or_non_string_bindings(self) -> None:
        cases = (
            ("private_evaluator_commit", "0" * 40, "private evaluator commit"),
            ("private_evaluator_commit", int("4" * 40), "private evaluator commit"),
            ("private_independent_review_attestation_sha256", "0" * 64, "attestation binding"),
        )
        for field, value, message in cases:
            with self.subTest(field=field, value_type=type(value).__name__):
                original = self.readiness_document[field]
                self.readiness_document[field] = value
                self.write_readiness()
                try:
                    with (
                        mock.patch.object(adapter, "READINESS_PATH", self.readiness),
                        mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
                        self.assertRaisesRegex(adapter.AdapterError, message),
                    ):
                        adapter.validate_readiness(self.packet, self.schema)
                finally:
                    self.readiness_document[field] = original
                    self.write_readiness()

    def test_readiness_binds_public_adapter_policy_and_nested_reviews(self) -> None:
        cases = (
            ("public_adapter_identifier", "wrong", "public controller"),
            ("public_adapter_sha256", "0" * 64, "public controller"),
            ("public_execution_policy_sha256", "0" * 64, "public controller"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                original = self.readiness_document[field]
                self.readiness_document[field] = value
                self.write_readiness()
                try:
                    with (
                        mock.patch.object(adapter, "READINESS_PATH", self.readiness),
                        mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
                        self.assertRaisesRegex(adapter.AdapterError, message),
                    ):
                        adapter.validate_readiness(self.packet, self.schema)
                finally:
                    self.readiness_document[field] = original
                    self.write_readiness()

        self.readiness_document["proportionality"]["safe_grouping_review_status"] = (
            "pending_independent_review"
        )
        self.write_readiness()
        with (
            mock.patch.object(adapter, "READINESS_PATH", self.readiness),
            mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
            self.assertRaisesRegex(adapter.AdapterError, "nested independent review"),
        ):
            adapter.validate_readiness(self.packet, self.schema)

    def test_readiness_execution_limits_require_exact_integers(self) -> None:
        self.readiness_document["execution_limits"]["semantic_attempts"] = True
        self.write_readiness()
        with (
            mock.patch.object(adapter, "READINESS_PATH", self.readiness),
            mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
            self.assertRaisesRegex(adapter.AdapterError, "execution limits"),
        ):
            adapter.validate_readiness(self.packet, self.schema)

    def test_readiness_top_level_coverage_counts_match_direct_policy(self) -> None:
        cases = (
            ("hidden_comprehension_behavior_count", 0),
            ("full_behavior_lane_gate_count", 108),
            ("static_credit_behavior_count", 108),
            ("static_credit_behavior_count", False),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                original = self.readiness_document[field]
                self.readiness_document[field] = value
                self.write_readiness()
                try:
                    with (
                        mock.patch.object(adapter, "READINESS_PATH", self.readiness),
                        mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
                        self.assertRaisesRegex(adapter.AdapterError, "direct hidden coverage"),
                    ):
                        adapter.validate_readiness(self.packet, self.schema)
                finally:
                    self.readiness_document[field] = original
                    self.write_readiness()

    def test_readiness_rejects_coordinated_counts_that_do_not_match_inventory(self) -> None:
        fields = (
            "behavior_id_count",
            "case_count",
            "single_behavior_case_count",
            "assertion_count",
            "hidden_comprehension_behavior_count",
        )
        for field in fields:
            self.readiness_document[field] = 1
        self.readiness_document["hard_scored_field_instance_count"] = 5
        self.readiness_document["covered_behavior_ids"] = self.readiness_document[
            "covered_behavior_ids"
        ][:1]
        self.readiness_document["coverage_credit_policy"][
            "hidden_deterministic_comprehension_assertions"
        ] = 1
        self.write_readiness()
        with (
            mock.patch.object(adapter, "READINESS_PATH", self.readiness),
            mock.patch.object(adapter, "VOCABULARY_PATH", self.schema),
            self.assertRaisesRegex(adapter.AdapterError, "direct hidden coverage"),
        ):
            adapter.validate_readiness(self.packet, self.schema)

    def test_load_policy_rejects_boolean_integer_fields(self) -> None:
        policy = self.inputs / "policy.json"
        document = dict(adapter.EXPECTED_POLICY)
        document["semantic_attempts"] = True
        policy.write_text(json.dumps(document) + "\n", encoding="utf-8")
        with (
            mock.patch.object(adapter, "POLICY_PATH", policy),
            self.assertRaisesRegex(adapter.AdapterError, "frozen public policy"),
        ):
            adapter.load_policy()

    def test_initialize_rejects_unexpected_package_file(self) -> None:
        extra = self.packages[1] / "unexpected.txt"
        extra.write_text("unexpected\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(adapter.AdapterError, "unexpected"):
                self.initialize()
        finally:
            extra.unlink()

    def test_launch_poll_and_single_pre_output_restart(self) -> None:
        _, state_path = self.initialize()
        identities: dict[int, dict[str, object]] = {}
        next_pid = iter((41001, 41002, 41003))

        def launcher(command, _stdout, _stderr):
            pid = next(next_pid)
            identities[pid] = {
                "pid": pid,
                "ps_identity_sha256": str(pid).zfill(64),
                "command_sha256": adapter.sha256_bytes(adapter.canonical_json(command)),
            }
            return SimpleNamespace(pid=pid)

        def identity(pid, _command):
            return identities[pid]

        with (
            self.live_binding_patches(),
            mock.patch.object(adapter, "same_process", return_value=False),
        ):
            launched = adapter.launch_arm(state_path, "baseline", launcher=launcher, identity_reader=identity)
            state = adapter.load_state(state_path)
            attempt = state["arms"]["baseline"]["attempts"][-1]
            Path(attempt["result_path"]).write_text(json.dumps({
                "schema_version": 1, "attempt": 1, "exit_code": 1,
                "error_type": "OSError", "error": "pre-output infrastructure",
            }) + "\n", encoding="utf-8")
            failed = adapter.poll_arm(state_path, "baseline", now=attempt["started_at"] + 15)
            self.assertEqual(failed["failure_classification"], "infrastructure_failure_before_output")
            self.assertTrue(failed["restart_permitted"])
            restarted = adapter.launch_arm(
                state_path, "baseline", restart_infrastructure=True,
                launcher=launcher, identity_reader=identity,
            )
            self.assertEqual((launched["attempt"], restarted["attempt"]), (1, 2))
            state = adapter.load_state(state_path)
            attempt = state["arms"]["baseline"]["attempts"][-1]
            Path(attempt["result_path"]).write_text(json.dumps({
                "schema_version": 1, "attempt": 2, "exit_code": 1,
                "error_type": "OSError", "error": "again",
            }) + "\n", encoding="utf-8")
            adapter.poll_arm(state_path, "baseline", now=attempt["started_at"] + 15)
            with self.assertRaisesRegex(adapter.AdapterError, "not eligible"):
                adapter.launch_arm(
                    state_path, "baseline", restart_infrastructure=True,
                    launcher=launcher, identity_reader=identity,
                )

    def test_launch_reattaches_only_to_same_verified_process(self) -> None:
        _, state_path = self.initialize()
        evidence = {"pid": 41501, "ps_identity_sha256": "a" * 64, "command_sha256": "b" * 64}
        launcher = lambda _command, _stdout, _stderr: SimpleNamespace(pid=41501)
        with self.live_binding_patches():
            first = adapter.launch_arm(
                state_path, "baseline", launcher=launcher,
                identity_reader=lambda _pid, _command: evidence,
            )
            with mock.patch.object(adapter, "same_process", return_value=True):
                second = adapter.launch_arm(state_path, "baseline")
            self.assertFalse(first["reattached"])
            self.assertTrue(second["reattached"])
            with mock.patch.object(adapter, "same_process", return_value=False):
                with self.assertRaisesRegex(adapter.AdapterError, "reattachment rejected"):
                    adapter.launch_arm(state_path, "baseline")

    def test_restart_preserves_the_first_launch_deadline(self) -> None:
        _, state_path = self.initialize()
        first_started_at = 1_000.0
        self.fail_first_attempt_before_output(state_path, started_at=first_started_at)
        deadline = first_started_at + adapter.EXPECTED_POLICY["arm_total_seconds"]
        evidence = {
            "pid": 43002,
            "ps_identity_sha256": "9" * 64,
            "command_sha256": "a" * 64,
        }
        with self.live_binding_patches():
            adapter.launch_arm(
                state_path,
                "baseline",
                now=2_000.0,
                restart_infrastructure=True,
                launcher=lambda _command, _stdout, _stderr: SimpleNamespace(pid=43002),
                identity_reader=lambda _pid, _command: evidence,
            )
        arm_state = adapter.load_state(state_path)["arms"]["baseline"]
        self.assertEqual(arm_state["arm_started_at"], first_started_at)
        self.assertEqual(arm_state["deadline_at"], deadline)
        self.assertEqual(arm_state["attempts"][1]["started_at"], 2_000.0)

    def test_restart_after_arm_deadline_is_rejected(self) -> None:
        _, state_path = self.initialize()
        started_at = 1_000.0
        self.fail_first_attempt_before_output(state_path, started_at=started_at)
        deadline = started_at + adapter.EXPECTED_POLICY["arm_total_seconds"]
        with self.live_binding_patches(), self.assertRaisesRegex(
            adapter.AdapterError, "arm total timeout",
        ):
            adapter.launch_arm(
                state_path, "baseline", now=deadline, restart_infrastructure=True,
            )
        arm_state = adapter.load_state(state_path)["arms"]["baseline"]
        self.assertEqual(arm_state["status"], "failed")
        self.assertEqual(arm_state["failure_classification"], "arm_total_timeout")
        self.assertEqual(arm_state["restart_count"], 0)

    def test_poll_attempt_two_uses_the_first_launch_deadline(self) -> None:
        _, state_path = self.initialize()
        started_at = 1_000.0
        self.fail_first_attempt_before_output(state_path, started_at=started_at)
        evidence = {
            "pid": 43003,
            "ps_identity_sha256": "b" * 64,
            "command_sha256": "c" * 64,
        }
        terminated: list[bool] = []
        with self.live_binding_patches():
            adapter.launch_arm(
                state_path,
                "baseline",
                now=2_000.0,
                restart_infrastructure=True,
                launcher=lambda _command, _stdout, _stderr: SimpleNamespace(pid=43003),
                identity_reader=lambda _pid, _command: evidence,
            )
            with mock.patch.object(adapter, "same_process", return_value=True):
                result = adapter.poll_arm(
                    state_path,
                    "baseline",
                    now=started_at + adapter.EXPECTED_POLICY["arm_total_seconds"],
                    terminator=lambda _evidence, _command: terminated.append(True),
                )
        self.assertEqual(result["failure_classification"], "arm_total_timeout")
        self.assertFalse(result["restart_permitted"])
        self.assertEqual(terminated, [True])

    def test_launch_failure_is_durable_and_restartable_only_once(self) -> None:
        _, state_path = self.initialize()
        with self.live_binding_patches():
            with self.assertRaisesRegex(OSError, "spawn failed"):
                adapter.launch_arm(
                    state_path, "baseline",
                    launcher=lambda _command, _stdout, _stderr: (_ for _ in ()).throw(OSError("spawn failed")),
                )
        state = adapter.load_state(state_path)
        self.assertEqual(state["arms"]["baseline"]["status"], "failed")
        self.assertEqual(
            state["arms"]["baseline"]["failure_classification"],
            "infrastructure_failure_before_output",
        )
        evidence = {"pid": 41601, "ps_identity_sha256": "c" * 64, "command_sha256": "d" * 64}
        with self.live_binding_patches():
            adapter.launch_arm(
                state_path, "baseline", restart_infrastructure=True,
                launcher=lambda _command, _stdout, _stderr: SimpleNamespace(pid=41601),
                identity_reader=lambda _pid, _command: evidence,
            )
        self.assertEqual(adapter.load_state(state_path)["arms"]["baseline"]["restart_count"], 1)

    def test_state_rejects_malformed_attempt_identity(self) -> None:
        _, state_path = self.initialize()
        state = adapter.load_state(state_path)
        state["arms"]["baseline"].update({
            "status": "running",
            "arm_started_at": 1.0,
            "deadline_at": 1.0 + adapter.EXPECTED_POLICY["arm_total_seconds"],
            "attempts": [{"attempt": 1}],
        })
        adapter.atomic_json(state_path, state)
        with self.assertRaisesRegex(adapter.AdapterError, "attempt fields"):
            adapter.load_state(state_path)

    def test_state_rejects_malformed_arm_deadline(self) -> None:
        _, state_path = self.initialize()
        state = adapter.load_state(state_path)
        state["arms"]["baseline"]["arm_started_at"] = 1.0
        state["arms"]["baseline"]["deadline_at"] = 2.0
        adapter.atomic_json(state_path, state)
        with self.assertRaisesRegex(adapter.AdapterError, "deadline identity"):
            adapter.load_state(state_path)

    def test_behavior_lane_composes_v11_controls_in_order(self) -> None:
        _, state_path = self.initialize()
        state = adapter.load_state(state_path)
        runtime = Path(state["binding"]["runtime"]["real_path"])
        arm_root = adapter.control_root(runtime) / "arms" / "baseline"
        for scenario in adapter.SCENARIOS:
            inbox = arm_root / "inbox" / scenario
            (inbox / "record").mkdir(parents=True)
            (inbox / "pre-packet-validation.log").write_text("validated\n", encoding="utf-8")
            (inbox / "record" / "run-record.json").write_text('{}\n', encoding="utf-8")
        calls: list[str] = []

        def preflight(path):
            calls.append("preflight")
            path.write_text('{}\n', encoding="utf-8")

        def prepare(scenario, _package, stage, _preflight):
            calls.append(f"{scenario}:prepare")
            (stage / "evaluator").mkdir(parents=True)

        def run(stage, phase):
            calls.append(f"{stage.name.rsplit('-', 1)[0]}:{phase}")

        def freeze(stage, _validation):
            calls.append(f"{stage.name.rsplit('-', 1)[0]}:freeze")

        def stage_packet(stage):
            calls.append(f"{stage.name.rsplit('-', 1)[0]}:stage")

        def finalize(stage, _record):
            calls.append(f"{stage.name.rsplit('-', 1)[0]}:finalize")
            output = stage / "evaluator" / "output-freeze.json"
            output.write_text('{}\n', encoding="utf-8")
            return output

        def normalize(output):
            return {"source": str(output)}

        with (
            mock.patch.object(adapter.v11, "preflight_runner", side_effect=preflight),
            mock.patch.object(adapter.v11, "prepare_scenario", side_effect=prepare),
            mock.patch.object(adapter.v11, "run_scenario", side_effect=run),
            mock.patch.object(adapter.v11, "freeze_pre_packet", side_effect=freeze),
            mock.patch.object(adapter.v11, "stage_review_packet", side_effect=stage_packet),
            mock.patch.object(adapter.v11, "finalize_arm", side_effect=finalize),
            mock.patch.object(adapter.v11, "normalize_run", side_effect=normalize),
        ):
            adapter.run_behavior_lanes(state, "baseline", adapter.time.time() + 60)
        expected = ["preflight"]
        for scenario in adapter.SCENARIOS:
            expected.extend([
                f"{scenario}:prepare", f"{scenario}:pre-packet", f"{scenario}:freeze",
                f"{scenario}:stage", f"{scenario}:remediation", f"{scenario}:finalize",
            ])
        self.assertEqual(calls, expected)

    def test_poll_enforces_interval_and_no_progress_timeout(self) -> None:
        _, state_path = self.initialize()
        evidence = {"pid": 42001, "ps_identity_sha256": "5" * 64, "command_sha256": "6" * 64}

        def launcher(_command, _stdout, _stderr):
            return SimpleNamespace(pid=42001)

        with self.live_binding_patches():
            launched = adapter.launch_arm(
                state_path, "baseline", launcher=launcher,
                identity_reader=lambda _pid, _command: evidence,
            )
            started = adapter.load_state(state_path)["arms"]["baseline"]["attempts"][-1]["started_at"]
            with mock.patch.object(adapter, "same_process", return_value=True):
                early = adapter.poll_arm(state_path, "baseline", now=started + 14)
                self.assertTrue(early["poll_deferred"])
                terminated: list[bool] = []
                timed_out = adapter.poll_arm(
                    state_path, "baseline", now=started + 900,
                    terminator=lambda _evidence, _command: terminated.append(True),
                )
            self.assertEqual(launched["status"], "running")
            self.assertEqual(timed_out["failure_classification"], "no_progress_timeout")
            self.assertEqual(terminated, [True])

    def test_process_complete_reconciliation_rejects_expired_arm(self) -> None:
        _, state_path = self.initialize()
        started_at = 1_000.0
        self.mark_process_complete(state_path, "baseline", started_at=started_at)
        state = adapter.load_state(state_path)
        state["arms"]["baseline"]["status"] = "running"
        deadline = state["arms"]["baseline"]["deadline_at"]
        with mock.patch.object(adapter, "same_process", return_value=False), self.assertRaisesRegex(
            adapter.AdapterError, "arm total timeout",
        ):
            adapter.reconcile_process_complete(
                state_path, state, "baseline", now=deadline,
            )
        self.assertEqual(state["arms"]["baseline"]["status"], "failed")
        self.assertEqual(
            state["arms"]["baseline"]["failure_classification"], "arm_total_timeout",
        )

    def test_seal_rejects_process_complete_arm_after_deadline(self) -> None:
        _, state_path = self.initialize()
        started_at = 1_000.0
        self.mark_process_complete(state_path, "baseline", started_at=started_at)
        deadline = started_at + adapter.EXPECTED_POLICY["arm_total_seconds"]
        with self.live_binding_patches(), self.assertRaisesRegex(
            adapter.AdapterError, "arm total timeout",
        ):
            adapter.seal_arm(state_path, "baseline", now=deadline)
        arm_state = adapter.load_state(state_path)["arms"]["baseline"]
        self.assertEqual(arm_state["status"], "failed")
        self.assertEqual(arm_state["failure_classification"], "arm_total_timeout")

    def test_seal_uses_real_files_rejects_malformed_response_and_freezes_handoff(self) -> None:
        _, state_path = self.initialize()
        baseline_response = self.mark_process_complete(state_path, "baseline")
        baseline_response.write_text("{}", encoding="utf-8")
        with self.live_binding_patches(), self.assertRaisesRegex(adapter.AdapterError, "type"):
            adapter.seal_arm(state_path, "baseline")
        baseline_response.write_text('[{"workflow_record_code":"R-0001"}]', encoding="utf-8")
        observed = {
            "schema_version": 1,
            "adapter_identifier": adapter.ADAPTER_IDENTIFIER,
            "arm": "baseline",
            "scenarios": {scenario: {} for scenario in adapter.SCENARIOS},
        }
        with self.live_binding_patches(), mock.patch.object(adapter, "behavior_artifact", return_value=observed):
            baseline = adapter.seal_arm(state_path, "baseline")
        self.assertEqual(baseline["status"], "sealed")
        baseline_state = adapter.load_state(state_path)["arms"]["baseline"]
        process_evidence = adapter.load_json(
            Path(baseline_state["artifacts"]["process_evidence"]["path"]),
            "process evidence",
        )
        self.assertEqual(process_evidence["arm_started_at"], baseline_state["arm_started_at"])
        self.assertEqual(process_evidence["deadline_at"], baseline_state["deadline_at"])

        candidate_response = self.mark_process_complete(state_path, "candidate")
        observed["arm"] = "candidate"
        with self.live_binding_patches(), mock.patch.object(adapter, "behavior_artifact", return_value=observed):
            candidate = adapter.seal_arm(state_path, "candidate")
            first = adapter.freeze_handoff(state_path)
            second = adapter.freeze_handoff(state_path)
        self.assertEqual(candidate["status"], "sealed")
        self.assertEqual(first, second)
        self.assertEqual(adapter.sha256_file(Path(first["handoff_path"])), first["handoff_sha256"])

        state = adapter.load_state(state_path)
        sealed_trace = Path(state["arms"]["candidate"]["artifacts"]["trace"]["path"])
        sealed_trace.write_text("tampered\n", encoding="utf-8")
        with self.live_binding_patches(), self.assertRaisesRegex(adapter.AdapterError, "drifted"):
            adapter.freeze_handoff(state_path)


if __name__ == "__main__":
    unittest.main()
