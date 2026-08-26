from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from evals.deliver import harness


def successful_trace(command: str = harness.FIRST_TOOL_GATE_TRACE_COMMAND) -> str:
    gate = {
        "id": "gate", "type": "command_execution",
        "command": command,
    }
    events = [
        {"type": "thread.started", "thread_id": "opaque"},
        {"type": "turn.started"},
        {"type": "item.started", "item": {**gate, "status": "in_progress"}},
        {"type": "item.completed", "item": {
            **gate, "status": "completed", "exit_code": 0,
            "aggregated_output": harness.FIRST_TOOL_GATE_OUTPUT,
        }},
        {"type": "turn.completed"},
    ]
    return "".join(json.dumps(event) + "\n" for event in events)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class FakeStdout:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    def fileno(self) -> int:
        return 42

    def read1(self, _size: int) -> bytes:
        return self.chunks.pop(0) if self.chunks else b""


class FakeProcess:
    def __init__(self, chunks: list[bytes]) -> None:
        self.stdout = FakeStdout(chunks)
        self.returncode: int | None = None
        self.killed = False
        self.wait_count = 0

    def poll(self) -> int | None:
        return self.returncode

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self) -> int:
        self.wait_count += 1
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


def stop_fake_process_group(process: FakeProcess, _process_group_id: int) -> None:
    process.kill()
    process.wait()


class DeliverEvalHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(dir=harness.STAGE_ROOT)
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
            stdout=successful_trace(), stderr="",
        )
        with mock.patch.object(harness, "execute_codex", return_value=completed):
            harness.preflight_runner(self.preflight)

    def prepare_retry(self, name: str = "stage") -> Path:
        runtime = tempfile.TemporaryDirectory(
            prefix=f"deliver-eval-{name}-", dir=harness.STAGE_ROOT
        )
        self.addCleanup(runtime.cleanup)
        stage = Path(runtime.name) / "retry-failed-baseline"
        harness.prepare_scenario("retry-failed", self.contract, stage, self.preflight)
        return stage

    def arm_path(self, name: str, scenario: str = "retry-failed") -> Path:
        runtime = tempfile.TemporaryDirectory(
            prefix=f"deliver-eval-{name}-", dir=harness.STAGE_ROOT
        )
        self.addCleanup(runtime.cleanup)
        return Path(runtime.name) / f"{scenario}-baseline"

    def initialize_v11_comparison(self, name: str) -> tuple[Path, dict[str, str]]:
        runtime = tempfile.TemporaryDirectory(
            prefix=f"deliver-eval-{name}-", dir=harness.STAGE_ROOT
        )
        self.addCleanup(runtime.cleanup)
        package_root = self.root / f"{name}-packages"
        baseline = package_root / "baseline"
        candidate = package_root / "candidate"
        for package, ref, paths in (
            (baseline, harness.BASELINE_REF, harness.BASELINE_PACKAGE_PATHS),
            (candidate, harness.CANDIDATE_REF, harness.CANDIDATE_PACKAGE_PATHS),
        ):
            for relative in paths:
                target = package / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(subprocess.check_output(
                    ["git", "show", f"{ref}:{relative}"], cwd=harness.SOURCE_ROOT
                ))
                listing = subprocess.check_output(
                    ["git", "ls-tree", ref, "--", relative],
                    cwd=harness.SOURCE_ROOT, text=True,
                ).split("\t", 1)[0]
                target.chmod(int(listing.split()[0], 8) & 0o777)
        identity = {
            "commit": "1" * 40,
            "evals_tree": "2" * 40,
            "file_manifest_sha256": "3" * 64,
        }
        real_git_output = harness.git_output

        def frozen_git_output(arguments: list[str]) -> str:
            if arguments == [
                "diff", "--name-only", harness.EVALUATOR_BASE_REF, "HEAD",
                "--", "evals/deliver",
            ]:
                return "evals/deliver/harness.py"
            return real_git_output(arguments)

        with (
            mock.patch.object(harness, "evaluator_identity", return_value=identity),
            mock.patch.object(harness, "assert_candidate_owned_paths_frozen"),
            mock.patch.object(harness, "git_output", side_effect=frozen_git_output),
        ):
            manifest = harness.initialize_comparison(
                Path(runtime.name), baseline, candidate, comparison_id=f"{name}-comparison"
            )
        return manifest, identity

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
        absent_runtime = harness.STAGE_ROOT / f"deliver-eval-absent-{self.root.name}"
        self.assertFalse(absent_runtime.exists())
        self.addCleanup(shutil.rmtree, absent_runtime, ignore_errors=True)
        absent = absent_runtime / "retry-failed-baseline"
        harness.prepare_scenario("retry-failed", self.contract, absent, self.preflight)
        self.assertTrue((absent_runtime / harness.SIBLING_PROBE).is_dir())
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

        stage = self.arm_path("package-stage")
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
                "retry-failed", package, self.arm_path("two-contracts"), self.preflight
            )

    def test_historical_fixture_is_exactly_pinned(self) -> None:
        stage = self.arm_path("holdout", "preflight-remediation-holdout")
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

    def test_historical_holdout_discloses_defects_only_after_packet_staging(self) -> None:
        stage = self.arm_path("holdout-blind", "preflight-remediation-holdout")
        harness.prepare_scenario(
            "preflight-remediation-holdout", self.contract, stage, self.preflight
        )
        pre_packet = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((stage / "scenario").rglob("*"))
            if path.is_file()
        )
        for withheld in (
            ".last-session-update",
            "Bash arithmetic",
            "always backgrounds",
            "sanitize the throttle value",
            "explicit foreground path",
        ):
            self.assertNotIn(withheld, pre_packet)
        self.assertTrue((stage / "scenario/starting-state-contract.md").is_file())
        self.assertFalse((stage / "scenario/acceptance-contract.md").exists())
        self.assertFalse((stage / "scenario/approved-paused-plan.md").exists())

        validation = self.root / "holdout-blind-validation.txt"
        validation.write_text("starting state inspected\n", encoding="utf-8")
        self.run_mocked_phase(stage, "pre-packet")
        harness.freeze_pre_packet(stage, validation)
        harness.stage_review_packet(stage)
        packet = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((stage / "scenario/review-packet").rglob("*"))
            if path.is_file()
        )
        self.assertIn(".last-session-update", packet)
        self.assertIn("Bash arithmetic", packet)
        self.assertIn("explicit foreground path", packet)

    def test_historical_holdout_freeze_requires_exact_pinned_source_states(self) -> None:
        script = Path("scripts/prime-directive-codex-preflight.sh")

        def commit(repo: Path, message: str) -> str:
            subprocess.run(
                [
                    "git", "-c", "user.name=Deliver Eval", "-c",
                    "user.email=eval@example.invalid", "commit", "-q",
                    "--no-gpg-sign", "-m", message,
                ],
                cwd=repo,
                check=True,
            )
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()

        def prepare(name: str) -> tuple[Path, Path]:
            stage = self.arm_path(name, "preflight-remediation-holdout")
            harness.prepare_scenario(
                "preflight-remediation-holdout", self.contract, stage, self.preflight
            )
            self.run_mocked_phase(stage, "pre-packet")
            return stage, stage / "repo"

        def expect_rejection(stage: Path, name: str, pattern: str) -> None:
            validation = self.root / f"holdout-{name}-validation.txt"
            validation.write_text("passed\n", encoding="utf-8")
            with self.assertRaisesRegex(harness.HarnessError, pattern):
                harness.freeze_pre_packet(stage, validation)

        allowed, _ = prepare("holdout-bookkeeping")
        note = allowed / "repo/tasks/pre-packet-note.md"
        note.parent.mkdir()
        note.write_text("inspection only\n", encoding="utf-8")
        allowed_validation = self.root / "holdout-bookkeeping-validation.txt"
        allowed_validation.write_text("passed\n", encoding="utf-8")
        harness.freeze_pre_packet(allowed, allowed_validation)

        for mutation in ("staged", "unstaged", "deleted", "mode"):
            with self.subTest(mutation=mutation):
                stage, repo = prepare(f"holdout-{mutation}")
                target = repo / script
                if mutation == "deleted":
                    target.unlink()
                elif mutation == "mode":
                    target.chmod(0o644)
                else:
                    target.write_text(
                        target.read_text(encoding="utf-8") + "\n# pre-packet drift\n",
                        encoding="utf-8",
                    )
                    if mutation == "staged":
                        subprocess.run(["git", "add", script.as_posix()], cwd=repo, check=True)
                expect_rejection(stage, mutation, "pinned pre-packet source drift")

        for history_case in (
            "commit",
            "reset",
            "side-ref",
            "replace-ref",
            "reflog",
            "grafts",
            "shallow",
        ):
            with self.subTest(history_case=history_case):
                stage, repo = prepare(f"holdout-{history_case}")
                initial = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=repo, text=True
                ).strip()
                if history_case in {"commit", "reset"}:
                    target = repo / script
                    target.write_text(
                        target.read_text(encoding="utf-8") + "\n# hidden repair\n",
                        encoding="utf-8",
                    )
                    subprocess.run(["git", "add", script.as_posix()], cwd=repo, check=True)
                    commit(repo, "Hidden pre-packet repair")
                    if history_case == "reset":
                        subprocess.run(
                            ["git", "reset", "--hard", "-q", initial], cwd=repo, check=True
                        )
                elif history_case == "side-ref":
                    subprocess.run(
                        ["git", "branch", "hidden-prepacket", initial],
                        cwd=repo,
                        check=True,
                    )
                elif history_case == "replace-ref":
                    tree = subprocess.check_output(
                        ["git", "rev-parse", f"{initial}^{{tree}}"],
                        cwd=repo,
                        text=True,
                    ).strip()
                    replacement = subprocess.check_output(
                        [
                            "git", "-c", "user.name=Deliver Eval", "-c",
                            "user.email=eval@example.invalid", "commit-tree", tree,
                            "-m", "Synthetic replacement",
                        ],
                        cwd=repo,
                        text=True,
                    ).strip()
                    subprocess.run(
                        ["git", "replace", initial, replacement], cwd=repo, check=True
                    )
                elif history_case == "reflog":
                    blob = subprocess.check_output(
                        ["git", "rev-parse", f"{initial}:{script.as_posix()}"],
                        cwd=repo,
                        text=True,
                    ).strip()
                    with (repo / ".git/logs/HEAD").open("a", encoding="ascii") as handle:
                        handle.write(
                            f"{initial} {blob} Eval <eval@example.invalid> 0 +0000\tbad\n"
                        )
                else:
                    relative = (
                        Path(".git/info/grafts")
                        if history_case == "grafts"
                        else Path(".git/shallow")
                    )
                    metadata = repo / relative
                    metadata.parent.mkdir(parents=True, exist_ok=True)
                    metadata.write_text(f"{initial}\n", encoding="ascii")
                expect_rejection(stage, history_case, "unsupported Git history state")

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
        with self.assertRaisesRegex(harness.HarnessError, "named baseline/candidate"):
            harness.prepare_scenario(
                "retry-failed", self.contract,
                harness.SOURCE_ROOT / "agent-scratch/eval-stage", self.preflight,
            )

    def test_outer_sandbox_allows_only_current_arm_and_blocks_all_escape_forms(self) -> None:
        stage = self.prepare_retry("sandbox-stage")
        sentinel_binding = harness.ensure_external_sentinel(stage.parent)
        sentinel = Path(sentinel_binding["path"])
        sentinel_alias = Path(str(sentinel).replace("/private/tmp/", "/tmp/", 1))
        symlink_escape = stage / "repo/external-sentinel-link"
        symlink_escape.symlink_to(sentinel)
        profile = self.root / "runner.sb"
        profile.write_text(harness.sandbox_profile(stage), encoding="utf-8")
        denied = [
            Path(f"/Users/fromdarkness/.deliver-eval-probe-{self.root.name}"),
            Path(f"/Volumes/Code/.deliver-eval-probe-{self.root.name}"),
        ]
        self.assertTrue(all(not path.exists() and not path.is_symlink() for path in denied))
        script = """from pathlib import Path
import sys
stage, ledger, auth, sibling, external, alias, traversal, symlink = map(Path, sys.argv[1:9])
(stage / "outer-sandbox-write.txt").write_text("ok")
(stage / "README.md").read_bytes()
for label, path, read in (("source-read", ledger, True), ("home-read", auth, True), ("sibling-read", sibling, True), ("external-read", external, True), ("external-write", external, False), ("alias-read", alias, True), ("alias-write", alias, False), ("traversal-read", traversal, True), ("traversal-write", traversal, False), ("symlink-read", symlink, True), ("symlink-write", symlink, False), ("user-write", Path(sys.argv[9]), False), ("volume-write", Path(sys.argv[10]), False)):
    try: path.read_bytes() if read else path.write_text("blocked")
    except OSError: print(label)
    else: raise SystemExit(2)
"""
        try:
            result = subprocess.run(
                [str(harness.SANDBOX_EXEC), "-f", str(profile), sys.executable, "-c", script,
                 str(stage / "repo"), str(harness.OUTCOME_LEDGER), str(harness.CODEX_AUTH),
                 str(stage.parent / harness.SIBLING_PROBE / harness.SIBLING_SENTINEL),
                 str(sentinel), str(sentinel_alias),
                 "../../.deliver-evaluator/external-temp-sentinel.txt",
                 str(symlink_escape),
                 *(str(path) for path in denied)],
                cwd=stage / "repo", capture_output=True, text=True, check=False,
            )
            if result.returncode == 71 and "sandbox_apply: Operation not permitted" in result.stderr:
                self.skipTest("the enclosing test sandbox forbids nested sandbox-exec")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.splitlines(),
                [
                    "source-read", "home-read", "sibling-read", "external-read",
                    "external-write", "alias-read", "alias-write", "traversal-read",
                    "traversal-write", "symlink-read", "symlink-write", "user-write",
                    "volume-write",
                ],
            )
            self.assertEqual((stage / "repo/outer-sandbox-write.txt").read_text(), "ok")
            self.assertTrue(all(not path.exists() for path in denied))
            self.assertEqual(
                harness.verify_external_sentinel(sentinel_binding, stage.parent), sentinel
            )
            sentinel.unlink()
            with self.assertRaisesRegex(harness.HarnessError, "regular file"):
                harness.verify_external_sentinel(sentinel_binding, stage.parent)
        finally:
            for path in denied:
                if path.exists() or path.is_symlink():
                    path.unlink()

    def test_v11_comparison_freezes_identity_packages_order_and_one_time_seals(self) -> None:
        manifest, identity = self.initialize_v11_comparison("comparison-state")
        binding = {
            "comparison_manifest_sha256": harness.sha256_file(manifest),
            "evaluator_identity": identity,
        }
        with mock.patch.object(harness, "evaluator_identity", return_value=identity):
            self.assertEqual(
                harness.binding_from_comparison(
                    harness.validate_comparison_manifest(manifest)
                ),
                binding,
            )
            with self.assertRaisesRegex(harness.HarnessError, "precommitted"):
                harness.begin_arm_attempt(
                    manifest, "retry-failed-candidate", "a" * 64
                )
            harness.begin_arm_attempt(
                manifest, "retry-failed-baseline", "a" * 64
            )
            with self.assertRaisesRegex(harness.HarnessError, "active"):
                harness.begin_arm_attempt(
                    manifest, "retry-failed-baseline", "a" * 64
                )

            def submit() -> str:
                try:
                    harness.register_terminal_seal(
                        manifest, "retry-failed-baseline", "b" * 64
                    )
                except harness.HarnessError:
                    return "rejected"
                return "sealed"

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = sorted(executor.map(lambda _index: submit(), range(2)))
            self.assertEqual(results, ["rejected", "sealed"])
            state = harness.validate_attempt_state(manifest)["state"]
            self.assertEqual(
                state["arms"]["retry-failed-baseline"]["terminal_seal_sha256"],
                "b" * 64,
            )
            harness.begin_arm_attempt(
                manifest, "retry-failed-candidate", "c" * 64
            )
            harness.record_external_interruption(
                manifest, "retry-failed-candidate", "host terminated runner"
            )
            with self.assertRaisesRegex(harness.HarnessError, "byte-identical"):
                harness.begin_arm_attempt(
                    manifest, "retry-failed-candidate", "d" * 64
                )
            restarted = harness.begin_arm_attempt(
                manifest, "retry-failed-candidate", "c" * 64
            )
            self.assertEqual(restarted["attempt"], 2)

            preflight = self.root / "bound-runner-preflight.json"
            completed = subprocess.CompletedProcess(
                args=[str(harness.BUNDLED_CODEX)], returncode=0,
                stdout=successful_trace(), stderr="",
            )
            with mock.patch.object(harness, "execute_codex", return_value=completed):
                harness.preflight_runner(preflight, manifest)
            candidate_package = self.root / "comparison-state-packages/candidate"
            candidate_skill = candidate_package / "skills/deliver/SKILL.md"
            candidate_skill.write_text(
                candidate_skill.read_text(encoding="utf-8") + "\n# Drifted package\n",
                encoding="utf-8",
            )
            runtime = Path(json.loads(manifest.read_text())["runtime_root"])
            with self.assertRaisesRegex(harness.HarnessError, "bytes or modes differ"):
                harness.prepare_scenario(
                    "retry-failed", candidate_package,
                    runtime / "retry-failed-candidate", preflight, manifest,
                )

            restart_manifest, _ = self.initialize_v11_comparison("comparison-restart")
            restart_runtime = Path(json.loads(
                restart_manifest.read_text(encoding="utf-8")
            )["runtime_root"])
            restart_preflight = self.root / "restart-runner-preflight.json"
            with mock.patch.object(harness, "execute_codex", return_value=completed):
                harness.preflight_runner(restart_preflight, restart_manifest)
            restart_stage = restart_runtime / "retry-failed-baseline"
            harness.prepare_scenario(
                "retry-failed",
                self.root / "comparison-restart-packages/baseline",
                restart_stage,
                restart_preflight,
                restart_manifest,
            )
            with mock.patch.object(harness, "execute_codex", return_value=completed):
                harness.run_scenario(restart_stage, "pre-packet")
            poisoned = restart_stage / "runner/attempt-2/pre-packet"
            poisoned.mkdir(parents=True)
            with self.assertRaisesRegex(harness.HarnessError, "unregistered"):
                harness.runner_paths(restart_stage, ("pre-packet",))
            shutil.rmtree(poisoned.parent)
            validation = self.root / "restart-validation.txt"
            validation.write_text("passed\n", encoding="utf-8")
            harness.freeze_pre_packet(restart_stage, validation)
            harness.stage_review_packet(restart_stage)
            with mock.patch.object(
                harness, "execute_codex", side_effect=RuntimeError("host stopped")
            ):
                with self.assertRaisesRegex(RuntimeError, "host stopped"):
                    harness.run_scenario(restart_stage, "remediation")
            with self.assertRaisesRegex(harness.HarnessError, "active unsealed"):
                harness.record_external_interruption(
                    restart_manifest, "retry-failed-baseline", "wrong phase",
                    "pre-packet",
                )
            harness.record_external_interruption(
                restart_manifest, "retry-failed-baseline", "host stopped",
                "remediation",
            )
            with mock.patch.object(harness, "execute_codex", return_value=completed):
                harness.run_scenario(restart_stage, "remediation")
            selected = harness.runner_paths(restart_stage)
            self.assertTrue(
                selected["pre_packet_metadata"].is_relative_to(
                    restart_stage / "runner/attempt-1/pre-packet"
                )
            )
            self.assertTrue(
                selected["remediation_metadata"].is_relative_to(
                    restart_stage / "runner/attempt-2/remediation"
                )
            )
            stream_root = (
                restart_runtime / harness.SIBLING_PROBE / "runner-streams"
                / restart_stage.name
            )
            self.assertTrue((stream_root / "attempt-1/pre-packet").is_dir())
            self.assertTrue((stream_root / "attempt-1/remediation").is_dir())
            self.assertTrue((stream_root / "attempt-2/remediation").is_dir())
            retry_attempts = harness.validate_attempt_state(restart_manifest)["state"][
                "arms"
            ]["retry-failed-baseline"]["attempts"]
            self.assertEqual(set(retry_attempts[1]["phase_inputs"]), {"remediation"})
            self.assertEqual(
                retry_attempts[1]["input_sha256"],
                retry_attempts[0]["phase_inputs"]["remediation"],
            )

        changed_identity = {**identity, "evals_tree": "9" * 40}
        advanced_identity = {**identity, "commit": "4" * 40}
        with (
            mock.patch.object(
                harness, "evaluator_identity", return_value=advanced_identity
            ),
            mock.patch.object(harness, "git_commit_is_ancestor", return_value=True),
            mock.patch.object(
                harness, "git_history_touches_evaluator", return_value=False
            ),
        ):
            harness.validate_comparison_manifest(manifest)
        with (
            mock.patch.object(
                harness, "evaluator_identity", return_value=advanced_identity
            ),
            mock.patch.object(harness, "git_commit_is_ancestor", return_value=True),
            mock.patch.object(
                harness, "git_history_touches_evaluator", return_value=True
            ),
        ):
            with self.assertRaisesRegex(harness.HarnessError, "identity drifted"):
                harness.validate_comparison_manifest(manifest)
        with (
            mock.patch.object(
                harness, "evaluator_identity", return_value=advanced_identity
            ),
            mock.patch.object(harness, "git_commit_is_ancestor", return_value=False),
        ):
            with self.assertRaisesRegex(harness.HarnessError, "identity drifted"):
                harness.validate_comparison_manifest(manifest)
        with mock.patch.object(
            harness, "evaluator_identity", return_value=changed_identity
        ):
            with self.assertRaisesRegex(harness.HarnessError, "identity drifted"):
                harness.validate_comparison_manifest(manifest)

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
        self.assertEqual(preflight["arm_timeout_policy"], harness.ARM_TIMEOUT_POLICY)
        self.assertEqual(
            preflight["smoke"]["timeout_policy"], harness.PREFLIGHT_TIMEOUT_POLICY
        )
        self.assertIn(str(harness.BUNDLED_CODEX), preflight["smoke"]["command"])
        tampered = self.root / "tampered-preflight.json"
        tampered_data = json.loads(self.preflight.read_text(encoding="utf-8"))
        tampered_data["binary_version"] = "different"
        harness.write_json(tampered, tampered_data)
        with self.assertRaisesRegex(harness.HarnessError, "identity drifted"):
            harness.validate_runner_preflight(tampered)
        tampered_data = json.loads(self.preflight.read_text(encoding="utf-8"))
        tampered_data["arm_timeout_policy"]["arm_total_seconds"] -= 1
        harness.write_json(tampered, tampered_data)
        with self.assertRaisesRegex(harness.HarnessError, "identity or smoke"):
            harness.validate_runner_preflight(tampered, check_binary=False)
        stage = self.prepare_retry("runner-stage")
        completed = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout=successful_trace(),
            stderr="",
        )
        auth_copy = stage / "runner/pre-packet/codex-state/home/auth.json"
        def execute_with_atomic_auth(
            *_args: object, **_kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            self.assertEqual(auth_copy.stat().st_mode & 0o777, 0o600)
            return completed
        with mock.patch.object(harness, "execute_codex", side_effect=execute_with_atomic_auth) as execute:
            trace = harness.run_scenario(stage, "pre-packet")
        command, prompt, repo = execute.call_args.args
        self.assertEqual(command, harness.codex_command(
            stage / "repo", stage / "runner/pre-packet/runner.sb"
        ))
        for fixed in (
            "--json", "--ephemeral", "--ignore-user-config", "gpt-5.6-sol",
            "--dangerously-bypass-approvals-and-sandbox",
        ):
            self.assertIn(fixed, command)
        self.assertNotIn("--sandbox", command)
        self.assertEqual(command[3:5], ["/usr/bin/env", "-i"])
        self.assertEqual(
            command[5:5 + len(harness.runner_environment(stage / "runner/pre-packet/runner.sb"))],
            harness.runner_environment(stage / "runner/pre-packet/runner.sb"),
        )
        self.assertNotIn(harness.INHERITED_SENTINEL, " ".join(command))
        self.assertEqual(repo, stage / "repo")
        trace_stream_path = execute.call_args.kwargs["trace_stream_path"]
        self.assertIn(harness.SIBLING_PROBE, trace_stream_path.parts)
        self.assertIn(
            f'(subpath "{stage.parent / harness.SIBLING_PROBE}")',
            (stage / "runner/pre-packet/runner.sb").read_text(encoding="utf-8"),
        )
        self.assertTrue(prompt.startswith(harness.FIRST_TOOL_GATE_PROMPT))
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
        self.assertEqual(metadata["execution_boundary"], "outer_sandbox_only")
        self.assertEqual(metadata["timeout_policy"], harness.ARM_TIMEOUT_POLICY)
        self.assertEqual(metadata["arm_elapsed_before_milliseconds"], 0)
        self.assertEqual(metadata["environment"], harness.runner_environment(
            stage / "runner/pre-packet/runner.sb"
        ))
        self.assertFalse(auth_copy.exists())
        self.assertEqual(
            metadata["runner_preflight_sha256"],
            harness.sha256_file(stage / "evidence/runner-preflight.json"),
        )
        with mock.patch.object(harness, "execute_codex") as second_execute:
            with self.assertRaisesRegex(harness.HarnessError, "already exist"):
                harness.run_scenario(stage, "pre-packet")
            second_execute.assert_not_called()
        failure_stage = self.prepare_retry("runner-failure")
        with mock.patch.object(harness, "execute_codex", side_effect=RuntimeError("probe")):
            with self.assertRaisesRegex(RuntimeError, "probe"):
                harness.run_scenario(failure_stage, "pre-packet")
        self.assertFalse(
            (failure_stage / "runner/pre-packet/codex-state/home/auth.json").exists()
        )
        invalid_traces = (
            b'{"type":"turn.completed"}\n',
            b'{"type":"thread.started"}\n{"type":"turn.completed"}\n{"type":"item.completed"}\n',
            b'{"type":"thread.started"}\n{"type":"turn.failed"}\n',
            successful_trace(harness.FIRST_TOOL_GATE_TRACE_COMMAND.replace(
                harness.FIRST_TOOL_GATE_OUTPUT, "altered-inner-gate"
            )).encode(),
        )
        for wrapper in harness.FIRST_TOOL_GATE_TRACE_COMMANDS:
            harness.validate_runner_trace(successful_trace(wrapper).encode())
        base = [json.loads(line) for line in successful_trace().splitlines()]
        file_change = [
            {"type": kind, "item": {"id": "file", "type": "file_change"}}
            for kind in ("item.started", "item.completed")
        ]
        with self.assertRaises(harness.HarnessError):
            harness.validate_runner_trace("".join(
                json.dumps(event) + "\n" for event in base[:2] + file_change + base[2:]
            ).encode())
        harness.validate_runner_trace("".join(
            json.dumps(event) + "\n" for event in base[:-1] + file_change + base[-1:]
        ).encode())
        for trace_bytes in invalid_traces:
            with self.assertRaises(harness.HarnessError):
                harness.validate_runner_trace(trace_bytes)

    def test_monitor_streams_jsonl_and_times_out_without_real_waiting(self) -> None:
        clock = FakeClock()
        event = b'{"type":"thread.started","thread_id":"opaque"}\n'
        process = FakeProcess([event])
        trace = self.root / "partial-trace.jsonl"
        auth = self.root / "partial-auth.json"
        auth.write_text("secret", encoding="utf-8")
        readable_once = True

        def wait_for_readable(
            readers: list[FakeStdout], _writers: list[object],
            _errors: list[object], timeout: float,
        ) -> tuple[list[FakeStdout], list[object], list[object]]:
            nonlocal readable_once
            if readable_once:
                readable_once = False
                clock.now += 1.5
                return readers, [], []
            clock.now += timeout
            return [], [], []

        with self.assertRaisesRegex(harness.HarnessError, "inactivity timeout"):
            harness.monitor_codex_process(
                process,
                trace,
                auth,
                total_timeout_seconds=5,
                inactivity_timeout_seconds=2,
                monotonic=clock,
                wait_for_readable=wait_for_readable,
                process_group_id=9001,
                stop_group=stop_fake_process_group,
            )
        self.assertEqual(trace.read_bytes(), event)
        self.assertFalse(auth.exists())
        self.assertTrue(process.killed)
        self.assertEqual(process.wait_count, 1)
        self.assertEqual(clock.now, 3.5)

    def test_monitor_enforces_total_budget_without_real_waiting(self) -> None:
        clock = FakeClock()
        process = FakeProcess([])
        trace = self.root / "total-timeout-trace.jsonl"
        auth = self.root / "total-timeout-auth.json"
        auth.write_text("secret", encoding="utf-8")

        def wait_for_readable(
            _readers: list[FakeStdout], _writers: list[object],
            _errors: list[object], timeout: float,
        ) -> tuple[list[object], list[object], list[object]]:
            clock.now += timeout
            return [], [], []

        with self.assertRaisesRegex(harness.HarnessError, "total timeout"):
            harness.monitor_codex_process(
                process,
                trace,
                auth,
                total_timeout_seconds=1,
                inactivity_timeout_seconds=3,
                monotonic=clock,
                wait_for_readable=wait_for_readable,
                process_group_id=9002,
                stop_group=stop_fake_process_group,
            )
        self.assertEqual(trace.read_bytes(), b"")
        self.assertTrue(process.killed)
        self.assertEqual(process.wait_count, 1)

    def test_fabricated_or_malformed_lines_do_not_refresh_inactivity(self) -> None:
        for label, chunk in (
            ("unknown", b'{"type":"fabricated"}\n'),
            ("malformed", b'{"type":"thread.started"\n'),
            ("partial", b'{"type":"thread.started"}'),
        ):
            with self.subTest(label=label):
                clock = FakeClock()
                process = FakeProcess([chunk])
                trace = self.root / f"{label}-trace.jsonl"
                auth = self.root / f"{label}-auth.json"
                auth.write_text("secret", encoding="utf-8")
                readable_once = True

                def wait_for_readable(
                    readers: list[FakeStdout], _writers: list[object],
                    _errors: list[object], timeout: float,
                ) -> tuple[list[FakeStdout], list[object], list[object]]:
                    nonlocal readable_once
                    if readable_once:
                        readable_once = False
                        clock.now += 1.5
                        return readers, [], []
                    clock.now += timeout
                    return [], [], []

                with self.assertRaisesRegex(harness.HarnessError, "inactivity timeout"):
                    harness.monitor_codex_process(
                        process,
                        trace,
                        auth,
                        total_timeout_seconds=5,
                        inactivity_timeout_seconds=2,
                        monotonic=clock,
                        wait_for_readable=wait_for_readable,
                        process_group_id=9010,
                        stop_group=stop_fake_process_group,
                    )
                self.assertEqual(clock.now, 2)
                self.assertTrue(auth.exists())

    def test_stream_capture_rejects_overwrite_and_replacement(self) -> None:
        original = b'{"type":"thread.started","thread_id":"opaque"}\n'
        capture = harness.StreamCapture()
        capture.update(original)
        stream = self.root / "parent-stream.jsonl"
        artifact = self.root / "trace.jsonl"

        stream.write_bytes(b"overwritten")
        with self.assertRaisesRegex(harness.HarnessError, "capture integrity"):
            harness.publish_captured_stream(stream, artifact, capture)
        self.assertFalse(artifact.exists())

        replacement = self.root / "replacement.jsonl"
        replacement.write_bytes(original)
        stream.unlink()
        stream.symlink_to(replacement)
        with self.assertRaisesRegex(harness.HarnessError, "regular parent stream"):
            harness.publish_captured_stream(stream, artifact, capture)
        self.assertFalse(artifact.exists())

        stream.unlink()
        stream.write_bytes(original)
        artifact.write_bytes(b"runner-controlled")
        harness.publish_captured_stream(stream, artifact, capture)
        self.assertEqual(artifact.read_bytes(), original)

    def test_group_cleanup_kills_descendant_after_leader_exits(self) -> None:
        script = (
            "import subprocess, sys; "
            "child = subprocess.Popen([sys.executable, '-c', "
            "'import time; time.sleep(60)']); "
            "print(child.pid, flush=True)"
        )
        leader = subprocess.Popen(
            [sys.executable, "-c", script],
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        assert leader.stdout is not None
        descendant = int(leader.stdout.readline())
        process_group_id = leader.pid
        try:
            leader.wait(timeout=5)
            self.assertNotEqual(process_group_id, os.getpgrp())
            harness.stop_process_group(leader, process_group_id)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    os.kill(descendant, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.01)
            else:
                self.fail("background descendant survived process-group cleanup")
            self.assertIsNotNone(leader.returncode)
        finally:
            try:
                os.killpg(process_group_id, signal.SIGKILL)
            except ProcessLookupError:
                pass
            leader.stdout.close()
            leader.wait()

    def test_timeout_is_fail_closed_and_policy_drift_is_rejected(self) -> None:
        stage = self.prepare_retry("runner-timeout")

        def timeout_with_diagnostics(
            *_args: object, **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            trace_path = kwargs["trace_path"]
            stderr_path = kwargs["stderr_path"]
            assert isinstance(trace_path, Path) and isinstance(stderr_path, Path)
            trace_path.write_text('{"type":"thread.started"}\n', encoding="utf-8")
            stderr_path.write_text("timed out\n", encoding="utf-8")
            raise harness.HarnessError("codex runner inactivity timeout")

        with mock.patch.object(harness, "execute_codex", side_effect=timeout_with_diagnostics):
            with self.assertRaisesRegex(harness.HarnessError, "inactivity timeout"):
                harness.run_scenario(stage, "pre-packet")
        runner = stage / "runner/pre-packet"
        self.assertEqual(
            (runner / "trace.jsonl").read_text(encoding="utf-8"),
            '{"type":"thread.started"}\n',
        )
        self.assertFalse((runner / "metadata.json").exists())
        self.assertFalse((stage / "evaluator/terminal-seal.json").exists())
        self.assertFalse((runner / "codex-state/home/auth.json").exists())

        valid_stage = self.prepare_retry("runner-policy-drift")
        self.run_mocked_phase(valid_stage, "pre-packet")
        metadata_path = valid_stage / "runner/pre-packet/metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["timeout_policy"]["arm_total_seconds"] -= 1
        harness.write_json(metadata_path, metadata)
        paths = harness.runner_paths(valid_stage, phases=("pre-packet",))
        with self.assertRaisesRegex(harness.HarnessError, "fixed conditions"):
            harness.validate_runner_bundles(
                paths,
                phases=("pre-packet",),
                repo=valid_stage / "repo",
                stage_root=valid_stage,
            )

    def test_remediation_receives_only_the_remaining_arm_budget(self) -> None:
        stage = self.prepare_retry("remaining-budget")
        self.run_mocked_phase(stage, "pre-packet")
        pre_metadata = json.loads(
            (stage / "runner/pre-packet/metadata.json").read_text(encoding="utf-8")
        )
        validation = self.root / "remaining-budget-validation.txt"
        validation.write_text("passed\n", encoding="utf-8")
        harness.freeze_pre_packet(stage, validation)
        harness.stage_review_packet(stage)
        completed = subprocess.CompletedProcess(
            args=["codex"], returncode=0, stdout=successful_trace(), stderr=""
        )
        with mock.patch.object(harness, "execute_codex", return_value=completed) as execute:
            harness.run_scenario(stage, "remediation")
        expected_remaining = (
            harness.ARM_TIMEOUT_POLICY["arm_total_seconds"]
            - pre_metadata["duration_milliseconds"] / 1000
        )
        self.assertAlmostEqual(
            execute.call_args.kwargs["total_timeout_seconds"], expected_remaining
        )
        remediation_metadata = json.loads(
            (stage / "runner/remediation/metadata.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            remediation_metadata["arm_elapsed_before_milliseconds"],
            pre_metadata["duration_milliseconds"],
        )
        self.assertEqual(
            remediation_metadata["timeout_policy"], harness.ARM_TIMEOUT_POLICY
        )

    def run_mocked_phase(self, stage: Path, phase: str) -> None:
        completed = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout=successful_trace(),
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
        stage: Path | None = None,
        scenario_id: str = "retry-failed",
        outcomes: dict[str, dict[str, object]] | None = None,
    ) -> tuple[Path, Path]:
        stage = stage or self.prepare_retry(f"{name}-stage")
        repo = stage / "repo"
        self.run_mocked_phase(stage, "pre-packet")
        implementation = repo / "queuectl/cli.py"
        if not implementation.is_file():
            implementation = repo / "eval_change.py"
            implementation.write_text(
                f"LABEL = {identity_text!r}\n", encoding="utf-8"
            )
        else:
            implementation.write_text(
                implementation.read_text(encoding="utf-8")
                + f"\n# committed {identity_text}\n",
                encoding="utf-8",
            )
        if commit_code:
            subprocess.run(
                ["git", "add", implementation.relative_to(repo)], cwd=repo, check=True
            )
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
            implementation.write_text(
                implementation.read_text(encoding="utf-8")
                + f"# working {identity_text}\n",
                encoding="utf-8",
            )
        new_module = (
            repo / "queuectl/new_module.py"
            if (repo / "queuectl").is_dir() else repo / "new_module.py"
        )
        new_module.write_text(
            f"LABEL = {identity_text!r}\n", encoding="utf-8"
        )
        (repo / "tests").mkdir(exist_ok=True)
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
        entries = [
            entry for entry in ledger["entries"]
            if entry["scenario"] == scenario_id
        ]
        runner_paths = harness.runner_paths(stage)
        trace_digest = harness.sha256_file(runner_paths["remediation_trace"])
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
                "test_disposition": (
                    outcomes[entry["finding_id"]]["test_disposition"]
                    if outcomes is not None else entry["test_disposition"]
                ),
                "rereview_scope": (
                    outcomes[entry["finding_id"]]["rereview_scope"]
                    if outcomes is not None else entry["rereview_scope"]
                ),
                "command": f"review {entry['finding_id']}",
                "exit_status": 0,
                "evidence": f"reviewed {identity_text}",
                "evidence_ref": "remediation_trace",
                "evidence_sha256": trace_digest,
            }
            for entry in entries
        ]
        if outcomes is None:
            round_specs = (
                ("full-1", "full", ["RF-001"], f"reviewed {identity_text}"),
                ("full-2", "full", ["RF-001"], "clean final round; no new findings"),
                ("targeted-1", "targeted", ["RF-001", "RF-002"], f"reviewed {identity_text}"),
                ("targeted-2", "targeted", ["RF-003"], f"reviewed {identity_text}"),
            )
        else:
            round_specs = tuple(
                (
                    f"round-{review['finding_id']}", review["rereview_scope"],
                    [review["finding_id"]], f"reviewed {identity_text}",
                )
                for review in reviews if review["rereview_scope"] is not None
            )
        rounds = [
            {
                "round_id": round_id, "scope": scope,
                "reviewed_finding_ids": finding_ids, "command": f"review {round_id}",
                "exit_status": 0, "evidence": evidence_text,
                "evidence_ref": "remediation_trace", "evidence_sha256": trace_digest,
            }
            for round_id, scope, finding_ids, evidence_text in round_specs
        ]
        (evidence / "probes.json").write_text(json.dumps(probes) + "\n", encoding="utf-8")
        (evidence / "reviews.json").write_text(json.dumps(reviews) + "\n", encoding="utf-8")
        (evidence / "rounds.json").write_text(json.dumps(rounds) + "\n", encoding="utf-8")
        measurements = harness.derived_measurements(
            test_diff,
            reviews,
            rounds,
            harness.validate_runner_bundles(runner_paths, repo=repo, stage_root=stage),
        )
        record = {
            "scenario_id": scenario_id,
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

    def test_v11_downstream_chain_rejects_cross_comparison_and_binds_every_input(self) -> None:
        manifest, identity = self.initialize_v11_comparison("artifact-chain")
        with mock.patch.object(harness, "evaluator_identity", return_value=identity):
            binding = harness.binding_from_comparison(
                harness.validate_comparison_manifest(manifest)
            )
            transition_cases = [
                *(
                    (failure, {}, {}, ("inconclusive", "uncomparable_runs", False))
                    for failure in (
                        "evaluator_defect", "baseline_terminal", "ambiguous", "incomparable"
                    )
                ),
                *(
                    (failure, {}, {}, ("candidate_regression", "candidate_regression", False))
                    for failure in (
                        "candidate_unscorable", "candidate_hard_gate", "blinded_regression"
                    )
                ),
                (
                    "candidate_not_exposed", {}, {},
                    ("inconclusive", "inconclusive_scenario", False),
                ),
                (None, {"passed": True}, {}, ("candidate_better", "clean_benefit", True)),
                (
                    None, {"non_preference_hard_gates_passed": True},
                    {"verdict": "materially neutral"},
                    ("candidate_neutral", "candidate_neutral", False),
                ),
                (
                    None, {"non_preference_hard_gates_passed": False},
                    {"verdict": "materially neutral"},
                    ("candidate_regression", "candidate_regression", False),
                ),
                (
                    None, {"non_preference_hard_gates_passed": True},
                    {"verdict": "inconclusive"},
                    ("inconclusive", "uncomparable_runs", False),
                ),
            ]
            for failure, gate_values, judge_values, expected in transition_cases:
                self.assertEqual(
                    harness.final_transition(failure, gate_values, judge_values),
                    expected,
                )
            with self.assertRaisesRegex(harness.HarnessError, "failure class"):
                harness.final_transition("external_interruption", {}, {})
            initial_state = harness.validate_attempt_state(manifest)["state"]
            early_failure = self.root / "pre-arm-failure-evidence.json"
            harness.write_json(early_failure, {
                "schema_version": harness.SCHEMA_VERSION,
                "comparison_binding": binding,
                "attempt_state_sha256": harness.attempt_state_sha256(initial_state),
                "observations": [{
                    "event": "integrity_defect", "subject": "evaluator",
                    "evidence_sha256": binding["comparison_manifest_sha256"],
                    "summary": "Evaluator setup failed.",
                }],
            })
            with self.assertRaisesRegex(harness.HarnessError, "before the first arm"):
                harness.validate_failure_evidence(early_failure, binding, initial_state)
            behavior_schema = json.loads(
                (harness.SUITE_ROOT / "evaluator/behavior-schema.json").read_text()
            )
            arm_schema = behavior_schema["properties"]["arm_binding"]
            self.assertEqual(
                set(arm_schema["properties"]),
                {"arm_name", "terminal_seal_sha256"},
            )
            self.assertIn("arm_binding", behavior_schema["required"])
            compliance_schema = json.loads(
                (harness.SUITE_ROOT / "evaluator/candidate-compliance-schema.json").read_text()
            )
            report_schema = compliance_schema["properties"]["candidate_report"]
            self.assertEqual(
                set(report_schema["properties"]), {"revealed_identity", "records"}
            )
            self.assertEqual(
                set(report_schema["properties"]["records"]["items"]["properties"]),
                {
                    "finding_id", "test_disposition", "test_rationale",
                    "repair_authorized", "rereview_scope", "rereview_rationale",
                },
            )
            records_schema = report_schema["properties"]["records"]
            self.assertEqual(
                (records_schema["minItems"], records_schema["maxItems"], records_schema["uniqueItems"]),
                (6, 6, True),
            )
            self.assertEqual(
                {
                    clause["contains"]["properties"]["finding_id"]["const"]
                    for clause in records_schema["allOf"]
                },
                {"RF-001", "RF-002", "RF-003", "RF-004", "PF-001", "PF-002"},
            )
            self.assertIn("candidate_report", compliance_schema["required"])
            shared_schema = json.loads(
                (
                    harness.SUITE_ROOT
                    / "evaluator/comparison-artifacts-schema.json"
                ).read_text()
            )
            self.assertEqual(
                set(shared_schema["$defs"]),
                {"digest", "evaluatorIdentity", "comparisonBinding"},
            )
            for schema in (
                behavior_schema,
                compliance_schema,
                json.loads((
                    harness.SUITE_ROOT / "evaluator/output-freeze-schema.json"
                ).read_text()),
                json.loads((
                    harness.SUITE_ROOT / "evaluator/terminal-seal-schema.json"
                ).read_text()),
            ):
                self.assertEqual(
                    schema["properties"]["comparison_binding"]["$ref"],
                    "comparison-artifacts-schema.json#/$defs/comparisonBinding",
                )

            interruption = harness.parser().parse_args([
                "record-external-interruption", "--comparison-manifest", "m.json",
                "--arm", "retry-failed-baseline", "--phase", "remediation",
                "--reason", "host stopped",
            ])
            self.assertEqual(interruption.phase, "remediation")
            reveal_command = harness.parser().parse_args([
                "reveal-identities", "--comparison-manifest", "m.json",
                "--blind-packet", "packet.json", "--judge-record", "judge.json",
                "--output", "reveal.json",
            ])
            self.assertFalse(hasattr(reveal_command, "mapping"))
            compliance_command = harness.parser().parse_args([
                "check-candidate-compliance", "report.json",
                "--comparison-manifest", "m.json", "--identity-reveal", "reveal.json",
                "--blind-packet", "packet.json", "--judge-record", "judge.json",
                "--output", "compliance.json",
            ])
            self.assertEqual(compliance_command.blind_packet, Path("packet.json"))
            gate_command = harness.parser().parse_args([
                "gate-official", "--comparison-manifest", "m.json",
                "--baseline", "b1.json", "b2.json",
                "--candidate", "c1.json", "c2.json",
                "--blind-packet", "packet.json", "--judge-record", "judge.json",
                "--identity-reveal", "reveal.json",
                "--candidate-compliance", "compliance.json", "--output", "gate.json",
            ])
            self.assertEqual(gate_command.blind_packet, Path("packet.json"))
            replay_command = harness.parser().parse_args([
                "validate-final-verdict", "--comparison-manifest", "m.json",
            ])
            self.assertEqual(replay_command.comparison_manifest, Path("m.json"))
            completed = subprocess.CompletedProcess(
                args=[str(harness.BUNDLED_CODEX)], returncode=0,
                stdout=successful_trace(), stderr="",
            )
            bound_preflight = self.root / "artifact-chain-preflight.json"
            with mock.patch.object(harness, "execute_codex", return_value=completed):
                harness.preflight_runner(bound_preflight, manifest)
            comparison = harness.validate_comparison_manifest(manifest)
            runtime = Path(comparison["runtime_root"])
            normalized_by_variant: dict[str, list[Path]] = {
                "baseline": [], "candidate": [],
            }
            for arm_name in harness.OFFICIAL_ARM_ORDER:
                scenario_id, variant = arm_name.rsplit("-", 1)
                stage = runtime / arm_name
                harness.prepare_scenario(
                    scenario_id,
                    self.root / f"artifact-chain-packages/{variant}",
                    stage, bound_preflight, manifest,
                )
                if arm_name == harness.OFFICIAL_ARM_ORDER[0]:
                    with mock.patch.object(
                        harness, "begin_arm_attempt",
                        side_effect=harness.HarnessError("registration failed"),
                    ):
                        with self.assertRaisesRegex(
                            harness.HarnessError, "registration failed"
                        ):
                            harness.run_scenario(stage, "pre-packet")
                    self.assertEqual(
                        harness.validate_attempt_state(manifest)["state"]["arms"][arm_name]["status"],
                        "pending",
                    )
                    self.assertFalse((stage / "runner/attempt-1/pre-packet").exists())
                    failed_stream = (
                        runtime / harness.SIBLING_PROBE / "runner-streams"
                        / arm_name / "attempt-1/pre-packet"
                    )
                    self.assertFalse(failed_stream.exists())
                _stage, record = self.make_freeze_inputs(
                    f"real-{arm_name}", arm_name, stage=stage,
                    scenario_id=scenario_id,
                    outcomes=(
                        self.inefficient_baseline()
                        if variant == "baseline" else self.frozen_outcomes()
                    ),
                )
                output_freeze = harness.finalize_arm(stage, record)
                normalized_path = self.root / f"normalized-{arm_name}.json"
                harness.write_json(
                    normalized_path, harness.normalize_run(output_freeze, manifest)
                )
                normalized_by_variant[variant].append(normalized_path)
            baseline = normalized_by_variant["baseline"]
            candidate = normalized_by_variant["candidate"]
            sealed_state = harness.validate_attempt_state(manifest)["state"]
            failure_evidence = self.root / "derived-failure-evidence.json"
            state_digest = harness.attempt_state_sha256(sealed_state)
            evidence_digest = sealed_state["arms"][harness.OFFICIAL_ARM_ORDER[0]][
                "terminal_seal_sha256"
            ]
            harness.write_json(failure_evidence, {
                "schema_version": harness.SCHEMA_VERSION,
                "comparison_binding": binding,
                "attempt_state_sha256": state_digest,
                "observations": [
                    {
                        "event": "scenario_coverage_failure",
                        "subject": "changed_contract",
                        "evidence_sha256": evidence_digest,
                        "summary": "Scenario does not expose the contract.",
                    },
                    {
                        "event": "integrity_defect",
                        "subject": "evaluator",
                        "evidence_sha256": evidence_digest,
                        "summary": "Evaluator evidence is invalid.",
                    },
                ],
            })
            self.assertEqual(
                harness.validate_failure_evidence(
                    failure_evidence, binding, sealed_state
                )[1],
                "evaluator_defect",
            )
            original_normalized = baseline[0].read_bytes()
            tampered_normalized = json.loads(original_normalized)
            tampered_normalized["behavior"]["implementation_additions"] += 1
            harness.write_json(baseline[0], tampered_normalized)
            with self.assertRaisesRegex(harness.HarnessError, "canonical arm normalization"):
                harness.validate_official_normalized(baseline[0], manifest)
            baseline[0].write_bytes(original_normalized)
            ordered = [baseline[0], candidate[0], baseline[1], candidate[1]]
            with self.assertRaisesRegex(harness.HarnessError, "duplicate"):
                harness.build_blind_packet(
                    [baseline[0], baseline[0], candidate[1], baseline[1]], manifest
                )
            self.assertEqual(
                harness.validate_attempt_state(manifest)["state"]["blind"]["status"],
                "pending",
            )
            real_atomic_write = harness.atomic_write_json

            def fail_authoritative_packet(path: Path, value: object) -> None:
                if path.name == "private-identity-map.json":
                    raise OSError("authoritative mapping write failed")
                real_atomic_write(path, value)

            with mock.patch.object(
                harness, "atomic_write_json", side_effect=fail_authoritative_packet
            ):
                with self.assertRaisesRegex(OSError, "mapping write failed"):
                    harness.build_blind_packet(list(reversed(ordered)), manifest)
            self.assertEqual(
                harness.validate_attempt_state(manifest)["state"]["blind"]["status"],
                "pending",
            )
            control = harness.comparison_control(runtime)
            self.assertFalse((control / "blind-packet.json").exists())
            with mock.patch.object(
                harness, "register_blind_packet",
                side_effect=harness.HarnessError("registration failed"),
            ):
                with self.assertRaisesRegex(harness.HarnessError, "registration failed"):
                    harness.build_blind_packet(list(reversed(ordered)), manifest)
            self.assertFalse((control / "blind-packet.json").exists())
            self.assertFalse((control / "private-identity-map.json").exists())
            packet_path = self.root / "v11-blind-packet.json"
            blind_command = [
                "blind-packet", *(str(path) for path in reversed(ordered)),
                "--output", str(packet_path),
                "--comparison-manifest", str(manifest),
            ]
            authoritative_packet = (
                harness.comparison_control(runtime) / "blind-packet.json"
            )
            with mock.patch.object(
                harness, "write_json", side_effect=OSError("publication failed")
            ):
                with self.assertRaisesRegex(OSError, "publication failed"):
                    harness.main(blind_command)
            self.assertTrue(authoritative_packet.is_file())
            self.assertFalse(packet_path.exists())
            self.assertEqual(
                harness.validate_attempt_state(manifest)["state"]["blind"]["status"],
                "frozen",
            )
            self.assertEqual(
                harness.sha256_file(authoritative_packet),
                harness.validate_attempt_state(manifest)["state"]["blind"]["blind_packet_sha256"],
            )
            self.assertEqual(harness.main(blind_command), 0)
            different_inputs = [
                "blind-packet", str(ordered[0]), str(ordered[0]),
                str(ordered[2]), str(ordered[3]),
                "--output", str(self.root / "different-blind-packet.json"),
                "--comparison-manifest", str(manifest),
            ]
            with self.assertRaisesRegex(harness.HarnessError, "duplicate"):
                harness.main(different_inputs)
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            packet_text = packet_path.read_text(encoding="utf-8").lower()
            self.assertNotIn("baseline", packet_text)
            self.assertNotIn("candidate", packet_text)
            mapping_path = (
                harness.comparison_control(Path(comparison["runtime_root"]))
                / "private-identity-map.json"
            )
            private_mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            candidate_run = next(
                run for run, identity_name in private_mapping["mapping"].items()
                if identity_name == "candidate"
            )
            harness.begin_judge_attempt(manifest, harness.sha256_file(packet_path))
            decision = self.root / "v11-judge-decision.json"
            harness.write_json(decision, {
                "verdict": f"{candidate_run} better",
                "rationale": "The candidate preserves correctness and improves both axes.",
                "material_correctness_preserved": True,
            })
            judge_path = self.root / "v11-judge-record.json"
            harness.freeze_judge_record(
                manifest, packet_path, decision, judge_path
            )
            reveal_path = self.root / "v11-identity-reveal.json"
            harness.write_json(
                reveal_path,
                harness.reveal_identities(
                    manifest, packet_path, judge_path
                ),
            )
            report = self.root / "v11-candidate-report.json"
            harness.write_json(report, {
                "revealed_identity": "candidate", "records": self.candidate_records()
            })
            compliance_path = self.root / "v11-candidate-compliance.json"
            harness.write_json(
                compliance_path,
                harness.check_candidate_compliance_bound(
                    manifest, report, reveal_path, packet_path, judge_path
                ),
            )
            gate = harness.gate_official_outcomes(
                manifest, baseline, candidate, packet_path, judge_path,
                reveal_path, compliance_path,
            )
            self.assertTrue(gate["passed"])
            self.assertEqual(gate["comparison_binding"], binding)
            gate_path = self.root / "v11-outcome-gate.json"
            harness.write_json(gate_path, gate)
            final = harness.freeze_final_verdict(
                manifest, gate_path, judge_path, compliance_path,
                list(reversed(baseline)), list(reversed(candidate)),
                packet_path, reveal_path,
            )
            self.assertEqual(
                (final["verdict"], final["stop_reason"], final["merge_ready"]),
                ("candidate_better", "clean_benefit", True),
            )
            final_control = harness.comparison_control(runtime)
            frozen_retry = json.loads((
                final_control / final["evidence_paths"][
                    "normalized_retry_failed_baseline"
                ]
            ).read_text(encoding="utf-8"))
            self.assertEqual(
                frozen_retry["arm_binding"]["arm_name"], "retry-failed-baseline"
            )
            harness.validate_final_verdict(manifest)
            finalized_mutators = (
                lambda: harness.begin_arm_attempt(
                    manifest, harness.OFFICIAL_ARM_ORDER[0], "a" * 64,
                    _comparison=comparison,
                ),
                lambda: harness.bind_arm_phase_input(
                    manifest, harness.OFFICIAL_ARM_ORDER[0], "remediation", "a" * 64,
                    _comparison=comparison,
                ),
                lambda: harness.record_external_interruption(
                    manifest, harness.OFFICIAL_ARM_ORDER[0], "late", "remediation",
                    _comparison=comparison,
                ),
                lambda: harness.register_terminal_seal(
                    manifest, harness.OFFICIAL_ARM_ORDER[0], "a" * 64,
                    _comparison=comparison,
                ),
                lambda: harness.begin_judge_attempt(
                    manifest, "a" * 64, _comparison=comparison
                ),
                lambda: harness.register_blind_packet(
                    manifest, "a" * 64, "b" * 64, _comparison=comparison
                ),
                lambda: harness.record_judge_interruption(
                    manifest, "late", _comparison=comparison
                ),
                lambda: harness.register_judge_record(
                    manifest, "a" * 64, _comparison=comparison
                ),
                lambda: harness.register_final_verdict(
                    manifest, "a" * 64, _comparison=comparison
                ),
            )
            for mutate in finalized_mutators:
                with self.assertRaisesRegex(harness.HarnessError, "immutable"):
                    mutate()
            control = harness.comparison_control(Path(comparison["runtime_root"]))
            frozen_packet = control / final["evidence_paths"]["blind_packet"]
            frozen_packet_bytes = frozen_packet.read_bytes()
            frozen_packet.write_bytes(frozen_packet_bytes + b" ")
            with self.assertRaisesRegex(harness.HarnessError, "digest drifted"):
                harness.validate_final_verdict(manifest)
            frozen_packet.write_bytes(frozen_packet_bytes)
            state_path = control / harness.COMPARISON_STATE
            frozen_state_bytes = state_path.read_bytes()
            tampered_state = json.loads(frozen_state_bytes)
            first_attempt = tampered_state["arms"][harness.OFFICIAL_ARM_ORDER[0]][
                "attempts"
            ][0]
            first_attempt["input_sha256"] = "9" * 64
            first_attempt["phase_inputs"]["pre-packet"] = "9" * 64
            harness.write_json(state_path, tampered_state)
            with self.assertRaisesRegex(harness.HarnessError, "frozen state drifted"):
                harness.validate_final_verdict(manifest)
            state_path.write_bytes(frozen_state_bytes)
            sentinel = Path(comparison["external_sentinel"]["path"])
            harness.cleanup_comparison(manifest)
            self.assertTrue(sentinel.is_file())
            cleaned_state = harness.validate_attempt_state(manifest)["state"]
            self.assertTrue(harness.is_digest(cleaned_state["cleanup_receipt_sha256"]))
            harness.validate_comparison_manifest(manifest)
            harness.validate_final_verdict(manifest)
            advanced_identity = {**identity, "commit": "4" * 40}
            with (
                mock.patch.object(
                    harness, "evaluator_identity", return_value=advanced_identity
                ),
                mock.patch.object(
                    harness, "git_commit_is_ancestor", return_value=True
                ),
                mock.patch.object(
                    harness, "git_history_touches_evaluator", return_value=False
                ),
            ):
                harness.validate_final_verdict(manifest)
            changed_evaluator_bytes = {
                **advanced_identity, "file_manifest_sha256": "9" * 64,
            }
            with (
                mock.patch.object(
                    harness, "evaluator_identity",
                    return_value=changed_evaluator_bytes,
                ),
                mock.patch.object(
                    harness, "git_commit_is_ancestor", return_value=True
                ),
            ):
                with self.assertRaisesRegex(
                    harness.HarnessError, "identity drifted"
                ):
                    harness.validate_final_verdict(manifest)

            foreign = json.loads(compliance_path.read_text(encoding="utf-8"))
            foreign["comparison_binding"]["comparison_manifest_sha256"] = "f" * 64
            harness.write_json(compliance_path, foreign)
            with self.assertRaises(harness.HarnessError):
                harness.gate_official_outcomes(
                    manifest, baseline, candidate, packet_path, judge_path,
                    reveal_path, compliance_path,
                )


if __name__ == "__main__":
    unittest.main()
