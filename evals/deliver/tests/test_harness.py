from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals.deliver import harness


class DeliverEvalHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.contract = self.root / "SKILL.md"
        self.contract.write_text(
            "---\nname: deliver\n---\n\n# Extracted Deliver contract\n",
            encoding="utf-8",
        )
        self.runner_identity = {
            "path": str(harness.BUNDLED_CODEX),
            "version": "codex-cli test",
            "sha256": "a" * 64,
        }
        identity_patch = mock.patch.object(
            harness, "runner_identity", return_value=self.runner_identity
        )
        identity_patch.start()
        self.addCleanup(identity_patch.stop)
        self.preflight = self.root / "runner-preflight.json"
        completed = subprocess.CompletedProcess(
            args=[str(harness.BUNDLED_CODEX)], returncode=0,
            stdout='{"type":"thread.started"}\n{"type":"turn.completed"}\n', stderr="",
        )
        with mock.patch.object(harness, "execute_codex", return_value=completed):
            harness.preflight_runner(self.preflight)

    def prepare_retry(self, name: str = "stage") -> Path:
        stage = self.root / name
        harness.prepare_scenario("retry-failed", self.contract, stage, self.preflight)
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
        self.run_mocked_phase(first, "pre-packet")
        harness.freeze_pre_packet(first, validation)
        harness.stage_review_packet(first)
        self.assertTrue((first / "scenario/review-packet/findings.md").is_file())
        harness.verify_manifest(first)

    def test_nested_contract_package_references_are_staged_and_hashed(self) -> None:
        package = self.root / "contract-package"
        reference = package / "references/review/review-protocol.md"
        reference.parent.mkdir(parents=True)
        (package / "SKILL.md").write_text(
            "---\nname: deliver\n---\n\n# Deliver\n", encoding="utf-8"
        )
        reference.write_text("# Review protocol\n", encoding="utf-8")

        stage = self.root / "package-stage"
        harness.prepare_scenario("retry-failed", package, stage, self.preflight)
        staged_reference = stage / "contract/references/review/review-protocol.md"
        self.assertEqual(staged_reference.read_text(encoding="utf-8"), "# Review protocol\n")
        manifest = json.loads((stage / "runner-manifest.json").read_text(encoding="utf-8"))
        entries = {entry["path"]: entry for entry in manifest["files"]}
        relative = "contract/references/review/review-protocol.md"
        self.assertEqual(entries[relative]["category"], "contract")
        self.assertEqual(entries[relative]["sha256"], harness.sha256_file(staged_reference))
        harness.verify_manifest(stage)

        (package / "references/other/SKILL.md").parent.mkdir(parents=True)
        (package / "references/other/SKILL.md").write_text(
            "---\nname: deliver\n---\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(harness.HarnessError, "exactly one SKILL.md"):
            harness.prepare_scenario(
                "retry-failed", package, self.root / "two-contracts", self.preflight
            )

    def test_historical_fixture_is_exactly_pinned(self) -> None:
        stage = self.root / "holdout"
        result = harness.prepare_scenario(
            "preflight-remediation-holdout", self.contract, stage, self.preflight
        )
        source = result["fixture_source"]
        self.assertEqual(source["resolved_commit"], "27103d3a05eb20072d29917532326a5cbd59dc8f")
        self.assertEqual(source["source_tree"], "e82fcd1e96b04cea2b9ed730a20c4d027b9e3049")
        self.assertEqual(
            source["blobs"],
            {
                "scripts/prime-directive-codex-preflight.sh": {
                    "blob": "c9e3571c2c0815843631c04cb47719653b2b7612",
                    "mode": "100755",
                },
                "scripts/prime-directive-session-update.sh": {
                    "blob": "2b0adb694eaade7d367ff234b74d1ba2f43b1f6a",
                    "mode": "100755",
                },
            },
        )
        visible_repo_files = sorted(
            path.relative_to(stage / "repo").as_posix()
            for path in (stage / "repo").rglob("*")
            if path.is_file() and ".git" not in path.relative_to(stage / "repo").parts
        )
        self.assertEqual(
            visible_repo_files,
            [
                "scripts/prime-directive-codex-preflight.sh",
                "scripts/prime-directive-session-update.sh",
            ],
        )
        runner_visible_skills = [
            path
            for root in (stage / "repo", stage / "scenario", stage / "contract")
            for path in root.rglob("SKILL.md")
        ]
        self.assertEqual(len(runner_visible_skills), 1)
        self.assertEqual(runner_visible_skills[0], stage / "contract/SKILL.md")
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
        with self.assertRaisesRegex(harness.HarnessError, "outside"):
            harness.prepare_scenario(
                "retry-failed", self.contract,
                harness.SOURCE_ROOT / "agent-scratch/eval-stage", self.preflight,
            )

    def test_outer_sandbox_denies_source_read_but_allows_staged_repo(self) -> None:
        stage = self.prepare_retry("sandbox-stage")
        profile = self.root / "runner.sb"
        profile.write_text(harness.sandbox_profile(), encoding="utf-8")
        script = (
            "from pathlib import Path; import sys; Path(sys.argv[1]).read_bytes(); "
            "\ntry: Path(sys.argv[2]).read_bytes()\n"
            "except OSError: print('blocked')\nelse: raise SystemExit(2)"
        )
        result = subprocess.run(
            [
                str(harness.SANDBOX_EXEC), "-f", str(profile), sys.executable, "-c", script,
                str(stage / "repo/README.md"), str(harness.OUTCOME_LEDGER),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 71 and "sandbox_apply: Operation not permitted" in result.stderr:
            self.skipTest("the enclosing test sandbox forbids nested sandbox-exec")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "blocked")

    def test_manifest_mutation_blocks_both_pre_packet_freeze_and_packet_staging(self) -> None:
        validation = self.root / "validation.txt"
        validation.write_text("passed\n", encoding="utf-8")

        before_freeze = self.prepare_retry("mutated-before-freeze")
        skill = before_freeze / "contract/SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "mutated\n", encoding="utf-8")
        with self.assertRaisesRegex(harness.HarnessError, "hash mismatch"):
            harness.freeze_pre_packet(before_freeze, validation)

        before_packet = self.prepare_retry("mutated-before-packet")
        self.run_mocked_phase(before_packet, "pre-packet")
        harness.freeze_pre_packet(before_packet, validation)
        acceptance = before_packet / "scenario/acceptance-contract.md"
        acceptance.write_text(
            acceptance.read_text(encoding="utf-8") + "mutated\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(harness.HarnessError, "hash mismatch"):
            harness.stage_review_packet(before_packet)

        fabricated_snapshot = self.prepare_retry("fabricated-snapshot")
        self.run_mocked_phase(fabricated_snapshot, "pre-packet")
        snapshot_path = harness.freeze_pre_packet(fabricated_snapshot, validation)
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["head"] = "0" * 40
        harness.write_json(snapshot_path, snapshot)
        with self.assertRaisesRegex(harness.HarnessError, "snapshot"):
            harness.stage_review_packet(fabricated_snapshot)

    def test_runner_uses_fixed_codex_exec_and_allowlisted_prompt(self) -> None:
        preflight = harness.validate_runner_preflight(self.preflight)
        self.assertEqual(preflight["binary_path"], str(harness.BUNDLED_CODEX))
        self.assertEqual(preflight["binary_version"], self.runner_identity["version"])
        self.assertEqual(preflight["binary_sha256"], self.runner_identity["sha256"])
        self.assertEqual(preflight["smoke"]["command"][3], str(harness.BUNDLED_CODEX))
        tampered = self.root / "tampered-preflight.json"
        tampered_data = json.loads(self.preflight.read_text(encoding="utf-8"))
        tampered_data["binary_version"] = "different"
        harness.write_json(tampered, tampered_data)
        with self.assertRaisesRegex(harness.HarnessError, "identity drifted"):
            harness.validate_runner_preflight(tampered)
        stage = self.prepare_retry("runner-stage")
        completed = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"type":"thread.started","thread_id":"opaque"}\n{"type":"turn.completed"}\n',
            stderr="",
        )
        with mock.patch.object(harness, "execute_codex", return_value=completed) as execute:
            trace = harness.run_scenario(stage, "pre-packet")
        command, prompt, repo = execute.call_args.args
        self.assertEqual(command, harness.codex_command(
            stage / "repo", stage / "runner/pre-packet/runner.sb"
        ))
        for fixed in ("--json", "--ephemeral", "--ignore-user-config", "gpt-5.6-sol", "workspace-write", 'approval_policy="never"'):
            self.assertIn(fixed, command)
        self.assertEqual(repo, stage / "repo")
        self.assertIn("contract/SKILL.md", prompt)
        self.assertIn("Approved as written. Implement the complete plan.", prompt)
        self.assertNotIn("Queuectl is a dependency-free command-line tool", prompt)
        self.assertEqual(trace.read_text(encoding="utf-8"), completed.stdout)
        metadata = json.loads(
            (stage / "runner/pre-packet/metadata.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["trace_sha256"], harness.sha256_file(trace))
        self.assertEqual(
            metadata["input_manifest_sha256"],
            harness.sha256_file(stage / "runner/pre-packet/input-manifest.json"),
        )
        self.assertEqual(
            metadata["prompt_sha256"],
            harness.sha256_file(stage / "runner/pre-packet/prompt.txt"),
        )
        self.assertEqual(metadata["runner_binary_sha256"], self.runner_identity["sha256"])
        self.assertEqual(
            metadata["runner_preflight_sha256"],
            harness.sha256_file(stage / "evidence/runner-preflight.json"),
        )
        with mock.patch.object(harness, "execute_codex") as second_execute:
            with self.assertRaisesRegex(harness.HarnessError, "already exist"):
                harness.run_scenario(stage, "pre-packet")
            second_execute.assert_not_called()
        invalid_traces = (
            b'{"type":"turn.completed"}\n',
            b'{"type":"thread.started"}\n{"type":"turn.completed"}\n{"type":"item.completed"}\n',
            b'{"type":"thread.started"}\n{"type":"turn.failed"}\n',
        )
        for trace_bytes in invalid_traces:
            with self.assertRaises(harness.HarnessError):
                harness.validate_runner_trace(trace_bytes)

    def run_mocked_phase(self, stage: Path, phase: str) -> None:
        completed = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"type":"thread.started","thread_id":"opaque"}\n{"type":"turn.completed"}\n',
            stderr="",
        )
        with mock.patch.object(harness, "execute_codex", return_value=completed):
            harness.run_scenario(stage, phase)

    def make_freeze_inputs(
        self,
        name: str,
        identity_text: str,
        *,
        commit_code: bool = False,
        omit_diffs: bool = False,
    ) -> tuple[Path, Path]:
        stage = self.prepare_retry(f"{name}-stage")
        repo = stage / "repo"
        self.run_mocked_phase(stage, "pre-packet")
        cli = repo / "queuectl/cli.py"
        cli.write_text(
            cli.read_text(encoding="utf-8") + f"\n# committed {identity_text}\n",
            encoding="utf-8",
        )
        if commit_code:
            subprocess.run(["git", "add", "queuectl/cli.py"], cwd=repo, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Deliver Eval",
                    "-c",
                    "user.email=eval@example.invalid",
                    "commit",
                    "-q",
                    "--no-gpg-sign",
                    "-m",
                    "Runner commit",
                ],
                cwd=repo,
                check=True,
            )
            cli.write_text(
                cli.read_text(encoding="utf-8") + f"# working {identity_text}\n",
                encoding="utf-8",
            )
        (repo / "queuectl/new_module.py").write_text(
            f"LABEL = {identity_text!r}\n", encoding="utf-8"
        )
        (repo / "tests/test_extra.py").write_text(
            "def test_extra():\n    assert True\n", encoding="utf-8"
        )
        validation = self.root / f"{name}-validation.txt"
        validation.write_text("public validation passed\n", encoding="utf-8")
        harness.freeze_pre_packet(stage, validation)
        harness.stage_review_packet(stage)
        self.run_mocked_phase(stage, "remediation")

        implementation_diff, test_diff = harness.repository_diffs(
            repo,
            json.loads((stage / "runner-manifest.json").read_text(encoding="utf-8"))[
                "initial_snapshot"
            ]["commit"],
        )
        run_root = self.root / name
        evidence = run_root / "evidence"
        evidence.mkdir(parents=True)
        (evidence / "implementation.diff").write_text(
            "" if omit_diffs else implementation_diff,
            encoding="utf-8",
        )
        (evidence / "tests.diff").write_text(
            "" if omit_diffs else test_diff, encoding="utf-8"
        )
        ledger = json.loads(harness.OUTCOME_LEDGER.read_text(encoding="utf-8"))
        entries = [entry for entry in ledger["entries"] if entry["scenario"] == "retry-failed"]
        trace_digest = harness.sha256_file(stage / "runner/remediation/trace.jsonl")
        probes = [
            {
                "id": entry["finding_id"],
                "command": f"probe {entry['finding_id']}",
                "exit_status": 0,
                "evidence": f"verified {identity_text}",
                "evidence_ref": "remediation_trace",
                "evidence_sha256": trace_digest,
            }
            for entry in entries
        ]
        reviews = [
            {
                "finding_id": entry["finding_id"],
                "test_disposition": entry["test_disposition"],
                "rereview_scope": entry["rereview_scope"],
                "command": f"review {entry['finding_id']}",
                "exit_status": 0,
                "evidence": f"reviewed {identity_text}",
                "evidence_ref": "remediation_trace",
                "evidence_sha256": trace_digest,
            }
            for entry in entries
        ]
        rounds = [
            {
                "round_id": round_id, "scope": scope,
                "reviewed_finding_ids": finding_ids, "command": f"review {round_id}",
                "exit_status": 0, "evidence": evidence_text,
                "evidence_ref": "remediation_trace", "evidence_sha256": trace_digest,
            }
            for round_id, scope, finding_ids, evidence_text in (
                ("full-1", "full", ["RF-001"], f"reviewed {identity_text}"),
                ("full-2", "full", ["RF-001"], "clean final round; no new findings"),
                ("targeted-1", "targeted", ["RF-001", "RF-002"], f"reviewed {identity_text}"),
                ("targeted-2", "targeted", ["RF-003"], f"reviewed {identity_text}"),
            )
        ]
        (evidence / "probes.json").write_text(json.dumps(probes) + "\n", encoding="utf-8")
        (evidence / "reviews.json").write_text(json.dumps(reviews) + "\n", encoding="utf-8")
        (evidence / "rounds.json").write_text(json.dumps(rounds) + "\n", encoding="utf-8")
        runner_paths = {
            f"{phase.replace('-', '_')}_{kind}": stage / "runner" / phase / filename
            for phase in harness.RUNNER_PHASES
            for kind, filename in harness.RUNNER_FILES.items()
        }
        measurements = harness.derived_measurements(
            test_diff,
            reviews,
            rounds,
            harness.validate_runner_bundles(runner_paths, repo=repo, stage_root=stage),
        )
        record = {
            "scenario_id": "retry-failed",
            "evidence": {
                "implementation_diff": "evidence/implementation.diff",
                "test_diff": "evidence/tests.diff",
                "probe_results": "evidence/probes.json",
                "review_log": "evidence/reviews.json",
                "review_rounds": "evidence/rounds.json",
            },
            "measurements": measurements,
            "identity_clues": [identity_text],
        }
        path = run_root / "run-record.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return stage, path

    def freeze_complete(
        self, name: str, identity_text: str, *, commit_code: bool = False
    ) -> tuple[Path, Path]:
        stage, record = self.make_freeze_inputs(
            name, identity_text, commit_code=commit_code
        )
        output_freeze = harness.finalize_arm(stage, record)
        return output_freeze, stage

    def test_freeze_includes_all_changes_and_counts_repeated_full_rounds(self) -> None:
        stage, record = self.make_freeze_inputs(
            "omitted-delta", "neutral-label", commit_code=True, omit_diffs=True
        )
        self.assertEqual(
            json.loads(record.read_text(encoding="utf-8"))["measurements"]["full_review_rounds"], 2
        )
        with self.assertRaisesRegex(harness.HarnessError, "omits committed"):
            harness.finalize_arm(stage, record)

        implementation_diff, test_diff = harness.repository_diffs(
            stage / "repo",
            json.loads((stage / "runner-manifest.json").read_text(encoding="utf-8"))[
                "initial_snapshot"
            ]["commit"],
        )
        self.assertIn("# committed neutral-label", implementation_diff)
        self.assertIn("# working neutral-label", implementation_diff)
        self.assertIn("new_module.py", implementation_diff)
        self.assertIn("test_extra.py", test_diff)

    def test_normalization_verifies_frozen_artifacts_redacts_recursively_and_is_swap_invariant(self) -> None:
        first_freeze, _ = self.freeze_complete("first-run", "baseline-arm-a")
        second_freeze, _ = self.freeze_complete("second-run", "candidate-arm-b")
        first = harness.normalize_run(first_freeze)
        second = harness.normalize_run(second_freeze)
        serialized = json.dumps([first, second]).lower()
        self.assertNotIn("baseline", serialized)
        self.assertNotIn("candidate", serialized)
        first_path = self.root / "normalized-first.json"
        second_path = self.root / "normalized-second.json"
        harness.write_json(first_path, first)
        harness.write_json(second_path, second)
        forward = harness.build_blind_packet([first_path, second_path])
        swapped = harness.build_blind_packet([second_path, first_path])
        self.assertEqual(harness.canonical_json(forward), harness.canonical_json(swapped))

    def test_normalizer_rechecks_terminal_seal_and_frozen_artifacts(self) -> None:
        output_freeze, _ = self.freeze_complete("snapshot-run", "neutral-label")
        original = json.loads(output_freeze.read_text(encoding="utf-8"))
        tampered = json.loads(json.dumps(original))
        tampered["snapshots"]["pre_packet"] = "f" * 64
        output_freeze.write_bytes(harness.canonical_json(tampered))
        with self.assertRaisesRegex(harness.HarnessError, "terminal seal"):
            harness.normalize_run(output_freeze)
        output_freeze.write_bytes(harness.canonical_json(original))
        frozen_diff = output_freeze.parent / original["artifacts"]["implementation_diff"]["path"]
        frozen_diff.write_text("tampered\n", encoding="utf-8")
        coordinated = json.loads(json.dumps(original))
        coordinated["artifacts"]["implementation_diff"]["sha256"] = harness.sha256_file(
            frozen_diff
        )
        coordinated["artifacts"]["implementation_diff"]["size"] = frozen_diff.stat().st_size
        output_freeze.write_bytes(harness.canonical_json(coordinated))
        with self.assertRaisesRegex(harness.HarnessError, "terminal seal"):
            harness.normalize_run(output_freeze)
        output_freeze.write_bytes(harness.canonical_json(original))
        with self.assertRaisesRegex(harness.HarnessError, "digest mismatch"):
            harness.normalize_run(output_freeze)

        normalized = self.freeze_complete("invalid-snapshot-run", "neutral-label")[0]
        normalized_data = harness.normalize_run(normalized)
        normalized_data["snapshots"]["pre_packet"] = "baseline-arm"
        with self.assertRaisesRegex(harness.HarnessError, "64-hex"):
            harness.validate_normalized_output(normalized_data)

    def test_finalization_requires_both_harness_runner_phases_and_metadata(self) -> None:
        validation = self.root / "missing-phase-validation.txt"
        validation.write_text("passed\n", encoding="utf-8")
        stage = self.prepare_retry("missing-both-runners")
        self.run_mocked_phase(stage, "pre-packet")
        harness.freeze_pre_packet(stage, validation)
        harness.stage_review_packet(stage)
        record = self.root / "empty-record.json"
        record.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(harness.HarnessError, "runner"):
            harness.finalize_arm(stage, record)

        stage, record = self.make_freeze_inputs("missing-metadata", "neutral-label")
        metadata = stage / "runner/pre-packet/metadata.json"
        metadata.rename(metadata.with_suffix(".missing"))
        with self.assertRaisesRegex(harness.HarnessError, "metadata"):
            harness.finalize_arm(stage, record)

    def test_finalization_rejects_runner_metadata_manifest_prompt_and_trace_mutation(self) -> None:
        cases = (
            ("metadata", "metadata.json", '{"fabricated":true}\n'),
            ("manifest", "input-manifest.json", "{}\n"),
            ("prompt", "prompt.txt", "fabricated prompt\n"),
            ("trace", "trace.jsonl", '{"type":"fabricated"}\n'),
        )
        for label, filename, content in cases:
            with self.subTest(label=label):
                stage, record = self.make_freeze_inputs(f"mutated-{label}", "neutral-label")
                (stage / "runner/pre-packet" / filename).write_text(content, encoding="utf-8")
                with self.assertRaises(harness.HarnessError):
                    harness.finalize_arm(stage, record)

    def test_finalization_rejects_malformed_evidence_and_measurement_mismatch(self) -> None:
        for label in (
            "probe-array", "probe-id", "review-action", "round-scope",
            "evidence-digest", "measurement",
        ):
            with self.subTest(label=label):
                stage, record = self.make_freeze_inputs(f"bad-{label}", "neutral-label")
                if label == "measurement":
                    data = json.loads(record.read_text(encoding="utf-8"))
                    data["measurements"]["test_size_lines"] = 0
                    record.write_text(json.dumps(data), encoding="utf-8")
                else:
                    evidence_name = (
                        "rounds" if label == "round-scope"
                        else "reviews" if label == "review-action" else "probes"
                    )
                    evidence = record.parent / f"evidence/{evidence_name}.json"
                    data = json.loads(evidence.read_text(encoding="utf-8"))
                    if label == "probe-array":
                        data = {}
                    elif label == "probe-id":
                        data[0]["id"] = "UNKNOWN"
                    elif label == "round-scope":
                        data[0]["scope"] = "invalid"
                    elif label == "evidence-digest":
                        data[0]["evidence_sha256"] = "f" * 64
                    else:
                        data[0].pop("command")
                    evidence.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(harness.HarnessError):
                    harness.finalize_arm(stage, record)

    def candidate_records(self) -> list[dict[str, object]]:
        ledger = json.loads(harness.OUTCOME_LEDGER.read_text(encoding="utf-8"))
        return [
            {
                "finding_id": entry["finding_id"],
                "test_disposition": entry["test_disposition"],
                "test_rationale": "Frozen evaluator rationale.",
                "repair_authorized": entry["rereview_scope"] is not None,
                "rereview_scope": entry["rereview_scope"],
                "rereview_rationale": (
                    "Frozen evaluator scope rationale."
                    if entry["rereview_scope"] is not None
                    else ""
                ),
            }
            for entry in ledger["entries"]
        ]

    def test_candidate_compliance_is_strict_and_covers_the_frozen_ledger(self) -> None:
        report = self.root / "candidate-fields.json"
        report.write_text(
            json.dumps({"revealed_identity": "candidate", "records": self.candidate_records()}),
            encoding="utf-8",
        )
        self.assertEqual(harness.check_candidate_compliance(report), {"compliant": True, "violations": []})
        records = self.candidate_records()
        records[0]["repair_authorized"] = 1
        records.append(dict(records[1]))
        records.pop(2)
        report.write_text(
            json.dumps({"revealed_identity": "candidate", "records": records}),
            encoding="utf-8",
        )
        result = harness.check_candidate_compliance(report)
        self.assertFalse(result["compliant"])
        self.assertTrue(any("repair_authorized" in item for item in result["violations"]))
        self.assertIn("duplicate finding IDs", result["violations"])
        self.assertTrue(any("missing ledger findings" in item for item in result["violations"]))

    def frozen_outcomes(self) -> dict[str, dict[str, object]]:
        ledger = json.loads(harness.OUTCOME_LEDGER.read_text(encoding="utf-8"))
        return {
            entry["finding_id"]: {
                key: entry[key] for key in ("test_disposition", "rereview_scope")
            }
            for entry in ledger["entries"]
        }

    def write_normalized_arm(
        self, name: str, outcomes: dict[str, dict[str, object]]
    ) -> list[Path]:
        paths: list[Path] = []
        required_hashes = {
            "implementation_diff", "test_diff", "probe_results", "review_log",
            "review_rounds", "run_record", "runner_preflight", "pre_packet_snapshot",
            "pre_packet_validation",
        } | harness.runner_artifact_names()
        for scenario_id in harness.OUTCOME_SCENARIOS:
            finding_ids = harness.expected_finding_ids(scenario_id)
            common = {
                "command": "normalized evidence", "exit_status": 0,
                "evidence": "Bound normalized evidence.",
                "evidence_ref": "remediation_trace", "evidence_sha256": "0" * 64,
            }
            actions = [
                {
                    "finding_id": finding_id, **outcomes[finding_id],
                    **common,
                }
                for finding_id in sorted(finding_ids)
            ]
            probes = [{"id": finding_id, **common} for finding_id in sorted(finding_ids)]
            rounds = [
                {
                    "round_id": f"round-{action['finding_id']}",
                    "scope": action["rereview_scope"],
                    "reviewed_finding_ids": [action["finding_id"]], **common,
                }
                for action in actions if action["rereview_scope"] is not None
            ]
            path = self.root / f"{name}-{scenario_id}.json"
            harness.write_json(
                path,
                {
                    "schema_version": 1,
                    "scenario_id": scenario_id,
                    "snapshots": {"pre_packet": "1" * 64, "post_remediation": "2" * 64},
                    "behavior": {
                        "implementation_diff": "", "test_diff": "",
                        "implementation_additions": 0, "implementation_deletions": 0,
                        "test_additions": 0, "probe_results": probes,
                        "review_actions": actions, "review_rounds": rounds,
                    },
                    "measurements": {
                        "test_count": 0, "test_size_lines": 0,
                        "full_review_rounds": sum(r["scope"] == "full" for r in rounds),
                        "targeted_rereviews": sum(r["scope"] == "targeted" for r in rounds),
                        "wall_time_seconds": 2,
                    },
                    "source_hashes": {key: "0" * 64 for key in required_hashes},
                },
            )
            paths.append(path)
        return paths

    def inefficient_baseline(self) -> dict[str, dict[str, object]]:
        outcomes = json.loads(json.dumps(self.frozen_outcomes()))
        for outcome in outcomes.values():
            if outcome["test_disposition"] in {"table_case", "probe_only", "no_test"}:
                outcome["test_disposition"] = "permanent"
            if outcome["rereview_scope"] in {"targeted", None}:
                outcome["rereview_scope"] = "full"
        return outcomes

    def test_outcome_gate_uses_four_normalized_outputs_and_enforces_both_axes(self) -> None:
        baseline = self.write_normalized_arm("baseline-pass", self.inefficient_baseline())
        candidate = self.write_normalized_arm("candidate-pass", self.frozen_outcomes())
        output = self.root / "outcome-gate.json"
        result = harness.gate_outcomes(baseline, candidate)
        self.assertTrue(result["passed"])
        self.assertTrue(result["axes"]["unjustified_permanent_decisions"]["strict_improvement"])
        self.assertTrue(result["axes"]["unnecessary_full_rereviews"]["strict_improvement"])
        self.assertFalse(result["correctness_gate_evaluated"])
        self.assertFalse(result["judge_verdict_evaluated"])
        self.assertEqual(
            harness.main(
                [
                    "gate-outcomes",
                    "--baseline",
                    *(str(path) for path in baseline),
                    "--candidate",
                    *(str(path) for path in candidate),
                    "--output",
                    str(output),
                ]
            ),
            0,
        )
        self.assertTrue(json.loads(output.read_text(encoding="utf-8"))["passed"])
        self.assertEqual(
            result["input_sha256s"]["candidate"],
            {
                json.loads(path.read_text(encoding="utf-8"))["scenario_id"]: harness.sha256_file(path)
                for path in candidate
            },
        )
        candidate_outcomes = self.frozen_outcomes()
        candidate_outcomes["RF-002"]["test_disposition"] = "permanent"
        regressive = self.write_normalized_arm("candidate-regression", candidate_outcomes)
        regression = harness.gate_outcomes(baseline, regressive)
        self.assertFalse(regression["passed"])
        self.assertEqual(regression["candidate_category_regressions"][0]["finding_id"], "RF-002")

        malformed = json.loads(regressive[0].read_text(encoding="utf-8"))
        malformed["behavior"]["review_actions"].pop()
        harness.write_json(regressive[0], malformed)
        with self.assertRaisesRegex(harness.HarnessError, "finding ID"):
            harness.gate_outcomes(baseline, regressive)

        baseline_outcomes = self.frozen_outcomes()
        for outcome in baseline_outcomes.values():
            if outcome["test_disposition"] in {"table_case", "probe_only", "no_test"}:
                outcome["test_disposition"] = "permanent"
        one_axis = harness.gate_outcomes(
            self.write_normalized_arm("baseline-one-axis", baseline_outcomes), candidate
        )
        self.assertFalse(one_axis["passed"])
        self.assertTrue(one_axis["axes"]["unjustified_permanent_decisions"]["strict_improvement"])
        self.assertFalse(one_axis["axes"]["unnecessary_full_rereviews"]["strict_improvement"])


if __name__ == "__main__":
    unittest.main()
