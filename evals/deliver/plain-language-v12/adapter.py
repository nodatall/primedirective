#!/usr/bin/env python3
"""Public, answer-free controller for the Deliver plain-language v12 evaluation."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Iterable


ADAPTER_PATH = Path(__file__).resolve()
V12_ROOT = ADAPTER_PATH.parent
REPO_ROOT = V12_ROOT.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evals.deliver import harness as v11  # noqa: E402

if str(V12_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_ROOT))
import readiness_transition  # noqa: E402


ADAPTER_IDENTIFIER = "deliver_plain_language_v12"
SCHEMA_VERSION = 1
READINESS_SCHEMA_VERSION = 24
ORACLE_VERSION = "deliver-plain-language-v12.27"
ADAPTER_RELATIVE_PATH = "evals/deliver/plain-language-v12/adapter.py"
POLICY_RELATIVE_PATH = "evals/deliver/plain-language-v12/execution-policy.json"
STATE_NAME = "controller-state.json"
CONTROL_RELATIVE = Path(v11.COMPARISON_CONTROL) / "v12"
POLICY_PATH = V12_ROOT / "execution-policy.json"
READINESS_PATH = V12_ROOT / "oracle-readiness.json"
VOCABULARY_PATH = V12_ROOT / "comprehension-vocabulary.json"
BASELINE_MANIFEST_PATH = V12_ROOT / "baseline-package-manifest.json"
CANDIDATE_MANIFEST_PATH = V12_ROOT / "candidate-package-manifest.json"
INVENTORY_PATH = V12_ROOT / "public-contract-inventory.json"
CANDIDATE_BEHAVIOR_MAP_PATH = V12_ROOT / "candidate-behavior-map.json"
WORDING_APPROVAL_RELATIVE_PATH = "evals/deliver/plain-language-v12/wording-approval.json"
WORDING_APPROVAL_PATH = V12_ROOT / "wording-approval.json"
V11_MANIFEST_PATH = V12_ROOT / "v11-file-manifest.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SAFE_RUNTIME = re.compile(r"^deliver-eval-v12-[0-9a-f]{32}$")
ARMS = ("baseline", "candidate")
SCENARIOS = ("retry-failed", "preflight-remediation-holdout")
REQUIRED_ARTIFACTS = (
    "package_manifest",
    "runner_provenance",
    "process_evidence",
    "trace",
    "stderr",
    "sealed_output",
    "readability_package",
    "observed_behavior",
)

EXPECTED_POLICY = {
    "schema_version": 1,
    "adapter_identifier": ADAPTER_IDENTIFIER,
    "model": "gpt-5.6-sol",
    "reasoning": "xhigh",
    "context_window_tokens": 262144,
    "max_input_tokens": 196608,
    "max_output_tokens": 16384,
    "context_reserve_tokens": 32768,
    "maximum_contract_package_bytes": 300000,
    "maximum_contract_package_words": 50000,
    "arm_order": list(ARMS),
    "behavior_scenarios": list(SCENARIOS),
    "poll_interval_seconds": 15,
    "shell_yield_seconds": 60,
    "no_progress_seconds": 900,
    "process_limit_seconds": 7200,
    "arm_total_seconds": 10800,
    "semantic_attempts": 1,
    "maximum_pre_output_infrastructure_restarts": 1,
    "restart_condition": "infrastructure_failure_before_any_output",
    "reattachment_condition": "same_verified_process_only",
}

REQUIRED_READINESS_PASS_FIELDS = (
    "author_validation_status",
    "independent_semantic_review_status",
    "hidden_material_noninterference_independent_review_status",
    "judge_packet_structural_blinding_author_status",
    "case_grouping_independent_review_status",
    "zero_static_coverage_independent_review_status",
    "arm_projection_status",
    "byte_identical_arm_packet_status",
    "public_adapter_deterministic_integration_status",
    "comparison_runtime_author_validation_status",
    "comparison_runtime_review_status",
    "durable_comparison_lifecycle_author_status",
    "durable_comparison_lifecycle_independent_review_status",
    "trusted_root_author_status",
    "trusted_root_independent_review_status",
    "sealed_artifact_derivation_author_status",
    "sealed_artifact_derivation_independent_review_status",
    "isolation_probe_status",
)
INDEPENDENT_RESULT_KIND = "orchestrator_observed_agent_result_not_signature"
ISOLATION_RESULT_KIND = "root_observed_probe_result_not_signature"
READINESS_EXECUTION_LIMITS = {
    "context_window_tokens": EXPECTED_POLICY["context_window_tokens"],
    "max_input_tokens": EXPECTED_POLICY["max_input_tokens"],
    "max_output_tokens": EXPECTED_POLICY["max_output_tokens"],
    "context_reserve_tokens": EXPECTED_POLICY["context_reserve_tokens"],
    "maximum_contract_package_bytes": EXPECTED_POLICY["maximum_contract_package_bytes"],
    "maximum_contract_package_words": EXPECTED_POLICY["maximum_contract_package_words"],
    "per_process_timeout_seconds": EXPECTED_POLICY["process_limit_seconds"],
    "total_arm_timeout_seconds": EXPECTED_POLICY["arm_total_seconds"],
    "durable_poll_interval_seconds": EXPECTED_POLICY["poll_interval_seconds"],
    "no_progress_timeout_seconds": EXPECTED_POLICY["no_progress_seconds"],
    "shell_yield_seconds": EXPECTED_POLICY["shell_yield_seconds"],
    "semantic_attempts": EXPECTED_POLICY["semantic_attempts"],
    "maximum_pre_output_infrastructure_restarts": EXPECTED_POLICY[
        "maximum_pre_output_infrastructure_restarts"
    ],
}

READINESS_ALLOWED_FIELDS = frozenset({
    "schema_version", "oracle_version", "status", "model", "reasoning",
    "public_adapter_identifier", "public_adapter_introducing_commit", "public_adapter_path",
    "public_adapter_sha256", "public_execution_policy_path", "public_execution_policy_sha256",
    "public_contract_inventory_sha256", "baseline_package_manifest_sha256",
    "baseline_package_content_manifest_sha256", "baseline_commit",
    "candidate_package_manifest_sha256", "candidate_package_content_manifest_sha256",
    "candidate_behavior_map_sha256", "candidate_commit",
    "wording_approval_record_path", "wording_approval_record_sha256",
    "wording_approval_record_commit", "wording_approval_candidate_commit",
    "private_evaluator_source_commit", "private_evaluator_commit",
    "independent_review_result_kind", "private_independent_reviewed_source_commit",
    "private_independent_reviewed_final_commit", "trusted_host_isolation_result_kind",
    "private_trusted_host_isolation_tested_source_commit",
    "private_trusted_host_isolation_tested_final_commit",
    "private_projected_packet_sha256", "per_arm_response_schema_sha256",
    "projected_packet_bytes", "projected_packet_lexical_word_count",
    "expected_per_arm_output_bytes", "context_margin_tokens",
    "case_count", "single_behavior_case_count", "multi_behavior_case_count",
    "previous_oracle_case_reuse_count", "previous_oracle_case_digest_overlap_count",
    "baseline_behavior_id_count", "behavior_id_count", "covered_behavior_ids",
    "approved_removal_behavior_count", "approved_removed_behavior_ids",
    "removal_absence_assertion_count", "removal_absence_static_control_count",
    "assertion_count", "hard_scored_field_instance_count", "clause_obligation_count",
    "hidden_comprehension_behavior_count", "full_behavior_lane_gate_count",
    "static_credit_behavior_count", "accepted_equivalent_value_count",
    "noncanonical_response_mutation_count", "distinct_mutation_payload_count",
    "canonical_invariance_control_count", "answer_free_selector_diagnostic_count",
    "answer_free_selector_diagnostic_maximum_recovery_count",
    "hidden_material_noninterference_control_count", "runtime_positive_test_count",
    "runtime_negative_test_count", "fresh_judge_allocation_count",
    "durable_lifecycle_positive_control_count",
    "lifecycle_order_tamper_negative_control_count",
    "unbound_verdict_shape_negative_control_count",
    "trusted_root_positive_control_count", "trusted_root_negative_control_count",
    "gate_recomputation_negative_control_count", "lane_schema_negative_control_count",
    "comparability_negative_control_count", "aggregation_negative_control_count",
    "sealed_artifact_packet_positive_control_count",
    "caller_payload_rejection_negative_control_count",
    "artifact_transitive_binding_negative_control_count",
    "judge_packet_schema_control_count", "discarded_channel_reachability_control_count",
    "clean_content_preservation_control_count", "rationale_discarded_before_judge_input",
    "rationale_affects_deterministic_score", "rationale_affects_combined_verdict",
    "proportionality", "coverage_credit_policy", "execution_limits",
    "author_validation_status", "independent_semantic_review_status",
    "hidden_material_noninterference_author_status",
    "hidden_material_noninterference_independent_review_status",
    "judge_packet_structural_blinding_author_status",
    "case_grouping_independent_review_status", "zero_static_coverage_independent_review_status",
    "arm_projection_status", "byte_identical_arm_packet_status",
    "public_adapter_deterministic_integration_status",
    "comparison_runtime_author_validation_status", "comparison_runtime_review_status",
    "durable_comparison_lifecycle_author_status",
    "durable_comparison_lifecycle_independent_review_status",
    "trusted_root_author_status", "trusted_root_independent_review_status",
    "sealed_artifact_derivation_author_status",
    "sealed_artifact_derivation_independent_review_status",
    "isolation_probe_status", "live_model_feasibility_status", "live_model_execution_performed",
    "deterministic_controls_are_live_arm_execution",
    "deterministic_controls_are_judge_verdict_evidence",
    "immutable_readiness_sha256", "frozen_public_file_digests",
    "frozen_public_file_commits", "readiness_predecessor_commit",
    "readiness_predecessor_sha256", "independent_review_record_path",
    "independent_review_record_sha256", "trusted_host_isolation_receipt_path",
    "trusted_host_isolation_receipt_sha256",
})
READINESS_NESTED_ALLOWED_FIELDS = {
    "proportionality": frozenset({
        "packet_byte_count", "packet_lexical_word_count", "expected_per_arm_output_byte_count",
        "safe_grouping_review_status",
    }),
    "coverage_credit_policy": frozenset({
        "hidden_deterministic_comprehension_assertions", "full_behavior_lane_gates",
        "static_owner_or_route_proofs", "unchanged_owner_bytes_or_route_text_can_earn_credit",
        "caller_authored_coverage_can_earn_credit", "independent_review_status",
    }),
    "execution_limits": frozenset(READINESS_EXECUTION_LIMITS),
}


class AdapterError(RuntimeError):
    """Raised when a public v12 controller invariant fails."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    require_regular_file(path, "digest input")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nonzero_hex(value: object, pattern: re.Pattern[str], width: int) -> bool:
    return isinstance(value, str) and value != "0" * width and pattern.fullmatch(value) is not None


def lexical_word_count(value: str) -> int:
    return len(re.findall(r"\b\w+\b", value))


def expected_response_schema(vocabulary: dict[str, Any], item_count: int) -> dict[str, Any]:
    fields = (
        "next_action",
        "required_artifact",
        "required_check",
        "stop_condition",
        "user_approval",
    )
    global_vocabulary = vocabulary.get("global_vocabulary")
    if not isinstance(global_vocabulary, dict) or set(global_vocabulary) != set(fields):
        raise AdapterError("public vocabulary fields are not exact")
    codes: dict[str, list[str]] = {}
    for field in fields:
        entries = global_vocabulary[field]
        if not isinstance(entries, list) or not entries:
            raise AdapterError(f"public vocabulary has no {field} entries")
        field_codes: list[str] = []
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or set(entry) != {"code", "operational_meaning"}
                or not isinstance(entry.get("code"), str)
                or not entry["code"]
                or not isinstance(entry.get("operational_meaning"), str)
                or not entry["operational_meaning"].strip()
            ):
                raise AdapterError(f"public vocabulary {field} entry is malformed")
            field_codes.append(entry["code"])
        if len(field_codes) != len(set(field_codes)):
            raise AdapterError(f"public vocabulary {field} codes are not unique")
        codes[field] = field_codes
    properties: dict[str, Any] = {
        "case_code": {"type": "string", "pattern": r"^K-[A-F0-9]{8}$"},
        "rationale": {"type": "string", "minLength": 1, "maxLength": 240},
        "user_approval": {"type": "string", "enum": codes["user_approval"]},
    }
    for field in fields[:-1]:
        properties[field] = {
            "type": "array",
            "minItems": 0,
            "maxItems": len(codes[field]),
            "uniqueItems": True,
            "items": {"type": "string", "enum": codes[field]},
        }
    required = (
        "case_code",
        "next_action",
        "required_artifact",
        "required_check",
        "stop_condition",
        "user_approval",
        "rationale",
    )
    return {
        "type": "array",
        "minItems": item_count,
        "maxItems": item_count,
        "uniqueItems": True,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": list(required),
            "properties": {field: properties[field] for field in required},
        },
    }


def load_json(path: Path, label: str) -> Any:
    require_regular_file(path, label)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"{label} is not valid UTF-8 JSON: {path}") from exc


def reject_symlink_chain(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            raise AdapterError(f"symlink path rejected: {path}")


def require_regular_file(path: Path, label: str) -> Path:
    reject_symlink_chain(path)
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise AdapterError(f"{label} must be a regular file: {path}")
    return path


def require_directory(path: Path, label: str) -> Path:
    reject_symlink_chain(path)
    if not path.is_dir():
        raise AdapterError(f"{label} must be a regular directory: {path}")
    return path


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    v11.atomic_write_json(path, value)


def write_once(path: Path, data: bytes) -> None:
    if path.exists() or path.is_symlink():
        require_regular_file(path, "write-once artifact")
        if path.read_bytes() != data:
            raise AdapterError(f"write-once artifact changed: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{secrets.token_hex(8)}.tmp"
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_once_json(path: Path, value: object) -> None:
    write_once(path, canonical_json(value) + b"\n")


def git(arguments: list[str], *, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, check=False, capture_output=True,
        text=not binary,
    )
    if result.returncode:
        stderr = result.stderr.decode(errors="replace") if binary else result.stderr
        raise AdapterError(f"git {' '.join(arguments)} failed: {stderr.strip()}")
    return result.stdout if binary else result.stdout.strip()


def git_tree(commit: str) -> str:
    tree = str(git(["rev-parse", f"{commit}^{{tree}}"])).strip()
    if not HEX40.fullmatch(tree):
        raise AdapterError("Git source tree is invalid")
    return tree


def repository_identity() -> dict[str, str]:
    relative = ADAPTER_PATH.relative_to(REPO_ROOT).as_posix()
    commit = str(git(["rev-parse", "HEAD"])).strip()
    if not HEX40.fullmatch(commit):
        raise AdapterError("evaluator Git commit is invalid")
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
    )
    if tracked.returncode:
        raise AdapterError("adapter must be committed before initialization")
    status = str(git([
        "status", "--porcelain=v1", "--untracked-files=all", "--", "evals/deliver",
    ])).strip()
    if status:
        raise AdapterError("Deliver evaluator tree must be clean before initialization")
    committed = bytes(git(["show", f"HEAD:{relative}"], binary=True))
    current = ADAPTER_PATH.read_bytes()
    if committed != current:
        raise AdapterError("adapter bytes differ from the clean Git commit")
    return {
        "commit": commit,
        "evals_tree": str(git(["rev-parse", "HEAD:evals/deliver"])),
        "adapter_sha256": sha256_bytes(current),
    }


def load_policy() -> dict[str, Any]:
    policy = load_json(POLICY_PATH, "execution policy")
    integer_fields = (
        "schema_version",
        "context_window_tokens",
        "max_input_tokens",
        "max_output_tokens",
        "context_reserve_tokens",
        "maximum_contract_package_bytes",
        "maximum_contract_package_words",
        "poll_interval_seconds",
        "shell_yield_seconds",
        "no_progress_seconds",
        "process_limit_seconds",
        "arm_total_seconds",
        "semantic_attempts",
        "maximum_pre_output_infrastructure_restarts",
    )
    if (
        not isinstance(policy, dict)
        or any(type(policy.get(field)) is not int for field in integer_fields)
        or policy != EXPECTED_POLICY
    ):
        raise AdapterError("execution policy differs from the frozen public policy")
    return policy


def verify_v11_files() -> dict[str, Any]:
    manifest = load_json(V11_MANIFEST_PATH, "v11 file manifest")
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version", "baseline_commit", "files", "manifest_sha256",
    }:
        raise AdapterError("v11 file manifest fields are not exact")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if (
        manifest["schema_version"] != 1
        or not HEX40.fullmatch(str(manifest["baseline_commit"]))
        or not HEX64.fullmatch(str(manifest["manifest_sha256"]))
        or sha256_bytes(canonical_json(payload)) != manifest["manifest_sha256"]
        or not isinstance(manifest["files"], list)
        or not manifest["files"]
    ):
        raise AdapterError("v11 file manifest identity is invalid")
    paths: set[str] = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {
            "path", "git_mode", "byte_size", "sha256",
        }:
            raise AdapterError("v11 file manifest entry fields are not exact")
        relative = entry["path"]
        if (
            not isinstance(relative, str)
            or not relative
            or relative in paths
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            raise AdapterError("v11 file manifest contains an invalid path")
        paths.add(relative)
        path = REPO_ROOT / relative
        require_regular_file(path, "v11 immutable file")
        listing = str(git(["ls-tree", manifest["baseline_commit"], "--", relative]))
        if not listing:
            raise AdapterError(f"v11 file is absent from baseline: {relative}")
        metadata, listed = listing.split("\t", 1)
        mode, kind, object_id = metadata.split()
        baseline_bytes = bytes(git(["cat-file", "blob", object_id], binary=True))
        if (
            listed != relative
            or kind != "blob"
            or mode != entry["git_mode"]
            or mode == "120000"
            or len(baseline_bytes) != entry["byte_size"]
            or sha256_bytes(baseline_bytes) != entry["sha256"]
            or path.read_bytes() != baseline_bytes
            or sha256_file(path) != entry["sha256"]
        ):
            raise AdapterError(f"v11 immutable file drifted: {relative}")
    return manifest


def manifest_digest(document: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json({
        key: value for key, value in document.items() if key != "manifest_sha256"
    }))


def package_files(root: Path) -> list[Path]:
    require_directory(root, "package root")
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        v11.reject_symlink_chain(root, relative)
        if path.is_dir():
            continue
        require_regular_file(path, "package input")
        files.append(path)
    if not files:
        raise AdapterError("package cannot be empty")
    return files


def source_commit_from_manifest(document: dict[str, Any]) -> str:
    candidates = [
        document.get("source_commit"), document.get("baseline_commit"),
        document.get("candidate_commit"),
    ]
    commits = {value for value in candidates if isinstance(value, str) and value}
    if len(commits) != 1:
        raise AdapterError("package authority must identify exactly one source commit")
    commit = str(git(["rev-parse", f"{commits.pop()}^{{commit}}"])).strip()
    if not HEX40.fullmatch(commit):
        raise AdapterError("package source commit is invalid")
    return commit


def verify_package(
    root: Path, authority_path: Path, arm: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = require_directory(root.resolve(strict=True), f"{arm} package root")
    authority = load_json(authority_path, f"{arm} package authority")
    if not isinstance(authority, dict) or not isinstance(authority.get("files"), list):
        raise AdapterError(f"{arm} package authority is malformed")
    if authority.get("schema_version") != 1 or not HEX64.fullmatch(
        str(authority.get("manifest_sha256", ""))
    ) or manifest_digest(authority) != authority["manifest_sha256"]:
        raise AdapterError(f"{arm} package authority digest is invalid")
    source_commit = source_commit_from_manifest(authority)
    source_tree = git_tree(source_commit)
    if "source_tree" in authority and authority["source_tree"] != source_tree:
        raise AdapterError(f"{arm} package source tree differs from Git")
    entries = authority["files"]
    authority_paths = [entry.get("path") for entry in entries if isinstance(entry, dict)]
    actual_paths = [path.relative_to(root).as_posix() for path in package_files(root)]
    if authority_paths != sorted(authority_paths) or actual_paths != authority_paths:
        raise AdapterError(f"{arm} package has unexpected, missing, or unordered files")
    total_bytes = sum((root / relative).stat().st_size for relative in actual_paths)
    try:
        total_words = sum(
            lexical_word_count((root / relative).read_text(encoding="utf-8"))
            for relative in actual_paths
        )
    except UnicodeDecodeError as exc:
        raise AdapterError(f"{arm} package must contain UTF-8 public contract files") from exc
    if (
        total_bytes > EXPECTED_POLICY["maximum_contract_package_bytes"]
        or total_words > EXPECTED_POLICY["maximum_contract_package_words"]
    ):
        raise AdapterError(f"{arm} package exceeds the frozen public execution limits")
    role_paths: dict[str, list[str]] = {}
    for key in ("full_contract_paths", "behavior_runner_paths", "interface_paths"):
        paths = authority.get(key)
        if (
            not isinstance(paths, list)
            or not paths
            or any(not isinstance(path, str) or path not in authority_paths for path in paths)
            or len(paths) != len(set(paths))
        ):
            raise AdapterError(f"{arm} package authority has invalid {key}")
        role_paths[key] = paths
    if role_paths["full_contract_paths"] != authority_paths:
        raise AdapterError(f"{arm} full contract path list differs from its file manifest")
    canonical_entries: list[dict[str, Any]] = []
    for entry, relative in zip(entries, authority_paths, strict=True):
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise AdapterError(f"{arm} package path is invalid")
        path = root / relative
        listing = str(git(["ls-tree", source_commit, "--", relative]))
        if not listing:
            raise AdapterError(f"{arm} package source path is missing: {relative}")
        metadata, listed = listing.split("\t", 1)
        mode, kind, object_id = metadata.split()
        source_bytes = bytes(git(["cat-file", "blob", object_id], binary=True))
        expected_mode = entry.get("git_mode", entry.get("mode"))
        expected_size = entry.get("byte_size", entry.get("size"))
        if (
            listed != relative
            or kind != "blob"
            or mode == "120000"
            or expected_mode != mode
            or entry.get("sha256") != sha256_bytes(source_bytes)
            or expected_size != len(source_bytes)
            or path.read_bytes() != source_bytes
            or stat.S_IMODE(path.stat().st_mode) != (int(mode, 8) & 0o777)
            or (entry.get("git_blob_sha") not in {None, object_id})
        ):
            raise AdapterError(f"{arm} package does not reproduce Git: {relative}")
        canonical_entries.append({
            "path": relative,
            "git_mode": mode,
            "byte_size": len(source_bytes),
            "sha256": sha256_bytes(source_bytes),
            "source_commit": source_commit,
            "source_tree": source_tree,
        })
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "adapter_identifier": ADAPTER_IDENTIFIER,
        "arm": arm,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "role_paths": role_paths,
        "files": canonical_entries,
    }
    manifest["manifest_sha256"] = manifest_digest(manifest)
    source_binding = {
        "real_path": str(root),
        "device": root.stat().st_dev,
        "inode": root.stat().st_ino,
        "authority_path": str(authority_path.resolve(strict=True)),
        "authority_sha256": sha256_file(authority_path),
    }
    return manifest, source_binding


def copy_package(source: Path, destination: Path, manifest: dict[str, Any]) -> None:
    if destination.exists() or destination.is_symlink():
        raise AdapterError(f"package destination already exists: {destination}")
    destination.mkdir(parents=True, mode=0o700)
    for entry in manifest["files"]:
        relative = Path(entry["path"])
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, int(entry["git_mode"], 8) & 0o777)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write((source / relative).read_bytes())
        target.chmod(int(entry["git_mode"], 8) & 0o777)
    reproduced, _ = verify_staged_package(destination, manifest)
    if reproduced != manifest:
        raise AdapterError("staged package does not reproduce its manifest")


def verify_staged_package(
    root: Path, expected: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int | str]]:
    root = require_directory(root.resolve(strict=True), "staged package root")
    actual_paths = [path.relative_to(root).as_posix() for path in package_files(root)]
    expected_paths = [entry["path"] for entry in expected["files"]]
    if actual_paths != expected_paths:
        raise AdapterError("staged package path set drifted")
    entries: list[dict[str, Any]] = []
    for item in expected["files"]:
        path = root / item["path"]
        actual = {
            "path": item["path"],
            "git_mode": "100755" if stat.S_IMODE(path.stat().st_mode) & 0o111 else "100644",
            "byte_size": path.stat().st_size,
            "sha256": sha256_file(path),
            "source_commit": item["source_commit"],
            "source_tree": item["source_tree"],
        }
        entries.append(actual)
    document = {key: value for key, value in expected.items() if key not in {"files", "manifest_sha256"}}
    document["files"] = entries
    document["manifest_sha256"] = manifest_digest(document)
    if document != expected:
        raise AdapterError("staged package bytes, modes, or source binding drifted")
    return document, {
        "real_path": str(root), "device": root.stat().st_dev, "inode": root.stat().st_ino,
    }


def scoped_package_manifest(full: dict[str, Any], scope: str, paths: list[str]) -> dict[str, Any]:
    selected = [entry for entry in full["files"] if entry["path"] in set(paths)]
    if [entry["path"] for entry in selected] != sorted(paths) or len(selected) != len(paths):
        raise AdapterError(f"{scope} package paths do not reproduce the full package")
    document: dict[str, Any] = {
        "schema_version": 1,
        "adapter_identifier": ADAPTER_IDENTIFIER,
        "arm": full["arm"],
        "scope": scope,
        "source_commit": full["source_commit"],
        "source_tree": full["source_tree"],
        "files": selected,
    }
    document["manifest_sha256"] = manifest_digest(document)
    return document


def validate_candidate_behavior_map(inventory: dict[str, Any]) -> tuple[list[str], list[str]]:
    mapping = load_json(CANDIDATE_BEHAVIOR_MAP_PATH, "candidate behavior map")
    all_behavior_ids = [item["behavior_id"] for item in inventory["behaviors"]]
    removed = mapping.get("intentionally_removed_behavior_ids") if isinstance(mapping, dict) else None
    clauses = mapping.get("clauses") if isinstance(mapping, dict) else None
    if (
        mapping.get("schema_version") != 6
        or mapping.get("oracle_version") != ORACLE_VERSION
        or mapping.get("inventory_id") != inventory.get("inventory_id")
        or mapping.get("baseline_commit") != inventory.get("baseline_commit")
        or mapping.get("candidate_state") != "approved_candidate_commit"
        or mapping.get("candidate_commit")
        != "23b3d4e38b30f882c4a6f20f293b73f701138e3b"
        or mapping.get("user_wording_approval_status") != "approved"
        or mapping.get("baseline_behavior_count") != len(all_behavior_ids)
        or not isinstance(removed, list)
        or removed != [
            "DLV-ACT-005", "DLV-MODE-004", "DLV-PLAN-005", "DLV-PLAN-006",
            "DLV-STOP-008",
        ]
        or mapping.get("intentionally_removed_behavior_count") != len(removed)
        or not isinstance(clauses, list)
        or mapping.get("clause_count") != len(clauses)
    ):
        raise AdapterError("candidate behavior map does not bind the approved removal")
    mapped: list[str] = []
    for clause in clauses:
        behavior_ids = clause.get("behavior_ids") if isinstance(clause, dict) else None
        if not isinstance(behavior_ids, list) or any(not isinstance(item, str) for item in behavior_ids):
            raise AdapterError("candidate behavior map clauses are malformed")
        mapped.extend(behavior_ids)
    retained = [item for item in all_behavior_ids if item not in set(removed)]
    if (
        len(mapped) != len(set(mapped))
        or set(mapped) != set(retained)
        or any(item in set(removed) for item in mapped)
        or mapping.get("retained_behavior_count") != len(retained)
    ):
        raise AdapterError("candidate behavior map retained coverage is not exact")
    return retained, removed


def validate_readiness_lifecycle() -> dict[str, str]:
    try:
        return readiness_transition.verify_ready(REPO_ROOT)
    except readiness_transition.ReadinessTransitionError as exc:
        raise AdapterError(f"oracle readiness lifecycle is invalid: {exc}") from exc


def validate_readiness(packet: Path, schema: Path) -> dict[str, Any]:
    lifecycle = validate_readiness_lifecycle()
    readiness = load_json(READINESS_PATH, "oracle readiness")
    vocabulary = load_json(VOCABULARY_PATH, "public response schema")
    baseline_manifest = load_json(BASELINE_MANIFEST_PATH, "baseline package manifest")
    candidate_manifest = load_json(CANDIDATE_MANIFEST_PATH, "candidate package manifest")
    approval = load_json(WORDING_APPROVAL_PATH, "wording approval record")
    inventory = load_json(INVENTORY_PATH, "public contract inventory")
    if not isinstance(readiness, dict) or not isinstance(vocabulary, dict):
        raise AdapterError("public readiness artifacts are malformed")
    unknown_fields = set(readiness) - READINESS_ALLOWED_FIELDS
    if unknown_fields:
        raise AdapterError("oracle readiness contains an unknown field")
    for field, allowed in READINESS_NESTED_ALLOWED_FIELDS.items():
        value = readiness.get(field)
        if not isinstance(value, dict) or set(value) - allowed:
            raise AdapterError(f"oracle readiness {field} contains an unknown field")
    behaviors = inventory.get("behaviors") if isinstance(inventory, dict) else None
    if (
        not isinstance(behaviors, list)
        or not behaviors
        or any(not isinstance(item, dict) for item in behaviors)
    ):
        raise AdapterError("public contract inventory behaviors are malformed")
    expected_behavior_ids = [item.get("behavior_id") for item in behaviors]
    if (
        any(not isinstance(item, str) or not item for item in expected_behavior_ids)
        or len(expected_behavior_ids) != len(set(expected_behavior_ids))
    ):
        raise AdapterError("public contract inventory behavior IDs are malformed")
    retained_behavior_ids, removed_behavior_ids = validate_candidate_behavior_map(inventory)
    if (
        readiness.get("schema_version") != READINESS_SCHEMA_VERSION
        or readiness.get("oracle_version") != ORACLE_VERSION
        or vocabulary.get("schema_version") != READINESS_SCHEMA_VERSION
        or vocabulary.get("oracle_version") != ORACLE_VERSION
    ):
        raise AdapterError("oracle readiness or vocabulary version differs from the frozen adapter")
    if readiness.get("status") != "ready":
        raise AdapterError("oracle readiness is not frozen ready")
    if (
        lifecycle.get("status") != "ready"
        or lifecycle.get("sha256") != sha256_file(READINESS_PATH)
        or not nonzero_hex(lifecycle.get("commit"), HEX40, 40)
    ):
        raise AdapterError("oracle readiness lifecycle does not bind the consumed ready bytes")
    failed_gates = [
        field for field in REQUIRED_READINESS_PASS_FIELDS if readiness.get(field) != "pass"
    ]
    if failed_gates:
        raise AdapterError(
            "oracle readiness review, validation, or isolation gate is not passed: "
            + ", ".join(failed_gates)
        )
    commit_fields = (
        "private_evaluator_source_commit",
        "private_evaluator_commit",
        "private_independent_reviewed_source_commit",
        "private_independent_reviewed_final_commit",
        "private_trusted_host_isolation_tested_source_commit",
        "private_trusted_host_isolation_tested_final_commit",
    )
    if any(not nonzero_hex(readiness.get(field), HEX40, 40) for field in commit_fields):
        raise AdapterError("oracle readiness private evaluator commit is missing or malformed")
    source_commit = readiness["private_evaluator_source_commit"]
    final_commit = readiness["private_evaluator_commit"]
    if (
        readiness.get("independent_review_result_kind") != INDEPENDENT_RESULT_KIND
        or readiness.get("trusted_host_isolation_result_kind") != ISOLATION_RESULT_KIND
        or readiness["private_independent_reviewed_source_commit"] != source_commit
        or readiness["private_independent_reviewed_final_commit"] != final_commit
        or readiness["private_trusted_host_isolation_tested_source_commit"] != source_commit
        or readiness["private_trusted_host_isolation_tested_final_commit"] != final_commit
    ):
        raise AdapterError("oracle readiness observed results do not bind the evaluator commits")
    if (
        readiness.get("live_model_feasibility_status") != "pending_official_execution"
        or readiness.get("live_model_execution_performed") is not False
    ):
        raise AdapterError("oracle readiness live execution state is not the frozen pre-run state")
    public_bindings = {
        "public_adapter_identifier": ADAPTER_IDENTIFIER,
        "public_adapter_path": ADAPTER_RELATIVE_PATH,
        "public_adapter_sha256": sha256_file(ADAPTER_PATH),
        "public_execution_policy_path": POLICY_RELATIVE_PATH,
        "public_execution_policy_sha256": sha256_file(POLICY_PATH),
        "public_contract_inventory_sha256": sha256_file(INVENTORY_PATH),
        "baseline_package_manifest_sha256": sha256_file(BASELINE_MANIFEST_PATH),
        "baseline_package_content_manifest_sha256": baseline_manifest.get("manifest_sha256"),
        "baseline_commit": baseline_manifest.get("baseline_commit"),
        "candidate_package_manifest_sha256": sha256_file(CANDIDATE_MANIFEST_PATH),
        "candidate_package_content_manifest_sha256": candidate_manifest.get("manifest_sha256"),
        "candidate_behavior_map_sha256": sha256_file(CANDIDATE_BEHAVIOR_MAP_PATH),
        "candidate_commit": candidate_manifest.get("candidate_commit"),
    }
    if any(readiness.get(key) != value for key, value in public_bindings.items()):
        raise AdapterError(
            "oracle readiness differs from frozen public controller, inventory, baseline, or candidate"
        )
    if (
        not isinstance(approval, dict)
        or set(approval) != {
            "schema_version", "approval_record_id", "candidate_commit", "approval_status",
            "approved_removed_behavior_ids", "scope",
        }
        or approval["schema_version"] != 1
        or approval["candidate_commit"] != candidate_manifest.get("candidate_commit")
        or approval["approval_status"] != "approved"
        or approval["approved_removed_behavior_ids"] != removed_behavior_ids
        or readiness.get("wording_approval_record_path") != WORDING_APPROVAL_RELATIVE_PATH
        or readiness.get("wording_approval_record_sha256") != sha256_file(WORDING_APPROVAL_PATH)
        or readiness.get("wording_approval_candidate_commit") != approval["candidate_commit"]
        or not nonzero_hex(readiness.get("wording_approval_record_commit"), HEX40, 40)
    ):
        raise AdapterError("wording approval record is not exactly bound")
    approval_commit = readiness["wording_approval_record_commit"]
    if (
        bytes(git(["cat-file", "blob", f"{approval_commit}:{WORDING_APPROVAL_RELATIVE_PATH}"], binary=True))
        != WORDING_APPROVAL_PATH.read_bytes()
        or subprocess.run(
            ["git", "merge-base", "--is-ancestor", approval_commit, "HEAD"],
            cwd=REPO_ROOT, check=False, capture_output=True,
        ).returncode
        != 0
    ):
        raise AdapterError("wording approval record is not committed in public ancestry")
    if not nonzero_hex(readiness.get("public_adapter_introducing_commit"), HEX40, 40):
        raise AdapterError("oracle readiness public adapter commit is missing or malformed")
    if readiness.get("model") != EXPECTED_POLICY["model"] or readiness.get("reasoning") != EXPECTED_POLICY["reasoning"]:
        raise AdapterError("oracle readiness model or reasoning differs from policy")
    limits = readiness.get("execution_limits")
    if (
        not isinstance(limits, dict)
        or set(limits) != set(READINESS_EXECUTION_LIMITS)
        or any(type(limits[key]) is not int for key in READINESS_EXECUTION_LIMITS)
        or limits != READINESS_EXECUTION_LIMITS
    ):
        raise AdapterError("oracle readiness execution limits differ from public policy")
    proportionality = readiness.get("proportionality")
    coverage = readiness.get("coverage_credit_policy")
    if (
        not isinstance(proportionality, dict)
        or proportionality.get("safe_grouping_review_status") != "pass"
        or not isinstance(coverage, dict)
        or coverage.get("independent_review_status") != "pass"
    ):
        raise AdapterError("oracle readiness nested independent review gate is not passed")
    baseline_behavior_count = len(expected_behavior_ids)
    behavior_count = len(retained_behavior_ids)
    removal_count = len(removed_behavior_ids)
    case_count = behavior_count + removal_count
    if (
        type(readiness.get("baseline_behavior_id_count")) is not int
        or readiness.get("baseline_behavior_id_count") != baseline_behavior_count
        or type(readiness.get("behavior_id_count")) is not int
        or readiness.get("behavior_id_count") != behavior_count
        or readiness.get("covered_behavior_ids") != retained_behavior_ids
        or type(readiness.get("approved_removal_behavior_count")) is not int
        or readiness.get("approved_removal_behavior_count") != removal_count
        or readiness.get("approved_removed_behavior_ids") != removed_behavior_ids
        or type(readiness.get("case_count")) is not int
        or readiness.get("case_count") != case_count
        or type(readiness.get("single_behavior_case_count")) is not int
        or readiness.get("single_behavior_case_count") != case_count
        or type(readiness.get("multi_behavior_case_count")) is not int
        or readiness.get("multi_behavior_case_count") != 0
        or type(readiness.get("assertion_count")) is not int
        or readiness.get("assertion_count") != case_count
        or type(readiness.get("hard_scored_field_instance_count")) is not int
        or readiness.get("hard_scored_field_instance_count") != case_count * 5
        or type(readiness.get("previous_oracle_case_reuse_count")) is not int
        or readiness.get("previous_oracle_case_reuse_count") != 0
        or type(readiness.get("previous_oracle_case_digest_overlap_count")) is not int
        or readiness.get("previous_oracle_case_digest_overlap_count") != 0
        or type(readiness.get("hidden_comprehension_behavior_count")) is not int
        or readiness.get("hidden_comprehension_behavior_count") != behavior_count
        or type(readiness.get("removal_absence_assertion_count")) is not int
        or readiness.get("removal_absence_assertion_count") != removal_count
        or type(readiness.get("removal_absence_static_control_count")) is not int
        or readiness.get("removal_absence_static_control_count") <= 0
        or type(readiness.get("full_behavior_lane_gate_count")) is not int
        or readiness.get("full_behavior_lane_gate_count") != 0
        or type(readiness.get("static_credit_behavior_count")) is not int
        or readiness.get("static_credit_behavior_count") != 0
        or type(coverage.get("hidden_deterministic_comprehension_assertions")) is not int
        or coverage.get("hidden_deterministic_comprehension_assertions") != case_count
        or type(coverage.get("full_behavior_lane_gates")) is not int
        or coverage.get("full_behavior_lane_gates") != 0
        or type(coverage.get("static_owner_or_route_proofs")) is not int
        or coverage.get("static_owner_or_route_proofs") != 0
        or coverage.get("unchanged_owner_bytes_or_route_text_can_earn_credit") is not False
        or coverage.get("caller_authored_coverage_can_earn_credit") is not False
    ):
        raise AdapterError("oracle readiness direct hidden coverage policy is not exact")
    if (
        readiness.get("deterministic_controls_are_live_arm_execution") is not False
        or readiness.get("deterministic_controls_are_judge_verdict_evidence") is not False
    ):
        raise AdapterError("oracle readiness overstates deterministic control evidence")
    if (
        type(readiness.get("durable_lifecycle_positive_control_count")) is not int
        or readiness.get("durable_lifecycle_positive_control_count") < 1
        or type(readiness.get("lifecycle_order_tamper_negative_control_count")) is not int
        or readiness.get("lifecycle_order_tamper_negative_control_count") < 1
        or type(readiness.get("unbound_verdict_shape_negative_control_count")) is not int
        or readiness.get("unbound_verdict_shape_negative_control_count") != 1
    ):
        raise AdapterError("oracle readiness durable comparison lifecycle controls are incomplete")
    for field in (
        "trusted_root_positive_control_count", "trusted_root_negative_control_count",
        "gate_recomputation_negative_control_count", "lane_schema_negative_control_count",
        "comparability_negative_control_count", "aggregation_negative_control_count",
        "sealed_artifact_packet_positive_control_count",
        "caller_payload_rejection_negative_control_count",
        "artifact_transitive_binding_negative_control_count",
    ):
        if type(readiness.get(field)) is not int or readiness[field] < 1:
            raise AdapterError("oracle readiness trusted-root and recomputation controls are incomplete")
    if (
        readiness.get("judge_packet_structural_blinding_author_status") != "pass"
        or type(readiness.get("judge_packet_schema_control_count")) is not int
        or readiness.get("judge_packet_schema_control_count") <= 0
        or type(readiness.get("discarded_channel_reachability_control_count")) is not int
        or readiness.get("discarded_channel_reachability_control_count") <= 0
        or type(readiness.get("clean_content_preservation_control_count")) is not int
        or readiness.get("clean_content_preservation_control_count") <= 0
        or readiness.get("rationale_discarded_before_judge_input") is not True
        or readiness.get("rationale_affects_deterministic_score") is not False
        or readiness.get("rationale_affects_combined_verdict") is not False
    ):
        raise AdapterError("oracle readiness structural judge blinding controls are not passed")
    require_regular_file(packet, "projected packet")
    require_regular_file(schema, "supplied public schema")
    expected_packet = readiness.get("private_projected_packet_sha256")
    expected_schema = readiness.get("per_arm_response_schema_sha256")
    if not HEX64.fullmatch(str(expected_packet)) or sha256_file(packet) != expected_packet:
        raise AdapterError("projected packet digest differs from frozen readiness")
    if not HEX64.fullmatch(str(expected_schema)) or sha256_file(schema) != expected_schema:
        raise AdapterError("supplied public schema digest differs from frozen readiness")
    if schema.read_bytes() != VOCABULARY_PATH.read_bytes():
        raise AdapterError("supplied public schema is not the frozen public vocabulary")
    if readiness.get("projected_packet_bytes") != packet.stat().st_size or readiness.get(
        "projected_packet_lexical_word_count"
    ) != lexical_word_count(packet.read_text(encoding="utf-8")):
        raise AdapterError("projected packet size differs from frozen readiness")
    response_schema = vocabulary.get("per_arm_response_schema")
    if response_schema != expected_response_schema(vocabulary, case_count):
        raise AdapterError("public vocabulary response schema differs from the frozen contract")
    return readiness


def state_path_for(runtime_root: Path) -> Path:
    return runtime_root / CONTROL_RELATIVE / STATE_NAME


def control_root(runtime_root: Path) -> Path:
    return runtime_root / CONTROL_RELATIVE


def runtime_identity(runtime_root: Path) -> dict[str, int | str]:
    root = require_directory(runtime_root.resolve(strict=True), "runtime root")
    if root.parent != v11.STAGE_ROOT or not SAFE_RUNTIME.fullmatch(root.name):
        raise AdapterError("runtime root is not canonical /private/tmp Deliver v12 state")
    return {"real_path": str(root), "device": root.stat().st_dev, "inode": root.stat().st_ino}


def initial_arm_state() -> dict[str, Any]:
    return {
        "status": "pending",
        "arm_started_at": None,
        "deadline_at": None,
        "attempts": [],
        "restart_count": 0,
        "last_poll_at": None,
        "last_progress_at": None,
        "progress_fingerprint": None,
        "failure_classification": None,
        "seal_sha256": None,
        "artifacts": None,
    }


def initialize_runtime(
    parent: Path,
    packet: Path,
    schema: Path,
    baseline_package: Path,
    candidate_package: Path,
    candidate_manifest: Path,
    run_label_map: Path,
    baseline_manifest: Path = BASELINE_MANIFEST_PATH,
) -> dict[str, Any]:
    policy = load_policy()
    v11_manifest = verify_v11_files()
    evaluator = repository_identity()
    readiness = validate_readiness(packet, schema)
    readiness_lifecycle = validate_readiness_lifecycle()
    require_regular_file(baseline_manifest, "baseline package authority")
    if (
        sha256_file(baseline_manifest) != readiness["baseline_package_manifest_sha256"]
        or baseline_manifest.read_bytes() != BASELINE_MANIFEST_PATH.read_bytes()
    ):
        raise AdapterError("baseline package authority differs from frozen public manifest")
    parent = require_directory(parent.resolve(strict=True), "runtime parent")
    if parent != v11.STAGE_ROOT:
        raise AdapterError("v11 composition requires the safe parent /private/tmp")
    require_regular_file(run_label_map, "run label map")
    baseline, baseline_source = verify_package(baseline_package, baseline_manifest, "baseline")
    require_regular_file(candidate_manifest, "candidate package authority")
    if (
        sha256_file(candidate_manifest) != readiness["candidate_package_manifest_sha256"]
        or candidate_manifest.read_bytes() != CANDIDATE_MANIFEST_PATH.read_bytes()
    ):
        raise AdapterError("candidate package authority differs from frozen public manifest")
    candidate, candidate_source = verify_package(candidate_package, candidate_manifest, "candidate")
    run_id = uuid.uuid4().hex
    nonce = secrets.token_hex(32)
    runtime_root = parent / f"deliver-eval-v12-{run_id}"
    try:
        runtime_root.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise AdapterError("generated runtime identity unexpectedly already exists") from exc
    try:
        control = control_root(runtime_root)
        inputs = control / "inputs"
        arms_root = control / "arms"
        inputs.mkdir(parents=True, mode=0o700)
        arms_root.mkdir(mode=0o700)
        input_specs = (
            (packet, inputs / "projected-packet"),
            (schema, inputs / "response-schema.json"),
            (run_label_map, inputs / "run-label-map"),
        )
        for source, destination in input_specs:
            write_once(destination, source.read_bytes())
        if (
            sha256_file(inputs / "projected-packet") != readiness["private_projected_packet_sha256"]
            or sha256_file(inputs / "response-schema.json")
            != readiness["per_arm_response_schema_sha256"]
        ):
            raise AdapterError("frozen packet or schema changed during initialization")
        bindings: dict[str, Any] = {}
        for arm, source_root, manifest, source_binding in (
            ("baseline", baseline_package, baseline, baseline_source),
            ("candidate", candidate_package, candidate, candidate_source),
        ):
            arm_root = arms_root / arm
            arm_root.mkdir(mode=0o700)
            readability = arm_root / "readability-package"
            copy_package(source_root.resolve(strict=True), readability, manifest)
            write_once_json(arm_root / "package-manifest.json", manifest)
            staged_manifest, staged_identity = verify_staged_package(readability, manifest)
            behavior_manifest = scoped_package_manifest(
                manifest, "behavior_runner", manifest["role_paths"]["behavior_runner_paths"]
            )
            behavior_root = arm_root / "behavior-package"
            copy_package(readability, behavior_root, behavior_manifest)
            behavior_manifest_path = arm_root / "behavior-package-manifest.json"
            write_once_json(behavior_manifest_path, behavior_manifest)
            reproduced_behavior, behavior_identity = verify_staged_package(
                behavior_root, behavior_manifest
            )
            skill_files = sorted(behavior_root.rglob("SKILL.md"))
            if len(skill_files) != 1 or skill_files[0].relative_to(behavior_root).as_posix() != "skills/deliver/SKILL.md":
                raise AdapterError(f"{arm} behavior package must expose only Deliver SKILL.md")
            bindings[arm] = {
                "source_root": source_binding,
                "staged_root": staged_identity,
                "package_manifest": staged_manifest,
                "package_manifest_sha256": staged_manifest["manifest_sha256"],
                "behavior_staged_root": behavior_identity,
                "behavior_package_manifest": reproduced_behavior,
                "behavior_package_manifest_sha256": reproduced_behavior["manifest_sha256"],
            }
        sentinel = v11.ensure_external_sentinel(runtime_root)
        binding = {
            "adapter_identifier": ADAPTER_IDENTIFIER,
            "evaluator": evaluator,
            "runtime": runtime_identity(runtime_root),
            "packet_sha256": sha256_file(inputs / "projected-packet"),
            "schema_sha256": sha256_file(inputs / "response-schema.json"),
            "execution_policy_sha256": sha256_file(POLICY_PATH),
            "run_label_map_sha256": sha256_file(inputs / "run-label-map"),
            "public_readiness_sha256": sha256_file(READINESS_PATH),
            "public_readiness_commit": readiness_lifecycle["commit"],
            "wording_approval_sha256": sha256_file(WORDING_APPROVAL_PATH),
            "v11_file_manifest_sha256": v11_manifest["manifest_sha256"],
            "model": policy["model"],
            "reasoning": policy["reasoning"],
            "arm_order": policy["arm_order"],
            "packages": bindings,
            "external_sentinel": sentinel,
        }
        state: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "adapter_identifier": ADAPTER_IDENTIFIER,
            "run_id": run_id,
            "nonce": nonce,
            "created_at": int(time.time()),
            "binding": binding,
            "binding_sha256": sha256_bytes(canonical_json(binding)),
            "arms": {arm: initial_arm_state() for arm in ARMS},
            "handoff": {"status": "pending", "sha256": None},
        }
        path = state_path_for(runtime_root)
        atomic_json(path, state)
        return {
            "adapter_identifier": ADAPTER_IDENTIFIER,
            "run_id": run_id,
            "nonce": nonce,
            "runtime_root": str(runtime_root),
            "state_path": str(path),
            "binding_sha256": state["binding_sha256"],
        }
    except BaseException:
        if runtime_root.exists() and runtime_root.parent == v11.STAGE_ROOT and SAFE_RUNTIME.fullmatch(runtime_root.name):
            shutil.rmtree(runtime_root)
        raise


def validate_state(document: Any, path: Path) -> dict[str, Any]:
    if not isinstance(document, dict) or set(document) != {
        "schema_version", "adapter_identifier", "run_id", "nonce", "created_at",
        "binding", "binding_sha256", "arms", "handoff",
    }:
        raise AdapterError("controller state fields are not exact")
    if (
        document["schema_version"] != SCHEMA_VERSION
        or document["adapter_identifier"] != ADAPTER_IDENTIFIER
        or not re.fullmatch(r"[0-9a-f]{32}", str(document["run_id"]))
        or not re.fullmatch(r"[0-9a-f]{64}", str(document["nonce"]))
        or not isinstance(document["created_at"], int)
        or set(document["arms"]) != set(ARMS)
        or set(document["handoff"]) != {"status", "sha256"}
    ):
        raise AdapterError("controller state identity is invalid")
    binding = document["binding"]
    if not isinstance(binding, dict) or sha256_bytes(canonical_json(binding)) != document["binding_sha256"]:
        raise AdapterError("controller immutable binding digest is invalid")
    runtime = Path(str(binding.get("runtime", {}).get("real_path", "")))
    if path != state_path_for(runtime) or runtime_identity(runtime) != binding["runtime"]:
        raise AdapterError("controller state path or filesystem identity drifted")
    if binding.get("adapter_identifier") != ADAPTER_IDENTIFIER:
        raise AdapterError("controller state belongs to another adapter")
    for arm in ARMS:
        value = document["arms"][arm]
        if not isinstance(value, dict) or set(value) != set(initial_arm_state()):
            raise AdapterError(f"{arm} controller state fields are not exact")
        if value["status"] not in {"pending", "launching", "running", "process_complete", "failed", "sealed"}:
            raise AdapterError(f"{arm} controller status is invalid")
        if not isinstance(value["attempts"], list) or len(value["attempts"]) > 2:
            raise AdapterError(f"{arm} attempt state is invalid")
        if value["restart_count"] not in {0, 1}:
            raise AdapterError(f"{arm} restart count is invalid")
        arm_started_at = value["arm_started_at"]
        deadline_at = value["deadline_at"]
        invalid_arm_clock = (
            (arm_started_at is None) != (deadline_at is None)
            or (
                arm_started_at is not None
                and (
                    isinstance(arm_started_at, bool)
                    or not isinstance(arm_started_at, (int, float))
                    or not -float("inf") < arm_started_at < float("inf")
                    or isinstance(deadline_at, bool)
                    or not isinstance(deadline_at, (int, float))
                    or not -float("inf") < deadline_at < float("inf")
                    or deadline_at != arm_started_at + EXPECTED_POLICY["arm_total_seconds"]
                )
            )
            or (not value["attempts"] and arm_started_at is not None)
            or (value["attempts"] and arm_started_at is None)
        )
        if invalid_arm_clock:
            raise AdapterError(f"{arm} arm deadline identity is invalid")
        for number, attempt in enumerate(value["attempts"], 1):
            if not isinstance(attempt, dict) or set(attempt) != {
                "attempt", "started_at", "process", "result_path", "stdout_path", "stderr_path",
            }:
                raise AdapterError(f"{arm} attempt fields are not exact")
            process = attempt["process"]
            invalid_process = process is not None and (
                not isinstance(process, dict)
                or set(process) != {"pid", "ps_identity_sha256", "command_sha256"}
                or isinstance(process["pid"], bool)
                or not isinstance(process["pid"], int)
                or process["pid"] <= 0
                or not HEX64.fullmatch(str(process["ps_identity_sha256"]))
                or not HEX64.fullmatch(str(process["command_sha256"]))
            )
            if (
                attempt["attempt"] != number
                or isinstance(attempt["started_at"], bool)
                or not isinstance(attempt["started_at"], (int, float))
                or not -float("inf") < attempt["started_at"] < float("inf")
                or invalid_process
                or any(not isinstance(attempt[key], str) or not attempt[key] for key in (
                    "result_path", "stdout_path", "stderr_path",
                ))
                or (number == 1 and attempt["started_at"] != arm_started_at)
                or attempt["started_at"] < arm_started_at
                or attempt["started_at"] >= deadline_at
            ):
                raise AdapterError(f"{arm} attempt identity is invalid")
        process_may_be_unbound = value["status"] == "launching" or (
            value["status"] == "failed"
            and value["failure_classification"] == "infrastructure_failure_before_output"
        )
        if (
            not process_may_be_unbound
            and value["attempts"]
            and value["attempts"][-1]["process"] is None
        ):
            raise AdapterError(f"{arm} has an unbound process outside launch setup")
        if value["seal_sha256"] is not None and not HEX64.fullmatch(str(value["seal_sha256"])):
            raise AdapterError(f"{arm} seal digest is invalid")
    if document["handoff"]["status"] not in {"pending", "frozen"} or (
        document["handoff"]["sha256"] is not None
        and not HEX64.fullmatch(str(document["handoff"]["sha256"]))
    ):
        raise AdapterError("handoff state is invalid")
    return document


def load_state(path: Path) -> dict[str, Any]:
    path = require_regular_file(path.resolve(strict=True), "controller state")
    return validate_state(load_json(path, "controller state"), path)


@contextlib.contextmanager
def locked_state(path: Path) -> Iterable[dict[str, Any]]:
    path = path.resolve(strict=True)
    lock_path = path.with_suffix(".lock")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    with os.fdopen(descriptor, "r+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = load_state(path)
        try:
            yield state
        finally:
            atomic_json(path, state)


def verify_live_bindings(state: dict[str, Any]) -> None:
    policy = load_policy()
    if sha256_file(POLICY_PATH) != state["binding"]["execution_policy_sha256"]:
        raise AdapterError("execution policy digest drifted")
    if sha256_file(READINESS_PATH) != state["binding"].get("public_readiness_sha256"):
        raise AdapterError("public readiness digest drifted")
    readiness_lifecycle = validate_readiness_lifecycle()
    if (
        readiness_lifecycle.get("commit") != state["binding"].get("public_readiness_commit")
        or readiness_lifecycle.get("sha256") != state["binding"].get("public_readiness_sha256")
    ):
        raise AdapterError("public readiness committed lifecycle drifted")
    if sha256_file(WORDING_APPROVAL_PATH) != state["binding"].get("wording_approval_sha256"):
        raise AdapterError("wording approval digest drifted")
    if policy["model"] != state["binding"]["model"] or policy["reasoning"] != state["binding"]["reasoning"]:
        raise AdapterError("model or reasoning binding drifted")
    v11_manifest = verify_v11_files()
    if v11_manifest["manifest_sha256"] != state["binding"]["v11_file_manifest_sha256"]:
        raise AdapterError("v11 immutable manifest binding drifted")
    evaluator = repository_identity()
    if evaluator != state["binding"]["evaluator"]:
        raise AdapterError("clean evaluator Git identity drifted")
    runtime = Path(state["binding"]["runtime"]["real_path"])
    v11.verify_external_sentinel(state["binding"]["external_sentinel"], runtime)
    inputs = control_root(runtime) / "inputs"
    for name, key in (
        ("projected-packet", "packet_sha256"),
        ("response-schema.json", "schema_sha256"),
        ("run-label-map", "run_label_map_sha256"),
    ):
        if sha256_file(inputs / name) != state["binding"][key]:
            raise AdapterError(f"frozen input drifted: {name}")
    for arm in ARMS:
        package = state["binding"]["packages"][arm]
        staged = Path(package["staged_root"]["real_path"])
        if verify_staged_package(staged, package["package_manifest"])[1] != package["staged_root"]:
            raise AdapterError(f"{arm} staged package filesystem identity drifted")
        behavior_staged = Path(package["behavior_staged_root"]["real_path"])
        if verify_staged_package(
            behavior_staged, package["behavior_package_manifest"]
        )[1] != package["behavior_staged_root"]:
            raise AdapterError(f"{arm} behavior package filesystem identity drifted")
        source = Path(package["source_root"]["real_path"])
        source_identity = package["source_root"]
        require_directory(source, f"{arm} source package")
        if source.stat().st_dev != source_identity["device"] or source.stat().st_ino != source_identity["inode"]:
            raise AdapterError(f"{arm} source package root identity drifted")
        authority = Path(source_identity["authority_path"])
        if sha256_file(authority) != source_identity["authority_sha256"]:
            raise AdapterError(f"{arm} package authority drifted")
        verify_package(source, authority, arm)


def worker_command(state_path: Path, arm: str, attempt: int) -> list[str]:
    return [
        sys.executable, str(ADAPTER_PATH), "_worker", "--state", str(state_path),
        "--arm", arm, "--attempt", str(attempt),
    ]


def process_identity(pid: int, command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
        check=False, capture_output=True, text=True,
    )
    line = result.stdout.strip()
    if result.returncode or not line:
        raise AdapterError("worker process is not alive for identity capture")
    return {
        "pid": pid,
        "ps_identity_sha256": sha256_bytes(line.encode()),
        "command_sha256": sha256_bytes(canonical_json(command)),
    }


def same_process(evidence: dict[str, Any], command: list[str]) -> bool:
    try:
        current = process_identity(int(evidence["pid"]), command)
    except (AdapterError, KeyError, TypeError, ValueError):
        return False
    return current == evidence


def output_observed(arm_root: Path, attempt: int) -> bool:
    attempt_root = arm_root / "comprehension" / f"attempt-{attempt}"
    candidates = (
        attempt_root / "trace.jsonl",
        arm_root / "comprehension" / "runner-sibling-probe" / "runner-streams"
        / f"attempt-{attempt}" / "comprehension" / "trace.jsonl",
        attempt_root / "response.json",
    )
    return any(path.is_file() and path.stat().st_size > 0 for path in candidates)


def progress_fingerprint(runtime: Path, arm: str) -> str:
    arm_root = control_root(runtime) / "arms" / arm
    roots = [arm_root, runtime / v11.SIBLING_PROBE / "runner-streams"]
    entries: list[list[int | str]] = []
    for root in roots:
        if not root.exists() or root.is_symlink():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            info = path.stat()
            entries.append([str(path.relative_to(runtime)), info.st_size, info.st_mtime_ns])
    return sha256_bytes(canonical_json(entries))


def spawn_worker(
    command: list[str], stdout_path: Path, stderr_path: Path,
) -> subprocess.Popen[bytes]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout = stdout_path.open("xb")
    stderr = stderr_path.open("xb")
    try:
        return subprocess.Popen(
            command, cwd=REPO_ROOT, stdin=subprocess.DEVNULL, stdout=stdout,
            stderr=stderr, start_new_session=True,
        )
    finally:
        stdout.close()
        stderr.close()


def arm_deadline_expired(arm_state: dict[str, Any], now: float) -> bool:
    deadline = arm_state["deadline_at"]
    return deadline is not None and now >= float(deadline)


def fail_arm_total_timeout(arm_state: dict[str, Any]) -> None:
    arm_state["status"] = "failed"
    arm_state["failure_classification"] = "arm_total_timeout"


def launch_arm(
    state_path: Path,
    arm: str,
    *,
    restart_infrastructure: bool = False,
    launcher: Callable[[list[str], Path, Path], Any] = spawn_worker,
    identity_reader: Callable[[int, list[str]], dict[str, Any]] = process_identity,
    terminator: Callable[[dict[str, Any], list[str]], None] | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise AdapterError("arm must be baseline or candidate")
    supplied_now = now
    now = time.time() if now is None else now
    terminator = terminate_verified_process if terminator is None else terminator
    with locked_state(state_path) as state:
        verify_live_bindings(state)
        arm_state = state["arms"][arm]
        if arm == "candidate" and state["arms"]["baseline"]["status"] != "sealed":
            raise AdapterError("candidate cannot launch before baseline is sealed")
        if arm_state["status"] == "sealed":
            raise AdapterError("sealed arm cannot launch again")
        if arm_deadline_expired(arm_state, now):
            if arm_state["status"] in {"launching", "running"} and arm_state["attempts"]:
                attempt = arm_state["attempts"][-1]
                command = worker_command(state_path.resolve(), arm, attempt["attempt"])
                if attempt["process"] is not None and same_process(attempt["process"], command):
                    terminator(attempt["process"], command)
            fail_arm_total_timeout(arm_state)
            raise AdapterError("arm total timeout expired before launch")
        if arm_state["status"] in {"launching", "running"}:
            attempt = arm_state["attempts"][-1]
            command = worker_command(state_path.resolve(), arm, attempt["attempt"])
            if same_process(attempt["process"], command):
                return {"arm": arm, "status": "running", "reattached": True, "attempt": attempt["attempt"]}
            raise AdapterError("reattachment rejected because the verified process is gone or changed")
        runtime = Path(state["binding"]["runtime"]["real_path"])
        arm_root = control_root(runtime) / "arms" / arm
        if arm_state["attempts"]:
            previous = arm_state["attempts"][-1]
            if not restart_infrastructure:
                raise AdapterError("failed arm requires an explicit permitted infrastructure restart")
            if (
                arm_state["restart_count"] >= EXPECTED_POLICY["maximum_pre_output_infrastructure_restarts"]
                or arm_state["failure_classification"] != "infrastructure_failure_before_output"
                or output_observed(arm_root, previous["attempt"])
            ):
                raise AdapterError("arm is not eligible for a pre-output infrastructure restart")
            arm_state["restart_count"] += 1
        elif restart_infrastructure:
            raise AdapterError("first semantic attempt is not a restart")
        attempt_number = len(arm_state["attempts"]) + 1
        attempt_root = arm_root / "controller" / f"attempt-{attempt_number}"
        attempt_root.mkdir(parents=True, mode=0o700)
        command = worker_command(state_path.resolve(), arm, attempt_number)
        started_at = now
        if arm_state["arm_started_at"] is None:
            arm_state["arm_started_at"] = started_at
            arm_state["deadline_at"] = started_at + EXPECTED_POLICY["arm_total_seconds"]
        attempt = {
            "attempt": attempt_number,
            "started_at": started_at,
            "process": None,
            "result_path": str(attempt_root / "result.json"),
            "stdout_path": str(attempt_root / "stdout.txt"),
            "stderr_path": str(attempt_root / "stderr.txt"),
        }
        arm_state["attempts"].append(attempt)
        arm_state["status"] = "launching"
        arm_state["failure_classification"] = None
        atomic_json(state_path, state)
        process: Any | None = None
        try:
            process = launcher(command, Path(attempt["stdout_path"]), Path(attempt["stderr_path"]))
            evidence = identity_reader(int(process.pid), command)
        except BaseException as exc:
            if process is not None and callable(getattr(process, "poll", None)) and process.poll() is None:
                process.kill()
                process.wait()
            arm_state["status"] = "failed"
            arm_state["failure_classification"] = "infrastructure_failure_before_output"
            write_once_json(Path(attempt["result_path"]), {
                "schema_version": 1, "attempt": attempt_number, "exit_code": None,
                "error_type": type(exc).__name__, "error": str(exc),
            })
            raise
        attempt["process"] = evidence
        after_launch = time.time() if supplied_now is None else now
        if arm_deadline_expired(arm_state, after_launch):
            terminator(evidence, command)
            fail_arm_total_timeout(arm_state)
            raise AdapterError("arm total timeout expired during launch")
        arm_state["status"] = "running"
        arm_state["last_poll_at"] = started_at
        arm_state["last_progress_at"] = started_at
        arm_state["progress_fingerprint"] = progress_fingerprint(runtime, arm)
        return {
            "arm": arm,
            "status": "running",
            "reattached": False,
            "attempt": attempt_number,
            "pid": process.pid,
            "arm_started_at": arm_state["arm_started_at"],
            "deadline_at": arm_state["deadline_at"],
        }


def terminate_verified_process(evidence: dict[str, Any], command: list[str]) -> None:
    if not same_process(evidence, command):
        raise AdapterError("refusing to signal an unverified or replaced worker process")
    pid = int(evidence["pid"])
    try:
        if os.getpgid(pid) != pid:
            raise AdapterError("worker is not leader of its isolated process group")
        os.kill(pid, signal.SIGINT)
    except ProcessLookupError:
        return
    deadline = time.time() + 10
    while time.time() < deadline:
        if not same_process(evidence, command):
            return
        time.sleep(0.1)
    if same_process(evidence, command):
        os.killpg(pid, signal.SIGKILL)


def worker_result(attempt: dict[str, Any]) -> dict[str, Any] | None:
    path = Path(attempt["result_path"])
    if not path.exists():
        return None
    value = load_json(path, "worker result")
    if not isinstance(value, dict) or value.get("schema_version") != 1 or value.get("attempt") != attempt["attempt"]:
        raise AdapterError("worker result identity is invalid")
    return value


def poll_arm(
    state_path: Path,
    arm: str,
    *,
    now: float | None = None,
    terminator: Callable[[dict[str, Any], list[str]], None] = terminate_verified_process,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise AdapterError("arm must be baseline or candidate")
    now = time.time() if now is None else now
    with locked_state(state_path) as state:
        verify_live_bindings(state)
        arm_state = state["arms"][arm]
        runtime = Path(state["binding"]["runtime"]["real_path"])
        response: dict[str, Any] = {"arm": arm, "status": arm_state["status"]}
        timeout_eligible = arm_state["status"] in {
            "launching", "running", "process_complete",
        } or (
            arm_state["status"] == "failed"
            and arm_state["failure_classification"] == "infrastructure_failure_before_output"
        )
        if timeout_eligible and arm_deadline_expired(arm_state, now):
            if arm_state["status"] == "running":
                attempt = arm_state["attempts"][-1]
                command = worker_command(state_path.resolve(), arm, attempt["attempt"])
                if same_process(attempt["process"], command):
                    terminator(attempt["process"], command)
            fail_arm_total_timeout(arm_state)
            response.update({
                "status": "failed",
                "failure_classification": "arm_total_timeout",
                "restart_permitted": False,
            })
            return response
        if arm_state["status"] != "running":
            return response
        if now - float(arm_state["last_poll_at"]) < EXPECTED_POLICY["poll_interval_seconds"]:
            response["poll_deferred"] = True
            response["next_poll_after"] = arm_state["last_poll_at"] + EXPECTED_POLICY["poll_interval_seconds"]
            return response
        arm_state["last_poll_at"] = now
        attempt = arm_state["attempts"][-1]
        command = worker_command(state_path.resolve(), arm, attempt["attempt"])
        result = worker_result(attempt)
        alive = same_process(attempt["process"], command)
        if result is not None and not alive:
            exit_code = result.get("exit_code")
            if exit_code == 0:
                arm_state["status"] = "process_complete"
                response["status"] = "process_complete"
                return response
            arm_root = control_root(runtime) / "arms" / arm
            before_output = not output_observed(arm_root, attempt["attempt"])
            arm_state["status"] = "failed"
            arm_state["failure_classification"] = (
                "infrastructure_failure_before_output" if before_output
                else "terminal_failure_after_output"
            )
            response.update({
                "status": "failed",
                "failure_classification": arm_state["failure_classification"],
                "restart_permitted": before_output and arm_state["restart_count"] == 0,
            })
            return response
        if not alive:
            arm_state["status"] = "failed"
            arm_root = control_root(runtime) / "arms" / arm
            before_output = not output_observed(arm_root, attempt["attempt"])
            arm_state["failure_classification"] = (
                "infrastructure_failure_before_output" if before_output
                else "terminal_failure_after_output"
            )
            response.update({"status": "failed", "failure_classification": arm_state["failure_classification"]})
            return response
        fingerprint = progress_fingerprint(runtime, arm)
        if fingerprint != arm_state["progress_fingerprint"]:
            arm_state["progress_fingerprint"] = fingerprint
            arm_state["last_progress_at"] = now
        progress_path = control_root(runtime) / "arms" / arm / "controller" / "progress.json"
        progress = load_json(progress_path, "worker progress") if progress_path.exists() else None
        classification: str | None = None
        if isinstance(progress, dict) and isinstance(progress.get("process_started_at"), (int, float)) and (
            now - float(progress["process_started_at"]) >= EXPECTED_POLICY["process_limit_seconds"]
        ):
            classification = "process_timeout"
        elif now - float(arm_state["last_progress_at"]) >= EXPECTED_POLICY["no_progress_seconds"]:
            classification = "no_progress_timeout"
        if classification is not None:
            terminator(attempt["process"], command)
            arm_state["status"] = "failed"
            arm_state["failure_classification"] = classification
            response.update({"status": "failed", "failure_classification": classification, "restart_permitted": False})
            return response
        response.update({
            "status": "running",
            "poll_deferred": False,
            "next_poll_after": now + EXPECTED_POLICY["poll_interval_seconds"],
            "progress": progress,
            "shell_yield_is_failure": False,
        })
        return response


def progress_path(state: dict[str, Any], arm: str) -> Path:
    runtime = Path(state["binding"]["runtime"]["real_path"])
    return control_root(runtime) / "arms" / arm / "controller" / "progress.json"


def record_progress(
    state: dict[str, Any], arm: str, phase: str, *, process_started_at: float | None,
    expected_input: str | None = None,
) -> None:
    path = progress_path(state, arm)
    previous = load_json(path, "worker progress") if path.exists() else {"sequence": 0}
    atomic_json(path, {
        "schema_version": 1,
        "arm": arm,
        "sequence": int(previous["sequence"]) + 1,
        "phase": phase,
        "recorded_at": time.time(),
        "process_started_at": process_started_at,
        "expected_input": expected_input,
    })


def wait_for_regular_input(
    state: dict[str, Any], arm: str, path: Path, phase: str, deadline: float,
) -> Path:
    record_progress(state, arm, phase, process_started_at=None, expected_input=str(path))
    while True:
        if path.exists() or path.is_symlink():
            return require_regular_file(path, phase)
        if time.time() >= deadline:
            raise AdapterError("arm total timeout while waiting for evaluator evidence")
        time.sleep(EXPECTED_POLICY["poll_interval_seconds"])


def require_arm_time_remaining(deadline: float, now: float | None = None) -> None:
    now = time.time() if now is None else now
    if now >= deadline:
        raise AdapterError("arm total timeout")


def extract_agent_response(trace: Path) -> str:
    v11.validate_runner_trace(trace.read_bytes())
    messages: list[str] = []
    for line in trace.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        item = event.get("item")
        if event.get("type") == "item.completed" and isinstance(item, dict) and item.get("type") == "agent_message":
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                messages.append(text)
    if len(messages) != 1:
        raise AdapterError("comprehension trace must contain exactly one final agent message")
    return messages[0]


def validate_schema(value: Any, schema: Any, location: str = "$") -> None:
    if not isinstance(schema, dict):
        raise AdapterError(f"schema node is invalid at {location}")
    if "enum" in schema and value not in schema["enum"]:
        raise AdapterError(f"response violates enum at {location}")
    expected_type = schema.get("type")
    matches = {
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }
    if expected_type is not None and (expected_type not in matches or not matches[expected_type]):
        raise AdapterError(f"response type is invalid at {location}")
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)) or (
            "maxItems" in schema and len(value) > int(schema["maxItems"])
        ):
            raise AdapterError(f"response array length is invalid at {location}")
        if schema.get("uniqueItems") and len({canonical_json(item) for item in value}) != len(value):
            raise AdapterError(f"response array items are not unique at {location}")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], f"{location}[{index}]")
    if isinstance(value, dict):
        required = schema.get("required", [])
        if any(key not in value for key in required):
            raise AdapterError(f"response object is missing a required key at {location}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and any(key not in properties for key in value):
            raise AdapterError(f"response object has an unexpected key at {location}")
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], f"{location}.{key}")
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)) or (
            "maxLength" in schema and len(value) > int(schema["maxLength"])
        ):
            raise AdapterError(f"response string length is invalid at {location}")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise AdapterError(f"response string pattern is invalid at {location}")


def validate_response(response_path: Path, schema_path: Path) -> Any:
    value = load_json(response_path, "comprehension response")
    vocabulary = load_json(schema_path, "public response schema")
    schema = vocabulary.get("per_arm_response_schema") if isinstance(vocabulary, dict) else None
    validate_schema(value, schema)
    case_codes = [item["case_code"] for item in value]
    if len(case_codes) != len(set(case_codes)):
        raise AdapterError("comprehension response case codes are not unique")
    return value


def run_comprehension(state: dict[str, Any], arm: str, attempt: int, deadline: float) -> None:
    require_arm_time_remaining(deadline)
    runtime = Path(state["binding"]["runtime"]["real_path"])
    arm_root = control_root(runtime) / "arms" / arm
    root = arm_root / "comprehension" / f"attempt-{attempt}"
    root.mkdir(parents=True, mode=0o700)
    repo = root / "repo"
    manifest = state["binding"]["packages"][arm]["package_manifest"]
    copy_package(arm_root / "readability-package", repo, manifest)
    packet = control_root(runtime) / "inputs" / "projected-packet"
    schema = control_root(runtime) / "inputs" / "response-schema.json"
    staged_packet = root / "projected-packet"
    write_once(staged_packet, packet.read_bytes())
    if sha256_file(staged_packet) != state["binding"]["packet_sha256"]:
        raise AdapterError("arm projected packet staging drifted")
    profile = root / "runner.sb"
    profile.write_text(v11.sandbox_profile(root), encoding="utf-8")
    sentinel = Path(state["binding"]["external_sentinel"]["path"])
    auth_copy = v11.prepare_codex_state(profile)
    trace, stderr = root / "trace.jsonl", root / "stderr.txt"
    v11.ensure_sibling_probe(root)
    trace_stream, stderr_stream = v11.parent_stream_paths(root, "comprehension")
    command = v11.codex_command(repo, profile, sentinel)
    started = time.time()
    record_progress(state, arm, "comprehension", process_started_at=started)
    remaining = min(EXPECTED_POLICY["process_limit_seconds"], max(1, deadline - started))
    try:
        result = v11.execute_codex(
            command, v11.FIRST_TOOL_GATE_PROMPT + staged_packet.read_text(encoding="utf-8"), repo,
            trace_path=trace, stderr_path=stderr, trace_stream_path=trace_stream,
            stderr_stream_path=stderr_stream, total_timeout_seconds=remaining,
            inactivity_timeout_seconds=EXPECTED_POLICY["no_progress_seconds"],
        )
    finally:
        auth_copy.unlink(missing_ok=True)
    if result.returncode:
        raise AdapterError(f"comprehension runner failed with exit {result.returncode}")
    response_text = extract_agent_response(trace)
    response = root / "response.json"
    write_once(response, response_text.encode("utf-8"))
    validate_response(response, schema)
    write_once_json(root / "metadata.json", {
        "schema_version": 1,
        "model": EXPECTED_POLICY["model"],
        "reasoning": EXPECTED_POLICY["reasoning"],
        "command_sha256": sha256_bytes(canonical_json(command)),
        "packet_sha256": sha256_file(staged_packet),
        "schema_sha256": sha256_file(schema),
        "trace_sha256": sha256_file(trace),
        "stderr_sha256": sha256_file(stderr),
        "response_sha256": sha256_file(response),
        "duration_milliseconds": max(1, int((time.time() - started) * 1000)),
    })


def run_behavior_lanes(state: dict[str, Any], arm: str, deadline: float) -> None:
    runtime = Path(state["binding"]["runtime"]["real_path"])
    arm_root = control_root(runtime) / "arms" / arm
    package = arm_root / "behavior-package"
    preflight = arm_root / "runner-preflight.json"
    require_arm_time_remaining(deadline)
    record_progress(state, arm, "v11_runner_preflight", process_started_at=time.time())
    v11.preflight_runner(preflight)
    require_arm_time_remaining(deadline)
    for scenario in SCENARIOS:
        stage = runtime / f"{scenario}-{arm}"
        record_progress(state, arm, f"{scenario}:prepare", process_started_at=None)
        v11.prepare_scenario(scenario, package, stage, preflight)
        require_arm_time_remaining(deadline)
        record_progress(state, arm, f"{scenario}:pre-packet", process_started_at=time.time())
        v11.run_scenario(stage, "pre-packet")
        require_arm_time_remaining(deadline)
        inbox = arm_root / "inbox" / scenario
        validation = wait_for_regular_input(
            state, arm, inbox / "pre-packet-validation.log",
            f"{scenario}:awaiting_pre_packet_validation", deadline,
        )
        v11.freeze_pre_packet(stage, validation)
        v11.stage_review_packet(stage)
        require_arm_time_remaining(deadline)
        record_progress(state, arm, f"{scenario}:remediation", process_started_at=time.time())
        v11.run_scenario(stage, "remediation")
        require_arm_time_remaining(deadline)
        record = wait_for_regular_input(
            state, arm, inbox / "record" / "run-record.json",
            f"{scenario}:awaiting_run_record", deadline,
        )
        output_freeze = v11.finalize_arm(stage, record)
        normalized = v11.normalize_run(output_freeze)
        require_arm_time_remaining(deadline)
        normalized_path = arm_root / "behavior" / f"{scenario}.normalized.json"
        write_once_json(normalized_path, normalized)
        if v11.normalize_run(output_freeze) != load_json(normalized_path, "normalized behavior"):
            raise AdapterError("v11 normalized behavior replay drifted")


def run_worker(state_path: Path, arm: str, attempt: int) -> int:
    state = load_state(state_path)
    verify_live_bindings(state)
    arm_state = state["arms"].get(arm)
    if not arm_state or not arm_state["attempts"] or arm_state["attempts"][-1]["attempt"] != attempt:
        raise AdapterError("worker attempt is not registered by controller state")
    result_path = Path(arm_state["attempts"][-1]["result_path"])
    deadline = float(arm_state["deadline_at"])
    result: dict[str, Any]
    try:
        require_arm_time_remaining(deadline)
        run_comprehension(state, arm, attempt, deadline)
        require_arm_time_remaining(deadline)
        run_behavior_lanes(state, arm, deadline)
        require_arm_time_remaining(deadline)
        record_progress(state, arm, "process_complete", process_started_at=None)
        require_arm_time_remaining(deadline)
        result = {"schema_version": 1, "attempt": attempt, "exit_code": 0, "error_type": None, "error": None}
        write_once_json(result_path, result)
        return 0
    except BaseException as exc:
        result = {
            "schema_version": 1, "attempt": attempt, "exit_code": 1,
            "error_type": type(exc).__name__, "error": str(exc),
        }
        write_once_json(result_path, result)
        return 1


def artifact_entry(path: Path, *, directory_manifest: str | None = None) -> dict[str, Any]:
    if directory_manifest is not None:
        require_directory(path, "artifact directory")
        return {"path": str(path), "sha256": directory_manifest, "kind": "directory_manifest"}
    require_regular_file(path, "sealed artifact")
    return {"path": str(path), "sha256": sha256_file(path), "byte_size": path.stat().st_size, "kind": "file"}


def behavior_artifact(state: dict[str, Any], arm: str) -> dict[str, Any]:
    runtime = Path(state["binding"]["runtime"]["real_path"])
    arm_root = control_root(runtime) / "arms" / arm
    scenarios: dict[str, Any] = {}
    for scenario in SCENARIOS:
        stage = runtime / f"{scenario}-{arm}"
        output_freeze = stage / "evaluator" / "output-freeze.json"
        terminal_seal = stage / "evaluator" / "terminal-seal.json"
        normalized_path = arm_root / "behavior" / f"{scenario}.normalized.json"
        normalized = load_json(normalized_path, "normalized behavior")
        replay = v11.normalize_run(output_freeze)
        if replay != normalized:
            raise AdapterError(f"{scenario} normalized behavior does not replay")
        v11.validate_normalized_output(normalized)
        scenarios[scenario] = {
            "output_freeze": artifact_entry(output_freeze),
            "terminal_seal": artifact_entry(terminal_seal),
            "normalized": artifact_entry(normalized_path),
        }
    return {
        "schema_version": 1,
        "adapter_identifier": ADAPTER_IDENTIFIER,
        "arm": arm,
        "scenarios": scenarios,
    }


def reconcile_process_complete(
    state_path: Path,
    state: dict[str, Any],
    arm: str,
    *,
    now: float | None = None,
    terminator: Callable[[dict[str, Any], list[str]], None] = terminate_verified_process,
) -> None:
    arm_state = state["arms"][arm]
    now = time.time() if now is None else now
    if arm_deadline_expired(arm_state, now):
        if arm_state["status"] == "running" and arm_state["attempts"]:
            attempt = arm_state["attempts"][-1]
            command = worker_command(state_path.resolve(), arm, attempt["attempt"])
            if same_process(attempt["process"], command):
                terminator(attempt["process"], command)
        fail_arm_total_timeout(arm_state)
        raise AdapterError("arm total timeout prevents process reconciliation")
    if arm_state["status"] == "process_complete":
        return
    if arm_state["status"] != "running":
        raise AdapterError("arm process is not complete")
    attempt = arm_state["attempts"][-1]
    command = worker_command(state_path.resolve(), arm, attempt["attempt"])
    if same_process(attempt["process"], command):
        raise AdapterError("arm process is still running")
    result = worker_result(attempt)
    if result is None or result.get("exit_code") != 0:
        raise AdapterError("arm process did not complete successfully")
    arm_state["status"] = "process_complete"


def seal_arm(state_path: Path, arm: str, *, now: float | None = None) -> dict[str, Any]:
    if arm not in ARMS:
        raise AdapterError("arm must be baseline or candidate")
    supplied_now = now
    now = time.time() if now is None else now
    with locked_state(state_path) as state:
        verify_live_bindings(state)
        arm_state = state["arms"][arm]
        if arm_state["status"] == "sealed":
            return {"arm": arm, "status": "sealed", "seal_sha256": arm_state["seal_sha256"], "replayed": True}
        reconcile_process_complete(state_path, state, arm, now=now)
        runtime = Path(state["binding"]["runtime"]["real_path"])
        arm_root = control_root(runtime) / "arms" / arm
        attempt = arm_state["attempts"][-1]["attempt"]
        comprehension = arm_root / "comprehension" / f"attempt-{attempt}"
        response_path = comprehension / "response.json"
        schema_path = control_root(runtime) / "inputs" / "response-schema.json"
        response = validate_response(response_path, schema_path)
        behavior = behavior_artifact(state, arm)
        artifacts_root = arm_root / "artifacts"
        package_manifest_path = arm_root / "package-manifest.json"
        package_manifest = load_json(package_manifest_path, "package manifest")
        verify_staged_package(arm_root / "readability-package", package_manifest)
        observed_path = artifacts_root / "observed-behavior.json"
        write_once_json(observed_path, behavior)
        canonical_trace = artifacts_root / "trace.jsonl"
        canonical_stderr = artifacts_root / "stderr.txt"
        write_once(canonical_trace, (comprehension / "trace.jsonl").read_bytes())
        write_once(canonical_stderr, (comprehension / "stderr.txt").read_bytes())
        runner_provenance = {
            "schema_version": 1,
            "adapter_identifier": ADAPTER_IDENTIFIER,
            "arm": arm,
            "adapter_sha256": state["binding"]["evaluator"]["adapter_sha256"],
            "execution_policy_sha256": state["binding"]["execution_policy_sha256"],
            "comprehension_metadata": artifact_entry(comprehension / "metadata.json"),
            "runner_preflight": artifact_entry(arm_root / "runner-preflight.json"),
            "behavior_package_manifest": artifact_entry(
                arm_root / "behavior-package-manifest.json"
            ),
            "v11_file_manifest_sha256": state["binding"]["v11_file_manifest_sha256"],
        }
        provenance_path = artifacts_root / "runner-provenance.json"
        write_once_json(provenance_path, runner_provenance)
        process_evidence = {
            "schema_version": 1,
            "adapter_identifier": ADAPTER_IDENTIFIER,
            "arm": arm,
            "arm_started_at": arm_state["arm_started_at"],
            "deadline_at": arm_state["deadline_at"],
            "attempts": arm_state["attempts"],
            "restart_count": arm_state["restart_count"],
            "result": artifact_entry(Path(arm_state["attempts"][-1]["result_path"])),
        }
        process_path = artifacts_root / "process-evidence.json"
        write_once_json(process_path, process_evidence)
        sealed_output = {
            "schema_version": 1,
            "adapter_identifier": ADAPTER_IDENTIFIER,
            "arm": arm,
            "response": response,
            "response_sha256": sha256_file(response_path),
            "schema_sha256": state["binding"]["schema_sha256"],
            "packet_sha256": state["binding"]["packet_sha256"],
            "package_manifest_sha256": package_manifest["manifest_sha256"],
            "observed_behavior_sha256": sha256_file(observed_path),
            "trace_sha256": sha256_file(canonical_trace),
            "stderr_sha256": sha256_file(canonical_stderr),
        }
        sealed_output_path = artifacts_root / "sealed-output.json"
        write_once_json(sealed_output_path, sealed_output)
        readability_manifest_path = artifacts_root / "readability-package-manifest.json"
        write_once_json(readability_manifest_path, package_manifest)
        artifact_map = {
            "package_manifest": artifact_entry(package_manifest_path),
            "runner_provenance": artifact_entry(provenance_path),
            "process_evidence": artifact_entry(process_path),
            "trace": artifact_entry(canonical_trace),
            "stderr": artifact_entry(canonical_stderr),
            "sealed_output": artifact_entry(sealed_output_path),
            "readability_package": artifact_entry(
                arm_root / "readability-package", directory_manifest=package_manifest["manifest_sha256"]
            ),
            "observed_behavior": artifact_entry(observed_path),
        }
        if set(artifact_map) != set(REQUIRED_ARTIFACTS):
            raise AdapterError("sealed arm artifact set is incomplete")
        seal = {
            "schema_version": 1,
            "adapter_identifier": ADAPTER_IDENTIFIER,
            "arm": arm,
            "binding_sha256": state["binding_sha256"],
            "artifacts": artifact_map,
        }
        final_now = time.time() if supplied_now is None else now
        if arm_deadline_expired(arm_state, final_now):
            fail_arm_total_timeout(arm_state)
            raise AdapterError("arm total timeout prevents sealing")
        seal_path = artifacts_root / "arm-seal.json"
        write_once_json(seal_path, seal)
        arm_state["status"] = "sealed"
        arm_state["seal_sha256"] = sha256_file(seal_path)
        arm_state["artifacts"] = artifact_map
        return {"arm": arm, "status": "sealed", "seal_path": str(seal_path), "seal_sha256": arm_state["seal_sha256"], "replayed": False}


def validate_sealed_arm(state: dict[str, Any], arm: str) -> dict[str, Any]:
    arm_state = state["arms"][arm]
    if arm_state["status"] != "sealed" or not HEX64.fullmatch(str(arm_state["seal_sha256"])):
        raise AdapterError(f"{arm} is not sealed")
    runtime = Path(state["binding"]["runtime"]["real_path"])
    seal_path = control_root(runtime) / "arms" / arm / "artifacts" / "arm-seal.json"
    seal = load_json(seal_path, f"{arm} arm seal")
    if sha256_file(seal_path) != arm_state["seal_sha256"] or seal.get("artifacts") != arm_state["artifacts"]:
        raise AdapterError(f"{arm} seal binding drifted")
    if set(seal["artifacts"]) != set(REQUIRED_ARTIFACTS):
        raise AdapterError(f"{arm} seal artifact set is incomplete")
    for name, entry in seal["artifacts"].items():
        path = Path(entry["path"])
        if entry["kind"] == "file":
            if sha256_file(path) != entry["sha256"] or path.stat().st_size != entry["byte_size"]:
                raise AdapterError(f"{arm} sealed artifact drifted: {name}")
        elif name == "readability_package" and entry["kind"] == "directory_manifest":
            package = state["binding"]["packages"][arm]["package_manifest"]
            if verify_staged_package(path, package)[0]["manifest_sha256"] != entry["sha256"]:
                raise AdapterError(f"{arm} readability package drifted")
        else:
            raise AdapterError(f"{arm} sealed artifact kind is invalid: {name}")
    return seal


def freeze_handoff(state_path: Path) -> dict[str, Any]:
    with locked_state(state_path) as state:
        verify_live_bindings(state)
        seals = {arm: validate_sealed_arm(state, arm) for arm in ARMS}
        runtime = Path(state["binding"]["runtime"]["real_path"])
        handoff_path = control_root(runtime) / "handoff.json"
        handoff = {
            "schema_version": 1,
            "adapter_identifier": ADAPTER_IDENTIFIER,
            "binding_sha256": state["binding_sha256"],
            "arm_order": list(ARMS),
            "arms": {
                arm: {
                    "seal_path": str(control_root(runtime) / "arms" / arm / "artifacts" / "arm-seal.json"),
                    "seal_sha256": state["arms"][arm]["seal_sha256"],
                    "artifacts": seals[arm]["artifacts"],
                }
                for arm in ARMS
            },
        }
        write_once_json(handoff_path, handoff)
        digest = sha256_file(handoff_path)
        if state["handoff"]["status"] == "frozen" and state["handoff"]["sha256"] != digest:
            raise AdapterError("frozen handoff digest drifted")
        state["handoff"] = {"status": "frozen", "sha256": digest}
        return {"status": "frozen", "handoff_path": str(handoff_path), "handoff_sha256": digest}


def describe() -> dict[str, Any]:
    policy = load_policy()
    return {
        "schema_version": 1,
        "adapter_identifier": ADAPTER_IDENTIFIER,
        "operations": {
            "describe": {"arguments": ["--json"], "mutates_runtime": False},
            "initialize": {
                "arguments": [
                    "--parent", "--packet", "--schema", "--baseline-package",
                    "--baseline-manifest", "--candidate-package", "--candidate-manifest",
                    "--run-label-map",
                ],
                "creates_run_identity": True,
            },
            "launch-arm": {"arguments": ["--state", "--arm", "--restart-infrastructure"]},
            "poll-arm": {"arguments": ["--state", "--arm"]},
            "seal-arm": {"arguments": ["--state", "--arm"]},
            "freeze-handoff": {"arguments": ["--state"], "write_once": True},
        },
        "process_policy": policy,
        "state_machine": {
            "arm_states": ["pending", "launching", "running", "process_complete", "failed", "sealed"],
            "happy_path": ["pending", "launching", "running", "process_complete", "sealed"],
            "restart_path": "failed infrastructure_failure_before_output -> launching; once only",
            "terminal_states": ["failed", "sealed"],
            "candidate_gate": "baseline must be sealed",
            "handoff_gate": "both arms must be sealed with unchanged bytes",
        },
        "package_manifest_contract": {
            "paths": "exact sorted repo-relative regular files; no extras or links",
            "per_file_fields": [
                "path", "git_mode", "byte_size", "sha256", "source_commit", "source_tree",
            ],
            "proof": "each extracted file must reproduce its Git blob, mode, commit, and tree",
        },
        "required_arm_artifacts": list(REQUIRED_ARTIFACTS),
        "behavior_evidence_inbox": {
            "pre_packet_validation": "<runtime>/.deliver-evaluator/v12/arms/<arm>/inbox/<scenario>/pre-packet-validation.log",
            "run_record": "<runtime>/.deliver-evaluator/v12/arms/<arm>/inbox/<scenario>/record/run-record.json",
            "validation": "v11 finalization recomputes evidence; caller-authored flags and digests are not proof",
        },
        "public_files": {
            "execution_policy": str(POLICY_PATH),
            "readiness": str(READINESS_PATH),
            "response_schema": str(VOCABULARY_PATH),
            "baseline_manifest": str(BASELINE_MANIFEST_PATH),
            "candidate_manifest": str(CANDIDATE_MANIFEST_PATH),
            "candidate_behavior_map": str(CANDIDATE_BEHAVIOR_MAP_PATH),
            "public_inventory": str(INVENTORY_PATH),
            "v11_file_manifest": str(V11_MANIFEST_PATH),
        },
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    describe_parser = commands.add_parser("describe")
    describe_parser.add_argument("--json", action="store_true", required=True)
    initialize = commands.add_parser("initialize")
    initialize.add_argument("--parent", type=Path, default=v11.STAGE_ROOT)
    initialize.add_argument("--packet", type=Path, required=True)
    initialize.add_argument("--schema", type=Path, required=True)
    initialize.add_argument("--baseline-package", type=Path, required=True)
    initialize.add_argument("--baseline-manifest", type=Path, default=BASELINE_MANIFEST_PATH)
    initialize.add_argument("--candidate-package", type=Path, required=True)
    initialize.add_argument("--candidate-manifest", type=Path, default=CANDIDATE_MANIFEST_PATH)
    initialize.add_argument("--run-label-map", type=Path, required=True)
    for name in ("launch-arm", "poll-arm", "seal-arm"):
        command = commands.add_parser(name)
        command.add_argument("--state", type=Path, required=True)
        command.add_argument("--arm", choices=ARMS, required=True)
        if name == "launch-arm":
            command.add_argument("--restart-infrastructure", action="store_true")
    handoff = commands.add_parser("freeze-handoff")
    handoff.add_argument("--state", type=Path, required=True)
    worker = commands.add_parser("_worker", help=argparse.SUPPRESS)
    worker.add_argument("--state", type=Path, required=True)
    worker.add_argument("--arm", choices=ARMS, required=True)
    worker.add_argument("--attempt", type=int, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == "describe":
        result = describe()
    elif arguments.command == "initialize":
        result = initialize_runtime(
            arguments.parent, arguments.packet, arguments.schema,
            arguments.baseline_package, arguments.candidate_package,
            arguments.candidate_manifest, arguments.run_label_map,
            arguments.baseline_manifest,
        )
    elif arguments.command == "launch-arm":
        result = launch_arm(
            arguments.state, arguments.arm,
            restart_infrastructure=arguments.restart_infrastructure,
        )
    elif arguments.command == "poll-arm":
        result = poll_arm(arguments.state, arguments.arm)
    elif arguments.command == "seal-arm":
        result = seal_arm(arguments.state, arguments.arm)
    elif arguments.command == "freeze-handoff":
        result = freeze_handoff(arguments.state)
    elif arguments.command == "_worker":
        return run_worker(arguments.state, arguments.arm, arguments.attempt)
    else:
        raise AdapterError("unknown adapter operation")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AdapterError, v11.HarnessError) as exc:
        print(f"adapter error: {exc}", file=sys.stderr)
        raise SystemExit(2)
