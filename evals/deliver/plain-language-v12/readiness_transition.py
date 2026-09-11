#!/usr/bin/env python3
"""Version-pinned, auditable readiness transitions for Deliver oracle v12.34."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ORACLE_VERSION = "deliver-plain-language-v12.34"
SCHEMA_VERSION = 30
READINESS_RELATIVE_PATH = "evals/deliver/plain-language-v12/oracle-readiness.json"
REVIEW_RELATIVE_PATH = "evals/deliver/plain-language-v12/independent-review-record.json"
ISOLATION_RELATIVE_PATH = "evals/deliver/plain-language-v12/trusted-host-isolation-receipt.json"
PROBE_RELATIVE_PATH = "evals/deliver/plain-language-v12/root_isolation_probe.py"
TRANSITION_RELATIVE_PATH = "evals/deliver/plain-language-v12/readiness_transition.py"
PRIVATE_RUNTIME_LAUNCHER_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/private_runtime_launcher.py"
)
PRIVATE_RUNTIME_CLOSURE_MANIFEST_RELATIVE_PATH = (
    "private-oracle/private-runtime-closure.json"
)
HARNESS_RELATIVE_PATH = "evals/deliver/harness.py"
CASE_BUNDLE_VALIDATOR_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/case_bundle_validator.py"
)
BUNDLE_INTERFACE_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/independent-case-bundle-interface.json"
)
STANDALONE_BUNDLE_VALIDATOR_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/standalone_case_bundle_validator.mjs"
)
DEPENDENCY_MANIFEST_RELATIVE_PATH = (
    "evals/deliver/plain-language-v12/root-isolation-dependencies.json"
)
DEPENDENCY_ROLES = {
    TRANSITION_RELATIVE_PATH: "readiness_transition_entrypoint",
    PROBE_RELATIVE_PATH: "root_isolation_probe_entrypoint",
    PRIVATE_RUNTIME_LAUNCHER_RELATIVE_PATH: "private_runtime_git_object_launcher",
    HARNESS_RELATIVE_PATH: "dynamic_deliver_harness_import",
    CASE_BUNDLE_VALIDATOR_RELATIVE_PATH: "private_bundle_integrity_validator",
    STANDALONE_BUNDLE_VALIDATOR_RELATIVE_PATH: "standalone_bundle_validator_executable",
    BUNDLE_INTERFACE_RELATIVE_PATH: "independent_bundle_interface_data",
    "evals/deliver/plain-language-v12/adapter.py": "public_adapter_binding_data",
    "evals/deliver/plain-language-v12/baseline-package-manifest.json": "baseline_package_binding_data",
    "evals/deliver/plain-language-v12/candidate-behavior-map.json": "candidate_behavior_binding_data",
    "evals/deliver/plain-language-v12/candidate-package-manifest.json": "candidate_package_binding_data",
    "evals/deliver/plain-language-v12/comprehension-vocabulary.json": "response_schema_binding_data",
    "evals/deliver/plain-language-v12/execution-policy.json": "execution_policy_binding_data",
    "evals/deliver/plain-language-v12/public-contract-inventory.json": "public_inventory_binding_data",
    "evals/deliver/plain-language-v12/wording-approval.json": "wording_approval_binding_data",
}
PYTHON_SOURCE_DEPENDENCIES = frozenset({
    TRANSITION_RELATIVE_PATH,
    PROBE_RELATIVE_PATH,
    PRIVATE_RUNTIME_LAUNCHER_RELATIVE_PATH,
    HARNESS_RELATIVE_PATH,
    CASE_BUNDLE_VALIDATOR_RELATIVE_PATH,
})
REPO_LOCAL_DATA_INPUTS = tuple(sorted(
    set(DEPENDENCY_ROLES) - PYTHON_SOURCE_DEPENDENCIES
    - {STANDALONE_BUNDLE_VALIDATOR_RELATIVE_PATH}
))
DEPENDENCY_OBSERVED_ROLES = {
    **DEPENDENCY_ROLES,
    DEPENDENCY_MANIFEST_RELATIVE_PATH: "dependency_manifest_root",
}
PUBLIC_REPOSITORY = Path("/Volumes/Code/primedirective")
PRIVATE_EVALUATOR_REPOSITORY = Path(
    "/private/tmp/deliver-plain-language-v134-evaluator/repo"
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
INDEPENDENT_RESULT_KIND = "orchestrator_observed_agent_result_not_signature"
ISOLATION_RESULT_KIND = "root_command_observed_probe_result_not_signature"
NETWORK_POLICY = (
    "bundled Codex connectivity is required; network isolation and arbitrary outbound "
    "denial are not claimed; parent network credentials, inherited environment, and "
    "hidden evaluator data remain unavailable to the arm"
)
OUTER_PROBE_ID = "deliver-v12.34-outer-sandbox-v1"
PREFLIGHT_PROBE_ID = "deliver-v12.34-real-preflight-v1"
OUTER_CLAIMS = frozenset({
    "stage_read_allowed",
    "stage_write_allowed",
    "sibling_read_denied",
    "sibling_write_denied",
    "evaluator_read_denied",
    "evaluator_write_denied",
    "other_temp_read_denied",
    "other_temp_write_denied",
    "home_read_denied",
    "home_write_denied",
    "volume_read_denied",
    "volume_write_denied",
    "external_sentinel_unchanged",
})
PREFLIGHT_CLAIMS = frozenset({
    "isolated_codex_home",
    "isolated_home",
    "isolated_tmpdir",
    "empty_inherited_environment",
    "credential_copy_boundary",
    "pinned_bundled_codex_identity",
    "required_codex_connectivity",
})
PROBE_SPECS = {
    "outer-sandbox": (OUTER_PROBE_ID, OUTER_CLAIMS),
    "real-preflight": (PREFLIGHT_PROBE_ID, PREFLIGHT_CLAIMS),
}
PROBE_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "LANG": "en_US.UTF-8",
    "LC_ALL": "en_US.UTF-8",
    "PYTHONSAFEPATH": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
}

MUTABLE_TOP_LEVEL_FIELDS = frozenset({
    "status",
    "readiness_predecessor_commit",
    "readiness_predecessor_sha256",
    "independent_review_record_path",
    "independent_review_record_sha256",
    "trusted_host_isolation_receipt_path",
    "trusted_host_isolation_receipt_sha256",
    "independent_review_result_kind",
    "private_independent_reviewed_source_commit",
    "private_independent_reviewed_final_commit",
    "trusted_host_isolation_result_kind",
    "private_trusted_host_isolation_tested_source_commit",
    "private_trusted_host_isolation_tested_final_commit",
    "independent_semantic_review_status",
    "hidden_material_noninterference_independent_review_status",
    "judge_packet_recursive_identity_scan_independent_review_status",
    "content_control_plane_separation_independent_review_status",
    "case_grouping_independent_review_status",
    "zero_static_coverage_independent_review_status",
    "comparison_runtime_review_status",
    "durable_comparison_lifecycle_independent_review_status",
    "trusted_root_independent_review_status",
    "sealed_artifact_derivation_independent_review_status",
    "isolation_probe_status",
})
MUTABLE_NESTED_FIELDS = {
    "proportionality": frozenset({"safe_grouping_review_status"}),
    "coverage_credit_policy": frozenset({"independent_review_status"}),
}
INDEPENDENT_PASS_FIELDS = (
    "independent_semantic_review_status",
    "hidden_material_noninterference_independent_review_status",
    "judge_packet_recursive_identity_scan_independent_review_status",
    "content_control_plane_separation_independent_review_status",
    "case_grouping_independent_review_status",
    "zero_static_coverage_independent_review_status",
    "comparison_runtime_review_status",
    "durable_comparison_lifecycle_independent_review_status",
    "trusted_root_independent_review_status",
    "sealed_artifact_derivation_independent_review_status",
)
REVIEW_CHECKS = frozenset({
    "semantic_review",
    "hidden_noninterference",
    "recursive_identity_blinding",
    "content_control_plane_separation",
    "case_disjointness",
    "runtime_controls",
    "lifecycle_controls",
    "public_bindings",
})
ISOLATION_CHECKS = OUTER_CLAIMS | PREFLIGHT_CLAIMS


class ReadinessTransitionError(RuntimeError):
    """Raised when a readiness state or transition is not authentic."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json_bytes(value: bytes, label: str) -> dict[str, Any]:
    try:
        result = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReadinessTransitionError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(result, dict):
        raise ReadinessTransitionError(f"{label} must be an object")
    return result


def canonical_file_bytes(document: dict[str, Any]) -> bytes:
    return json.dumps(document, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def git(repo: Path, arguments: list[str], *, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *arguments], cwd=repo, check=False, capture_output=True, text=not binary,
    )
    if result.returncode:
        stderr = result.stderr.decode(errors="replace") if binary else result.stderr
        raise ReadinessTransitionError(
            f"git {' '.join(arguments)} failed: {stderr.strip()}"
        )
    return result.stdout if binary else result.stdout.strip()


def _commit(repo: Path, ref: str) -> str:
    value = str(git(repo, ["rev-parse", f"{ref}^{{commit}}"])).strip()
    if not HEX40.fullmatch(value):
        raise ReadinessTransitionError("readiness Git commit is malformed")
    return value


def _blob(repo: Path, commit: str, relative_path: str) -> bytes:
    return bytes(git(repo, ["cat-file", "blob", f"{commit}:{relative_path}"], binary=True))


def _tree(repo: Path, commit: str) -> str:
    value = str(git(repo, ["rev-parse", f"{commit}^{{tree}}"]))
    if not HEX40.fullmatch(value):
        raise ReadinessTransitionError("public Git tree is malformed")
    return value


def _ls_tree_entry(repo: Path, commit: str, relative_path: str) -> tuple[str, str]:
    output = str(git(repo, ["ls-tree", commit, "--", relative_path]))
    lines = output.splitlines()
    if len(lines) != 1:
        raise ReadinessTransitionError(f"dependency is missing or ambiguous: {relative_path}")
    try:
        metadata, listed_path = lines[0].split("\t", 1)
        mode, kind, object_id = metadata.split()
    except ValueError as exc:
        raise ReadinessTransitionError(
            f"dependency Git metadata is malformed: {relative_path}"
        ) from exc
    if (
        listed_path != relative_path
        or kind != "blob"
        or mode not in {"100644", "100755"}
        or not HEX40.fullmatch(object_id)
    ):
        raise ReadinessTransitionError(
            f"dependency is not a regular tracked Git blob: {relative_path}"
        )
    return mode, object_id


def _last_touch(repo: Path, commit: str, relative_path: str) -> str:
    value = str(git(repo, ["log", "-1", "--format=%H", commit, "--", relative_path])).strip()
    if not HEX40.fullmatch(value):
        raise ReadinessTransitionError(f"no committed origin for {relative_path}")
    return value


def _file_mode(path: Path) -> str:
    return "100755" if stat.S_IMODE(path.stat().st_mode) & 0o111 else "100644"


def _require_regular_checkout_file(repo: Path, relative_path: str) -> Path:
    path = repo / relative_path
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ReadinessTransitionError(f"dependency is unavailable: {relative_path}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ReadinessTransitionError(
            f"dependency must be a regular non-symlink file: {relative_path}"
        )
    return path


def _dependency_observations(repo: Path, ref: str) -> list[dict[str, str]]:
    commit = _commit(repo, ref)
    observations: list[dict[str, str]] = []
    for relative_path in sorted(DEPENDENCY_OBSERVED_ROLES):
        mode, object_id = _ls_tree_entry(repo, commit, relative_path)
        blob = _blob(repo, commit, relative_path)
        path = _require_regular_checkout_file(repo, relative_path)
        if path.read_bytes() != blob or _file_mode(path) != mode:
            raise ReadinessTransitionError(
                f"dependency checkout bytes or mode differ from Git: {relative_path}"
            )
        observations.append({
            "path": relative_path,
            "role": DEPENDENCY_OBSERVED_ROLES[relative_path],
            "sha256": sha256_bytes(blob),
            "git_blob": object_id,
            "git_mode": mode,
            "last_touch_commit": _last_touch(repo, commit, relative_path),
        })
    return observations


def _manifest_payload(document: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != "manifest_sha256"}


def _stdlib_only_imports(source: bytes, label: str) -> None:
    try:
        tree = ast.parse(source, filename=label)
    except SyntaxError as exc:
        raise ReadinessTransitionError(f"dependency source is invalid Python: {label}") from exc
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    allowed = set(sys.stdlib_module_names) | {"__future__"}
    unexpected = sorted(roots - allowed)
    if unexpected:
        raise ReadinessTransitionError(
            f"unlisted non-stdlib import in {label}: {', '.join(unexpected)}"
        )


def _validate_dependency_source_closure(entries: list[dict[str, str]], blobs: dict[str, bytes]) -> None:
    if [entry["path"] for entry in entries] != sorted(DEPENDENCY_ROLES):
        raise ReadinessTransitionError("dependency manifest entry set is not exact")
    for relative_path in sorted(PYTHON_SOURCE_DEPENDENCIES):
        _stdlib_only_imports(blobs[relative_path], relative_path)
    probe_source = blobs[PROBE_RELATIVE_PATH].decode("utf-8")
    transition_source = blobs[TRANSITION_RELATIVE_PATH].decode("utf-8")
    launcher_source = blobs[PRIVATE_RUNTIME_LAUNCHER_RELATIVE_PATH].decode("utf-8")
    harness_source = blobs[HARNESS_RELATIVE_PATH].decode("utf-8")
    bundle_validator_source = blobs[CASE_BUNDLE_VALIDATOR_RELATIVE_PATH].decode("utf-8")
    if (
        probe_source.count("spec_from_file_location(") != 1
        or transition_source.count("spec_from_file_location(") != 4
        or "HARNESS_RELATIVE_PATH" not in probe_source
        or "CASE_BUNDLE_VALIDATOR_RELATIVE_PATH" not in transition_source
        or "--closure-root" not in probe_source
        or "--dependency-manifest-sha256" not in probe_source
        or "-I" not in transition_source
        or "PROBE_ENVIRONMENT" not in transition_source
        or "str(python), \"-I\", \"-B\", \"-c\"" not in launcher_source
        or "--untracked-files=all" not in launcher_source
        or "PRIVATE_RUNTIME_ROLES" not in launcher_source
        or "subprocess" not in harness_source
        or "validate_bundle(" not in bundle_validator_source
    ):
        raise ReadinessTransitionError("dependency execution closure source audit failed")


def _validate_dependency_manifest_document(
    document: dict[str, Any], blobs: dict[str, bytes], modes: dict[str, str],
) -> None:
    expected_fields = {
        "schema_version", "oracle_version", "manifest_kind", "entry_count", "entries",
        "entries_sha256", "closure_policy", "manifest_sha256",
    }
    entries = document.get("entries")
    if (
        set(document) != expected_fields
        or document.get("schema_version") != 1
        or document.get("oracle_version") != ORACLE_VERSION
        or document.get("manifest_kind")
        != "root_isolation_repo_local_execution_and_data_dependency_closure"
        or not isinstance(entries, list)
        or document.get("entry_count") != len(entries)
        or document.get("entries_sha256") != sha256_bytes(canonical_json(entries))
        or document.get("closure_policy")
        != root_isolation_contract()["dependency_closure_policy"]
        or document.get("manifest_sha256")
        != sha256_bytes(canonical_json(_manifest_payload(document)))
    ):
        raise ReadinessTransitionError("dependency manifest schema or digest is invalid")
    expected_entries = [
        {
            "path": path,
            "role": DEPENDENCY_ROLES[path],
            "sha256": sha256_bytes(blobs[path]),
            "git_mode": modes[path],
        }
        for path in sorted(DEPENDENCY_ROLES)
    ]
    if entries != expected_entries:
        raise ReadinessTransitionError("dependency manifest has missing, extra, or drifted entries")
    _validate_dependency_source_closure(entries, blobs)


def build_dependency_manifest(repo: Path) -> dict[str, Any]:
    blobs: dict[str, bytes] = {}
    modes: dict[str, str] = {}
    for relative_path in sorted(DEPENDENCY_ROLES):
        path = _require_regular_checkout_file(repo, relative_path)
        blobs[relative_path] = path.read_bytes()
        modes[relative_path] = _file_mode(path)
    entries = [
        {
            "path": path,
            "role": DEPENDENCY_ROLES[path],
            "sha256": sha256_bytes(blobs[path]),
            "git_mode": modes[path],
        }
        for path in sorted(DEPENDENCY_ROLES)
    ]
    document: dict[str, Any] = {
        "schema_version": 1,
        "oracle_version": ORACLE_VERSION,
        "manifest_kind": "root_isolation_repo_local_execution_and_data_dependency_closure",
        "entry_count": len(entries),
        "entries": entries,
        "entries_sha256": sha256_bytes(canonical_json(entries)),
        "closure_policy": root_isolation_contract()["dependency_closure_policy"],
    }
    document["manifest_sha256"] = sha256_bytes(canonical_json(document))
    _validate_dependency_manifest_document(document, blobs, modes)
    return document


def dependency_binding(repo: Path, ref: str) -> dict[str, Any]:
    commit = _commit(repo, ref)
    observations = _dependency_observations(repo, commit)
    blobs = {
        entry["path"]: _blob(repo, commit, entry["path"])
        for entry in observations if entry["path"] in DEPENDENCY_ROLES
    }
    modes = {
        entry["path"]: entry["git_mode"]
        for entry in observations if entry["path"] in DEPENDENCY_ROLES
    }
    raw = _blob(repo, commit, DEPENDENCY_MANIFEST_RELATIVE_PATH)
    manifest = load_json_bytes(raw, "root isolation dependency manifest")
    _validate_dependency_manifest_document(manifest, blobs, modes)
    return {
        "manifest_path": DEPENDENCY_MANIFEST_RELATIVE_PATH,
        "manifest_sha256": sha256_bytes(raw),
        "entries_sha256": sha256_bytes(canonical_json(observations)),
        "controller_commit": commit,
        "controller_tree": _tree(repo, commit),
        "entries": observations,
    }


def _parent(repo: Path, commit: str) -> str:
    return _commit(repo, f"{commit}^")


def _previous_readiness_commit(repo: Path, commit: str) -> str:
    values = str(git(
        repo, ["log", "-2", "--format=%H", commit, "--", READINESS_RELATIVE_PATH]
    )).splitlines()
    if len(values) != 2 or not HEX40.fullmatch(values[1]):
        raise ReadinessTransitionError("readiness predecessor commit is unavailable")
    return values[1]


def immutable_projection(document: dict[str, Any]) -> dict[str, Any]:
    projection: dict[str, Any] = {}
    for key, value in document.items():
        if key in MUTABLE_TOP_LEVEL_FIELDS or key == "immutable_readiness_sha256":
            continue
        if key in MUTABLE_NESTED_FIELDS:
            if not isinstance(value, dict):
                raise ReadinessTransitionError(f"readiness {key} must be an object")
            projection[key] = {
                nested_key: nested_value
                for nested_key, nested_value in value.items()
                if nested_key not in MUTABLE_NESTED_FIELDS[key]
            }
        else:
            projection[key] = value
    return projection


def immutable_digest(document: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(immutable_projection(document)))


def root_isolation_contract() -> dict[str, Any]:
    return {
        "operation": "run-root-isolation",
        "public_repository": str(PUBLIC_REPOSITORY),
        "probe_path": PROBE_RELATIVE_PATH,
        "dependency_manifest_path": DEPENDENCY_MANIFEST_RELATIVE_PATH,
        "dependency_paths": sorted(DEPENDENCY_ROLES),
        "dependency_roles": dict(sorted(DEPENDENCY_ROLES.items())),
        "dependency_closure_policy": {
            "normal_imports": "stdlib_only_ast_validated",
            "dynamic_imports": {
                PROBE_RELATIVE_PATH: [HARNESS_RELATIVE_PATH],
                TRANSITION_RELATIVE_PATH: [CASE_BUNDLE_VALIDATOR_RELATIVE_PATH],
            },
            "repo_local_subprocess_entrypoints": [
                STANDALONE_BUNDLE_VALIDATOR_RELATIVE_PATH,
            ],
            "repo_local_data_inputs": list(REPO_LOCAL_DATA_INPUTS),
            "unlisted_repo_local_resolution_allowed": False,
            "execution_source": "verified_git_blobs_in_sealed_staging",
            "python_isolated_mode_required": True,
            "caller_pythonpath_allowed": False,
            "private_runtime_launch": {
                "launcher": PRIVATE_RUNTIME_LAUNCHER_RELATIVE_PATH,
                "source": "exact_private_final_git_blobs",
                "private_worktree_must_include_no_untracked_files": True,
                "private_head_must_equal_final": True,
            },
        },
        "private_evaluator_repository": str(PRIVATE_EVALUATOR_REPOSITORY),
        "probe_ids": [OUTER_PROBE_ID, PREFLIGHT_PROBE_ID],
        "required_claims": {
            OUTER_PROBE_ID: sorted(OUTER_CLAIMS),
            PREFLIGHT_PROBE_ID: sorted(PREFLIGHT_CLAIMS),
        },
        "network_policy": NETWORK_POLICY,
        "caller_receipt_or_pass_flags_allowed": False,
        "ready_transition_file_allowlist": [
            READINESS_RELATIVE_PATH,
            ISOLATION_RELATIVE_PATH,
        ],
    }


def _validate_common(document: dict[str, Any]) -> None:
    if document.get("schema_version") != SCHEMA_VERSION or document.get("oracle_version") != ORACLE_VERSION:
        raise ReadinessTransitionError("readiness version is not v12.34")
    if document.get("status") not in {"author_ready", "independent_review_pass", "ready"}:
        raise ReadinessTransitionError("readiness status is invalid")
    if document.get("immutable_readiness_sha256") != immutable_digest(document):
        raise ReadinessTransitionError("immutable readiness projection digest is invalid")
    for field in ("private_evaluator_source_commit", "private_evaluator_commit"):
        if not HEX40.fullmatch(str(document.get(field))):
            raise ReadinessTransitionError(f"{field} is malformed")
    if (
        document.get("private_runtime_launcher_path")
        != PRIVATE_RUNTIME_LAUNCHER_RELATIVE_PATH
        or document.get("private_runtime_launcher_sha256")
        != document.get("frozen_public_file_digests", {}).get(
            PRIVATE_RUNTIME_LAUNCHER_RELATIVE_PATH
        )
        or document.get("private_runtime_closure_manifest_path")
        != PRIVATE_RUNTIME_CLOSURE_MANIFEST_RELATIVE_PATH
        or not HEX64.fullmatch(
            str(document.get("private_runtime_closure_manifest_sha256"))
        )
    ):
        raise ReadinessTransitionError("private runtime launch binding is malformed")
    if document.get("root_isolation_contract") != root_isolation_contract():
        raise ReadinessTransitionError("root isolation contract is not exact")
    if (
        document.get("independent_case_bundle_interface_path")
        != BUNDLE_INTERFACE_RELATIVE_PATH
        or not HEX64.fullmatch(
            str(document.get("independent_case_bundle_interface_sha256"))
        )
        or not HEX40.fullmatch(
            str(document.get("independent_case_bundle_source_commit"))
        )
        or document.get("independent_case_bundle_controller_commit")
        != "5bdd3d012e9a85da91747b975971f25c3c5bfe55"
        or not HEX40.fullmatch(str(document.get("independent_case_bundle_source_tree")))
        or not HEX64.fullmatch(
            str(document.get("independent_case_bundle_manifest_sha256"))
        )
        or not HEX64.fullmatch(
            str(document.get("independent_case_bundle_validation_sha256"))
        )
        or document.get("independent_case_bundle_complete_import_status") != "pass"
    ):
        raise ReadinessTransitionError("independent case bundle binding is malformed")
    frozen_digests = document.get("frozen_public_file_digests")
    frozen_commits = document.get("frozen_public_file_commits")
    if (
        not isinstance(frozen_digests, dict)
        or not frozen_digests
        or set(frozen_digests) != set(frozen_commits or {})
        or READINESS_RELATIVE_PATH in frozen_digests
        or REVIEW_RELATIVE_PATH in frozen_digests
        or ISOLATION_RELATIVE_PATH in frozen_digests
    ):
        raise ReadinessTransitionError("frozen public file maps are not exact")
    required_frozen_paths = set(DEPENDENCY_ROLES) | {DEPENDENCY_MANIFEST_RELATIVE_PATH}
    if not required_frozen_paths.issubset(frozen_digests):
        raise ReadinessTransitionError("root isolation dependency closure is not fully frozen")
    if (
        frozen_digests.get(BUNDLE_INTERFACE_RELATIVE_PATH)
        != document.get("independent_case_bundle_interface_sha256")
    ):
        raise ReadinessTransitionError("independent case bundle interface is not frozen")
    for path, digest in frozen_digests.items():
        if (
            not isinstance(path, str)
            or not path.startswith("evals/deliver/")
            or not HEX64.fullmatch(str(digest))
            or not HEX40.fullmatch(str(frozen_commits[path]))
        ):
            raise ReadinessTransitionError("frozen public file binding is malformed")
    binding = document.get("root_isolation_dependency_binding")
    if (
        not isinstance(binding, dict)
        or set(binding) != {
            "manifest_path", "manifest_sha256", "entries_sha256", "controller_commit",
            "controller_tree", "entries",
        }
        or binding.get("manifest_path") != DEPENDENCY_MANIFEST_RELATIVE_PATH
        or not HEX64.fullmatch(str(binding.get("manifest_sha256")))
        or not HEX64.fullmatch(str(binding.get("entries_sha256")))
        or binding.get("controller_commit") != document.get("public_adapter_introducing_commit")
        or not HEX40.fullmatch(str(binding.get("controller_tree")))
        or not isinstance(binding.get("entries"), list)
    ):
        raise ReadinessTransitionError("root isolation dependency binding is malformed")


def _load_case_bundle_validator() -> Any:
    path = _require_regular_checkout_file(PUBLIC_REPOSITORY, CASE_BUNDLE_VALIDATOR_RELATIVE_PATH)
    spec = importlib.util.spec_from_file_location("deliver_v1234_case_bundle_validator", path)
    if spec is None or spec.loader is None:
        raise ReadinessTransitionError("case bundle validator cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_private_runtime_launcher() -> Any:
    path = _require_regular_checkout_file(
        PUBLIC_REPOSITORY, PRIVATE_RUNTIME_LAUNCHER_RELATIVE_PATH
    )
    spec = importlib.util.spec_from_file_location("deliver_v1234_private_runtime_launcher", path)
    if spec is None or spec.loader is None:
        raise ReadinessTransitionError("private runtime launcher cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _verify_private_evaluator(document: dict[str, Any]) -> None:
    repo = PRIVATE_EVALUATOR_REPOSITORY.resolve(strict=True)
    if repo.is_symlink() or not (repo / ".git").exists():
        raise ReadinessTransitionError("private evaluator repository is unavailable")
    source = document["private_evaluator_source_commit"]
    final = document["private_evaluator_commit"]
    if _commit(repo, source) != source or _commit(repo, final) != final:
        raise ReadinessTransitionError("private evaluator commits do not resolve exactly")
    if _commit(repo, "HEAD") != final:
        raise ReadinessTransitionError("private evaluator HEAD is not the frozen final commit")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source, final],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if ancestor.returncode:
        raise ReadinessTransitionError("private evaluator source is not an ancestor of final")
    if str(git(repo, ["status", "--porcelain=v1", "--untracked-files=all"])).strip():
        raise ReadinessTransitionError(
            "private evaluator state is not completely clean, including untracked files"
        )
    try:
        launcher = _load_private_runtime_launcher()
        launcher.require_clean_exact_private_final(repo, final)
        launcher.validate_manifest(
            repo, final, document["private_runtime_closure_manifest_sha256"]
        )
    except Exception as exc:
        raise ReadinessTransitionError("private runtime closure is not authentic") from exc
    manifest_path = "private-oracle/source-provenance-manifest.json"
    manifest = load_json_bytes(_blob(repo, final, manifest_path), "private source provenance")
    expected_fields = {
        "schema_version", "oracle_version", "private_evaluator_source_commit",
        "reviewed_logic_unchanged_from_source", "reviewed_path_count",
        "reviewed_paths_sha256", "reviewed_paths",
    }
    entries = manifest.get("reviewed_paths")
    if (
        set(manifest) != expected_fields
        or manifest.get("schema_version") != 1
        or manifest.get("oracle_version") != ORACLE_VERSION
        or manifest.get("private_evaluator_source_commit") != source
        or manifest.get("reviewed_logic_unchanged_from_source") is not True
        or not isinstance(entries, list)
        or manifest.get("reviewed_path_count") != len(entries)
        or manifest.get("reviewed_paths_sha256") != sha256_bytes(canonical_json(entries))
    ):
        raise ReadinessTransitionError("private source provenance is not exactly bound")
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "sha256"}
            or not isinstance(entry.get("path"), str)
            or not entry["path"].startswith("private-oracle/")
            or not HEX64.fullmatch(str(entry.get("sha256")))
            or sha256_bytes(_blob(repo, source, entry["path"])) != entry["sha256"]
            or sha256_bytes(_blob(repo, final, entry["path"])) != entry["sha256"]
        ):
            raise ReadinessTransitionError("private reviewed source bytes drifted")
    validation_path = "private-oracle/bundle-validation.json"
    validation_raw = _blob(repo, final, validation_path)
    if sha256_bytes(validation_raw) != document["independent_case_bundle_validation_sha256"]:
        raise ReadinessTransitionError("private bundle validation artifact digest drifted")
    validation = load_json_bytes(validation_raw, "private bundle validation")
    try:
        recomputed = _load_case_bundle_validator().validate_bundle(
            PUBLIC_REPOSITORY,
            document["independent_case_bundle_controller_commit"],
            repo,
            document["independent_case_bundle_source_commit"],
            repo / "private-oracle",
        )
    except Exception as exc:
        raise ReadinessTransitionError("independent case bundle validation failed") from exc
    if (
        validation != recomputed
        or recomputed.get("bundle_source_commit")
        != document["independent_case_bundle_source_commit"]
        or recomputed.get("bundle_source_tree")
        != document["independent_case_bundle_source_tree"]
        or recomputed.get("bundle_manifest_sha256")
        != document["independent_case_bundle_manifest_sha256"]
        or recomputed.get("controller_commit")
        != document["independent_case_bundle_controller_commit"]
        or recomputed.get("public_file_sha256", {}).get(BUNDLE_INTERFACE_RELATIVE_PATH)
        != sha256_bytes(
            _blob(
                PUBLIC_REPOSITORY,
                document["independent_case_bundle_controller_commit"],
                BUNDLE_INTERFACE_RELATIVE_PATH,
            )
        )
    ):
        raise ReadinessTransitionError(
            "standalone, integrated, and readiness bundle bindings do not reconcile"
        )


def _validate_frozen_files(repo: Path, ref: str, document: dict[str, Any]) -> None:
    commit = _commit(repo, ref)
    controller = _commit(repo, document["public_adapter_introducing_commit"])
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", controller, commit],
        cwd=repo, check=False, capture_output=True,
    )
    if ancestor.returncode:
        raise ReadinessTransitionError("public controller is not an ancestor of readiness state")
    for path, digest in document["frozen_public_file_digests"].items():
        if sha256_bytes(_blob(repo, commit, path)) != digest:
            raise ReadinessTransitionError(f"frozen public file digest drifted: {path}")
        if _last_touch(repo, commit, path) != document["frozen_public_file_commits"][path]:
            raise ReadinessTransitionError(f"frozen public file was touched after freeze: {path}")
    expected_binding = dependency_binding(repo, controller)
    if document.get("root_isolation_dependency_binding") != expected_binding:
        raise ReadinessTransitionError("root isolation dependency binding is not authentic")
    current_observations = _dependency_observations(repo, commit)
    if current_observations != expected_binding["entries"]:
        raise ReadinessTransitionError(
            "root isolation dependency closure changed after controller freeze"
        )


def _readiness_at(repo: Path, commit: str) -> tuple[dict[str, Any], bytes]:
    raw = _blob(repo, commit, READINESS_RELATIVE_PATH)
    return load_json_bytes(raw, "committed readiness"), raw


def verify_controller_frozen(repo: Path, ref: str = "HEAD") -> dict[str, Any]:
    """Verify the Phase-A controller without claiming evaluator readiness."""
    controller = _commit(repo, ref)
    if _last_touch(repo, controller, READINESS_RELATIVE_PATH) != controller:
        raise ReadinessTransitionError(
            "controller-frozen scaffold must be committed with the controller"
        )
    document, raw = _readiness_at(repo, controller)
    expected = {
        "schema_version": SCHEMA_VERSION,
        "oracle_version": ORACLE_VERSION,
        "status": "controller_frozen_awaiting_independent_bundle",
        "public_adapter_identifier": "deliver_plain_language_v12",
        "independent_case_bundle_interface_path": BUNDLE_INTERFACE_RELATIVE_PATH,
        "independent_case_bundle_interface_sha256": sha256_bytes(
            _blob(repo, controller, BUNDLE_INTERFACE_RELATIVE_PATH)
        ),
        "hidden_case_authoring_performed": False,
        "private_evaluator_freeze_performed": False,
        "independent_review_performed": False,
        "trusted_host_isolation_performed": False,
        "official_arm_execution_performed": False,
        "official_judge_execution_performed": False,
    }
    if document != expected or raw != canonical_file_bytes(expected):
        raise ReadinessTransitionError("controller-frozen scaffold is not exact")
    interface = load_json_bytes(
        _blob(repo, controller, BUNDLE_INTERFACE_RELATIVE_PATH), "bundle interface"
    )
    public_paths = interface.get("public_binding_paths")
    expected_paths = sorted((*DEPENDENCY_ROLES, DEPENDENCY_MANIFEST_RELATIVE_PATH))
    carry = interface.get("carried_bundle_binding")
    if (
        interface.get("schema_version") != 2
        or interface.get("oracle_version") != ORACLE_VERSION
        or interface.get("bundle_oracle_version")
        != "deliver-plain-language-v12.32"
        or interface.get("integrated_validator_path")
        != CASE_BUNDLE_VALIDATOR_RELATIVE_PATH
        or public_paths != expected_paths
        or not isinstance(carry, dict)
        or carry.get("bundle_controller_commit")
        != "5bdd3d012e9a85da91747b975971f25c3c5bfe55"
        or carry.get("bundle_source_commit")
        != "ab2ce57b733c3f04629121cdf3e6dce845431240"
        or carry.get("bundle_source_tree")
        != "8b3f4c18655ee77f6d3f09f52ce125abc0457509"
        or carry.get("bundle_manifest_sha256")
        != "97f43a97aa462c1be94ef679a008fff7271f2467e4b1b7f1b4a76f009c7b9956"
        or carry.get("manifest_payload_sha256")
        != "8297e7e0a5aefa08a545eeeb97d456702aea4973b821ecba424f4a9ef58db47d"
        or carry.get("official_arm_execution_performed") is not False
        or carry.get("official_judge_execution_performed") is not False
    ):
        raise ReadinessTransitionError("controller bundle interface public closure is not exact")
    dependency_binding(repo, controller)
    digests: dict[str, str] = {}
    for relative_path in public_paths:
        source = _blob(repo, controller, relative_path)
        live = _require_regular_checkout_file(repo, relative_path)
        mode, _ = _ls_tree_entry(repo, controller, relative_path)
        if live.read_bytes() != source or _file_mode(live) != mode:
            raise ReadinessTransitionError(
                f"controller public binding drifted: {relative_path}"
            )
        digests[relative_path] = sha256_bytes(source)
    return {
        "status": document["status"],
        "commit": controller,
        "tree": _tree(repo, controller),
        "sha256": sha256_bytes(raw),
        "interface_sha256": document["independent_case_bundle_interface_sha256"],
        "public_file_sha256": digests,
    }


def _record_at(repo: Path, commit: str, relative_path: str, label: str) -> tuple[dict[str, Any], bytes]:
    raw = _blob(repo, commit, relative_path)
    return load_json_bytes(raw, label), raw


def _changed_paths(repo: Path, commit: str) -> set[str]:
    parent = _parent(repo, commit)
    output = str(git(repo, ["diff", "--name-only", parent, commit])).splitlines()
    return {item for item in output if item}


def _same_immutable(before: dict[str, Any], after: dict[str, Any]) -> None:
    if immutable_projection(before) != immutable_projection(after):
        raise ReadinessTransitionError("readiness immutable fields changed during transition")


def _require_pending_review(document: dict[str, Any]) -> None:
    if any(document.get(field) != "pending_independent_review" for field in INDEPENDENT_PASS_FIELDS):
        raise ReadinessTransitionError("author readiness review gates are not pending")
    if document.get("proportionality", {}).get("safe_grouping_review_status") != "pending_independent_review":
        raise ReadinessTransitionError("author readiness proportionality review is not pending")
    if document.get("coverage_credit_policy", {}).get("independent_review_status") != "pending_independent_review":
        raise ReadinessTransitionError("author readiness coverage review is not pending")


def _require_passed_review(document: dict[str, Any]) -> None:
    if any(document.get(field) != "pass" for field in INDEPENDENT_PASS_FIELDS):
        raise ReadinessTransitionError("independent review gates are not passed")
    if document.get("proportionality", {}).get("safe_grouping_review_status") != "pass":
        raise ReadinessTransitionError("proportionality review is not passed")
    if document.get("coverage_credit_policy", {}).get("independent_review_status") != "pass":
        raise ReadinessTransitionError("coverage review is not passed")


def _validate_author_document(document: dict[str, Any]) -> None:
    _validate_common(document)
    if document["status"] != "author_ready":
        raise ReadinessTransitionError("expected author_ready predecessor")
    _require_pending_review(document)
    expected = {
        "readiness_predecessor_commit": "pending_transition",
        "readiness_predecessor_sha256": "pending_transition",
        "independent_review_record_path": REVIEW_RELATIVE_PATH,
        "independent_review_record_sha256": "pending_independent_review",
        "trusted_host_isolation_receipt_path": ISOLATION_RELATIVE_PATH,
        "trusted_host_isolation_receipt_sha256": "pending_trusted_host_isolation",
        "independent_review_result_kind": "pending_independent_review",
        "private_independent_reviewed_source_commit": "pending_independent_review",
        "private_independent_reviewed_final_commit": "pending_independent_review",
        "trusted_host_isolation_result_kind": "pending_trusted_host_isolation",
        "private_trusted_host_isolation_tested_source_commit": "pending_trusted_host_isolation",
        "private_trusted_host_isolation_tested_final_commit": "pending_trusted_host_isolation",
        "isolation_probe_status": "pending_trusted_host_isolation",
    }
    if any(document.get(key) != value for key, value in expected.items()):
        raise ReadinessTransitionError("author readiness mutable fields are not the frozen pending state")


def _validate_review_record(
    record: dict[str, Any], predecessor_commit: str, predecessor_digest: str,
    readiness: dict[str, Any],
) -> None:
    expected_fields = {
        "schema_version", "oracle_version", "record_kind", "result",
        "reviewer_allocation_id", "reviewer_nonce", "private_evaluator_source_commit",
        "private_evaluator_final_commit", "public_controller_commit",
        "predecessor_readiness_commit", "predecessor_readiness_sha256",
        "immutable_readiness_sha256", "reviewed_public_file_digests_sha256", "checks",
    }
    checks = record.get("checks")
    expected_digest = sha256_bytes(canonical_json(readiness["frozen_public_file_digests"]))
    if (
        set(record) != expected_fields
        or record.get("schema_version") != 1
        or record.get("oracle_version") != ORACLE_VERSION
        or record.get("record_kind") != "independent_review"
        or record.get("result") != "pass"
        or not isinstance(record.get("reviewer_allocation_id"), str)
        or not record["reviewer_allocation_id"].strip()
        or not HEX64.fullmatch(str(record.get("reviewer_nonce")))
        or record.get("private_evaluator_source_commit") != readiness["private_evaluator_source_commit"]
        or record.get("private_evaluator_final_commit") != readiness["private_evaluator_commit"]
        or record.get("public_controller_commit") != readiness["public_adapter_introducing_commit"]
        or record.get("predecessor_readiness_commit") != predecessor_commit
        or record.get("predecessor_readiness_sha256") != predecessor_digest
        or record.get("immutable_readiness_sha256") != readiness["immutable_readiness_sha256"]
        or record.get("reviewed_public_file_digests_sha256") != expected_digest
        or not isinstance(checks, dict)
        or set(checks) != REVIEW_CHECKS
        or any(value != "pass" for value in checks.values())
    ):
        raise ReadinessTransitionError("independent reviewer record is not exactly bound")


def _validate_isolation_receipt(
    receipt: dict[str, Any], predecessor_commit: str, predecessor_digest: str,
    review_record_sha256: str, readiness: dict[str, Any],
) -> None:
    expected_fields = {
        "schema_version", "oracle_version", "record_kind", "result",
        "root_observed_operation", "isolation_nonce", "private_evaluator_source_commit",
        "private_evaluator_final_commit",
        "public_controller_commit", "predecessor_readiness_commit",
        "predecessor_readiness_sha256", "independent_review_record_sha256",
        "independent_review_transition_commit", "immutable_readiness_sha256",
        "root_isolation_contract_sha256", "network_policy", "python_identity", "probes",
        "dependency_manifest_sha256", "dependency_pre_observations",
        "dependency_pre_observations_sha256", "dependency_post_observations",
        "dependency_post_observations_sha256", "staged_dependency_observations",
        "staged_dependency_observations_sha256",
    }
    python_identity = receipt.get("python_identity")
    probes = receipt.get("probes")
    if (
        set(receipt) != expected_fields
        or receipt.get("schema_version") != 2
        or receipt.get("oracle_version") != ORACLE_VERSION
        or receipt.get("record_kind") != "trusted_host_isolation"
        or receipt.get("result") != "pass"
        or receipt.get("root_observed_operation") != "run-root-isolation"
        or not HEX64.fullmatch(str(receipt.get("isolation_nonce")))
        or receipt.get("private_evaluator_source_commit") != readiness["private_evaluator_source_commit"]
        or receipt.get("private_evaluator_final_commit") != readiness["private_evaluator_commit"]
        or receipt.get("public_controller_commit") != readiness["public_adapter_introducing_commit"]
        or receipt.get("predecessor_readiness_commit") != predecessor_commit
        or receipt.get("predecessor_readiness_sha256") != predecessor_digest
        or receipt.get("independent_review_record_sha256") != review_record_sha256
        or receipt.get("independent_review_transition_commit") != predecessor_commit
        or receipt.get("immutable_readiness_sha256") != readiness["immutable_readiness_sha256"]
        or receipt.get("root_isolation_contract_sha256")
        != sha256_bytes(canonical_json(readiness["root_isolation_contract"]))
        or receipt.get("network_policy") != NETWORK_POLICY
        or not isinstance(python_identity, dict)
        or set(python_identity) != {"path", "version", "sha256"}
        or not isinstance(python_identity.get("path"), str)
        or not Path(python_identity["path"]).is_absolute()
        or not isinstance(python_identity.get("version"), str)
        or not python_identity["version"].strip()
        or not HEX64.fullmatch(str(python_identity.get("sha256")))
        or not isinstance(probes, list)
        or len(probes) != len(PROBE_SPECS)
    ):
        raise ReadinessTransitionError("trusted-host isolation receipt is not exactly bound")
    binding = readiness["root_isolation_dependency_binding"]
    expected_observations = binding["entries"]
    staged_observations = [
        {
            "path": entry["path"], "role": entry["role"],
            "sha256": entry["sha256"], "git_mode": entry["git_mode"],
        }
        for entry in expected_observations
    ]
    if (
        receipt.get("dependency_manifest_sha256") != binding["manifest_sha256"]
        or receipt.get("dependency_pre_observations") != expected_observations
        or receipt.get("dependency_post_observations") != expected_observations
        or receipt.get("staged_dependency_observations") != staged_observations
        or receipt.get("dependency_pre_observations_sha256")
        != sha256_bytes(canonical_json(expected_observations))
        or receipt.get("dependency_post_observations_sha256")
        != sha256_bytes(canonical_json(expected_observations))
        or receipt.get("staged_dependency_observations_sha256")
        != sha256_bytes(canonical_json(staged_observations))
    ):
        raise ReadinessTransitionError("trusted-host dependency closure evidence is invalid")
    python_path = Path(python_identity["path"])
    try:
        observed_python = _python_identity(python_path)
    except (OSError, ReadinessTransitionError) as exc:
        raise ReadinessTransitionError("root probe Python identity is unavailable") from exc
    if observed_python != python_identity:
        raise ReadinessTransitionError("root probe Python identity drifted")
    probe_by_id = {
        probe.get("probe_id"): probe for probe in probes if isinstance(probe, dict)
    }
    if set(probe_by_id) != {OUTER_PROBE_ID, PREFLIGHT_PROBE_ID}:
        raise ReadinessTransitionError("trusted-host probe set is not exact")
    for operation, (probe_id, claims) in PROBE_SPECS.items():
        probe = probe_by_id[probe_id]
        expected_probe_fields = {
            "probe_id", "operation", "command_identity_sha256", "source_path",
            "source_sha256", "stdout_sha256", "stderr_sha256", "exit_status",
            "evidence",
        }
        evidence = probe.get("evidence")
        if (
            set(probe) != expected_probe_fields
            or probe.get("operation") != operation
            or probe.get("source_path") != PROBE_RELATIVE_PATH
            or probe.get("source_sha256")
            != readiness["frozen_public_file_digests"].get(PROBE_RELATIVE_PATH)
            or probe.get("exit_status") != 0
            or not HEX64.fullmatch(str(probe.get("command_identity_sha256")))
            or not HEX64.fullmatch(str(probe.get("stdout_sha256")))
            or probe.get("stderr_sha256") != sha256_bytes(b"")
        ):
            raise ReadinessTransitionError("trusted-host probe binding is invalid")
        _validate_probe_evidence(evidence, probe_id, claims, receipt["isolation_nonce"])
        if probe["stdout_sha256"] != sha256_bytes(canonical_json(evidence) + b"\n"):
            raise ReadinessTransitionError("trusted-host probe output digest drifted")
        command = _probe_command(
            Path(python_identity["path"]),
            Path(readiness["root_isolation_contract"]["public_repository"]),
            Path("<sealed-dependency-closure>"), operation,
            receipt["isolation_nonce"], receipt["dependency_manifest_sha256"],
        )
        if probe["command_identity_sha256"] != _probe_command_identity(command):
            raise ReadinessTransitionError("trusted-host probe command identity drifted")


def _validate_probe_evidence(
    evidence: object, probe_id: str, claims: frozenset[str], challenge: str,
) -> None:
    common = {
        "schema_version", "oracle_version", "probe_id", "challenge", "result", "claims",
    }
    extra = (
        {"sandbox_profile_sha256"}
        if probe_id == OUTER_PROBE_ID
        else {"bundled_codex_identity", "runner_trace_sha256", "runner_profile_sha256"}
    )
    extra |= {"dependency_manifest_sha256", "staged_dependency_observations_sha256"}
    if (
        not isinstance(evidence, dict)
        or set(evidence) != common | extra
        or evidence.get("schema_version") != 1
        or evidence.get("oracle_version") != ORACLE_VERSION
        or evidence.get("probe_id") != probe_id
        or evidence.get("challenge") != challenge
        or evidence.get("result") != "pass"
        or not isinstance(evidence.get("claims"), dict)
        or set(evidence["claims"]) != claims
        or any(value is not True for value in evidence["claims"].values())
        or not HEX64.fullmatch(str(evidence.get("dependency_manifest_sha256")))
        or not HEX64.fullmatch(str(evidence.get("staged_dependency_observations_sha256")))
    ):
        raise ReadinessTransitionError("trusted-host probe evidence is incomplete or invalid")
    if probe_id == OUTER_PROBE_ID:
        if not HEX64.fullmatch(str(evidence.get("sandbox_profile_sha256"))):
            raise ReadinessTransitionError("outer sandbox profile identity is invalid")
        return
    identity = evidence.get("bundled_codex_identity")
    if (
        not isinstance(identity, dict)
        or set(identity) != {"path", "version", "sha256"}
        or identity.get("path") != "/Applications/ChatGPT.app/Contents/Resources/codex"
        or not isinstance(identity.get("version"), str)
        or not identity["version"].strip()
        or not HEX64.fullmatch(str(identity.get("sha256")))
        or not HEX64.fullmatch(str(evidence.get("runner_trace_sha256")))
        or not HEX64.fullmatch(str(evidence.get("runner_profile_sha256")))
    ):
        raise ReadinessTransitionError("real preflight identity evidence is invalid")


def verify_author_ready(repo: Path, ref: str = "HEAD") -> dict[str, str]:
    head = _commit(repo, ref)
    commit = _last_touch(repo, head, READINESS_RELATIVE_PATH)
    document, raw = _readiness_at(repo, commit)
    _validate_author_document(document)
    if _parent(repo, commit) != document.get("public_adapter_introducing_commit"):
        raise ReadinessTransitionError("author readiness is not anchored directly to the frozen controller")
    _validate_frozen_files(repo, head, document)
    return {"status": "author_ready", "commit": commit, "sha256": sha256_bytes(raw)}


def _verify_review_at(repo: Path, commit: str) -> tuple[dict[str, Any], dict[str, str]]:
    document, raw = _readiness_at(repo, commit)
    _validate_common(document)
    if document["status"] != "independent_review_pass":
        raise ReadinessTransitionError("expected independent_review_pass state")
    predecessor = _previous_readiness_commit(repo, commit)
    before, before_raw = _readiness_at(repo, predecessor)
    _validate_author_document(before)
    if _parent(repo, predecessor) != before.get("public_adapter_introducing_commit"):
        raise ReadinessTransitionError("author readiness predecessor is not controller-anchored")
    _same_immutable(before, document)
    _require_passed_review(document)
    if document.get("isolation_probe_status") != "pending_trusted_host_isolation":
        raise ReadinessTransitionError("isolation must remain pending after independent review")
    if _changed_paths(repo, commit) != {READINESS_RELATIVE_PATH, REVIEW_RELATIVE_PATH}:
        raise ReadinessTransitionError("independent review transition changed files outside its allowlist")
    if document.get("readiness_predecessor_commit") != predecessor or document.get(
        "readiness_predecessor_sha256"
    ) != sha256_bytes(before_raw):
        raise ReadinessTransitionError("independent review predecessor binding is invalid")
    review, review_raw = _record_at(repo, commit, REVIEW_RELATIVE_PATH, "review record")
    _validate_review_record(review, predecessor, sha256_bytes(before_raw), document)
    if (
        document.get("independent_review_record_path") != REVIEW_RELATIVE_PATH
        or document.get("independent_review_record_sha256") != sha256_bytes(review_raw)
        or document.get("independent_review_result_kind") != INDEPENDENT_RESULT_KIND
        or document.get("private_independent_reviewed_source_commit") != document["private_evaluator_source_commit"]
        or document.get("private_independent_reviewed_final_commit") != document["private_evaluator_commit"]
        or document.get("trusted_host_isolation_receipt_sha256") != "pending_trusted_host_isolation"
        or document.get("trusted_host_isolation_result_kind") != "pending_trusted_host_isolation"
    ):
        raise ReadinessTransitionError("independent review readiness fields are not exactly bound")
    _validate_frozen_files(repo, commit, document)
    return document, {
        "status": "independent_review_pass", "commit": commit,
        "sha256": sha256_bytes(raw), "review_record_sha256": sha256_bytes(review_raw),
    }


def verify_independent_review_pass(repo: Path, ref: str = "HEAD") -> dict[str, str]:
    head = _commit(repo, ref)
    commit = _last_touch(repo, head, READINESS_RELATIVE_PATH)
    document, result = _verify_review_at(repo, commit)
    _validate_frozen_files(repo, head, document)
    if _last_touch(repo, head, REVIEW_RELATIVE_PATH) != commit:
        raise ReadinessTransitionError("independent review record was overwritten")
    return result


def verify_ready(repo: Path, ref: str = "HEAD") -> dict[str, str]:
    head = _commit(repo, ref)
    readiness_commit = _last_touch(repo, head, READINESS_RELATIVE_PATH)
    document, raw = _readiness_at(repo, readiness_commit)
    _validate_common(document)
    if document["status"] != "ready":
        raise ReadinessTransitionError("oracle readiness is not in ready state")
    predecessor = _previous_readiness_commit(repo, readiness_commit)
    review_document, review_result = _verify_review_at(repo, predecessor)
    _same_immutable(review_document, document)
    _require_passed_review(document)
    if _changed_paths(repo, readiness_commit) != {READINESS_RELATIVE_PATH, ISOLATION_RELATIVE_PATH}:
        raise ReadinessTransitionError("ready transition changed files outside its allowlist")
    if document.get("readiness_predecessor_commit") != predecessor or document.get(
        "readiness_predecessor_sha256"
    ) != review_result["sha256"]:
        raise ReadinessTransitionError("ready predecessor binding is invalid")
    receipt, receipt_raw = _record_at(
        repo, readiness_commit, ISOLATION_RELATIVE_PATH, "isolation receipt"
    )
    _validate_isolation_receipt(
        receipt, predecessor, review_result["sha256"],
        review_result["review_record_sha256"], document,
    )
    if (
        document.get("trusted_host_isolation_receipt_path") != ISOLATION_RELATIVE_PATH
        or document.get("trusted_host_isolation_receipt_sha256") != sha256_bytes(receipt_raw)
        or document.get("trusted_host_isolation_result_kind") != ISOLATION_RESULT_KIND
        or document.get("private_trusted_host_isolation_tested_source_commit") != document["private_evaluator_source_commit"]
        or document.get("private_trusted_host_isolation_tested_final_commit") != document["private_evaluator_commit"]
        or document.get("isolation_probe_status") != "pass"
    ):
        raise ReadinessTransitionError("ready isolation fields are not exactly bound")
    _validate_frozen_files(repo, head, document)
    if _last_touch(repo, head, REVIEW_RELATIVE_PATH) != predecessor:
        raise ReadinessTransitionError("independent review record was overwritten")
    if _last_touch(repo, head, ISOLATION_RELATIVE_PATH) != readiness_commit:
        raise ReadinessTransitionError("isolation receipt was overwritten")
    return {
        "status": "ready", "commit": readiness_commit, "sha256": sha256_bytes(raw),
        "independent_review_commit": predecessor,
        "review_record_sha256": review_result["review_record_sha256"],
        "isolation_receipt_sha256": sha256_bytes(receipt_raw),
    }


def _atomic_write(path: Path, data: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def prepare_independent_review(repo: Path, record_path: Path) -> None:
    predecessor = verify_author_ready(repo)
    readiness_path = repo / READINESS_RELATIVE_PATH
    document = load_json_bytes(readiness_path.read_bytes(), "working readiness")
    record_raw = record_path.read_bytes()
    record = load_json_bytes(record_raw, "supplied independent review record")
    _validate_review_record(record, predecessor["commit"], predecessor["sha256"], document)
    for field in INDEPENDENT_PASS_FIELDS:
        document[field] = "pass"
    document["proportionality"]["safe_grouping_review_status"] = "pass"
    document["coverage_credit_policy"]["independent_review_status"] = "pass"
    document.update({
        "status": "independent_review_pass",
        "readiness_predecessor_commit": predecessor["commit"],
        "readiness_predecessor_sha256": predecessor["sha256"],
        "independent_review_record_sha256": sha256_bytes(record_raw),
        "independent_review_result_kind": INDEPENDENT_RESULT_KIND,
        "private_independent_reviewed_source_commit": document["private_evaluator_source_commit"],
        "private_independent_reviewed_final_commit": document["private_evaluator_commit"],
    })
    _atomic_write(repo / REVIEW_RELATIVE_PATH, record_raw)
    _atomic_write(readiness_path, canonical_file_bytes(document))


def _python_identity(path: Path) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise ReadinessTransitionError("root probe Python executable is unavailable")
    result = subprocess.run(
        [str(resolved), "--version"], check=False, capture_output=True, text=True,
        env=PROBE_ENVIRONMENT,
    )
    version = (result.stdout or result.stderr).strip()
    if result.returncode or not version:
        raise ReadinessTransitionError("root probe Python identity cannot be observed")
    return {
        "path": str(resolved),
        "version": version,
        "sha256": sha256_bytes(resolved.read_bytes()),
    }


def _probe_command(
    python: Path, repo: Path, closure_root: Path, operation: str, challenge: str,
    dependency_manifest_sha256: str,
) -> list[str]:
    if operation not in PROBE_SPECS:
        raise ReadinessTransitionError("root probe operation is unknown")
    return [
        str(python), "-I", "-B", str(closure_root / PROBE_RELATIVE_PATH), operation,
        "--repo", str(repo),
        "--closure-root", str(closure_root),
        "--dependency-manifest-sha256", dependency_manifest_sha256,
        "--private-repo", str(PRIVATE_EVALUATOR_REPOSITORY),
        "--challenge", challenge,
    ]


def _probe_command_identity(command: list[str]) -> str:
    logical = list(command)
    if logical[1:3] != ["-I", "-B"]:
        raise ReadinessTransitionError("root probe command lacks isolated no-bytecode mode")
    logical[3] = f"<sealed-dependency-closure>/{PROBE_RELATIVE_PATH}"
    try:
        logical[logical.index("--closure-root") + 1] = "<sealed-dependency-closure>"
    except (ValueError, IndexError) as exc:
        raise ReadinessTransitionError("root probe command lacks sealed closure binding") from exc
    return sha256_bytes(canonical_json(logical))


def _validate_probe_environment() -> None:
    if set(PROBE_ENVIRONMENT) != {
        "PATH", "LANG", "LC_ALL", "PYTHONSAFEPATH", "PYTHONDONTWRITEBYTECODE",
    } or any(name in PROBE_ENVIRONMENT for name in ("PYTHONPATH", "PYTHONHOME")):
        raise ReadinessTransitionError("root probe environment is not the frozen scrubbed allowlist")


def _execute_probe_command(command: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    _validate_probe_environment()
    return subprocess.run(
        command,
        cwd=repo,
        env=PROBE_ENVIRONMENT,
        check=False,
        capture_output=True,
        text=True,
    )


def _observe_probe(
    repo: Path, closure_root: Path, python: Path, operation: str, challenge: str,
    probe_source_sha256: str, dependency_manifest_sha256: str,
    staged_dependency_observations_sha256: str,
) -> dict[str, Any]:
    probe_id, claims = PROBE_SPECS[operation]
    command = _probe_command(
        python, repo, closure_root, operation, challenge, dependency_manifest_sha256,
    )
    result = _execute_probe_command(command, repo)
    if result.returncode != 0:
        raise ReadinessTransitionError(
            f"required {operation} host probe failed with exit {result.returncode}"
        )
    if result.stderr:
        raise ReadinessTransitionError(f"required {operation} host probe emitted stderr")
    try:
        evidence = load_json_bytes(result.stdout.encode("utf-8"), f"{operation} probe output")
    except ReadinessTransitionError as exc:
        raise ReadinessTransitionError(f"required {operation} host probe evidence failed") from exc
    _validate_probe_evidence(evidence, probe_id, claims, challenge)
    if (
        evidence["dependency_manifest_sha256"] != dependency_manifest_sha256
        or evidence["staged_dependency_observations_sha256"]
        != staged_dependency_observations_sha256
    ):
        raise ReadinessTransitionError(f"required {operation} closure evidence drifted")
    canonical_stdout = canonical_json(evidence) + b"\n"
    if result.stdout.encode("utf-8") != canonical_stdout:
        raise ReadinessTransitionError(f"required {operation} host probe output is not canonical")
    return {
        "probe_id": probe_id,
        "operation": operation,
        "command_identity_sha256": _probe_command_identity(command),
        "source_path": PROBE_RELATIVE_PATH,
        "source_sha256": probe_source_sha256,
        "stdout_sha256": sha256_bytes(canonical_stdout),
        "stderr_sha256": sha256_bytes(result.stderr.encode("utf-8")),
        "exit_status": result.returncode,
        "evidence": evidence,
    }


def _stage_dependency_closure(
    repo: Path, commit: str, destination: Path, observations: list[dict[str, str]],
) -> list[dict[str, str]]:
    expected_paths = [entry["path"] for entry in observations]
    if expected_paths != sorted(DEPENDENCY_OBSERVED_ROLES):
        raise ReadinessTransitionError("dependency observation set is not exact")
    for entry in observations:
        relative_path = entry["path"]
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            raise ReadinessTransitionError("sealed dependency staging target already exists")
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(_blob(repo, commit, relative_path))
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        target.chmod(0o755 if entry["git_mode"] == "100755" else 0o644)
    staged: list[dict[str, str]] = []
    for entry in observations:
        path = _require_regular_checkout_file(destination, entry["path"])
        observed = {
            "path": entry["path"], "role": entry["role"],
            "sha256": sha256_bytes(path.read_bytes()), "git_mode": _file_mode(path),
        }
        if observed != {
            "path": entry["path"], "role": entry["role"],
            "sha256": entry["sha256"], "git_mode": entry["git_mode"],
        }:
            raise ReadinessTransitionError("sealed dependency staging bytes drifted")
        staged.append(observed)
    return staged


def _stage_dependency_closure_observations(destination: Path) -> list[dict[str, str]]:
    observed_paths = sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*") if path.is_file() or path.is_symlink()
    )
    if observed_paths != sorted(DEPENDENCY_OBSERVED_ROLES):
        raise ReadinessTransitionError("sealed dependency staging file set is not exact")
    observations: list[dict[str, str]] = []
    for relative_path in observed_paths:
        current = destination
        for part in Path(relative_path).parts:
            current = current / part
            if current.is_symlink():
                raise ReadinessTransitionError("sealed dependency staging contains a symlink")
        path = _require_regular_checkout_file(destination, relative_path)
        observations.append({
            "path": relative_path,
            "role": DEPENDENCY_OBSERVED_ROLES[relative_path],
            "sha256": sha256_bytes(path.read_bytes()),
            "git_mode": _file_mode(path),
        })
    return observations


def run_root_isolation(repo: Path) -> None:
    repo = repo.resolve(strict=True)
    if repo != PUBLIC_REPOSITORY.resolve(strict=True):
        raise ReadinessTransitionError("root isolation must run in the pinned public repository")
    predecessor = verify_independent_review_pass(repo)
    if str(git(repo, ["status", "--porcelain=v1", "--untracked-files=no"])).strip():
        raise ReadinessTransitionError("tracked public state must be clean before root isolation")
    head_before = _commit(repo, "HEAD")
    readiness_path = repo / READINESS_RELATIVE_PATH
    readiness_before = readiness_path.read_bytes()
    document = load_json_bytes(readiness_path.read_bytes(), "working readiness")
    receipt_path = repo / ISOLATION_RELATIVE_PATH
    if receipt_path.exists() or receipt_path.is_symlink():
        raise ReadinessTransitionError("trusted-host isolation receipt is write-once")
    _verify_private_evaluator(document)
    _validate_probe_environment()
    _validate_frozen_files(repo, head_before, document)
    dependency_binding_value = document["root_isolation_dependency_binding"]
    dependency_pre_observations = _dependency_observations(repo, head_before)
    if dependency_pre_observations != dependency_binding_value["entries"]:
        raise ReadinessTransitionError("pre-probe dependency closure is not frozen")
    probe_source_sha256 = document["frozen_public_file_digests"][PROBE_RELATIVE_PATH]
    python_identity = _python_identity(Path(sys.executable))
    python = Path(python_identity["path"])
    challenge = secrets.token_hex(32)
    with tempfile.TemporaryDirectory(
        prefix="deliver-v1234-frozen-closure-", dir="/private/tmp"
    ) as closure_text:
        closure_root = Path(closure_text)
        staged_dependency_observations = _stage_dependency_closure(
            repo, head_before, closure_root, dependency_pre_observations,
        )
        staged_dependency_observations_sha256 = sha256_bytes(
            canonical_json(staged_dependency_observations)
        )
        probes = [
            _observe_probe(
                repo, closure_root, python, operation, challenge, probe_source_sha256,
                dependency_binding_value["manifest_sha256"],
                staged_dependency_observations_sha256,
            )
            for operation in PROBE_SPECS
        ]
        if _stage_dependency_closure_observations(closure_root) != staged_dependency_observations:
            raise ReadinessTransitionError("sealed dependency staging changed while probes ran")
    if _commit(repo, "HEAD") != head_before:
        raise ReadinessTransitionError("public HEAD changed while root probes ran")
    if readiness_path.read_bytes() != readiness_before:
        raise ReadinessTransitionError("readiness changed while root probes ran")
    if str(git(repo, ["status", "--porcelain=v1", "--untracked-files=no"])).strip():
        raise ReadinessTransitionError("tracked public state changed while root probes ran")
    dependency_post_observations = _dependency_observations(repo, head_before)
    if dependency_post_observations != dependency_pre_observations:
        raise ReadinessTransitionError("dependency closure changed while root probes ran")
    _validate_frozen_files(repo, head_before, document)
    _verify_private_evaluator(document)
    receipt = {
        "schema_version": 2,
        "oracle_version": ORACLE_VERSION,
        "record_kind": "trusted_host_isolation",
        "result": "pass",
        "root_observed_operation": "run-root-isolation",
        "isolation_nonce": challenge,
        "private_evaluator_source_commit": document["private_evaluator_source_commit"],
        "private_evaluator_final_commit": document["private_evaluator_commit"],
        "public_controller_commit": document["public_adapter_introducing_commit"],
        "predecessor_readiness_commit": predecessor["commit"],
        "predecessor_readiness_sha256": predecessor["sha256"],
        "independent_review_record_sha256": predecessor["review_record_sha256"],
        "independent_review_transition_commit": predecessor["commit"],
        "immutable_readiness_sha256": document["immutable_readiness_sha256"],
        "root_isolation_contract_sha256": sha256_bytes(
            canonical_json(document["root_isolation_contract"])
        ),
        "network_policy": NETWORK_POLICY,
        "python_identity": python_identity,
        "dependency_manifest_sha256": dependency_binding_value["manifest_sha256"],
        "dependency_pre_observations": dependency_pre_observations,
        "dependency_pre_observations_sha256": sha256_bytes(
            canonical_json(dependency_pre_observations)
        ),
        "dependency_post_observations": dependency_post_observations,
        "dependency_post_observations_sha256": sha256_bytes(
            canonical_json(dependency_post_observations)
        ),
        "staged_dependency_observations": staged_dependency_observations,
        "staged_dependency_observations_sha256": sha256_bytes(
            canonical_json(staged_dependency_observations)
        ),
        "probes": probes,
    }
    receipt_raw = canonical_file_bytes(receipt)
    _validate_isolation_receipt(
        receipt, predecessor["commit"], predecessor["sha256"],
        predecessor["review_record_sha256"], document,
    )
    document.update({
        "status": "ready",
        "readiness_predecessor_commit": predecessor["commit"],
        "readiness_predecessor_sha256": predecessor["sha256"],
        "trusted_host_isolation_receipt_sha256": sha256_bytes(receipt_raw),
        "trusted_host_isolation_result_kind": ISOLATION_RESULT_KIND,
        "private_trusted_host_isolation_tested_source_commit": document["private_evaluator_source_commit"],
        "private_trusted_host_isolation_tested_final_commit": document["private_evaluator_commit"],
        "isolation_probe_status": "pass",
    })
    _atomic_write(repo / ISOLATION_RELATIVE_PATH, receipt_raw)
    _atomic_write(readiness_path, canonical_file_bytes(document))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "verify-controller-frozen", "verify-author-ready",
        "verify-independent-review", "verify-ready",
    ):
        child = subparsers.add_parser(command)
        child.add_argument("--repo", type=Path, default=Path.cwd())
        child.add_argument("--ref", default="HEAD")
    review = subparsers.add_parser("prepare-independent-review")
    review.add_argument("--repo", type=Path, default=Path.cwd())
    review.add_argument("--record", type=Path, required=True)
    ready = subparsers.add_parser("run-root-isolation")
    ready.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.command == "verify-controller-frozen":
        result = verify_controller_frozen(repo, args.ref)
    elif args.command == "verify-author-ready":
        result = verify_author_ready(repo, args.ref)
    elif args.command == "verify-independent-review":
        result = verify_independent_review_pass(repo, args.ref)
    elif args.command == "verify-ready":
        result = verify_ready(repo, args.ref)
    elif args.command == "prepare-independent-review":
        prepare_independent_review(repo, args.record.resolve())
        result = {"status": "prepared_independent_review", "commit_required": True}
    else:
        run_root_isolation(repo)
        result = {"status": "prepared_ready", "commit_required": True}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReadinessTransitionError as exc:
        print(f"readiness transition failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
