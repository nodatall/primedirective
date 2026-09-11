#!/usr/bin/env python3
"""Validate a v12.32 independent case bundle before and after private import."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any


ORACLE_VERSION = "deliver-plain-language-v12.32"
INTERFACE_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/independent-case-bundle-interface.json"
)
BUNDLE_SUBDIRECTORY = "private-oracle"
MANIFEST_NAME = "bundle-manifest.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NAMESPACE = re.compile(r"^v1232-[0-9a-f]{20}$")
MANIFEST_FIELDS = {
    "schema_version", "oracle_version", "namespace", "model", "reasoning",
    "controller_commit", "controller_tree", "required_files", "required_file_modes",
    "bundle_file_sha256", "public_file_sha256", "response_schema_public_path",
    "counts", "retained_behavior_ids", "approved_removed_behavior_ids", "freshness",
    "manifest_payload_sha256",
}
STANDALONE_OUTPUT_FIELDS = {
    "schema_version", "oracle_version", "status", "controller_commit", "controller_tree",
    "bundle_source_commit", "bundle_source_tree", "bundle_manifest_sha256",
    "manifest_payload_sha256", "public_file_sha256", "imported_file_sha256",
}
REQUIRED_FILES = (
    "author-v132.mjs", "bundle-manifest.json", "cases.json", "expected-answers.json",
    "judge-allocation-manifest.json", "projected-arm-packet.json",
    "response-schema.json", "validate-v132.mjs",
)
IMPORTED_FILES = tuple(name for name in REQUIRED_FILES if name != MANIFEST_NAME)
REQUIRED_FILE_MODES = {
    name: "100755" if name in {"author-v132.mjs", "validate-v132.mjs"} else "100644"
    for name in REQUIRED_FILES
}
PUBLIC_BINDING_PATHS = tuple(sorted({
    "evals/deliver/harness.py",
    "evals/deliver/plain-language-v12/adapter.py",
    "evals/deliver/plain-language-v12/baseline-package-manifest.json",
    "evals/deliver/plain-language-v12/candidate-behavior-map.json",
    "evals/deliver/plain-language-v12/candidate-package-manifest.json",
    "evals/deliver/plain-language-v12/case_bundle_validator.py",
    "evals/deliver/plain-language-v12/comprehension-vocabulary.json",
    "evals/deliver/plain-language-v12/execution-policy.json",
    INTERFACE_RELATIVE_PATH,
    "evals/deliver/plain-language-v12/public-contract-inventory.json",
    "evals/deliver/plain-language-v12/readiness_transition.py",
    "evals/deliver/plain-language-v12/root-isolation-dependencies.json",
    "evals/deliver/plain-language-v12/root_isolation_probe.py",
    "evals/deliver/plain-language-v12/standalone_case_bundle_validator.mjs",
    "evals/deliver/plain-language-v12/wording-approval.json",
}))


class BundleValidationError(RuntimeError):
    """Raised when an independent case bundle is not exactly reproducible."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json_bytes(value: bytes, label: str) -> dict[str, Any]:
    try:
        document = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleValidationError(f"{label} is not valid JSON") from exc
    if not isinstance(document, dict):
        raise BundleValidationError(f"{label} must be an object")
    return document


def git(repo: Path, *arguments: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", *arguments], cwd=repo, check=False, capture_output=True, text=not binary,
    )
    if result.returncode:
        stderr = result.stderr.decode(errors="replace") if binary else result.stderr
        raise BundleValidationError(
            f"git {' '.join(arguments)} failed: {stderr.strip()}"
        )
    return result.stdout if binary else result.stdout.strip()


def commit(repo: Path, ref: str) -> str:
    value = str(git(repo, "rev-parse", f"{ref}^{{commit}}"))
    if HEX40.fullmatch(value) is None:
        raise BundleValidationError("Git commit is malformed")
    return value


def tree(repo: Path, ref: str) -> str:
    value = str(git(repo, "rev-parse", f"{ref}^{{tree}}"))
    if HEX40.fullmatch(value) is None:
        raise BundleValidationError("Git tree is malformed")
    return value


def blob(repo: Path, ref: str, relative_path: str) -> bytes:
    return bytes(git(repo, "cat-file", "blob", f"{ref}:{relative_path}", binary=True))


def blob_mode(repo: Path, ref: str, relative_path: str) -> str:
    output = str(git(repo, "ls-tree", ref, "--", relative_path)).splitlines()
    if len(output) != 1:
        raise BundleValidationError(f"bundle file is missing or ambiguous: {relative_path}")
    try:
        metadata, listed = output[0].split("\t", 1)
        mode, kind, object_id = metadata.split()
    except ValueError as exc:
        raise BundleValidationError(f"bundle Git entry is malformed: {relative_path}") from exc
    if (
        listed != relative_path
        or kind != "blob"
        or mode not in {"100644", "100755"}
        or HEX40.fullmatch(object_id) is None
    ):
        raise BundleValidationError(f"bundle file is not a regular Git blob: {relative_path}")
    return mode


def require_regular(root: Path, relative_path: str) -> Path:
    current = root
    for part in Path(relative_path).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise BundleValidationError(f"required file is unavailable: {relative_path}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise BundleValidationError(f"required file has a symlink component: {relative_path}")
    if not stat.S_ISREG(current.stat().st_mode):
        raise BundleValidationError(f"required file is not regular: {relative_path}")
    return current


def file_mode(path: Path) -> str:
    return "100755" if stat.S_IMODE(path.stat().st_mode) & 0o111 else "100644"


def load_interface(public_repo: Path, controller: str) -> tuple[dict[str, Any], bytes]:
    raw = blob(public_repo, controller, INTERFACE_RELATIVE_PATH)
    interface = load_json_bytes(raw, "bundle interface")
    required_fields = {
        "schema_version", "oracle_version", "bundle_manifest_schema_version",
        "bundle_subdirectory", "required_files", "manifest_declared_imported_files",
        "required_file_modes", "public_binding_paths", "response_schema_binding",
        "standalone_validator_binding", "expected_counts", "expected_model",
        "expected_reasoning", "expected_allocation_status", "namespace_pattern",
        "freshness_contract", "import_policy", "standalone_validator_output_fields",
        "integrated_validator_path",
    }
    required = interface.get("required_files")
    imported = interface.get("manifest_declared_imported_files")
    public_paths = interface.get("public_binding_paths")
    if (
        set(interface) != required_fields
        or interface.get("schema_version") != 1
        or interface.get("oracle_version") != ORACLE_VERSION
        or interface.get("bundle_manifest_schema_version") != 2
        or interface.get("bundle_subdirectory") != BUNDLE_SUBDIRECTORY
        or not isinstance(required, list)
        or required != list(REQUIRED_FILES)
        or not isinstance(imported, list)
        or imported != list(IMPORTED_FILES)
        or interface.get("required_file_modes") != REQUIRED_FILE_MODES
        or not isinstance(public_paths, list)
        or public_paths != list(PUBLIC_BINDING_PATHS)
        or interface.get("standalone_validator_output_fields")
        != sorted(STANDALONE_OUTPUT_FIELDS)
        or interface.get("expected_counts") != {
            "public_behavior_count": 108,
            "retained_case_count": 103,
            "removal_absence_case_count": 5,
            "total_case_count": 108,
            "expected_answer_count": 108,
            "judge_lane_count": 3,
        }
        or interface.get("expected_model") != "gpt-5.6-sol"
        or interface.get("expected_reasoning") != "xhigh"
        or interface.get("expected_allocation_status") != "allocated_not_run"
        or interface.get("namespace_pattern") != NAMESPACE.pattern
    ):
        raise BundleValidationError("bundle interface schema is not exact")
    if interface.get("import_policy") != {
        "all_required_source_files_must_be_committed": True,
        "all_manifest_declared_files_must_import_byte_exact": True,
        "bundle_manifest_must_import_byte_exact": True,
        "post_import_rewrite_allowed": False,
        "derived_files_may_not_collide_with_required_files": True,
        "standalone_and_integrated_validation_must_reconcile": True,
    }:
        raise BundleValidationError("bundle import policy is not exact")
    return interface, raw


def public_digests(public_repo: Path, controller: str, interface: dict[str, Any]) -> dict[str, str]:
    head = commit(public_repo, "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", controller, head],
        cwd=public_repo, check=False, capture_output=True,
    ).returncode:
        raise BundleValidationError("controller is not in public HEAD ancestry")
    result: dict[str, str] = {}
    for relative_path in interface["public_binding_paths"]:
        source = blob(public_repo, controller, relative_path)
        live = require_regular(public_repo, relative_path)
        if live.read_bytes() != source:
            raise BundleValidationError(f"public controller file drifted: {relative_path}")
        result[relative_path] = sha256_bytes(source)
    return result


def manifest_payload(document: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != "manifest_payload_sha256"}


def _validate_manifest(
    public_repo: Path, manifest: dict[str, Any], interface: dict[str, Any], controller: str,
    controller_tree: str, expected_public_digests: dict[str, str], source_files: dict[str, bytes],
    source_modes: dict[str, str],
) -> None:
    inventory = load_json_bytes(
        source_files.pop("__public_inventory"), "public contract inventory"
    )
    behavior_map = load_json_bytes(
        source_files.pop("__candidate_map"), "candidate behavior map"
    )
    behavior_ids = [item.get("behavior_id") for item in inventory.get("behaviors", [])]
    removed = behavior_map.get("intentionally_removed_behavior_ids")
    retained = [item for item in behavior_ids if item not in set(removed or [])]
    if (
        len(behavior_ids) != 108
        or len(set(behavior_ids)) != 108
        or len(retained) != 103
        or removed != [
            "DLV-ACT-005", "DLV-MODE-004", "DLV-PLAN-005", "DLV-PLAN-006",
            "DLV-STOP-008",
        ]
        or set(manifest) != MANIFEST_FIELDS
        or manifest.get("schema_version") != 2
        or manifest.get("oracle_version") != ORACLE_VERSION
        or NAMESPACE.fullmatch(str(manifest.get("namespace"))) is None
        or manifest.get("model") != interface["expected_model"]
        or manifest.get("reasoning") != interface["expected_reasoning"]
        or manifest.get("controller_commit") != controller
        or manifest.get("controller_tree") != controller_tree
        or manifest.get("required_files") != interface["required_files"]
        or manifest.get("required_file_modes") != source_modes
        or manifest.get("public_file_sha256") != expected_public_digests
        or manifest.get("response_schema_public_path")
        != interface["response_schema_binding"]["public_source"]
        or manifest.get("counts") != interface["expected_counts"]
        or manifest.get("retained_behavior_ids") != retained
        or manifest.get("approved_removed_behavior_ids") != removed
        or manifest.get("freshness") != interface["freshness_contract"]
        or manifest.get("manifest_payload_sha256")
        != sha256_bytes(canonical_json(manifest_payload(manifest)))
    ):
        raise BundleValidationError("bundle manifest schema or public binding is not exact")
    imported = interface["manifest_declared_imported_files"]
    expected_imported_digests = {
        name: sha256_bytes(source_files[name]) for name in imported
    }
    if manifest.get("bundle_file_sha256") != expected_imported_digests:
        raise BundleValidationError("bundle manifest does not bind every imported file")
    response = interface["response_schema_binding"]
    standalone = interface["standalone_validator_binding"]
    if (
        source_files[response["bundle_file"]]
        != blob(public_repo, controller, response["public_source"])
        or source_files[standalone["bundle_file"]]
        != blob(public_repo, controller, standalone["public_source"])
    ):
        raise BundleValidationError("bundle response schema or standalone validator is not byte-exact")


def validate_bundle(
    public_repo: Path, controller_ref: str, bundle_repo: Path, bundle_source_ref: str,
    integrated_root: Path | None = None,
) -> dict[str, Any]:
    public_repo = public_repo.resolve(strict=True)
    bundle_repo = bundle_repo.resolve(strict=True)
    controller = commit(public_repo, controller_ref)
    bundle_source = commit(bundle_repo, bundle_source_ref)
    interface, _ = load_interface(public_repo, controller)
    expected_public_digests = public_digests(public_repo, controller, interface)
    controller_tree = tree(public_repo, controller)
    bundle_tree = tree(bundle_repo, bundle_source)
    required = interface["required_files"]
    prefix = f"{BUNDLE_SUBDIRECTORY}/"
    listed = str(git(
        bundle_repo, "ls-tree", "-r", "--name-only", bundle_source, "--", BUNDLE_SUBDIRECTORY,
    )).splitlines()
    expected_paths = [prefix + name for name in required]
    if listed != expected_paths:
        raise BundleValidationError("bundle source required file set is not exact")
    source_files = {
        name: blob(bundle_repo, bundle_source, prefix + name) for name in required
    }
    source_modes = {
        name: blob_mode(bundle_repo, bundle_source, prefix + name) for name in required
    }
    if source_modes != interface["required_file_modes"]:
        raise BundleValidationError("bundle source file modes are not exact")
    manifest_raw = source_files[MANIFEST_NAME]
    manifest = load_json_bytes(manifest_raw, "bundle manifest")
    validation_files = dict(source_files)
    validation_files["__public_inventory"] = blob(
        public_repo, controller, "evals/deliver/plain-language-v12/public-contract-inventory.json"
    )
    validation_files["__candidate_map"] = blob(
        public_repo, controller, "evals/deliver/plain-language-v12/candidate-behavior-map.json"
    )
    _validate_manifest(
        public_repo, manifest, interface, controller, controller_tree, expected_public_digests,
        validation_files, source_modes,
    )
    if integrated_root is not None:
        integrated_root = integrated_root.resolve(strict=True)
        for name in required:
            path = require_regular(integrated_root, name)
            if path.read_bytes() != source_files[name] or file_mode(path) != source_modes[name]:
                raise BundleValidationError(f"integrated bundle file drifted: {name}")
    with tempfile.TemporaryDirectory(prefix="deliver-v1232-bundle-", dir="/private/tmp") as temporary:
        stage = Path(temporary)
        for name in required:
            target = stage / name
            target.write_bytes(source_files[name])
            target.chmod(0o755 if source_modes[name] == "100755" else 0o644)
        command = [
            "/usr/bin/env", "-i", "PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "NODE_OPTIONS=--no-addons", "node", str(stage / "validate-v132.mjs"),
            "--public-repo", str(public_repo), "--controller-commit", controller,
            "--bundle-repo", str(bundle_repo), "--bundle-source-commit", bundle_source,
            "--bundle-root", str(stage),
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode or completed.stderr:
        raise BundleValidationError("standalone bundle validator failed")
    standalone = load_json_bytes(completed.stdout.encode("utf-8"), "standalone validation")
    imported_digests = {
        name: sha256_bytes(source_files[name])
        for name in interface["manifest_declared_imported_files"]
    }
    expected_output = {
        "schema_version": 1,
        "oracle_version": ORACLE_VERSION,
        "status": "pass",
        "controller_commit": controller,
        "controller_tree": controller_tree,
        "bundle_source_commit": bundle_source,
        "bundle_source_tree": bundle_tree,
        "bundle_manifest_sha256": sha256_bytes(manifest_raw),
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "public_file_sha256": expected_public_digests,
        "imported_file_sha256": imported_digests,
    }
    if set(standalone) != STANDALONE_OUTPUT_FIELDS or standalone != expected_output:
        raise BundleValidationError(
            "standalone and integrated bundle validation did not reconcile"
        )
    return expected_output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--controller-commit", required=True)
    parser.add_argument("--bundle-repo", type=Path, required=True)
    parser.add_argument("--bundle-source-commit", required=True)
    parser.add_argument("--integrated-root", type=Path)
    args = parser.parse_args()
    result = validate_bundle(
        args.repo, args.controller_commit, args.bundle_repo, args.bundle_source_commit,
        args.integrated_root,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BundleValidationError as exc:
        print(f"case bundle validation failed: {exc}", file=os.sys.stderr)
        raise SystemExit(2)
