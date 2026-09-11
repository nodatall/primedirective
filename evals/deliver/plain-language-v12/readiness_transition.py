#!/usr/bin/env python3
"""Version-pinned, auditable readiness transitions for Deliver oracle v12.30."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any


ORACLE_VERSION = "deliver-plain-language-v12.30"
SCHEMA_VERSION = 27
READINESS_RELATIVE_PATH = "evals/deliver/plain-language-v12/oracle-readiness.json"
REVIEW_RELATIVE_PATH = "evals/deliver/plain-language-v12/independent-review-record.json"
ISOLATION_RELATIVE_PATH = "evals/deliver/plain-language-v12/trusted-host-isolation-receipt.json"
PROBE_RELATIVE_PATH = "evals/deliver/plain-language-v12/root_isolation_probe.py"
PUBLIC_REPOSITORY = Path("/Volumes/Code/primedirective")
PRIVATE_EVALUATOR_REPOSITORY = Path(
    "/private/tmp/deliver-plain-language-v130-evaluator.SaR0Md/repo"
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
OUTER_PROBE_ID = "deliver-v12.30-outer-sandbox-v1"
PREFLIGHT_PROBE_ID = "deliver-v12.30-real-preflight-v1"
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


def _last_touch(repo: Path, commit: str, relative_path: str) -> str:
    value = str(git(repo, ["log", "-1", "--format=%H", commit, "--", relative_path])).strip()
    if not HEX40.fullmatch(value):
        raise ReadinessTransitionError(f"no committed origin for {relative_path}")
    return value


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
        raise ReadinessTransitionError("readiness version is not v12.30")
    if document.get("status") not in {"author_ready", "independent_review_pass", "ready"}:
        raise ReadinessTransitionError("readiness status is invalid")
    if document.get("immutable_readiness_sha256") != immutable_digest(document):
        raise ReadinessTransitionError("immutable readiness projection digest is invalid")
    for field in ("private_evaluator_source_commit", "private_evaluator_commit"):
        if not HEX40.fullmatch(str(document.get(field))):
            raise ReadinessTransitionError(f"{field} is malformed")
    if document.get("root_isolation_contract") != root_isolation_contract():
        raise ReadinessTransitionError("root isolation contract is not exact")
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
    for path, digest in frozen_digests.items():
        if (
            not isinstance(path, str)
            or not path.startswith("evals/deliver/plain-language-v12/")
            or not HEX64.fullmatch(str(digest))
            or not HEX40.fullmatch(str(frozen_commits[path]))
        ):
            raise ReadinessTransitionError("frozen public file binding is malformed")


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
    if str(git(repo, ["status", "--porcelain=v1", "--untracked-files=no"])).strip():
        raise ReadinessTransitionError("private evaluator tracked state is not clean")
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


def _validate_frozen_files(repo: Path, ref: str, document: dict[str, Any]) -> None:
    commit = _commit(repo, ref)
    for path, digest in document["frozen_public_file_digests"].items():
        if sha256_bytes(_blob(repo, commit, path)) != digest:
            raise ReadinessTransitionError(f"frozen public file digest drifted: {path}")
        if _last_touch(repo, commit, path) != document["frozen_public_file_commits"][path]:
            raise ReadinessTransitionError(f"frozen public file was touched after freeze: {path}")


def _readiness_at(repo: Path, commit: str) -> tuple[dict[str, Any], bytes]:
    raw = _blob(repo, commit, READINESS_RELATIVE_PATH)
    return load_json_bytes(raw, "committed readiness"), raw


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
            operation,
            receipt["isolation_nonce"],
        )
        if probe["command_identity_sha256"] != sha256_bytes(canonical_json(command)):
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
    python: Path, repo: Path, operation: str, challenge: str,
) -> list[str]:
    if operation not in PROBE_SPECS:
        raise ReadinessTransitionError("root probe operation is unknown")
    return [
        str(python), "-I", str(repo / PROBE_RELATIVE_PATH), operation,
        "--repo", str(repo),
        "--private-repo", str(PRIVATE_EVALUATOR_REPOSITORY),
        "--challenge", challenge,
    ]


def _execute_probe_command(command: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=repo,
        env=PROBE_ENVIRONMENT,
        check=False,
        capture_output=True,
        text=True,
    )


def _observe_probe(
    repo: Path, python: Path, operation: str, challenge: str,
    probe_source_sha256: str,
) -> dict[str, Any]:
    probe_id, claims = PROBE_SPECS[operation]
    command = _probe_command(python, repo, operation, challenge)
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
    canonical_stdout = canonical_json(evidence) + b"\n"
    if result.stdout.encode("utf-8") != canonical_stdout:
        raise ReadinessTransitionError(f"required {operation} host probe output is not canonical")
    return {
        "probe_id": probe_id,
        "operation": operation,
        "command_identity_sha256": sha256_bytes(canonical_json(command)),
        "source_path": PROBE_RELATIVE_PATH,
        "source_sha256": probe_source_sha256,
        "stdout_sha256": sha256_bytes(canonical_stdout),
        "stderr_sha256": sha256_bytes(result.stderr.encode("utf-8")),
        "exit_status": result.returncode,
        "evidence": evidence,
    }


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
    probe_source = repo / PROBE_RELATIVE_PATH
    if probe_source.is_symlink() or not probe_source.is_file():
        raise ReadinessTransitionError("root isolation probe source is unavailable")
    probe_source_sha256 = sha256_bytes(probe_source.read_bytes())
    if probe_source_sha256 != document["frozen_public_file_digests"].get(PROBE_RELATIVE_PATH):
        raise ReadinessTransitionError("root isolation probe source is not frozen")
    python_identity = _python_identity(Path(sys.executable))
    python = Path(python_identity["path"])
    challenge = secrets.token_hex(32)
    probes = [
        _observe_probe(repo, python, operation, challenge, probe_source_sha256)
        for operation in PROBE_SPECS
    ]
    if _commit(repo, "HEAD") != head_before:
        raise ReadinessTransitionError("public HEAD changed while root probes ran")
    if readiness_path.read_bytes() != readiness_before:
        raise ReadinessTransitionError("readiness changed while root probes ran")
    if str(git(repo, ["status", "--porcelain=v1", "--untracked-files=no"])).strip():
        raise ReadinessTransitionError("tracked public state changed while root probes ran")
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
    for command in ("verify-author-ready", "verify-independent-review", "verify-ready"):
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
    if args.command == "verify-author-ready":
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
