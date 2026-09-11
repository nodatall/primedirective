from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = Path(__file__).resolve().parents[1] / "case_bundle_validator.py"
SPEC = importlib.util.spec_from_file_location("deliver_v1234_case_bundle_validator", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class CaseBundleValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        original_controller = validator.BUNDLE_CONTROLLER_COMMIT
        self.addCleanup(setattr, validator, "BUNDLE_CONTROLLER_COMMIT", original_controller)
        base = Path(tempfile.mkdtemp(prefix="deliver-v1232-bundle-test-", dir="/private/tmp"))
        self.addCleanup(shutil.rmtree, base)
        self.public = base / "public"
        self.bundle = base / "bundle"
        self.integrated = base / "integrated"
        self.public.mkdir()
        self.bundle.mkdir()
        self.integrated.mkdir()
        self._init(self.public)
        self._init(self.bundle)
        interface = json.loads(subprocess.run(
            ["git", "show", f"{validator.BUNDLE_CONTROLLER_COMMIT}:{validator.INTERFACE_RELATIVE_PATH}"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout)
        for relative in interface["public_binding_paths"]:
            target = self.public / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.run(
                ["git", "show", f"{validator.BUNDLE_CONTROLLER_COMMIT}:{relative}"],
                cwd=ROOT, check=True, capture_output=True,
            ).stdout)
            target.chmod(0o755 if subprocess.run(
                ["git", "ls-tree", validator.BUNDLE_CONTROLLER_COMMIT, "--", relative],
                cwd=ROOT, check=True, capture_output=True, text=True,
            ).stdout.startswith("100755") else 0o644)
        self._commit(self.public, "controller")
        self.controller = self._git(self.public, "rev-parse", "HEAD")
        validator.BUNDLE_CONTROLLER_COMMIT = self.controller
        self.controller_tree = self._git(self.public, "rev-parse", "HEAD^{tree}")
        self.interface = interface
        self._build_bundle()

    def _git(self, repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
        ).stdout.strip()

    def _init(self, repo: Path) -> None:
        self._git(repo, "init", "-q")
        self._git(repo, "config", "user.email", "bundle-test@example.invalid")
        self._git(repo, "config", "user.name", "Bundle Test")

    def _commit(self, repo: Path, message: str) -> None:
        self._git(repo, "add", ".")
        self._git(repo, "commit", "-q", "-m", message)

    @staticmethod
    def _sha(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    @staticmethod
    def _canonical(value: object) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _build_bundle(self) -> None:
        root = self.bundle / validator.BUNDLE_SUBDIRECTORY
        root.mkdir()
        payloads = {
            "author-v132.mjs": b"#!/usr/bin/env node\nprocess.exit(0);\n",
            "cases.json": b'{"synthetic_fixture":true}\n',
            "expected-answers.json": b'{"synthetic_fixture":true}\n',
            "judge-allocation-manifest.json": b'{"synthetic_fixture":true}\n',
            "projected-arm-packet.json": b'{"synthetic_fixture":true}\n',
            "response-schema.json": (
                self.public / self.interface["response_schema_binding"]["public_source"]
            ).read_bytes(),
            "validate-v132.mjs": (
                self.public / self.interface["standalone_validator_binding"]["public_source"]
            ).read_bytes(),
        }
        for name, value in payloads.items():
            path = root / name
            path.write_bytes(value)
            path.chmod(0o755 if self.interface["required_file_modes"][name] == "100755" else 0o644)
        inventory = json.loads(
            (self.public / "evals/deliver/plain-language-v12/public-contract-inventory.json").read_text()
        )
        behavior_map = json.loads(
            (self.public / "evals/deliver/plain-language-v12/candidate-behavior-map.json").read_text()
        )
        removed = behavior_map["intentionally_removed_behavior_ids"]
        retained = [
            item["behavior_id"] for item in inventory["behaviors"]
            if item["behavior_id"] not in set(removed)
        ]
        public_digests = {
            relative: self._sha((self.public / relative).read_bytes())
            for relative in self.interface["public_binding_paths"]
        }
        manifest = {
            "schema_version": 2,
            "oracle_version": validator.ORACLE_VERSION,
            "namespace": "v1232-0123456789abcdefabcd",
            "model": self.interface["expected_model"],
            "reasoning": self.interface["expected_reasoning"],
            "controller_commit": self.controller,
            "controller_tree": self.controller_tree,
            "required_files": self.interface["required_files"],
            "required_file_modes": self.interface["required_file_modes"],
            "bundle_file_sha256": {
                name: self._sha(payloads[name])
                for name in self.interface["manifest_declared_imported_files"]
            },
            "public_file_sha256": public_digests,
            "response_schema_public_path": self.interface["response_schema_binding"]["public_source"],
            "counts": self.interface["expected_counts"],
            "retained_behavior_ids": retained,
            "approved_removed_behavior_ids": removed,
            "freshness": self.interface["freshness_contract"],
        }
        manifest["manifest_payload_sha256"] = self._sha(self._canonical(manifest))
        (root / validator.MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self._commit(self.bundle, "independent synthetic bundle fixture")
        self.bundle_source = self._git(self.bundle, "rev-parse", "HEAD")
        shutil.copytree(root, self.integrated, dirs_exist_ok=True, copy_function=shutil.copy2)

    def test_complete_bundle_reconciles_standalone_and_integrated_validation(self) -> None:
        result = validator.validate_bundle(
            self.public, self.controller, self.bundle, self.bundle_source, self.integrated,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            set(result["imported_file_sha256"]),
            set(self.interface["manifest_declared_imported_files"]),
        )

    def test_imported_response_schema_overwrite_is_rejected(self) -> None:
        (self.integrated / "response-schema.json").write_bytes(b"{}\n")
        with self.assertRaisesRegex(validator.BundleValidationError, "integrated bundle file drifted"):
            validator.validate_bundle(
                self.public, self.controller, self.bundle, self.bundle_source, self.integrated,
            )

    def test_four_file_subset_manifest_is_rejected(self) -> None:
        manifest_path = self.bundle / validator.BUNDLE_SUBDIRECTORY / validator.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text())
        manifest["bundle_file_sha256"] = dict(list(manifest["bundle_file_sha256"].items())[:4])
        manifest["manifest_payload_sha256"] = self._sha(
            self._canonical({key: value for key, value in manifest.items() if key != "manifest_payload_sha256"})
        )
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        self._commit(self.bundle, "incomplete manifest")
        with self.assertRaisesRegex(validator.BundleValidationError, "every imported file"):
            validator.validate_bundle(self.public, self.controller, self.bundle, "HEAD")

    def test_carried_bundle_uses_frozen_controller_not_descendant_live_bytes(self) -> None:
        relative = self.interface["public_binding_paths"][0]
        (self.public / relative).write_bytes(b"drift\n")
        result = validator.validate_bundle(
            self.public, self.controller, self.bundle, self.bundle_source
        )
        self.assertEqual(result["controller_commit"], self.controller)


if __name__ == "__main__":
    unittest.main()
