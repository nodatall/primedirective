#!/usr/bin/env python3
"""Version-pinned, auditable readiness transitions for Deliver oracle v12.27."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ORACLE_VERSION = "deliver-plain-language-v12.27"
SCHEMA_VERSION = 24
READINESS_RELATIVE_PATH = "evals/deliver/plain-language-v12/oracle-readiness.json"
REVIEW_RELATIVE_PATH = "evals/deliver/plain-language-v12/independent-review-record.json"
ISOLATION_RELATIVE_PATH = "evals/deliver/plain-language-v12/trusted-host-isolation-receipt.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
INDEPENDENT_RESULT_KIND = "orchestrator_observed_agent_result_not_signature"
ISOLATION_RESULT_KIND = "root_observed_probe_result_not_signature"

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
    "case_disjointness",
    "runtime_controls",
    "lifecycle_controls",
    "public_bindings",
})
ISOLATION_CHECKS = frozenset({
    "filesystem_isolation",
    "sibling_isolation",
    "hidden_material_isolation",
    "credential_boundary",
    "network_boundary",
})


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


def _validate_common(document: dict[str, Any]) -> None:
    if document.get("schema_version") != SCHEMA_VERSION or document.get("oracle_version") != ORACLE_VERSION:
        raise ReadinessTransitionError("readiness version is not v12.27")
    if document.get("status") not in {"author_ready", "independent_review_pass", "ready"}:
        raise ReadinessTransitionError("readiness status is invalid")
    if document.get("immutable_readiness_sha256") != immutable_digest(document):
        raise ReadinessTransitionError("immutable readiness projection digest is invalid")
    for field in ("private_evaluator_source_commit", "private_evaluator_commit"):
        if not HEX40.fullmatch(str(document.get(field))):
            raise ReadinessTransitionError(f"{field} is malformed")
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
        "schema_version", "oracle_version", "record_kind", "result", "root_observed",
        "isolation_nonce", "private_evaluator_source_commit", "private_evaluator_final_commit",
        "public_controller_commit", "predecessor_readiness_commit",
        "predecessor_readiness_sha256", "independent_review_record_sha256",
        "independent_review_transition_commit", "immutable_readiness_sha256", "checks",
    }
    checks = receipt.get("checks")
    if (
        set(receipt) != expected_fields
        or receipt.get("schema_version") != 1
        or receipt.get("oracle_version") != ORACLE_VERSION
        or receipt.get("record_kind") != "trusted_host_isolation"
        or receipt.get("result") != "pass"
        or receipt.get("root_observed") is not True
        or not HEX64.fullmatch(str(receipt.get("isolation_nonce")))
        or receipt.get("private_evaluator_source_commit") != readiness["private_evaluator_source_commit"]
        or receipt.get("private_evaluator_final_commit") != readiness["private_evaluator_commit"]
        or receipt.get("public_controller_commit") != readiness["public_adapter_introducing_commit"]
        or receipt.get("predecessor_readiness_commit") != predecessor_commit
        or receipt.get("predecessor_readiness_sha256") != predecessor_digest
        or receipt.get("independent_review_record_sha256") != review_record_sha256
        or receipt.get("independent_review_transition_commit") != predecessor_commit
        or receipt.get("immutable_readiness_sha256") != readiness["immutable_readiness_sha256"]
        or not isinstance(checks, dict)
        or set(checks) != ISOLATION_CHECKS
        or any(value != "pass" for value in checks.values())
    ):
        raise ReadinessTransitionError("trusted-host isolation receipt is not exactly bound")


def verify_author_ready(repo: Path, ref: str = "HEAD") -> dict[str, str]:
    commit = _commit(repo, ref)
    document, raw = _readiness_at(repo, commit)
    _validate_author_document(document)
    if _last_touch(repo, commit, READINESS_RELATIVE_PATH) != commit:
        raise ReadinessTransitionError("author readiness must be introduced by its own current commit")
    _validate_frozen_files(repo, commit, document)
    return {"status": "author_ready", "commit": commit, "sha256": sha256_bytes(raw)}


def _verify_review_at(repo: Path, commit: str) -> tuple[dict[str, Any], dict[str, str]]:
    document, raw = _readiness_at(repo, commit)
    _validate_common(document)
    if document["status"] != "independent_review_pass":
        raise ReadinessTransitionError("expected independent_review_pass state")
    predecessor = _parent(repo, commit)
    before, before_raw = _readiness_at(repo, predecessor)
    _validate_author_document(before)
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
    return _verify_review_at(repo, _commit(repo, ref))[1]


def verify_ready(repo: Path, ref: str = "HEAD") -> dict[str, str]:
    head = _commit(repo, ref)
    readiness_commit = _last_touch(repo, head, READINESS_RELATIVE_PATH)
    document, raw = _readiness_at(repo, readiness_commit)
    _validate_common(document)
    if document["status"] != "ready":
        raise ReadinessTransitionError("oracle readiness is not in ready state")
    predecessor = _parent(repo, readiness_commit)
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


def prepare_ready(repo: Path, receipt_path: Path) -> None:
    predecessor = verify_independent_review_pass(repo)
    readiness_path = repo / READINESS_RELATIVE_PATH
    document = load_json_bytes(readiness_path.read_bytes(), "working readiness")
    receipt_raw = receipt_path.read_bytes()
    receipt = load_json_bytes(receipt_raw, "supplied isolation receipt")
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
    ready = subparsers.add_parser("prepare-ready")
    ready.add_argument("--repo", type=Path, default=Path.cwd())
    ready.add_argument("--receipt", type=Path, required=True)
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
        prepare_ready(repo, args.receipt.resolve())
        result = {"status": "prepared_ready", "commit_required": True}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReadinessTransitionError as exc:
        print(f"readiness transition failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
