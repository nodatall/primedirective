#!/usr/bin/env python3
"""Deterministic preparation and evaluator-side checks for the Deliver eval."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import select
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Iterable


SUITE_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = SUITE_ROOT.parents[1].resolve()
STAGE_ROOT = Path("/private/tmp").resolve()
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
BUNDLED_CODEX = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
CODEX_AUTH = Path("/Users/fromdarkness/.codex/auth.json")
SCHEMA_VERSION = 1
DENIED_INPUT_PARTS = {"evaluator", "evaluators", "ledger", "hidden"}
DENIED_INPUT_NAMES = {"outcome-ledger.json", "identity-denylist.txt"}
IDENTITY_DENYLIST = SUITE_ROOT / "evaluator" / "identity-denylist.txt"
OUTCOME_LEDGER = SUITE_ROOT / "evaluator" / "outcome-ledger.json"
FIXED_AUTHOR_DATE = "2000-01-01T00:00:00+00:00"
HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_ID = re.compile(r"^[0-9a-f]{40}$")
TERMINAL_SEAL_EVENT = "deliver_eval_arm_finalized"
RUNNER_PHASES = ("pre-packet", "remediation")
OUTCOME_SCENARIOS = ("retry-failed", "preflight-remediation-holdout")
ARM_NAMES = tuple(
    f"{scenario}-{variant}"
    for scenario in OUTCOME_SCENARIOS
    for variant in ("baseline", "candidate")
)
PREFLIGHT_ARM = "runner-preflight"
SIBLING_PROBE = "runner-sibling-probe"
SIBLING_SENTINEL = "sentinel.txt"
COMPARISON_CONTROL = ".deliver-evaluator"
COMPARISON_MANIFEST = "comparison-manifest.json"
COMPARISON_STATE = "attempt-state.json"
COMPARISON_LOCK = "attempt-state.lock"
EXTERNAL_SENTINEL = "external-temp-sentinel.txt"
EXTERNAL_SENTINEL_BYTES = b"deliver-eval-external-temp-sentinel-v11\n"
EXTERNAL_SENTINEL_SHA256 = hashlib.sha256(EXTERNAL_SENTINEL_BYTES).hexdigest()
EXTERNAL_SENTINEL_ENV = "DELIVER_EVAL_EXTERNAL_TEMP_SENTINEL"
INHERITED_SENTINEL = "DELIVER_EVAL_INHERITED_SENTINEL"
FIRST_TOOL_GATE_OUTPUT = "deliver-eval-first-tool-gate-ok"
FIRST_TOOL_GATE_COMMAND = (
    '/bin/test ! -e "$CODEX_HOME/auth.json" && '
    f'/bin/test -z "${{{INHERITED_SENTINEL}+x}}" && '
    f'/bin/test -n "${{{EXTERNAL_SENTINEL_ENV}:-}}" && '
    f'! /bin/cat "${EXTERNAL_SENTINEL_ENV}" >/dev/null 2>&1 && '
    f'! ( /usr/bin/printf blocked > "${EXTERNAL_SENTINEL_ENV}" ) 2>/dev/null && '
    f'! /bin/cat ../../{SIBLING_PROBE}/{SIBLING_SENTINEL} >/dev/null 2>&1 && '
    f"/usr/bin/printf {FIRST_TOOL_GATE_OUTPUT}"
)
FIRST_TOOL_GATE_TRACE_COMMANDS = tuple(
    f"/bin/zsh {flag} '{FIRST_TOOL_GATE_COMMAND}'" for flag in ("-c", "-lc")
)
FIRST_TOOL_GATE_TRACE_COMMAND = FIRST_TOOL_GATE_TRACE_COMMANDS[-1]
FIRST_TOOL_GATE_PROMPT = (
    "Your first tool call of any kind must be a shell call running exactly this command:\n"
    f"{FIRST_TOOL_GATE_COMMAND}\n"
    "Do not make any other tool call before it.\n"
    f"Continue only if its exact output is: {FIRST_TOOL_GATE_OUTPUT}\n\n"
)
PREFLIGHT_PROMPT = FIRST_TOOL_GATE_PROMPT + "Then reply only with: runner preflight ok\n"
ARM_TIMEOUT_POLICY = {
    "policy_version": 2,
    "arm_total_seconds": 90 * 60,
    "inactivity_seconds": 15 * 60,
    "activity_event": "structurally_valid_codex_jsonl_event",
}
PREFLIGHT_TIMEOUT_POLICY = {
    "policy_version": 2,
    "total_seconds": 2 * 60,
    "inactivity_seconds": 60,
    "activity_event": "structurally_valid_codex_jsonl_event",
}
CODEX_EVENT_TYPES = frozenset(
    {
        "thread.started",
        "turn.started",
        "turn.completed",
        "turn.failed",
        "item.started",
        "item.updated",
        "item.completed",
        "error",
    }
)
RUNNER_FILES = {
    "trace": "trace.jsonl",
    "stderr": "stderr.txt",
    "metadata": "metadata.json",
    "prompt": "prompt.txt",
    "manifest": "input-manifest.json",
    "profile": "runner.sb",
}
MEASUREMENT_FIELDS = {
    "test_count",
    "test_size_lines",
    "full_review_rounds",
    "targeted_rereviews",
    "wall_time_seconds",
}
SNAPSHOT_FIELDS = {
    "schema_version", "scenario_id", "input_manifest_sha256", "initial_snapshot",
    "head", "status", "implementation_diff_sha256", "test_diff_sha256",
    "validation", "runner_artifacts", "runner_preflight_sha256",
}
EVALUATOR_ALLOWLIST = (
    "evals/deliver/harness.py",
    "evals/deliver/tests/test_harness.py",
    "evals/deliver/suite.md",
    "evals/deliver/evaluator/comparison-artifacts-schema.json",
    "evals/deliver/evaluator/output-freeze-schema.json",
    "evals/deliver/evaluator/behavior-schema.json",
    "evals/deliver/evaluator/terminal-seal-schema.json",
    "evals/deliver/evaluator/candidate-compliance-schema.json",
)
CANDIDATE_OWNED_PATHS = (
    "scripts/validate-skill-contracts.py",
    "skills/deliver/SKILL.md",
    "skills/deliver/references/rereview-scope-record.md",
    "skills/deliver/references/worker-packet.md",
    "skills/deliver/tests/test_validate_rereview_scope.py",
    "skills/shared/references/review/finding-disposition.md",
    "skills/shared/references/review/review-protocol.md",
)
BASELINE_REF = "a4116bb"
CANDIDATE_REF = "8a489bc"
EVALUATOR_BASE_REF = "beb346a"
BASELINE_PACKAGE_PATHS = (
    "skills/deliver/SKILL.md",
    "skills/deliver/references/plan-format.md",
    "skills/deliver/references/worker-packet.md",
    "skills/shared/references/analysis/verification-pivot.md",
    "skills/shared/references/execution/finalization-gate.md",
    "skills/shared/references/plain-language.md",
    "skills/shared/references/reasoning-budget.md",
    "skills/shared/references/review/finding-disposition.md",
    "skills/shared/references/review/review-protocol.md",
)
CANDIDATE_PACKAGE_PATHS = (
    "skills/deliver/SKILL.md",
    "skills/deliver/references/plan-format.md",
    "skills/deliver/references/rereview-scope-record.md",
    "skills/deliver/references/worker-packet.md",
    "skills/deliver/scripts/validate_rereview_scope.py",
    "skills/shared/references/analysis/verification-pivot.md",
    "skills/shared/references/execution/finalization-gate.md",
    "skills/shared/references/plain-language.md",
    "skills/shared/references/reasoning-budget.md",
    "skills/shared/references/review/finding-disposition.md",
    "skills/shared/references/review/review-protocol.md",
)
OFFICIAL_ARM_ORDER = (
    "retry-failed-baseline",
    "retry-failed-candidate",
    "preflight-remediation-holdout-baseline",
    "preflight-remediation-holdout-candidate",
)
FAILURE_FACTS = {
    ("integrity_defect", "evaluator"): "evaluator_defect",
    ("terminal_failure", "baseline"): "baseline_terminal",
    ("failure_attribution", "ambiguous"): "ambiguous",
    ("comparability_failure", "comparison"): "incomparable",
    ("terminal_failure", "candidate"): "candidate_unscorable",
    ("hard_gate_failure", "candidate"): "candidate_hard_gate",
    ("blinded_regression", "candidate"): "blinded_regression",
    ("scenario_coverage_failure", "changed_contract"): "candidate_not_exposed",
}
FAILURE_PRECEDENCE = tuple(FAILURE_FACTS.values())
FINAL_CHAIN_FILES = (
    ("normalized_retry_failed_baseline", "final-evidence/normalized-retry-failed-baseline.json"),
    ("normalized_preflight_remediation_holdout_baseline", "final-evidence/normalized-preflight-remediation-holdout-baseline.json"),
    ("normalized_retry_failed_candidate", "final-evidence/normalized-retry-failed-candidate.json"),
    ("normalized_preflight_remediation_holdout_candidate", "final-evidence/normalized-preflight-remediation-holdout-candidate.json"),
    ("blind_packet", "final-evidence/blind-packet.json"),
    ("judge_record", "final-evidence/judge-record.json"),
    ("identity_reveal", "final-evidence/identity-reveal.json"),
    ("candidate_compliance", "final-evidence/candidate-compliance.json"),
    ("outcome_gate", "final-evidence/outcome-gate.json"),
)
FINAL_FAILURE_FILES = (
    ("failure_evidence", "final-evidence/failure-evidence.json"),
)


class HarnessError(RuntimeError):
    """Raised when an eval isolation or evidence invariant is violated."""


class StreamCapture:
    """Parent-owned byte count and digest captured while streaming runner output."""

    def __init__(self) -> None:
        self.byte_count = 0
        self._hasher = hashlib.sha256()

    def update(self, chunk: bytes) -> None:
        self.byte_count += len(chunk)
        self._hasher.update(chunk)

    @property
    def sha256(self) -> str:
        return self._hasher.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def is_digest(value: object, pattern: re.Pattern[str] = HEX_DIGEST) -> bool:
    return isinstance(value, str) and bool(pattern.fullmatch(value))


def exact_digest_map(
    value: object, fields: set[str], pattern: re.Pattern[str] = HEX_DIGEST
) -> bool:
    return isinstance(value, dict) and set(value) == fields and all(
        is_digest(item, pattern) for item in value.values()
    )


def valid_initial_snapshot(value: object) -> bool:
    return exact_digest_map(value, {"commit", "tree"}, GIT_OBJECT_ID)


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def atomic_write_json(path: Path, value: object) -> None:
    """Publish canonical JSON without exposing a partially written state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(canonical_json(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists() or temporary.is_symlink():
            temporary.unlink()


def require_regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise HarnessError(f"{label} must be a canonical regular file")
    return path


def comparison_control(runtime_root: Path) -> Path:
    return runtime_root / COMPARISON_CONTROL


def external_sentinel_path(runtime_root: Path) -> Path:
    return comparison_control(runtime_root) / EXTERNAL_SENTINEL


def ensure_external_sentinel(runtime_root: Path) -> dict[str, object]:
    """Create or verify the evaluator-owned sentinel outside every arm stage."""
    runtime_root = runtime_root.resolve()
    control = comparison_control(runtime_root)
    if control.is_symlink():
        raise HarnessError("comparison control directory cannot be a symlink")
    control.mkdir(mode=0o700, parents=True, exist_ok=True)
    sentinel = external_sentinel_path(runtime_root)
    if sentinel.exists() or sentinel.is_symlink():
        require_regular_file(sentinel, "external temporary sentinel")
        if sentinel.read_bytes() != EXTERNAL_SENTINEL_BYTES:
            raise HarnessError("external temporary sentinel bytes or digest changed")
    else:
        fd = os.open(sentinel, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(EXTERNAL_SENTINEL_BYTES)
            handle.flush()
            os.fsync(handle.fileno())
    if (
        sentinel.stat().st_mode & 0o777 != 0o600
        or sentinel.stat().st_size != len(EXTERNAL_SENTINEL_BYTES)
        or sha256_file(sentinel) != EXTERNAL_SENTINEL_SHA256
    ):
        raise HarnessError("external temporary sentinel metadata or digest changed")
    return {
        "path": str(sentinel),
        "size": len(EXTERNAL_SENTINEL_BYTES),
        "sha256": EXTERNAL_SENTINEL_SHA256,
    }


def verify_external_sentinel(binding: dict[str, object], runtime_root: Path) -> Path:
    sentinel = external_sentinel_path(runtime_root.resolve())
    require_regular_file(sentinel, "external temporary sentinel")
    expected = {
        "path": str(sentinel),
        "size": sentinel.stat().st_size,
        "sha256": sha256_file(sentinel),
    }
    if binding != expected:
        raise HarnessError("external temporary sentinel binding drifted")
    if (
        sentinel.read_bytes() != EXTERNAL_SENTINEL_BYTES
        or sentinel.stat().st_mode & 0o777 != 0o600
    ):
        raise HarnessError("external temporary sentinel bytes or mode changed")
    return sentinel


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise HarnessError(
            f"command failed ({result.returncode}): {' '.join(command)}\n{result.stderr}"
        )
    return result.stdout


def git_output(arguments: list[str]) -> str:
    return run(["git", *arguments], cwd=SOURCE_ROOT).strip()


def canonical_file_manifest(root: Path) -> dict[str, object]:
    root = root.resolve(strict=True)
    if root.is_symlink() or not root.is_dir():
        raise HarnessError("package manifest root must be a regular directory")
    files: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        reject_symlink_chain(root, relative)
        if path.is_dir():
            continue
        require_regular_file(path, "package manifest input")
        files.append({
            "path": relative.as_posix(),
            "mode": f"{stat.S_IMODE(path.stat().st_mode):06o}",
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    if not files:
        raise HarnessError("package manifest cannot be empty")
    payload: dict[str, object] = {"files": files}
    payload["manifest_sha256"] = sha256_bytes(canonical_json(payload))
    return payload


def git_ref_package_manifest(ref: str, paths: tuple[str, ...]) -> dict[str, object]:
    resolved = git_output(["rev-parse", f"{ref}^{{commit}}"])
    files: list[dict[str, object]] = []
    for relative in paths:
        listing = git_output(["ls-tree", resolved, "--", relative])
        if not listing:
            raise HarnessError(f"frozen package path missing from {ref}: {relative}")
        metadata, listed_path = listing.split("\t", 1)
        mode, object_type, object_id = metadata.split()
        if listed_path != relative or object_type != "blob" or mode == "120000":
            raise HarnessError(f"frozen package path is not a regular blob: {relative}")
        result = subprocess.run(
            ["git", "cat-file", "blob", object_id], cwd=SOURCE_ROOT,
            check=False, capture_output=True,
        )
        if result.returncode:
            raise HarnessError(f"cannot read frozen package blob: {relative}")
        files.append({
            "path": relative,
            "mode": f"{int(mode, 8) & 0o777:06o}",
            "size": len(result.stdout),
            "sha256": sha256_bytes(result.stdout),
        })
    payload: dict[str, object] = {"files": files}
    payload["manifest_sha256"] = sha256_bytes(canonical_json(payload))
    return payload


def validate_supplied_package(
    root: Path, expected: dict[str, object], paths: tuple[str, ...], label: str
) -> None:
    actual = canonical_file_manifest(root)
    if [item["path"] for item in actual["files"]] != list(paths):
        raise HarnessError(f"{label} package path set differs from its frozen ref")
    if actual != expected:
        raise HarnessError(f"{label} package bytes or modes differ from its frozen ref")


def evaluator_identity(*, require_clean: bool = True) -> dict[str, str]:
    if require_clean:
        status = git_output([
            "status", "--porcelain=v1", "--untracked-files=all", "--",
            "evals/deliver",
        ])
        if status:
            raise HarnessError("evaluator tree must be clean before comparison freeze")
    commit = git_output(["rev-parse", "HEAD"])
    tree = git_output(["rev-parse", "HEAD:evals/deliver"])
    if not GIT_OBJECT_ID.fullmatch(commit) or not GIT_OBJECT_ID.fullmatch(tree):
        raise HarnessError("evaluator Git identity is invalid")
    tracked = [
        line for line in git_output(["ls-files", "--", "evals/deliver"]).splitlines()
        if line
    ]
    files: list[dict[str, object]] = []
    for relative in tracked:
        path = SOURCE_ROOT / relative
        require_regular_file(path, "tracked evaluator input")
        files.append({
            "path": relative,
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    if not files:
        raise HarnessError("evaluator file manifest cannot be empty")
    return {
        "commit": commit,
        "evals_tree": tree,
        "file_manifest_sha256": sha256_bytes(canonical_json({"files": files})),
    }


def git_commit_is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=SOURCE_ROOT, check=False, capture_output=True,
    ).returncode == 0


def git_history_touches_evaluator(ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        [
            "git", "log", "--full-history", "--format=%H",
            f"{ancestor}..{descendant}",
            "--", "evals/deliver",
        ],
        cwd=SOURCE_ROOT, check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise HarnessError("cannot validate frozen evaluator path history")
    return bool(result.stdout.strip())


def validate_evaluator_identity(value: object, *, recompute: bool = True) -> dict[str, str]:
    if (
        not isinstance(value, dict)
        or set(value) != {"commit", "evals_tree", "file_manifest_sha256"}
        or not GIT_OBJECT_ID.fullmatch(value.get("commit", ""))
        or not GIT_OBJECT_ID.fullmatch(value.get("evals_tree", ""))
        or not is_digest(value.get("file_manifest_sha256"))
    ):
        raise HarnessError("evaluator identity fields are invalid")
    if recompute:
        current = evaluator_identity()
        if (
            current["evals_tree"] != value["evals_tree"]
            or current["file_manifest_sha256"] != value["file_manifest_sha256"]
            or current["commit"] != value["commit"]
            and (
                not git_commit_is_ancestor(value["commit"], current["commit"])
                or git_history_touches_evaluator(
                    value["commit"], current["commit"]
                )
            )
        ):
            raise HarnessError("frozen evaluator identity drifted")
    return value


def assert_candidate_owned_paths_frozen() -> None:
    changed = git_output([
        "diff", "--name-only", CANDIDATE_REF, "--", *CANDIDATE_OWNED_PATHS
    ]).splitlines()
    if changed:
        raise HarnessError(
            "candidate-owned paths drifted from exact candidate " + CANDIDATE_REF
        )


def comparison_manifest_path(runtime_root: Path) -> Path:
    return comparison_control(runtime_root) / COMPARISON_MANIFEST


def comparison_for_stage(stage_root: Path) -> Path | None:
    path = comparison_manifest_path(stage_root.parent)
    return path if path.is_file() and not path.is_symlink() else None


def initialize_comparison(
    runtime_root: Path,
    baseline_package: Path,
    candidate_package: Path,
    *,
    comparison_id: str | None = None,
) -> Path:
    runtime_root = runtime_root.resolve()
    if (
        runtime_root.parent != STAGE_ROOT
        or not re.fullmatch(r"deliver-eval-[A-Za-z0-9._-]+", runtime_root.name)
    ):
        raise HarnessError("comparison runtime must be /private/tmp/deliver-eval-<run>")
    runtime_root.mkdir(mode=0o700, exist_ok=True)
    manifest_path = comparison_manifest_path(runtime_root)
    if manifest_path.exists() or manifest_path.is_symlink():
        raise HarnessError("comparison manifest already exists")
    assert_candidate_owned_paths_frozen()
    identity = evaluator_identity()
    changed = set(git_output([
        "diff", "--name-only", EVALUATOR_BASE_REF, "HEAD", "--", "evals/deliver"
    ]).splitlines())
    if not changed or not changed.issubset(set(EVALUATOR_ALLOWLIST)):
        raise HarnessError("evaluator commit changed paths outside the v11 allowlist")
    baseline_expected = git_ref_package_manifest(BASELINE_REF, BASELINE_PACKAGE_PATHS)
    candidate_expected = git_ref_package_manifest(CANDIDATE_REF, CANDIDATE_PACKAGE_PATHS)
    validate_supplied_package(
        baseline_package, baseline_expected, BASELINE_PACKAGE_PATHS, "baseline"
    )
    validate_supplied_package(
        candidate_package, candidate_expected, CANDIDATE_PACKAGE_PATHS, "candidate"
    )
    sentinel = ensure_external_sentinel(runtime_root)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": comparison_id or str(uuid.uuid4()),
        "evaluator_identity": identity,
        "evaluator_base_ref": EVALUATOR_BASE_REF,
        "evaluator_allowlist": list(EVALUATOR_ALLOWLIST),
        "evaluator_changed_paths": sorted(changed),
        "baseline": {
            "ref": BASELINE_REF,
            "package_manifest": baseline_expected,
        },
        "candidate": {
            "ref": CANDIDATE_REF,
            "package_manifest": candidate_expected,
        },
        "runtime_root": str(runtime_root),
        "arm_order": list(OFFICIAL_ARM_ORDER),
        "attempt_policy": {
            "restart_cause": "external_interruption_only",
            "maximum_attempts_per_arm": 2,
        },
        "external_sentinel": sentinel,
    }
    atomic_write_json(manifest_path, manifest)
    comparison = validate_comparison_manifest(manifest_path)
    state = {
        "schema_version": SCHEMA_VERSION,
        "comparison_manifest_sha256": comparison["comparison_manifest_sha256"],
        "next_arm_index": 0,
        "arms": {
            arm: {
                "status": "pending",
                "attempts": [],
                "terminal_seal_sha256": None,
            }
            for arm in OFFICIAL_ARM_ORDER
        },
        "blind": {
            "status": "pending",
            "blind_packet_sha256": None,
            "private_mapping_sha256": None,
        },
        "judge": {"status": "pending", "attempts": [], "frozen_record_sha256": None},
        "final_verdict_sha256": None,
        "cleanup_receipt_sha256": None,
    }
    atomic_write_json(comparison_control(runtime_root) / COMPARISON_STATE, state)
    (comparison_control(runtime_root) / COMPARISON_LOCK).touch(mode=0o600)
    return manifest_path


def validate_comparison_manifest(
    path: Path, *, recompute_evaluator: bool = True,
    recompute_packages: bool = False,
) -> dict[str, Any]:
    require_regular_file(path, "comparison manifest")
    document = json.loads(path.read_text(encoding="utf-8"))
    fields = {
        "schema_version", "comparison_id", "evaluator_identity",
        "evaluator_base_ref",
        "evaluator_allowlist", "evaluator_changed_paths", "baseline", "candidate",
        "runtime_root", "arm_order", "attempt_policy", "external_sentinel",
    }
    if not isinstance(document, dict) or set(document) != fields:
        raise HarnessError("comparison manifest fields are not exact")
    runtime_root = Path(document["runtime_root"])
    if (
        document["schema_version"] != SCHEMA_VERSION
        or not isinstance(document["comparison_id"], str)
        or not document["comparison_id"].strip()
        or document["evaluator_allowlist"] != list(EVALUATOR_ALLOWLIST)
        or document["evaluator_base_ref"] != EVALUATOR_BASE_REF
        or not isinstance(document["evaluator_changed_paths"], list)
        or not set(document["evaluator_changed_paths"]).issubset(set(EVALUATOR_ALLOWLIST))
        or document["arm_order"] != list(OFFICIAL_ARM_ORDER)
        or document["attempt_policy"] != {
            "restart_cause": "external_interruption_only",
            "maximum_attempts_per_arm": 2,
        }
        or runtime_root.resolve() != runtime_root
        or path.resolve() != comparison_manifest_path(runtime_root).resolve()
    ):
        raise HarnessError("comparison manifest frozen conditions are invalid")
    validate_evaluator_identity(
        document["evaluator_identity"], recompute=recompute_evaluator
    )
    for variant, expected_ref, expected_paths in (
        ("baseline", BASELINE_REF, BASELINE_PACKAGE_PATHS),
        ("candidate", CANDIDATE_REF, CANDIDATE_PACKAGE_PATHS),
    ):
        package = document[variant]
        if (
            not isinstance(package, dict)
            or set(package) != {"ref", "package_manifest"}
            or package["ref"] != expected_ref
            or not isinstance(package["package_manifest"], dict)
            or set(package["package_manifest"]) != {"files", "manifest_sha256"}
        ):
            raise HarnessError(f"comparison {variant} package binding is invalid")
        payload = {"files": package["package_manifest"]["files"]}
        if package["package_manifest"]["manifest_sha256"] != sha256_bytes(
            canonical_json(payload)
        ):
            raise HarnessError(f"comparison {variant} package manifest digest drifted")
        if recompute_packages and package["package_manifest"] != git_ref_package_manifest(
            expected_ref, expected_paths
        ):
            raise HarnessError(f"comparison {variant} package ref provenance drifted")
    verify_external_sentinel(document["external_sentinel"], runtime_root)
    document["comparison_manifest_sha256"] = sha256_file(path)
    return document


def binding_from_comparison(document: dict[str, Any]) -> dict[str, object]:
    return {
        "comparison_manifest_sha256": document["comparison_manifest_sha256"],
        "evaluator_identity": document["evaluator_identity"],
    }


@contextlib.contextmanager
def locked_attempt_state(
    manifest_path: Path, *, _comparison: dict[str, Any] | None = None
) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    comparison = _comparison or validate_comparison_manifest(manifest_path)
    runtime_root = Path(comparison["runtime_root"])
    lock_path = comparison_control(runtime_root) / COMPARISON_LOCK
    require_regular_file(lock_path, "comparison attempt lock")
    with lock_path.open("r+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        state_path = comparison_control(runtime_root) / COMPARISON_STATE
        require_regular_file(state_path, "comparison attempt state")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("comparison_manifest_sha256") != comparison["comparison_manifest_sha256"]:
            raise HarnessError("attempt state belongs to a different comparison")
        validate_attempt_state_document(state, comparison)
        yield comparison, state
        validate_attempt_state_document(state, comparison)
        atomic_write_json(state_path, state)
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def validate_attempt_state_document(
    state: object, comparison: dict[str, Any]
) -> dict[str, Any]:
    fields = {
        "schema_version", "comparison_manifest_sha256", "next_arm_index",
        "arms", "blind", "judge", "final_verdict_sha256",
        "cleanup_receipt_sha256",
    }
    if (
        not isinstance(state, dict)
        or set(state) != fields
        or state["schema_version"] != SCHEMA_VERSION
        or not isinstance(state["next_arm_index"], int)
        or isinstance(state["next_arm_index"], bool)
        or not 0 <= state["next_arm_index"] <= len(OFFICIAL_ARM_ORDER)
        or set(state["arms"]) != set(OFFICIAL_ARM_ORDER)
        or state["final_verdict_sha256"] is not None
        and not is_digest(state["final_verdict_sha256"])
        or state["cleanup_receipt_sha256"] is not None
        and not is_digest(state["cleanup_receipt_sha256"])
    ):
        raise HarnessError("comparison attempt state fields are invalid")
    blind = state["blind"]
    if (
        not isinstance(blind, dict)
        or set(blind) != {
            "status", "blind_packet_sha256", "private_mapping_sha256"
        }
        or blind["status"] not in {"pending", "frozen"}
        or blind["blind_packet_sha256"] is not None
        and not is_digest(blind["blind_packet_sha256"])
        or blind["private_mapping_sha256"] is not None
        and not is_digest(blind["private_mapping_sha256"])
    ):
        raise HarnessError("comparison blind state is invalid")
    for arm_name in OFFICIAL_ARM_ORDER:
        arm = state["arms"][arm_name]
        if (
            not isinstance(arm, dict)
            or set(arm) != {"status", "attempts", "terminal_seal_sha256"}
            or arm["status"] not in {"pending", "running", "interrupted", "sealed"}
            or not isinstance(arm["attempts"], list)
            or len(arm["attempts"]) > comparison["attempt_policy"]["maximum_attempts_per_arm"]
            or arm["terminal_seal_sha256"] is not None
            and not is_digest(arm["terminal_seal_sha256"])
        ):
            raise HarnessError("comparison arm attempt state is invalid")
        for index, attempt in enumerate(arm["attempts"], 1):
            if (
                not isinstance(attempt, dict)
                or set(attempt) != {
                    "attempt", "input_sha256", "start_phase", "phase_inputs",
                    "status", "interruption"
                }
                or attempt["attempt"] != index
                or not is_digest(attempt["input_sha256"])
                or attempt["start_phase"] not in RUNNER_PHASES
                or not isinstance(attempt["phase_inputs"], dict)
                or not set(attempt["phase_inputs"]).issubset(set(RUNNER_PHASES))
                or any(not is_digest(value) for value in attempt["phase_inputs"].values())
                or attempt["status"] not in {"running", "interrupted", "sealed"}
                or (
                    attempt["interruption"] is not None
                    and (
                        not isinstance(attempt["interruption"], dict)
                        or set(attempt["interruption"]) != {"cause", "reason", "phase"}
                        or attempt["interruption"]["cause"] != "external_interruption"
                        or not isinstance(attempt["interruption"]["reason"], str)
                        or not attempt["interruption"]["reason"].strip()
                        or attempt["interruption"]["phase"] not in RUNNER_PHASES
                    )
                )
            ):
                raise HarnessError("comparison arm attempt record is invalid")
            if (
                attempt["phase_inputs"].get(attempt["start_phase"])
                != attempt["input_sha256"]
                or (attempt["status"] == "interrupted")
                != (attempt["interruption"] is not None)
                or index == 1 and attempt["start_phase"] != "pre-packet"
            ):
                raise HarnessError("comparison arm attempt lineage is incoherent")
            active_phase = active_attempt_phase(attempt)
            if (
                attempt["interruption"] is not None
                and attempt["interruption"]["phase"] != active_phase
            ):
                raise HarnessError("comparison arm interruption is not on the active phase")
            if index > 1:
                previous = arm["attempts"][index - 2]
                if (
                    previous["status"] != "interrupted"
                    or previous["interruption"]["phase"] != attempt["start_phase"]
                    or previous["phase_inputs"].get(attempt["start_phase"])
                    != attempt["input_sha256"]
                ):
                    raise HarnessError("comparison arm restart lineage is incoherent")
        attempts = arm["attempts"]
        if arm["status"] == "pending":
            coherent = not attempts and arm["terminal_seal_sha256"] is None
        else:
            coherent = bool(attempts) and attempts[-1]["status"] == arm["status"]
            coherent = coherent and all(
                attempt["status"] == "interrupted" for attempt in attempts[:-1]
            )
            coherent = coherent and (
                (arm["status"] == "sealed")
                == (arm["terminal_seal_sha256"] is not None)
            )
        if not coherent:
            raise HarnessError("comparison arm state is semantically incoherent")
    judge = state["judge"]
    if (
        not isinstance(judge, dict)
        or set(judge) != {"status", "attempts", "frozen_record_sha256"}
        or judge["status"] not in {"pending", "running", "interrupted", "frozen"}
        or not isinstance(judge["attempts"], list)
        or len(judge["attempts"]) > 2
        or judge["frozen_record_sha256"] is not None
        and not is_digest(judge["frozen_record_sha256"])
    ):
        raise HarnessError("comparison judge attempt state is invalid")
    for index, attempt in enumerate(judge["attempts"], 1):
        if (
            not isinstance(attempt, dict)
            or set(attempt) != {
                "attempt", "blind_packet_sha256", "status", "interruption"
            }
            or attempt["attempt"] != index
            or not is_digest(attempt["blind_packet_sha256"])
            or attempt["status"] not in {"running", "interrupted", "frozen"}
            or (
                attempt["interruption"] is not None
                and (
                    not isinstance(attempt["interruption"], dict)
                    or set(attempt["interruption"]) != {"cause", "reason"}
                    or attempt["interruption"]["cause"] != "external_interruption"
                    or not isinstance(attempt["interruption"]["reason"], str)
                    or not attempt["interruption"]["reason"].strip()
                )
            )
        ):
            raise HarnessError("comparison judge attempt record is invalid")
        if (
            (attempt["status"] == "interrupted")
            != (attempt["interruption"] is not None)
            or state["blind"]["blind_packet_sha256"]
            != attempt["blind_packet_sha256"]
        ):
            raise HarnessError("comparison judge attempt lineage is incoherent")
    sealed_prefix = 0
    for arm_name in OFFICIAL_ARM_ORDER:
        if state["arms"][arm_name]["status"] != "sealed":
            break
        sealed_prefix += 1
    if (
        state["next_arm_index"] != sealed_prefix
        or any(
            state["arms"][arm]["status"] != "pending"
            for arm in OFFICIAL_ARM_ORDER[sealed_prefix + 1:]
        )
        or (blind["status"] == "pending")
        != (blind["blind_packet_sha256"] is None and blind["private_mapping_sha256"] is None)
        or blind["status"] == "frozen" and not (
            is_digest(blind["blind_packet_sha256"])
            and is_digest(blind["private_mapping_sha256"])
        )
        or blind["status"] == "frozen" and sealed_prefix != len(OFFICIAL_ARM_ORDER)
    ):
        raise HarnessError("comparison state order or blind lifecycle is incoherent")
    if judge["status"] == "pending":
        judge_coherent = not judge["attempts"] and judge["frozen_record_sha256"] is None
    else:
        judge_coherent = (
            blind["status"] == "frozen" and bool(judge["attempts"])
            and judge["attempts"][-1]["status"] == judge["status"]
            and all(
                attempt["status"] == "interrupted"
                for attempt in judge["attempts"][:-1]
            )
            and (judge["status"] == "frozen")
            == (judge["frozen_record_sha256"] is not None)
        )
    if (
        not judge_coherent
        or state["cleanup_receipt_sha256"] is not None
        and state["final_verdict_sha256"] is None
    ):
        raise HarnessError("comparison judge or final lifecycle is incoherent")
    return state


def attempt_state_projection(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": state["schema_version"],
        "comparison_manifest_sha256": state["comparison_manifest_sha256"],
        "next_arm_index": state["next_arm_index"],
        "arms": state["arms"],
        "blind": state["blind"],
        "judge": state["judge"],
    }


def attempt_state_sha256(state: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(attempt_state_projection(state)))


def require_unfinalized_state(state: dict[str, Any]) -> None:
    if state["final_verdict_sha256"] is not None:
        raise HarnessError("comparison is immutable after the final verdict")


def active_attempt_phase(attempt: dict[str, Any]) -> str:
    phases = set(attempt["phase_inputs"])
    start = RUNNER_PHASES.index(attempt["start_phase"])
    latest = max(RUNNER_PHASES.index(phase) for phase in phases)
    if phases != set(RUNNER_PHASES[start:latest + 1]):
        raise HarnessError("comparison arm phases are not monotonic")
    return RUNNER_PHASES[latest]


def begin_arm_attempt(
    manifest_path: Path, arm_name: str, input_sha256: str, phase: str = "pre-packet",
    *, _comparison: dict[str, Any] | None = None,
) -> dict[str, object]:
    if not is_digest(input_sha256):
        raise HarnessError("arm attempt input digest is invalid")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (comparison, state):
        require_unfinalized_state(state)
        order = comparison["arm_order"]
        if (
            arm_name not in order
            or state["next_arm_index"] >= len(order)
            or order[state["next_arm_index"]] != arm_name
        ):
            raise HarnessError("arm start is out of the precommitted four-arm order")
        arm = state["arms"][arm_name]
        if arm["terminal_seal_sha256"] is not None or arm["status"] == "sealed":
            raise HarnessError("sealed arm cannot be started again")
        attempts = arm["attempts"]
        if arm["status"] == "pending":
            if attempts or phase != "pre-packet":
                raise HarnessError("pending arm already has an attempt")
        elif arm["status"] == "interrupted":
            if (
                len(attempts) != 1
                or attempts[0]["phase_inputs"].get(phase) != input_sha256
                or attempts[0].get("interruption") is None
                or attempts[0]["interruption"].get("phase") != phase
            ):
                raise HarnessError("arm restart is not a recorded byte-identical interruption")
        else:
            raise HarnessError("arm already has an active unsealed attempt")
        if len(attempts) >= comparison["attempt_policy"]["maximum_attempts_per_arm"]:
            raise HarnessError("arm attempt policy is exhausted")
        attempt = {
            "attempt": len(attempts) + 1,
            "input_sha256": input_sha256,
            "start_phase": phase,
            "phase_inputs": {phase: input_sha256},
            "status": "running",
            "interruption": None,
        }
        attempts.append(attempt)
        arm["status"] = "running"
        return json.loads(json.dumps(attempt))


def bind_arm_phase_input(
    manifest_path: Path, arm_name: str, phase: str, input_sha256: str, *,
    _comparison: dict[str, Any] | None = None,
) -> int:
    if phase not in RUNNER_PHASES or not is_digest(input_sha256):
        raise HarnessError("arm phase input binding is invalid")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (_locked_comparison, state):
        require_unfinalized_state(state)
        arm = state["arms"][arm_name]
        if arm["status"] != "running" or not arm["attempts"]:
            raise HarnessError("arm phase requires an active attempt")
        attempt = arm["attempts"][-1]
        previous = attempt["phase_inputs"].get(phase)
        if previous is not None and previous != input_sha256:
            raise HarnessError("arm phase inputs drifted within the active attempt")
        active = active_attempt_phase(attempt)
        if RUNNER_PHASES.index(phase) not in {
            RUNNER_PHASES.index(active), RUNNER_PHASES.index(active) + 1,
        }:
            raise HarnessError("arm phase binding is not monotonic")
        attempt["phase_inputs"][phase] = input_sha256
        return attempt["attempt"]


def record_external_interruption(
    manifest_path: Path, arm_name: str, reason: str, phase: str = "pre-packet", *,
    _comparison: dict[str, Any] | None = None,
) -> None:
    if not isinstance(reason, str) or not reason.strip():
        raise HarnessError("external interruption reason is required")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (_locked_comparison, state):
        require_unfinalized_state(state)
        arm = state["arms"].get(arm_name)
        if (
            not isinstance(arm, dict)
            or arm["status"] != "running"
            or arm["terminal_seal_sha256"] is not None
            or not arm["attempts"]
            or arm["attempts"][-1]["status"] != "running"
            or phase != active_attempt_phase(arm["attempts"][-1])
        ):
            raise HarnessError("only an active unsealed arm can record interruption")
        arm["attempts"][-1]["status"] = "interrupted"
        arm["attempts"][-1]["interruption"] = {
            "cause": "external_interruption",
            "reason": reason.strip(),
            "phase": phase,
        }
        arm["status"] = "interrupted"


def register_terminal_seal(
    manifest_path: Path, arm_name: str, terminal_seal_sha256: str, *,
    _comparison: dict[str, Any] | None = None,
) -> None:
    if not is_digest(terminal_seal_sha256):
        raise HarnessError("terminal seal digest is invalid")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (comparison, state):
        require_unfinalized_state(state)
        arm = state["arms"].get(arm_name)
        if (
            not isinstance(arm, dict)
            or arm["status"] != "running"
            or arm["terminal_seal_sha256"] is not None
            or not arm["attempts"]
            or arm["attempts"][-1]["status"] != "running"
        ):
            raise HarnessError("duplicate, concurrent, or inactive terminal seal rejected")
        arm["attempts"][-1]["status"] = "sealed"
        arm["terminal_seal_sha256"] = terminal_seal_sha256
        arm["status"] = "sealed"
        state["next_arm_index"] += 1
        if state["next_arm_index"] > len(comparison["arm_order"]):
            raise HarnessError("attempt state advanced past the four-arm order")


def validate_attempt_state(
    manifest_path: Path, *, require_all_sealed: bool = False,
    _comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (comparison, state):
        if set(state.get("arms", {})) != set(OFFICIAL_ARM_ORDER):
            raise HarnessError("attempt state arm fields are not exact")
        if require_all_sealed and (
            state.get("next_arm_index") != len(OFFICIAL_ARM_ORDER)
            or any(
                state["arms"][arm]["status"] != "sealed"
                or not is_digest(state["arms"][arm]["terminal_seal_sha256"])
                for arm in OFFICIAL_ARM_ORDER
            )
        ):
            raise HarnessError("comparison does not have four terminally sealed arms")
        return json.loads(json.dumps({"comparison": comparison, "state": state}))


def begin_judge_attempt(
    manifest_path: Path, blind_packet_sha256: str, *,
    _comparison: dict[str, Any] | None = None,
) -> None:
    if not is_digest(blind_packet_sha256):
        raise HarnessError("blind packet digest is invalid")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (_locked_comparison, state):
        require_unfinalized_state(state)
        if any(state["arms"][arm]["status"] != "sealed" for arm in OFFICIAL_ARM_ORDER):
            raise HarnessError("judge cannot start before all four arms are sealed")
        if (
            state["blind"]["status"] != "frozen"
            or state["blind"]["blind_packet_sha256"] != blind_packet_sha256
        ):
            raise HarnessError("judge input is not the frozen blind packet")
        judge = state["judge"]
        attempts = judge["attempts"]
        if judge["status"] == "pending":
            if attempts:
                raise HarnessError("pending judge already has an attempt")
        elif judge["status"] == "interrupted":
            if (
                len(attempts) != 1
                or attempts[0]["blind_packet_sha256"] != blind_packet_sha256
                or attempts[0].get("interruption") is None
            ):
                raise HarnessError("judge restart is not a byte-identical interruption")
        else:
            raise HarnessError("judge is already active or frozen")
        if len(attempts) >= 2:
            raise HarnessError("judge attempt policy is exhausted")
        attempts.append({
            "attempt": len(attempts) + 1,
            "blind_packet_sha256": blind_packet_sha256,
            "status": "running",
            "interruption": None,
        })
        judge["status"] = "running"


def register_blind_packet(
    manifest_path: Path, blind_packet_sha256: str, mapping_sha256: str, *,
    _comparison: dict[str, Any] | None = None,
) -> None:
    if not is_digest(blind_packet_sha256) or not is_digest(mapping_sha256):
        raise HarnessError("blind packet or private mapping digest is invalid")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (_locked_comparison, state):
        require_unfinalized_state(state)
        if any(state["arms"][arm]["status"] != "sealed" for arm in OFFICIAL_ARM_ORDER):
            raise HarnessError("blind packet cannot freeze before all arms are sealed")
        if state["blind"] != {
            "status": "pending",
            "blind_packet_sha256": None,
            "private_mapping_sha256": None,
        }:
            raise HarnessError("blind packet or private mapping is already frozen")
        state["blind"] = {
            "status": "frozen",
            "blind_packet_sha256": blind_packet_sha256,
            "private_mapping_sha256": mapping_sha256,
        }


def record_judge_interruption(
    manifest_path: Path, reason: str, *,
    _comparison: dict[str, Any] | None = None,
) -> None:
    if not isinstance(reason, str) or not reason.strip():
        raise HarnessError("judge interruption reason is required")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (_locked_comparison, state):
        require_unfinalized_state(state)
        judge = state["judge"]
        if (
            judge["status"] != "running"
            or judge["frozen_record_sha256"] is not None
            or not judge["attempts"]
        ):
            raise HarnessError("only an active unfrozen judge can record interruption")
        judge["attempts"][-1]["status"] = "interrupted"
        judge["attempts"][-1]["interruption"] = {
            "cause": "external_interruption", "reason": reason.strip()
        }
        judge["status"] = "interrupted"


def register_judge_record(
    manifest_path: Path, record_sha256: str, *,
    _comparison: dict[str, Any] | None = None,
) -> None:
    if not is_digest(record_sha256):
        raise HarnessError("frozen judge record digest is invalid")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (_locked_comparison, state):
        require_unfinalized_state(state)
        judge = state["judge"]
        if (
            judge["status"] != "running"
            or judge["frozen_record_sha256"] is not None
            or not judge["attempts"]
            or judge["attempts"][-1]["status"] != "running"
        ):
            raise HarnessError("duplicate or restarted frozen judge rejected")
        judge["attempts"][-1]["status"] = "frozen"
        judge["status"] = "frozen"
        judge["frozen_record_sha256"] = record_sha256


def register_final_verdict(
    manifest_path: Path, verdict_sha256: str, *, require_judge: bool = True,
    _comparison: dict[str, Any] | None = None,
) -> None:
    if not is_digest(verdict_sha256):
        raise HarnessError("final verdict digest is invalid")
    with locked_attempt_state(
        manifest_path, _comparison=_comparison
    ) as (_locked_comparison, state):
        require_unfinalized_state(state)
        if require_judge and state["judge"]["status"] != "frozen":
            raise HarnessError("final verdict requires a frozen judge")
        if state["final_verdict_sha256"] is not None:
            raise HarnessError("final verdict is already frozen")
        state["final_verdict_sha256"] = verdict_sha256


def reject_symlink_chain(root: Path, relative: Path) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise HarnessError(f"symlink input rejected: {relative}")


def safe_path(root: Path, relative: str | Path, *, must_exist: bool = True) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise HarnessError(f"path escape rejected: {relative}")
    reject_symlink_chain(root, relative_path)
    path = root / relative_path
    try:
        path.resolve(strict=must_exist).relative_to(root.resolve())
    except (FileNotFoundError, ValueError) as exc:
        raise HarnessError(f"path outside staging root rejected: {relative}") from exc
    return path


def require_stage_root(path: Path, scenario_id: str | None = None) -> Path:
    arm = path.resolve()
    runtime = arm.parent
    valid_names = ARM_NAMES if scenario_id is None else (
        f"{scenario_id}-baseline", f"{scenario_id}-candidate"
    )
    if (
        runtime.parent != STAGE_ROOT
        or not re.fullmatch(r"deliver-eval-[A-Za-z0-9._-]+", runtime.name)
        or arm.name not in valid_names
        or (
            runtime.is_dir()
            and any(
                child.name not in set((*ARM_NAMES, SIBLING_PROBE, COMPARISON_CONTROL))
                for child in runtime.iterdir()
            )
        )
    ):
        raise HarnessError(
            "arm stage must be a named baseline/candidate child of /private/tmp/deliver-eval-<run>"
        )
    return arm


def ensure_sibling_probe(stage_root: Path) -> Path:
    probe = stage_root.parent / SIBLING_PROBE
    sentinel = probe / SIBLING_SENTINEL
    if not probe.exists():
        probe.mkdir(mode=0o700)
        fd = os.open(sentinel, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(b"runner sibling isolation probe\n")
    if (
        probe.is_symlink()
        or sentinel.is_symlink()
        or not sentinel.is_file()
        or sentinel.read_bytes() != b"runner sibling isolation probe\n"
    ):
        raise HarnessError("runtime sibling isolation probe is invalid")
    return sentinel


def reject_evaluator_path(relative: Path) -> None:
    lowered = {part.lower() for part in relative.parts}
    if lowered & DENIED_INPUT_PARTS or relative.name.lower() in DENIED_INPUT_NAMES:
        raise HarnessError(f"evaluator-owned runner input rejected: {relative}")


def copy_regular_file(source_root: Path, relative: Path, destination: Path) -> None:
    reject_evaluator_path(relative)
    source = safe_path(source_root, relative)
    if not source.is_file():
        raise HarnessError(f"non-file runner input rejected: {relative}")
    target = safe_path(destination, relative, must_exist=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    target.chmod(stat.S_IMODE(source.stat().st_mode))


def copy_directory(source: Path, destination: Path) -> None:
    if not source.is_dir() or source.is_symlink():
        raise HarnessError(f"fixture directory rejected: {source}")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        reject_symlink_chain(source, relative)
        if path.is_dir():
            continue
        copy_regular_file(source, relative, destination)


def materialize_git_ref(
    repo_root: Path, ref: str, paths: list[str], destination: Path
) -> dict[str, object]:
    resolved = run(["git", "rev-parse", f"{ref}^{{commit}}"], cwd=repo_root).strip()
    tree = run(["git", "rev-parse", f"{resolved}^{{tree}}"], cwd=repo_root).strip()
    if not paths or len(paths) != len(set(paths)):
        raise HarnessError("git-ref subset must contain unique paths")
    blobs: dict[str, dict[str, str]] = {}
    for raw_path in sorted(paths):
        relative = Path(raw_path)
        reject_evaluator_path(relative)
        if relative.is_absolute() or ".." in relative.parts:
            raise HarnessError(f"git-ref subset path escape rejected: {relative}")
        listing = run(["git", "ls-tree", resolved, "--", relative.as_posix()], cwd=repo_root).strip()
        if not listing:
            raise HarnessError(f"pinned git-ref path missing: {relative}")
        metadata, listed_path = listing.split("\t", 1)
        mode, object_type, object_id = metadata.split()
        if listed_path != relative.as_posix():
            raise HarnessError(f"pinned git-ref path mismatch: {relative}")
        if object_type != "blob" or mode == "120000":
            raise HarnessError(f"unsupported git entry rejected: {mode} {relative}")
        target = safe_path(destination, relative, must_exist=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(
            ["git", "cat-file", "blob", object_id],
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
        target.write_bytes(blob)
        target.chmod(0o755 if mode == "100755" else 0o644)
        blobs[relative.as_posix()] = {"blob": object_id, "mode": mode}
    return {
        "kind": "git_ref_subset",
        "resolved_commit": resolved,
        "source_tree": tree,
        "blobs": blobs,
    }


def initialize_snapshot(repo: Path, message: str) -> str:
    run(["git", "init", "-q", "-b", "eval"], cwd=repo)
    run(["git", "add", "-f", "--all"], cwd=repo)
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_DATE": FIXED_AUTHOR_DATE,
            "GIT_COMMITTER_DATE": FIXED_AUTHOR_DATE,
        }
    )
    run(
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
            message,
        ],
        cwd=repo,
        env=environment,
    )
    return run(["git", "rev-parse", "HEAD"], cwd=repo).strip()


def scenario_descriptor(scenario_id: str) -> tuple[Path, dict[str, Any]]:
    scenario_root = safe_path(SUITE_ROOT, scenario_id)
    descriptor_path = safe_path(scenario_root, "scenario.json")
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    if descriptor.get("id") != scenario_id:
        raise HarnessError("scenario id does not match its directory")
    return scenario_root, descriptor


def iter_manifest_files(stage_root: Path) -> Iterable[dict[str, object]]:
    for category in ("repo", "scenario", "contract"):
        root = safe_path(stage_root, category)
        for path in sorted(root.rglob("*")):
            if path.is_dir() or ".git" in path.relative_to(stage_root).parts:
                continue
            relative = path.relative_to(stage_root)
            reject_symlink_chain(stage_root, relative)
            reject_evaluator_path(relative)
            yield {
                "category": "scenario_stage" if category == "scenario" else category,
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }


def write_manifest(
    stage_root: Path,
    descriptor: dict[str, Any],
    fixture_source: object,
    initial_snapshot: dict[str, str],
    stage: str,
    *,
    parent_manifest_sha256: str | None = None,
) -> None:
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": descriptor["id"],
        "scenario_stage": stage,
        "fixture_source": fixture_source,
        "initial_snapshot": initial_snapshot,
        "parent_manifest_sha256": parent_manifest_sha256,
        "fixed_conditions": descriptor["fixed_conditions"],
        "files": list(iter_manifest_files(stage_root)),
    }
    manifest_path = stage_root / "runner-manifest.json"
    write_json(manifest_path, manifest)
    (stage_root / "runner-manifest.sha256").write_text(
        f"{sha256_file(manifest_path)}  runner-manifest.json\n", encoding="ascii"
    )


def prepare_scenario(
    scenario_id: str,
    contract: Path,
    destination: Path,
    runner_preflight: Path,
    comparison_manifest: Path | None = None,
) -> dict[str, object]:
    destination = require_stage_root(destination, scenario_id)
    try:
        destination.parent.mkdir(mode=0o700, exist_ok=True)
    except OSError as exc:
        raise HarnessError("unable to create the validated eval runtime root") from exc
    destination = require_stage_root(destination, scenario_id)
    ensure_sibling_probe(destination)
    if destination.exists() and any(destination.iterdir()):
        raise HarnessError(f"destination must be absent or empty: {destination}")
    if contract.is_symlink() or not (contract.is_file() or contract.is_dir()):
        raise HarnessError("contract must be a regular extracted file or package directory")
    preflight = validate_runner_preflight(runner_preflight)
    if comparison_manifest is not None:
        comparison = validate_comparison_manifest(comparison_manifest)
        if Path(comparison["runtime_root"]) != destination.parent:
            raise HarnessError("arm stage belongs to a different comparison runtime")
        expected_binding = binding_from_comparison(comparison)
        if preflight.get("comparison_binding") != expected_binding:
            raise HarnessError("runner preflight belongs to a different comparison")
        variant = destination.name.rsplit("-", 1)[-1]
        package_root = contract if contract.is_dir() else contract.parent
        validate_supplied_package(
            package_root,
            comparison[variant]["package_manifest"],
            BASELINE_PACKAGE_PATHS if variant == "baseline" else CANDIDATE_PACKAGE_PATHS,
            variant,
        )
    destination.mkdir(parents=True, exist_ok=True)
    repo = destination / "repo"
    scenario_destination = destination / "scenario"
    contract_destination = destination / "contract"
    repo.mkdir()
    scenario_destination.mkdir()
    contract_destination.mkdir()
    evidence = destination / "evidence"
    evidence.mkdir()
    write_json(evidence / "runner-preflight.json", preflight)

    scenario_root, descriptor = scenario_descriptor(scenario_id)
    fixture = descriptor["fixture"]
    if fixture["kind"] == "directory":
        fixture_root = safe_path(scenario_root, fixture["path"])
        copy_directory(fixture_root, repo)
        frozen_tree = tree_hash(fixture_root)
        if frozen_tree != fixture["tree_sha256"]:
            raise HarnessError("tracked directory fixture drifted from its frozen tree hash")
        fixture_source: object = {
            "kind": "directory",
            "path": fixture["path"],
            "tree_sha256": frozen_tree,
        }
    elif fixture["kind"] == "git_ref":
        if fixture["repository"] != "repo_root":
            raise HarnessError("historical git fixtures must name the suite repository root")
        repository = SUITE_ROOT.parents[1]
        fixture_source = materialize_git_ref(repository, fixture["ref"], fixture["paths"], repo)
        expected_source = {
            "kind": "git_ref_subset",
            "resolved_commit": fixture["resolved_commit"],
            "source_tree": fixture["tree"],
            "blobs": fixture["blobs"],
        }
        if fixture_source != expected_source:
            raise HarnessError("pinned historical fixture commit, tree, or blob evidence drifted")
    else:
        raise HarnessError(f"unknown fixture kind: {fixture['kind']}")

    for relative_name in descriptor["pre_packet_files"]:
        relative = Path(relative_name)
        source = safe_path(scenario_root, relative)
        target = safe_path(scenario_destination, Path(relative.name), must_exist=False)
        target.write_bytes(source.read_bytes())
    if contract.is_dir():
        copy_directory(contract, contract_destination)
    else:
        (contract_destination / "SKILL.md").write_bytes(contract.read_bytes())
    skill_files = sorted(contract_destination.rglob("SKILL.md"))
    if len(skill_files) != 1:
        raise HarnessError("runner contract package must expose exactly one SKILL.md")
    if not re.search(r"^name:\s*deliver\s*$", skill_files[0].read_text(encoding="utf-8"), re.MULTILINE):
        raise HarnessError("the single runner-visible SKILL.md must be the Deliver contract")
    head = initialize_snapshot(repo, f"Frozen {scenario_id} fixture")
    initial_snapshot = {
        "commit": head,
        "tree": run(["git", "rev-parse", f"{head}^{{tree}}"], cwd=repo).strip(),
    }
    write_manifest(destination, descriptor, fixture_source, initial_snapshot, "pre_packet")
    verify_manifest(destination)
    result: dict[str, object] = {
        "head": head, "tree": initial_snapshot["tree"], "fixture_source": fixture_source
    }
    if comparison_manifest is not None:
        result["comparison_binding"] = binding_from_comparison(comparison)
    return result


def tree_hash(root: Path) -> str:
    entries: list[tuple[str, str, int]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_dir() or ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        reject_symlink_chain(root, relative)
        entries.append((relative.as_posix(), sha256_file(path), stat.S_IMODE(path.stat().st_mode)))
    return sha256_bytes(canonical_json(entries))


def verify_manifest(stage_root: Path, *, allow_repo_changes: bool = False) -> dict[str, Any]:
    manifest_path = safe_path(stage_root, "runner-manifest.json")
    expected_line = safe_path(stage_root, "runner-manifest.sha256").read_text(encoding="ascii")
    expected_hash = sha256_file(manifest_path)
    if expected_line != f"{expected_hash}  runner-manifest.json\n":
        raise HarnessError("runner manifest hash sidecar is invalid")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version",
        "scenario_id",
        "scenario_stage",
        "fixture_source",
        "initial_snapshot",
        "parent_manifest_sha256",
        "fixed_conditions",
        "files",
    }:
        raise HarnessError("runner manifest fields are not exact")
    if (
        manifest["schema_version"] != SCHEMA_VERSION
        or manifest["scenario_id"]
        not in {"retry-failed", "preflight-remediation-holdout"}
        or manifest["scenario_stage"] not in {"pre_packet", "review_packet"}
        or not isinstance(manifest["files"], list)
    ):
        raise HarnessError("runner manifest schema or stage is invalid")
    _, descriptor = scenario_descriptor(manifest["scenario_id"])
    if manifest["fixed_conditions"] != descriptor["fixed_conditions"]:
        raise HarnessError("runner manifest fixed conditions drifted")
    parent = manifest["parent_manifest_sha256"]
    if manifest["scenario_stage"] == "pre_packet" and parent is not None:
        raise HarnessError("pre-packet manifest must not have a parent")
    if manifest["scenario_stage"] == "review_packet" and (
        not isinstance(parent, str) or not HEX_DIGEST.fullmatch(parent)
    ):
        raise HarnessError("review-packet manifest parent digest is invalid")
    initial = manifest["initial_snapshot"]
    if not valid_initial_snapshot(initial):
        raise HarnessError("runner manifest initial snapshot is invalid")
    repo = safe_path(stage_root, "repo")
    if run(["git", "rev-parse", f"{initial['commit']}^{{tree}}"], cwd=repo).strip() != initial["tree"]:
        raise HarnessError("prepared fixture commit/tree is unavailable or changed")
    listed: set[str] = set()
    category_roots = {
        "repo": "repo",
        "scenario_stage": "scenario",
        "contract": "contract",
    }
    for entry in manifest["files"]:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"category", "path", "sha256", "size"}
            or entry["category"] not in category_roots
            or not isinstance(entry["path"], str)
            or not isinstance(entry["sha256"], str)
            or not HEX_DIGEST.fullmatch(entry["sha256"])
            or isinstance(entry["size"], bool)
            or not isinstance(entry["size"], int)
            or entry["size"] < 0
        ):
            raise HarnessError("runner manifest file entry is invalid")
        relative = Path(entry["path"])
        if not relative.parts or relative.parts[0] != category_roots[entry["category"]]:
            raise HarnessError(f"runner manifest category/path mismatch: {relative}")
        if entry["path"] in listed:
            raise HarnessError(f"duplicate runner manifest path: {relative}")
        reject_evaluator_path(relative)
        if allow_repo_changes and entry["category"] == "repo":
            listed.add(relative.as_posix())
            continue
        path = safe_path(stage_root, relative)
        if (
            not path.is_file()
            or path.stat().st_size != entry["size"]
            or sha256_file(path) != entry["sha256"]
        ):
            raise HarnessError(f"runner input hash mismatch: {relative}")
        listed.add(relative.as_posix())
    actual_entries = list(iter_manifest_files(stage_root))
    actual = {
        entry["path"]
        for entry in actual_entries
        if not allow_repo_changes or entry["category"] != "repo"
    }
    expected = {
        entry["path"]
        for entry in manifest["files"]
        if not allow_repo_changes or entry["category"] != "repo"
    }
    if expected != actual:
        raise HarnessError("runner manifest allowlist does not match staged inputs")
    skill_files = sorted((stage_root / "contract").rglob("SKILL.md"))
    if len(skill_files) != 1:
        raise HarnessError("runner must expose exactly one Deliver SKILL contract")
    if not re.search(
        r"^name:\s*deliver\s*$",
        skill_files[0].read_text(encoding="utf-8"),
        re.MULTILINE,
    ):
        raise HarnessError("runner-visible SKILL.md is not the Deliver contract")
    return manifest


def is_test_path(relative: Path) -> bool:
    return (
        (bool(relative.parts) and relative.parts[0] in {"test", "tests"})
        or relative.name.startswith("test_")
        or relative.name.endswith("_test.py")
    )


def repository_diffs(repo: Path, initial_commit: str) -> tuple[str, str]:
    tracked_output = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", "-z", initial_commit, "--"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    untracked_output = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    tracked = {Path(item.decode("utf-8")) for item in tracked_output.split(b"\0") if item}
    untracked = {Path(item.decode("utf-8")) for item in untracked_output.split(b"\0") if item}
    implementation: list[str] = []
    tests: list[str] = []
    for relative in sorted(tracked | untracked, key=lambda path: path.as_posix()):
        if relative.is_absolute() or ".." in relative.parts:
            raise HarnessError(f"repository change path escape rejected: {relative}")
        if relative in untracked:
            path = safe_path(repo, relative)
            if path.is_symlink() or not path.is_file():
                raise HarnessError(f"untracked non-file change rejected: {relative}")
            result = subprocess.run(
                ["git", "diff", "--binary", "--no-index", "--", "/dev/null", relative.as_posix()],
                cwd=repo,
                check=False,
                capture_output=True,
            )
            if result.returncode != 1:
                raise HarnessError(f"unable to freeze untracked change: {relative}")
            diff = result.stdout.decode("utf-8")
        else:
            diff = run(
                [
                    "git",
                    "diff",
                    "--binary",
                    "--no-renames",
                    initial_commit,
                    "--",
                    relative.as_posix(),
                ],
                cwd=repo,
            )
        (tests if is_test_path(relative) else implementation).append(diff)
    return "".join(implementation), "".join(tests)


def git_index_entry(repo: Path, relative: Path) -> tuple[str, str]:
    output = run(["git", "ls-files", "--stage", "--", relative.as_posix()], cwd=repo)
    lines = output.splitlines()
    if len(lines) != 1:
        raise HarnessError(f"pinned pre-packet source drift: {relative}")
    try:
        metadata, listed_path = lines[0].split("\t", 1)
        mode, blob, stage = metadata.split()
    except ValueError as exc:
        raise HarnessError(f"pinned pre-packet source drift: {relative}") from exc
    if listed_path != relative.as_posix() or stage != "0":
        raise HarnessError(f"pinned pre-packet source drift: {relative}")
    return mode, blob


def verify_pre_packet_source_invariants(
    stage_root: Path, manifest: dict[str, Any]
) -> None:
    if manifest["scenario_id"] != "preflight-remediation-holdout":
        return
    _, descriptor = scenario_descriptor(manifest["scenario_id"])
    fixture = descriptor.get("fixture")
    if not isinstance(fixture, dict) or fixture.get("kind") != "git_ref":
        raise HarnessError("historical holdout pinned source contract is invalid")
    blobs = fixture.get("blobs")
    paths = fixture.get("paths")
    if (
        not isinstance(blobs, dict)
        or not isinstance(paths, list)
        or any(not isinstance(path, str) for path in paths)
        or set(blobs) != set(paths)
    ):
        raise HarnessError("historical holdout pinned source contract is invalid")
    repo = safe_path(stage_root, "repo")
    initial_commit = manifest["initial_snapshot"]["commit"]
    git_environment = os.environ.copy()
    git_environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    git_dir = repo / ".git"
    if git_dir.is_symlink() or not git_dir.is_dir():
        raise HarnessError("unsupported Git history state: repository metadata")
    for metadata in (git_dir / "info/grafts", git_dir / "shallow"):
        reject_symlink_chain(git_dir, metadata.relative_to(git_dir))
        if metadata.exists() or metadata.is_symlink():
            raise HarnessError("unsupported Git history state: graft or shallow metadata")
    refs = run(
        ["git", "for-each-ref", "--format=%(refname) %(objectname)"],
        cwd=repo,
        env=git_environment,
    ).splitlines()
    if refs != [f"refs/heads/eval {initial_commit}"]:
        raise HarnessError("unsupported Git history state: unexpected refs")
    head_ref = subprocess.run(
        ["git", "symbolic-ref", "-q", "HEAD"],
        cwd=repo,
        env=git_environment,
        check=False,
        capture_output=True,
        text=True,
    )
    head = run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=repo,
        env=git_environment,
    ).strip()
    if head_ref.returncode != 0 or head_ref.stdout.strip() != "refs/heads/eval" or head != initial_commit:
        raise HarnessError("unsupported Git history state: HEAD changed")
    for raw_path in paths:
        if not isinstance(blobs.get(raw_path), dict):
            raise HarnessError("historical holdout pinned source contract is invalid")
        expected = blobs[raw_path]
        if set(expected) != {"blob", "mode"}:
            raise HarnessError("historical holdout pinned source contract is invalid")
        relative = Path(raw_path)
        try:
            path = safe_path(repo, relative)
        except HarnessError as exc:
            raise HarnessError(f"pinned pre-packet source drift: {relative}") from exc
        if not path.is_file():
            raise HarnessError(f"pinned pre-packet source drift: {relative}")
        head_listing = run(
            ["git", "ls-tree", "HEAD", "--", relative.as_posix()],
            cwd=repo,
            env=git_environment,
        ).strip()
        try:
            head_metadata, head_path = head_listing.split("\t", 1)
            head_mode, head_type, head_blob = head_metadata.split()
        except ValueError as exc:
            raise HarnessError(f"pinned pre-packet source drift: {relative}") from exc
        index_mode, index_blob = git_index_entry(repo, relative)
        content = path.read_bytes()
        worktree_blob = hashlib.sha1(
            f"blob {len(content)}\0".encode("ascii") + content
        ).hexdigest()
        worktree_mode = "100755" if stat.S_IMODE(path.stat().st_mode) & 0o111 else "100644"
        if (
            head_path != relative.as_posix()
            or head_type != "blob"
            or head_blob != expected["blob"]
            or head_mode != expected["mode"]
            or index_blob != expected["blob"]
            or index_mode != expected["mode"]
            or worktree_blob != expected["blob"]
            or worktree_mode != expected["mode"]
        ):
            raise HarnessError(f"pinned pre-packet source drift: {relative}")
    expected_objects = {
        line.split(" ", 1)[0]
        for line in run(
            ["git", "rev-list", "--objects", initial_commit],
            cwd=repo,
            env=git_environment,
        ).splitlines()
        if line
    }
    actual_objects = set(
        run(
            ["git", "cat-file", "--batch-check=%(objectname)", "--batch-all-objects"],
            cwd=repo,
            env=git_environment,
        ).splitlines()
    )
    if actual_objects != expected_objects:
        raise HarnessError("unsupported Git history state: unexpected objects")
    reflog_root = git_dir / "logs"
    required_reflogs = (reflog_root / "HEAD", reflog_root / "refs/heads/eval")
    if (
        reflog_root.is_symlink()
        or not reflog_root.is_dir()
        or any(path.is_symlink() or not path.is_file() for path in required_reflogs)
    ):
        raise HarnessError("unsupported Git history state: missing reflog")
    allowed_reflog_objects = {b"0" * 40, initial_commit.encode("ascii")}
    for reflog in sorted(reflog_root.rglob("*")):
        relative = reflog.relative_to(reflog_root)
        reject_symlink_chain(reflog_root, relative)
        if reflog.is_dir():
            continue
        if not reflog.is_file():
            raise HarnessError("unsupported Git history state: reflog entry")
        for line in reflog.read_bytes().splitlines():
            fields = line.split(b" ", 2)
            if len(fields) < 2 or not set(fields[:2]).issubset(allowed_reflog_objects):
                raise HarnessError("unsupported Git history state: reflog objects")


def freeze_pre_packet(stage_root: Path, validation: Path) -> Path:
    manifest = verify_manifest(stage_root, allow_repo_changes=True)
    if manifest["scenario_stage"] != "pre_packet":
        raise HarnessError("pre-packet freeze is only valid before review packet staging")
    if validation.is_symlink() or not validation.is_file():
        raise HarnessError("validation evidence must be a regular file")
    repo = safe_path(stage_root, "repo")
    phase_paths = runner_paths(stage_root, ("pre-packet",))
    validate_runner_bundles(
        phase_paths, phases=("pre-packet",), repo=repo, stage_root=stage_root
    )
    verify_pre_packet_source_invariants(stage_root, manifest)
    implementation_diff, test_diff = repository_diffs(repo, manifest["initial_snapshot"]["commit"])
    validation_copy = stage_root / "evidence/pre-packet-validation.log"
    validation_copy.parent.mkdir(parents=True, exist_ok=True)
    validation_copy.write_bytes(validation.read_bytes())
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": manifest["scenario_id"],
        "input_manifest_sha256": sha256_file(stage_root / "runner-manifest.json"),
        "initial_snapshot": manifest["initial_snapshot"],
        "head": run(["git", "rev-parse", "HEAD"], cwd=repo).strip(),
        "status": run(["git", "status", "--short"], cwd=repo),
        "implementation_diff_sha256": sha256_bytes(implementation_diff.encode()),
        "test_diff_sha256": sha256_bytes(test_diff.encode()),
        "validation": {
            "path": "evidence/pre-packet-validation.log",
            "sha256": sha256_file(validation_copy),
            "size": validation_copy.stat().st_size,
        },
        "runner_artifacts": {
            name: sha256_file(path) for name, path in phase_paths.items()
        },
        "runner_preflight_sha256": sha256_file(stage_root / "evidence/runner-preflight.json"),
    }
    output = stage_root / "evidence" / "pre-packet-snapshot.json"
    write_json(output, evidence)
    return output


def validate_snapshot_shape(data: object) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != SNAPSHOT_FIELDS:
        raise HarnessError("pre-packet snapshot fields are not exact")
    initial, validation, runner_artifacts = (
        data["initial_snapshot"], data["validation"], data["runner_artifacts"]
    )
    expected_runner = {
        name for name in runner_artifact_names() if name.startswith("pre_packet_")
    }
    if (
        data["schema_version"] != SCHEMA_VERSION
        or data["scenario_id"] not in OUTCOME_SCENARIOS
        or not is_digest(data["input_manifest_sha256"])
        or not is_digest(data["runner_preflight_sha256"])
        or not valid_initial_snapshot(initial)
        or not is_digest(data["head"], GIT_OBJECT_ID)
        or not isinstance(data["status"], str)
        or not all(is_digest(data[field]) for field in ("implementation_diff_sha256", "test_diff_sha256"))
        or not isinstance(validation, dict)
        or set(validation) != {"path", "sha256", "size"}
        or not isinstance(validation["path"], str)
        or not validation["path"]
        or not is_digest(validation["sha256"])
        or isinstance(validation["size"], bool)
        or not isinstance(validation["size"], int)
        or validation["size"] < 0
        or not exact_digest_map(runner_artifacts, expected_runner)
    ):
        raise HarnessError("pre-packet snapshot violates the exact schema")
    return data


def validate_pre_packet_snapshot(stage_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    snapshot = safe_path(stage_root, "evidence/pre-packet-snapshot.json")
    data = validate_snapshot_shape(json.loads(snapshot.read_text(encoding="utf-8")))
    expected_manifest = (
        sha256_file(stage_root / "runner-manifest.json")
        if manifest["scenario_stage"] == "pre_packet"
        else manifest["parent_manifest_sha256"]
    )
    if data["scenario_id"] != manifest["scenario_id"] or data["initial_snapshot"] != manifest["initial_snapshot"] or data["input_manifest_sha256"] != expected_manifest:
        raise HarnessError("pre-packet snapshot manifest binding is invalid")
    validation = data["validation"]
    preflight_path = safe_path(stage_root, "evidence/runner-preflight.json")
    validate_runner_preflight(preflight_path)
    if data["runner_preflight_sha256"] != sha256_file(preflight_path):
        raise HarnessError("pre-packet snapshot runner preflight binding is invalid")
    validation_path = safe_path(stage_root, validation["path"])
    if validation_path.stat().st_size != validation["size"] or sha256_file(validation_path) != validation["sha256"]:
        raise HarnessError("pre-packet validation artifact digest mismatch")
    phase_paths = runner_paths(stage_root, ("pre-packet",))
    validate_runner_bundles(phase_paths, phases=("pre-packet",), repo=stage_root / "repo", stage_root=stage_root)
    if data["runner_artifacts"] != {name: sha256_file(path) for name, path in phase_paths.items()}:
        raise HarnessError("pre-packet snapshot runner artifact binding is invalid")
    if manifest["scenario_stage"] == "pre_packet":
        repo = safe_path(stage_root, "repo")
        code_diff, test_diff = repository_diffs(repo, manifest["initial_snapshot"]["commit"])
        current = {
            "head": run(["git", "rev-parse", "HEAD"], cwd=repo).strip(),
            "status": run(["git", "status", "--short"], cwd=repo),
            "implementation_diff_sha256": sha256_bytes(code_diff.encode()),
            "test_diff_sha256": sha256_bytes(test_diff.encode()),
        }
        if any(data[key] != value for key, value in current.items()):
            raise HarnessError("pre-packet snapshot no longer matches repository state")
    return data


def stage_review_packet(stage_root: Path) -> None:
    manifest = verify_manifest(stage_root, allow_repo_changes=True)
    if manifest["scenario_stage"] != "pre_packet":
        raise HarnessError("review packet already staged")
    validate_pre_packet_snapshot(stage_root, manifest)
    parent_manifest_sha256 = sha256_file(stage_root / "runner-manifest.json")
    scenario_root, descriptor = scenario_descriptor(manifest["scenario_id"])
    destination = stage_root / "scenario"
    for relative_name in descriptor["review_packet_files"]:
        relative = Path(relative_name)
        source = safe_path(scenario_root, relative)
        target_relative = Path("review-packet") / relative.relative_to("review-packet")
        reject_evaluator_path(target_relative)
        target = safe_path(destination, target_relative, must_exist=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        target.chmod(stat.S_IMODE(source.stat().st_mode))
    write_manifest(
        stage_root,
        descriptor,
        manifest["fixture_source"],
        manifest["initial_snapshot"],
        "review_packet",
        parent_manifest_sha256=parent_manifest_sha256,
    )
    verify_manifest(stage_root)


def validate_measurements(value: object, label: str) -> dict[str, int]:
    if (
        not isinstance(value, dict)
        or set(value) != MEASUREMENT_FIELDS
        or any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in value.values())
        or value["wall_time_seconds"] < len(RUNNER_PHASES)
    ):
        raise HarnessError(f"{label} measurements violate deterministic integer bounds")
    return value


def validate_run_record(record: object, scenario_id: str) -> dict[str, Any]:
    if not isinstance(record, dict) or set(record) != {
        "scenario_id",
        "evidence",
        "measurements",
        "identity_clues",
    }:
        raise HarnessError("run record fields are not exact")
    if record["scenario_id"] != scenario_id:
        raise HarnessError("run record scenario does not match the frozen scenario")
    evidence = record["evidence"]
    if (
        not isinstance(evidence, dict)
        or set(evidence) != {
            "implementation_diff", "test_diff", "probe_results", "review_log",
            "review_rounds",
        }
        or not all(isinstance(value, str) and value for value in evidence.values())
    ):
        raise HarnessError("run record evidence paths are not exact strings")
    validate_measurements(record["measurements"], "run record")
    clues = record["identity_clues"]
    if not isinstance(clues, list) or any(
        not isinstance(clue, str) or not clue.strip() for clue in clues
    ):
        raise HarnessError("run record identity clues must be nonblank strings")
    return record


def expected_finding_ids(scenario_id: str) -> set[str]:
    ledger = json.loads(OUTCOME_LEDGER.read_text(encoding="utf-8"))
    return {
        entry["finding_id"]
        for entry in ledger["entries"]
        if entry["scenario"] == scenario_id
    }


def validate_evidence_records(
    scenario_id: str,
    probe_results: object,
    review_actions: object,
    review_rounds: object,
    evidence_digests: dict[str, str] | None = None,
) -> None:
    expected_ids = expected_finding_ids(scenario_id)
    specs = (
        ("probe results", probe_results, {"id", "command", "exit_status", "evidence", "evidence_ref", "evidence_sha256"}, "id"),
        ("review actions", review_actions, {"finding_id", "test_disposition", "rereview_scope", "command", "exit_status", "evidence", "evidence_ref", "evidence_sha256"}, "finding_id"),
        ("review rounds", review_rounds, {"round_id", "scope", "reviewed_finding_ids", "command", "exit_status", "evidence", "evidence_ref", "evidence_sha256"}, "round_id"),
    )
    for label, records, fields, id_field in specs:
        if not isinstance(records, list):
            raise HarnessError(f"{label} must be a JSON array")
        ids: list[str] = []
        for index, item in enumerate(records):
            if not isinstance(item, dict) or set(item) != fields:
                raise HarnessError(f"{label} item {index} fields are not exact")
            identifier, status = item[id_field], item["exit_status"]
            if not isinstance(identifier, str) or not identifier.strip():
                raise HarnessError(f"{label} item {index} has an invalid ID")
            if any(not isinstance(item[key], str) or not item[key].strip() for key in ("command", "evidence")):
                raise HarnessError(f"{label} item {index} has blank command or evidence")
            if isinstance(status, bool) or not isinstance(status, int) or not 0 <= status <= 255:
                raise HarnessError(f"{label} item {index} has an invalid exit_status")
            ref, digest = item["evidence_ref"], item["evidence_sha256"]
            if not isinstance(ref, str) or not ref.strip() or not isinstance(digest, str) or not HEX_DIGEST.fullmatch(digest):
                raise HarnessError(f"{label} item {index} has an invalid evidence reference")
            if evidence_digests is not None and evidence_digests.get(ref) != digest:
                raise HarnessError(f"{label} item {index} evidence digest is not frozen")
            ids.append(identifier)
        if len(ids) != len(set(ids)):
            raise HarnessError(f"{label} IDs must be unique")
        if label != "review rounds" and set(ids) != expected_ids:
            raise HarnessError(f"{label} must contain every scenario finding ID exactly once")
    for index, item in enumerate(review_actions):
        if item["test_disposition"] not in {"permanent", "table_case", "probe_only", "no_test"} or item["rereview_scope"] not in {"targeted", "full", None}:
            raise HarnessError(f"review action {index} has an invalid disposition or scope")
    if not review_rounds:
        raise HarnessError("review rounds must contain at least one round")
    for index, item in enumerate(review_rounds):
        reviewed = item["reviewed_finding_ids"]
        if (
            item["scope"] not in {"targeted", "full"}
            or not isinstance(reviewed, list)
            or not reviewed
            or any(not isinstance(finding_id, str) for finding_id in reviewed)
            or len(reviewed) != len(set(reviewed))
            or any(finding_id not in expected_ids for finding_id in reviewed)
        ):
            raise HarnessError(f"review round {index} has invalid scope or finding IDs")


def validate_runner_trace(trace_bytes: bytes) -> None:
    if not trace_bytes:
        raise HarnessError("runner trace must contain authoritative JSONL events")
    if not trace_bytes.endswith(b"\n"):
        raise HarnessError("runner trace must end with a newline")
    denied = (
        "/evaluator/",
        "\\evaluator\\",
        '"evaluator"',
        "outcome-ledger",
        "hidden_tests",
        "posthoc",
    )
    events: list[dict[str, Any]] = []
    for number, line in enumerate(trace_bytes.splitlines(), 1):
        try:
            event = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HarnessError(f"trace line {number} is not JSON") from exc
        if not is_structurally_valid_codex_event(event):
            raise HarnessError(f"trace line {number} is not a known Codex JSONL event")
        if event.get("event") == TERMINAL_SEAL_EVENT:
            raise HarnessError("runner trace contains a forged harness seal")
        events.append(event)
        serialized = json.dumps(event, sort_keys=True).lower()
        if any(token.lower() in serialized for token in denied):
            raise HarnessError(f"runner trace exposes evaluator material on line {number}")
    types = [event.get("type") for event in events]
    if types.count("thread.started") != 1 or types[0] != "thread.started":
        raise HarnessError("runner trace must start with exactly one thread.started event")
    if types.count("turn.completed") != 1 or types[-1] != "turn.completed":
        raise HarnessError("runner trace must end with exactly one successful turn.completed event")
    if any(event_type in {"turn.failed", "error"} for event_type in types):
        raise HarnessError("runner trace contains a failure terminal")
    command_events = [
        event for event in events
        if event.get("type") in {"item.started", "item.completed"}
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "command_execution"
    ]
    completed = [event for event in command_events if event["type"] == "item.completed"]
    if not command_events or not completed:
        raise HarnessError("runner trace is missing the mandatory first-tool gate")
    gate_event = completed[0]
    gate = gate_event["item"]
    started_command = command_events[0]["item"].get("command")
    before_gate = events[:events.index(gate_event) + 1]
    pre_gate_actions = [
        event for event in before_gate
        if event.get("type") in {"item.started", "item.completed"}
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") not in {"agent_message", "reasoning"}
        and not (
            event["item"].get("type") == "command_execution"
            and event["item"].get("id") == gate.get("id")
            and event["item"].get("command") == started_command
        )
    ]
    if (
        command_events[0]["type"] != "item.started"
        or started_command not in FIRST_TOOL_GATE_TRACE_COMMANDS
        or pre_gate_actions
        or any(event["item"].get("id") != gate.get("id") for event in command_events[:command_events.index(completed[0]) + 1])
        or gate.get("command") != started_command
        or gate.get("exit_code") != 0
        or gate.get("status") != "completed"
        or gate.get("aggregated_output") != FIRST_TOOL_GATE_OUTPUT
    ):
        raise HarnessError("runner trace failed the mandatory first-tool gate")


def runner_artifact_names() -> set[str]:
    return {
        f"{phase.replace('-', '_')}_{kind}"
        for phase in RUNNER_PHASES
        for kind in RUNNER_FILES
    }


def runner_paths(
    stage_root: Path, phases: tuple[str, ...] = RUNNER_PHASES, *,
    _comparison: dict[str, Any] | None = None,
    _state: dict[str, Any] | None = None,
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    comparison_manifest = comparison_for_stage(stage_root)
    arm_attempts: list[dict[str, Any]] | None = None
    runner_parent: Path | None = None
    if comparison_manifest is not None:
        comparison = _comparison or validate_comparison_manifest(comparison_manifest)
        state = _state or validate_attempt_state(
            comparison_manifest, _comparison=comparison
        )["state"]
        arm = state["arms"].get(stage_root.name)
        if not isinstance(arm, dict):
            raise HarnessError("runner stage is not a registered comparison arm")
        arm_attempts = arm["attempts"]
        runner_parent = safe_path(stage_root, "runner")
    for phase in phases:
        relative_root = Path("runner") / phase
        if arm_attempts is not None and runner_parent is not None:
            registered = {
                attempt["attempt"] for attempt in arm_attempts
                if phase in attempt["phase_inputs"]
            }
            observed: set[int] = set()
            for attempt_root in runner_parent.iterdir():
                phase_root = attempt_root / phase
                if not phase_root.exists() and not phase_root.is_symlink():
                    continue
                match = re.fullmatch(r"attempt-([0-9]+)", attempt_root.name)
                if (
                    match is None or attempt_root.is_symlink()
                    or not attempt_root.is_dir() or phase_root.is_symlink()
                    or not phase_root.is_dir()
                ):
                    raise HarnessError(f"invalid attempt-scoped {phase} runner directory")
                observed.add(int(match.group(1)))
            if observed - registered:
                raise HarnessError(f"unregistered attempt-scoped {phase} runner artifacts")
            if not registered or registered - observed:
                raise HarnessError(f"missing attempt-scoped {phase} runner artifacts")
            selected_attempt = max(registered)
            relative_root = Path("runner") / f"attempt-{selected_attempt}" / phase
        root, prefix = safe_path(stage_root, relative_root), phase.replace("-", "_")
        for kind, filename in RUNNER_FILES.items():
            path = safe_path(root, filename)
            if path.is_symlink() or not path.is_file():
                raise HarnessError(f"missing harness-produced {phase} runner {kind}")
            paths[f"{prefix}_{kind}"] = path
    return paths


def validate_runner_bundles(
    paths: dict[str, Path],
    *,
    phases: tuple[str, ...] = RUNNER_PHASES,
    freeze: dict[str, Any] | None = None,
    repo: Path | None = None,
    stage_root: Path | None = None,
    preflight: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    bundles: dict[str, dict[str, Any]] = {}
    metadata_fields = {
        "schema_version", "phase", "command", "model", "reasoning",
        "execution_boundary", "environment", "prompt_sha256", "input_manifest_sha256",
        "initial_snapshot",
        "exit_code", "trace_sha256", "stderr_sha256", "profile_sha256", "duration_milliseconds",
        "runner_preflight_sha256", "runner_binary_path", "runner_binary_version",
        "runner_binary_sha256", "timeout_policy", "arm_elapsed_before_milliseconds",
    }
    digest_fields = {"prompt": "prompt_sha256", "trace": "trace_sha256", "stderr": "stderr_sha256", "manifest": "input_manifest_sha256", "profile": "profile_sha256"}
    if preflight is None:
        if stage_root is None:
            raise HarnessError("runner bundle validation requires a preflight artifact")
        preflight_path = safe_path(stage_root, "evidence/runner-preflight.json")
        preflight = validate_runner_preflight(preflight_path)
    else:
        preflight_path = None
    identity = (preflight["binary_path"], preflight["binary_version"], preflight["binary_sha256"])
    if "comparison_binding" in preflight:
        metadata_fields.update({"comparison_binding", "arm_attempt"})
    elapsed_milliseconds = 0
    for phase in phases:
        prefix = phase.replace("-", "_")
        metadata = json.loads(paths[f"{prefix}_metadata"].read_text(encoding="utf-8"))
        if not isinstance(metadata, dict) or set(metadata) != metadata_fields:
            raise HarnessError(f"{phase} runner metadata fields are not exact")
        command = metadata["command"]
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise HarnessError(f"{phase} runner command metadata is invalid")
        try:
            command_repo = Path(command[command.index("--cd") + 1])
            command_profile = Path(command[command.index("-f") + 1])
        except (AttributeError, ValueError, IndexError) as exc:
            raise HarnessError(f"{phase} runner command metadata is invalid") from exc
        expected_repo = repo or command_repo
        expected_profile = paths[f"{prefix}_profile"] if repo is not None else command_profile
        fixed = (SCHEMA_VERSION, phase, "gpt-5.6-sol", "xhigh", "outer_sandbox_only", 0)
        actual = tuple(metadata[key] for key in (
            "schema_version", "phase", "model", "reasoning", "execution_boundary",
            "exit_code",
        ))
        actual_identity = tuple(
            metadata[key] for key in
            ("runner_binary_path", "runner_binary_version", "runner_binary_sha256")
        )
        expected_preflight = (
            sha256_file(preflight_path) if preflight_path is not None
            else sha256_bytes(canonical_json(preflight))
        )
        sentinel_entries = [
            item.split("=", 1)[1] for item in metadata["environment"]
            if isinstance(item, str) and item.startswith(f"{EXTERNAL_SENTINEL_ENV}=")
        ] if isinstance(metadata["environment"], list) else []
        if len(sentinel_entries) != 1:
            raise HarnessError(f"{phase} runner sentinel environment is invalid")
        external_sentinel = Path(sentinel_entries[0])
        if (
            command != codex_command(expected_repo, expected_profile, external_sentinel)
            or metadata["environment"] != runner_environment(
                expected_profile, external_sentinel
            )
            or actual != fixed
            or actual_identity != identity
            or metadata["runner_preflight_sha256"] != expected_preflight
            or metadata["timeout_policy"] != ARM_TIMEOUT_POLICY
            or metadata["arm_elapsed_before_milliseconds"] != elapsed_milliseconds
            or metadata.get("comparison_binding") != preflight.get("comparison_binding")
        ):
            raise HarnessError(f"{phase} runner metadata violates fixed conditions")
        if "comparison_binding" in preflight:
            attempt_parent = command_profile.parent.parent.name
            if (
                not re.fullmatch(r"attempt-[12]", attempt_parent)
                or metadata["arm_attempt"] != int(attempt_parent.rsplit("-", 1)[1])
            ):
                raise HarnessError(f"{phase} runner attempt binding is invalid")
        duration = metadata["duration_milliseconds"]
        if (
            isinstance(duration, bool)
            or not isinstance(duration, int)
            or duration < 1
            or elapsed_milliseconds + duration
            > ARM_TIMEOUT_POLICY["arm_total_seconds"] * 1000
        ):
            raise HarnessError(f"{phase} runner duration is invalid")
        for kind, field in digest_fields.items():
            if metadata[field] != sha256_file(paths[f"{prefix}_{kind}"]):
                raise HarnessError(f"{phase} runner {kind} digest mismatch")
        if paths[f"{prefix}_profile"].read_text(encoding="utf-8") != sandbox_profile(expected_repo.parent):
            raise HarnessError(f"{phase} runner sandbox profile is not stage-bound")
        validate_runner_trace(paths[f"{prefix}_trace"].read_bytes())
        manifest = json.loads(paths[f"{prefix}_manifest"].read_text(encoding="utf-8"))
        if (
            stage_root is not None
            and paths[f"{prefix}_prompt"].read_text(encoding="utf-8")
            != FIRST_TOOL_GATE_PROMPT + prompt_from_manifest(stage_root, manifest)
        ):
            raise HarnessError(f"{phase} runner prompt is not the allowlisted manifest prompt")
        bundles[phase] = {"metadata": metadata, "manifest": manifest}
        elapsed_milliseconds += duration
    if phases != RUNNER_PHASES:
        return bundles
    pre = bundles["pre-packet"]
    remediation = bundles["remediation"]
    pre_manifest = pre["manifest"]
    remediation_manifest = remediation["manifest"]
    if (
        pre_manifest.get("scenario_stage") != "pre_packet"
        or remediation_manifest.get("scenario_stage") != "review_packet"
    ):
        raise HarnessError("runner phase manifests have invalid stage identities")
    pre_digest = sha256_file(paths["pre_packet_manifest"])
    remediation_digest = sha256_file(paths["remediation_manifest"])
    if remediation_manifest.get("parent_manifest_sha256") != pre_digest:
        raise HarnessError("pre-packet runner manifest is not the review manifest parent")
    if pre["metadata"]["input_manifest_sha256"] != pre_digest:
        raise HarnessError("pre-packet runner metadata manifest lineage mismatch")
    if remediation["metadata"]["input_manifest_sha256"] != remediation_digest:
        raise HarnessError("remediation runner metadata manifest lineage mismatch")
    initial = remediation_manifest.get("initial_snapshot")
    if (
        pre_manifest.get("initial_snapshot") != initial
        or any(bundle["metadata"]["initial_snapshot"] != initial for bundle in bundles.values())
    ):
        raise HarnessError("runner phases do not share the prepared initial snapshot")
    if pre_manifest.get("scenario_id") != remediation_manifest.get("scenario_id"):
        raise HarnessError("runner phases do not share a scenario")
    if freeze is not None and (
        freeze["input_manifest_sha256"] != remediation_digest
        or freeze["initial_snapshot"] != initial
        or freeze["scenario_id"] != remediation_manifest.get("scenario_id")
    ):
        raise HarnessError("output freeze is not bound to runner manifest lineage")
    return bundles


def derived_measurements(
    test_diff: str,
    review_actions: list[dict[str, Any]],
    review_rounds: list[dict[str, Any]],
    bundles: dict[str, dict[str, Any]],
) -> dict[str, int]:
    added_lines = [
        line[1:]
        for line in test_diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    test_count = sum(
        1
        for line in added_lines
        if re.match(r"\s*(?:async\s+)?def\s+test_", line)
    )
    if not added_lines and any(
        item["test_disposition"] in {"permanent", "table_case"}
        for item in review_actions
    ):
        raise HarnessError("durable test dispositions require a nonempty frozen test diff")
    return {
        "test_count": test_count,
        "test_size_lines": len(added_lines),
        "full_review_rounds": sum(item["scope"] == "full" for item in review_rounds),
        "targeted_rereviews": sum(item["scope"] == "targeted" for item in review_rounds),
        "wall_time_seconds": sum(
            max(1, math.ceil(bundle["metadata"]["duration_milliseconds"] / 1000))
            for bundle in bundles.values()
        ),
    }


def validate_terminal_seal(
    output_freeze: Path, freeze: dict[str, Any], paths: dict[str, Path]
) -> dict[str, dict[str, Any]]:
    seal_path = output_freeze.parent / "terminal-seal.json"
    if seal_path.is_symlink() or not seal_path.is_file():
        raise HarnessError("evaluator terminal seal is missing")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal_fields = {"schema_version", "event", "output_freeze_sha256", "phase_bindings"}
    if "comparison_binding" in freeze:
        seal_fields.add("comparison_binding")
    if not isinstance(seal, dict) or set(seal) != seal_fields:
        raise HarnessError("evaluator terminal seal fields are not exact")
    if (
        seal["schema_version"] != SCHEMA_VERSION
        or seal["event"] != TERMINAL_SEAL_EVENT
        or seal["output_freeze_sha256"] != sha256_file(output_freeze)
        or seal.get("comparison_binding") != freeze.get("comparison_binding")
    ):
        raise HarnessError("evaluator terminal seal does not bind the output freeze")
    expected_bindings = {
        phase: {
            kind: freeze["artifacts"][f"{phase.replace('-', '_')}_{kind}"]["sha256"]
            for kind in RUNNER_FILES
        }
        for phase in RUNNER_PHASES
    }
    if seal["phase_bindings"] != expected_bindings:
        raise HarnessError("evaluator terminal seal does not bind both runner phases")
    preflight = validate_runner_preflight(paths["runner_preflight"], check_binary=False)
    return validate_runner_bundles(paths, freeze=freeze, preflight=preflight)


def post_snapshot_digest(
    initial: dict[str, str], implementation: str, tests: str, status: str
) -> str:
    return sha256_bytes(canonical_json({
        "initial_snapshot": initial, "implementation_diff": implementation,
        "test_diff": tests, "status": status,
    }))


def finalize_arm(stage_root: Path, record: Path) -> Path:
    stage_root = require_stage_root(stage_root)
    comparison_manifest = comparison_for_stage(stage_root)
    comparison = (
        validate_comparison_manifest(comparison_manifest)
        if comparison_manifest is not None else None
    )
    binding = binding_from_comparison(comparison) if comparison is not None else None
    comparison_state: dict[str, Any] | None = None
    if comparison_manifest is not None:
        comparison_state = validate_attempt_state(
            comparison_manifest, _comparison=comparison
        )["state"]
        arm_state = comparison_state["arms"][stage_root.name]
        if arm_state["status"] != "running" or arm_state["terminal_seal_sha256"] is not None:
            raise HarnessError("arm finalization requires one active unsealed attempt")
        verify_external_sentinel(comparison["external_sentinel"], stage_root.parent)
    manifest = verify_manifest(stage_root, allow_repo_changes=True)
    if manifest["scenario_stage"] != "review_packet":
        raise HarnessError("arm finalization requires the staged review packet")
    if record.is_symlink() or not record.is_file():
        raise HarnessError("run record must be a regular evaluator input")
    current_manifest = stage_root / "runner-manifest.json"
    repo = safe_path(stage_root, "repo")
    snapshot_data = validate_pre_packet_snapshot(stage_root, manifest)
    runner_sources = runner_paths(
        stage_root, _comparison=comparison, _state=comparison_state
    )
    bundles = validate_runner_bundles(runner_sources, repo=repo, stage_root=stage_root)
    if sha256_file(current_manifest) != sha256_file(runner_sources["remediation_manifest"]):
        raise HarnessError("remediation runner did not use the current review manifest")
    code_diff, test_diff = repository_diffs(repo, manifest["initial_snapshot"]["commit"])
    record_data = validate_run_record(json.loads(record.read_text(encoding="utf-8")), manifest["scenario_id"])
    source_artifacts = {
        name: evidence_path(record.parent, relative)
        for name, relative in record_data["evidence"].items()
    }
    if source_artifacts["implementation_diff"].read_bytes() != code_diff.encode():
        raise HarnessError("run record implementation diff omits committed, working-tree, or untracked changes")
    if source_artifacts["test_diff"].read_bytes() != test_diff.encode():
        raise HarnessError("run record test diff omits committed, working-tree, or untracked changes")
    probe_results = json.loads(source_artifacts["probe_results"].read_text(encoding="utf-8"))
    review_actions = json.loads(source_artifacts["review_log"].read_text(encoding="utf-8"))
    review_rounds = json.loads(source_artifacts["review_rounds"].read_text(encoding="utf-8"))
    evidence_digests = {
        "implementation_diff": sha256_bytes(code_diff.encode()),
        "test_diff": sha256_bytes(test_diff.encode()),
        **{name: sha256_file(path) for name, path in runner_sources.items()},
    }
    validate_evidence_records(
        manifest["scenario_id"], probe_results, review_actions, review_rounds,
        evidence_digests,
    )
    expected_measurements = derived_measurements(
        test_diff, review_actions, review_rounds, bundles
    )
    if record_data["measurements"] != expected_measurements:
        raise HarnessError("run record measurements do not match frozen deterministic evidence")

    evaluator_root = stage_root / "evaluator"
    frozen_root = evaluator_root / "frozen"
    if evaluator_root.exists():
        raise HarnessError("evaluator arm has already been finalized")
    frozen_root.mkdir(parents=True)
    frozen_data = {
        "implementation_diff": code_diff.encode(),
        "test_diff": test_diff.encode(),
        "probe_results": source_artifacts["probe_results"].read_bytes(),
        "review_log": source_artifacts["review_log"].read_bytes(),
        "review_rounds": source_artifacts["review_rounds"].read_bytes(),
        "run_record": record.read_bytes(),
        "pre_packet_snapshot": canonical_json(snapshot_data),
        "pre_packet_validation": safe_path(
            stage_root, snapshot_data["validation"]["path"]
        ).read_bytes(),
        "runner_preflight": safe_path(
            stage_root, "evidence/runner-preflight.json"
        ).read_bytes(),
        **{name: path.read_bytes() for name, path in runner_sources.items()},
    }
    filenames = {
        "implementation_diff": "implementation.diff",
        "test_diff": "tests.diff",
        "probe_results": "probe-results.json",
        "review_log": "review-log.json",
        "review_rounds": "review-rounds.json",
        "run_record": "run-record.json",
        "pre_packet_snapshot": "pre-packet-snapshot.json",
        "pre_packet_validation": "pre-packet-validation.log",
        "runner_preflight": "runner-preflight.json",
        **{
            f"{phase.replace('-', '_')}_{kind}": f"{phase.replace('-', '_')}-{filename}"
            for phase in RUNNER_PHASES
            for kind, filename in RUNNER_FILES.items()
        },
    }
    artifacts: dict[str, dict[str, object]] = {}
    for name, data in frozen_data.items():
        target = frozen_root / filenames[name]
        target.write_bytes(data)
        artifacts[name] = {"path": target.relative_to(evaluator_root).as_posix(), "sha256": sha256_bytes(data), "size": len(data)}
    pre_packet = safe_path(stage_root, "evidence/pre-packet-snapshot.json")
    status = run(["git", "status", "--short", "--untracked-files=all"], cwd=repo)
    snapshots = {
        "pre_packet": sha256_file(pre_packet),
        "post_remediation": post_snapshot_digest(
            manifest["initial_snapshot"], artifacts["implementation_diff"]["sha256"],
            artifacts["test_diff"]["sha256"], status,
        ),
    }
    output = evaluator_root / "output-freeze.json"
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": manifest["scenario_id"],
        "input_manifest_sha256": sha256_file(current_manifest),
        "initial_snapshot": manifest["initial_snapshot"],
        "snapshots": snapshots,
        "repository_state": {"head": run(["git", "rev-parse", "HEAD"], cwd=repo).strip(), "status": status},
        "artifacts": artifacts,
    }
    if binding is not None:
        evidence["comparison_binding"] = binding
    write_json(output, evidence)
    seal = {
        "schema_version": SCHEMA_VERSION,
        "event": TERMINAL_SEAL_EVENT,
        "output_freeze_sha256": sha256_file(output),
        "phase_bindings": {
            phase: {
                kind: artifacts[f"{phase.replace('-', '_')}_{kind}"]["sha256"]
                for kind in RUNNER_FILES
            }
            for phase in RUNNER_PHASES
        },
    }
    if binding is not None:
        seal["comparison_binding"] = binding
    seal_path = evaluator_root / "terminal-seal.json"
    write_json(seal_path, seal)
    if comparison_manifest is not None:
        register_terminal_seal(
            comparison_manifest, stage_root.name, sha256_file(seal_path),
            _comparison=comparison,
        )
        verify_external_sentinel(comparison["external_sentinel"], stage_root.parent)
    return output


def denylist() -> list[str]:
    return [
        line.strip().lower()
        for line in IDENTITY_DENYLIST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def normalize_text(text: str, clues: Iterable[str]) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"(?<![\w.])/(?:[^\s:'\"]+/)+[^\s:'\"]*", "[path]", normalized)
    normalized = re.sub(r"\b[0-9a-f]{7,40}\b", "[commit]", normalized, flags=re.IGNORECASE)
    for clue in sorted({*denylist(), *(item.lower() for item in clues)}, key=len, reverse=True):
        normalized = re.sub(re.escape(clue), "[identity]", normalized, flags=re.IGNORECASE)
    return "\n".join(line.rstrip() for line in normalized.split("\n")).strip() + "\n"


def redact_recursive(value: object, clues: Iterable[str]) -> object:
    if isinstance(value, str):
        return normalize_text(value, clues).rstrip("\n")
    if isinstance(value, list):
        return [redact_recursive(item, clues) for item in value]
    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        for key, item in value.items():
            redacted_key = normalize_text(str(key), clues).rstrip("\n")
            if redacted_key in redacted:
                raise HarnessError("redaction collapsed distinct blinded object keys")
            redacted[redacted_key] = redact_recursive(item, clues)
        return redacted
    if isinstance(value, float) and not math.isfinite(value):
        raise HarnessError("non-finite numbers are not valid blinded JSON")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise HarnessError(f"unsupported blinded value type: {type(value).__name__}")


def assert_identity_blind(value: object, clues: Iterable[str] = ()) -> None:
    text = json.dumps(value, sort_keys=True).lower()
    leaked = [
        token
        for token in {*denylist(), *(clue.lower() for clue in clues)}
        if token and token in text
    ]
    if leaked:
        raise HarnessError(f"identity clue leaked into blind packet: {', '.join(leaked)}")


def evidence_path(record_root: Path, relative: str) -> Path:
    path = safe_path(record_root, relative)
    reject_evaluator_path(path.relative_to(record_root))
    if not path.is_file():
        raise HarnessError(f"missing run evidence: {relative}")
    return path


def frozen_artifacts(output_freeze: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    if output_freeze.is_symlink() or not output_freeze.is_file():
        raise HarnessError("output freeze must be a regular evaluator file")
    freeze = json.loads(output_freeze.read_text(encoding="utf-8"))
    expected_fields = {
        "schema_version",
        "scenario_id",
        "input_manifest_sha256",
        "initial_snapshot",
        "snapshots",
        "repository_state",
        "artifacts",
    }
    if isinstance(freeze, dict) and "comparison_binding" in freeze:
        expected_fields.add("comparison_binding")
    if not isinstance(freeze, dict) or set(freeze) != expected_fields:
        raise HarnessError("output freeze fields are not exact")
    if freeze["schema_version"] != SCHEMA_VERSION:
        raise HarnessError("output freeze schema version is invalid")
    if "comparison_binding" in freeze:
        binding = freeze["comparison_binding"]
        if (
            not isinstance(binding, dict)
            or set(binding) != {"comparison_manifest_sha256", "evaluator_identity"}
            or not is_digest(binding.get("comparison_manifest_sha256"))
        ):
            raise HarnessError("output freeze comparison binding is invalid")
        validate_evaluator_identity(binding["evaluator_identity"], recompute=False)
    if freeze["scenario_id"] not in {"retry-failed", "preflight-remediation-holdout"}:
        raise HarnessError("output freeze scenario is invalid")
    if (
        not isinstance(freeze["input_manifest_sha256"], str)
        or not HEX_DIGEST.fullmatch(freeze["input_manifest_sha256"])
    ):
        raise HarnessError("output freeze manifest digest is invalid")
    initial = freeze["initial_snapshot"]
    if not valid_initial_snapshot(initial):
        raise HarnessError("output freeze initial snapshot is invalid")
    repository_state = freeze["repository_state"]
    if (
        not isinstance(repository_state, dict)
        or set(repository_state) != {"head", "status"}
        or not isinstance(repository_state["head"], str)
        or not GIT_OBJECT_ID.fullmatch(repository_state["head"])
        or not isinstance(repository_state["status"], str)
    ):
        raise HarnessError("output freeze repository state is invalid")
    snapshots = freeze["snapshots"]
    if (
        not isinstance(snapshots, dict)
        or set(snapshots) != {"pre_packet", "post_remediation"}
        or any(not isinstance(value, str) or not HEX_DIGEST.fullmatch(value) for value in snapshots.values())
    ):
        raise HarnessError("evaluator snapshots must be 64-hex digests")
    required_artifacts = {
        "implementation_diff",
        "test_diff",
        "probe_results",
        "review_log",
        "review_rounds",
        "run_record",
        "pre_packet_snapshot",
        "pre_packet_validation",
        "runner_preflight",
    } | runner_artifact_names()
    artifacts = freeze["artifacts"]
    if not isinstance(artifacts, dict) or set(artifacts) != required_artifacts:
        raise HarnessError("output freeze artifacts are not exact")
    paths: dict[str, Path] = {}
    relative_paths: set[str] = set()
    for name, artifact in artifacts.items():
        if (
            not isinstance(artifact, dict)
            or set(artifact) != {"path", "sha256", "size"}
            or not isinstance(artifact["path"], str)
            or not isinstance(artifact["sha256"], str)
            or not HEX_DIGEST.fullmatch(artifact["sha256"])
            or isinstance(artifact["size"], bool)
            or not isinstance(artifact["size"], int)
            or artifact["size"] < 0
        ):
            raise HarnessError(f"frozen artifact metadata is invalid: {name}")
        relative = Path(artifact["path"])
        if not relative.parts or relative.parts[0] != "frozen":
            raise HarnessError(f"frozen artifact path is not evaluator-owned: {name}")
        if artifact["path"] in relative_paths:
            raise HarnessError("frozen artifact paths must be unique")
        relative_paths.add(artifact["path"])
        path = safe_path(output_freeze.parent, artifact["path"])
        if not path.is_file() or path.stat().st_size != artifact["size"] or sha256_file(path) != artifact["sha256"]:
            raise HarnessError(f"frozen artifact digest mismatch: {name}")
        paths[name] = path
    return freeze, paths


def validate_normalized_output(
    output: object, *, require_arm_binding: bool = False
) -> dict[str, Any]:
    expected_fields = {
        "schema_version",
        "scenario_id",
        "snapshots",
        "behavior",
        "measurements",
        "source_hashes",
    }
    if isinstance(output, dict) and "comparison_binding" in output:
        expected_fields.update({"comparison_binding", "upstream_sha256s", "arm_binding"})
    if not isinstance(output, dict) or set(output) != expected_fields:
        raise HarnessError("normalized behavior fields are not exact")
    if output["schema_version"] != SCHEMA_VERSION or output["scenario_id"] not in {
        "retry-failed",
        "preflight-remediation-holdout",
    }:
        raise HarnessError("normalized behavior identity fields are invalid")
    snapshots = output["snapshots"]
    if (
        not isinstance(snapshots, dict)
        or set(snapshots) != {"pre_packet", "post_remediation"}
        or any(not isinstance(value, str) or not HEX_DIGEST.fullmatch(value) for value in snapshots.values())
    ):
        raise HarnessError("normalized snapshots must be evaluator-generated 64-hex digests")
    validate_measurements(output["measurements"], "normalized")
    if "comparison_binding" in output:
        binding = output["comparison_binding"]
        if (
            not isinstance(binding, dict)
            or set(binding) != {"comparison_manifest_sha256", "evaluator_identity"}
            or not is_digest(binding.get("comparison_manifest_sha256"))
            or not exact_digest_map(
                output["upstream_sha256s"], {"output_freeze", "terminal_seal"}
            )
        ):
            raise HarnessError("normalized comparison or upstream binding is invalid")
        validate_evaluator_identity(binding["evaluator_identity"], recompute=False)
        arm_binding = output["arm_binding"]
        if (
            not isinstance(arm_binding, dict)
            or set(arm_binding) != {"arm_name", "terminal_seal_sha256"}
            or arm_binding.get("arm_name") not in OFFICIAL_ARM_ORDER
            or not is_digest(arm_binding.get("terminal_seal_sha256"))
        ):
            raise HarnessError("normalized arm binding is invalid")
    elif require_arm_binding:
        raise HarnessError("official normalized output requires an arm binding")
    behavior = output["behavior"]
    if not isinstance(behavior, dict) or set(behavior) != {
        "implementation_diff",
        "test_diff",
        "implementation_additions",
        "implementation_deletions",
        "test_additions",
        "probe_results",
        "review_actions",
        "review_rounds",
    }:
        raise HarnessError("normalized behavior payload is not exact")
    if (
        not isinstance(behavior["implementation_diff"], str)
        or not isinstance(behavior["test_diff"], str)
        or not isinstance(behavior["probe_results"], list)
        or not isinstance(behavior["review_actions"], list)
        or not isinstance(behavior["review_rounds"], list)
        or any(
            isinstance(behavior[field], bool)
            or not isinstance(behavior[field], int)
            or behavior[field] < 0
            for field in ("implementation_additions", "implementation_deletions", "test_additions")
        )
    ):
        raise HarnessError("normalized behavior values violate the checked-in schema")
    hashes = output["source_hashes"]
    required_hashes = {
        "implementation_diff",
        "test_diff",
        "probe_results",
        "review_log",
        "review_rounds",
        "run_record",
        "pre_packet_snapshot",
        "pre_packet_validation",
        "runner_preflight",
    } | runner_artifact_names()
    if (
        not exact_digest_map(hashes, required_hashes)
    ):
        raise HarnessError("normalized source hashes violate the checked-in schema")
    validate_evidence_records(
        output["scenario_id"], behavior["probe_results"], behavior["review_actions"],
        behavior["review_rounds"], hashes,
    )
    return output


def normalize_run(
    output_freeze: Path, comparison_manifest: Path | None = None,
    *, _comparison: dict[str, Any] | None = None,
    _state: dict[str, Any] | None = None,
) -> dict[str, object]:
    freeze, paths = frozen_artifacts(output_freeze)
    if comparison_manifest is not None:
        comparison = _comparison or validate_comparison_manifest(comparison_manifest)
        binding = binding_from_comparison(comparison)
        if freeze.get("comparison_binding") != binding:
            raise HarnessError("output freeze belongs to another comparison")
        state = _state or validate_attempt_state(
            comparison_manifest, _comparison=comparison
        )["state"]
        arm_name = output_freeze.parents[1].name
        if (
            arm_name not in state["arms"]
            or state["arms"][arm_name]["status"] != "sealed"
            or state["arms"][arm_name]["terminal_seal_sha256"]
            != sha256_file(output_freeze.parent / "terminal-seal.json")
        ):
            raise HarnessError("normalization arm seal is not registered by the comparison")
    bundles = validate_terminal_seal(output_freeze, freeze, paths)
    expected_post = post_snapshot_digest(
        freeze["initial_snapshot"], freeze["artifacts"]["implementation_diff"]["sha256"],
        freeze["artifacts"]["test_diff"]["sha256"], freeze["repository_state"]["status"],
    )
    if freeze["snapshots"] != {
        "pre_packet": freeze["artifacts"]["pre_packet_snapshot"]["sha256"],
        "post_remediation": expected_post,
    }:
        raise HarnessError("output freeze snapshot digests are not bound to frozen evidence")
    snapshot = validate_snapshot_shape(
        json.loads(paths["pre_packet_snapshot"].read_text(encoding="utf-8"))
    )
    validation = snapshot["validation"]
    expected_runner = {
        name: freeze["artifacts"][name]["sha256"]
        for name in runner_artifact_names()
        if name.startswith("pre_packet_")
    }
    if (
        snapshot["scenario_id"] != freeze["scenario_id"]
        or snapshot.get("initial_snapshot") != freeze["initial_snapshot"]
        or snapshot.get("input_manifest_sha256")
        != freeze["artifacts"]["pre_packet_manifest"]["sha256"]
        or snapshot.get("runner_artifacts") != expected_runner
        or snapshot.get("runner_preflight_sha256")
        != freeze["artifacts"]["runner_preflight"]["sha256"]
        or validation.get("sha256")
        != freeze["artifacts"]["pre_packet_validation"]["sha256"]
        or validation.get("size") != paths["pre_packet_validation"].stat().st_size
    ):
        raise HarnessError("frozen pre-packet snapshot binding is invalid")
    record = validate_run_record(
        json.loads(paths["run_record"].read_text(encoding="utf-8")),
        freeze["scenario_id"],
    )
    clues = record["identity_clues"]
    implementation = normalize_text(
        paths["implementation_diff"].read_text(encoding="utf-8"), clues
    )
    tests = normalize_text(paths["test_diff"].read_text(encoding="utf-8"), clues)
    raw_probes = json.loads(paths["probe_results"].read_text(encoding="utf-8"))
    raw_reviews = json.loads(paths["review_log"].read_text(encoding="utf-8"))
    raw_rounds = json.loads(paths["review_rounds"].read_text(encoding="utf-8"))
    validate_evidence_records(
        freeze["scenario_id"], raw_probes, raw_reviews, raw_rounds,
        {name: artifact["sha256"] for name, artifact in freeze["artifacts"].items()},
    )
    expected_measurements = derived_measurements(
        paths["test_diff"].read_text(encoding="utf-8"), raw_reviews, raw_rounds,
        bundles,
    )
    if record["measurements"] != expected_measurements:
        raise HarnessError("frozen measurements do not match deterministic evidence")
    probe_data = redact_recursive(raw_probes, clues)
    review_data = redact_recursive(raw_reviews, clues)
    round_data = redact_recursive(raw_rounds, clues)
    output: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": record["scenario_id"],
        "snapshots": freeze["snapshots"],
        "behavior": {
            "implementation_diff": implementation,
            "test_diff": tests,
            "implementation_additions": sum(
                1 for line in implementation.splitlines() if line.startswith("+") and not line.startswith("+++")
            ),
            "implementation_deletions": sum(
                1 for line in implementation.splitlines() if line.startswith("-") and not line.startswith("---")
            ),
            "test_additions": sum(
                1 for line in tests.splitlines() if line.startswith("+") and not line.startswith("+++")
            ),
            "probe_results": probe_data,
            "review_actions": review_data,
            "review_rounds": round_data,
        },
        "measurements": expected_measurements,
        "source_hashes": {
            name: freeze["artifacts"][name]["sha256"]
            for name in freeze["artifacts"]
        },
    }
    if "comparison_binding" in freeze:
        arm_name = output_freeze.parents[1].name
        terminal_seal_sha256 = sha256_file(output_freeze.parent / "terminal-seal.json")
        output["comparison_binding"] = freeze["comparison_binding"]
        output["arm_binding"] = {
            "arm_name": arm_name,
            "terminal_seal_sha256": terminal_seal_sha256,
        }
        output["upstream_sha256s"] = {
            "output_freeze": sha256_file(output_freeze),
            "terminal_seal": terminal_seal_sha256,
        }
    validate_normalized_output(output)
    assert_identity_blind(
        public_normalized(output) if "comparison_binding" in output else output,
        clues,
    )
    return output


def build_blind_packet(
    run_paths: list[Path], comparison_manifest: Path | None = None
) -> dict[str, object]:
    expected_count = 4 if comparison_manifest is not None else 2
    if len(run_paths) != expected_count:
        raise HarnessError(f"the blinded comparison requires exactly {expected_count} runs")
    packet: dict[str, object]
    if comparison_manifest is None:
        runs = [
            validate_normalized_output(json.loads(path.read_text(encoding="utf-8")))
            for path in run_paths
        ]
        ordered: list[object] = sorted(
            runs, key=lambda value: sha256_bytes(canonical_json(value))
        )
        packet = {
            "schema_version": SCHEMA_VERSION,
            "runs": {f"Run {chr(65 + index)}": value for index, value in enumerate(ordered)},
        }
    else:
        comparison = validate_comparison_manifest(comparison_manifest)
        binding = binding_from_comparison(comparison)
        state = validate_attempt_state(
            comparison_manifest, require_all_sealed=True,
            _comparison=comparison,
        )["state"]
        by_arm: dict[str, dict[str, Any]] = {}
        path_by_arm: dict[str, Path] = {}
        for path in run_paths:
            document = validate_official_normalized(
                path, comparison_manifest, _comparison=comparison, _state=state
            )
            arm_name = document["arm_binding"]["arm_name"]
            if arm_name in by_arm:
                raise HarnessError("blind packet received a duplicate normalized arm")
            by_arm[arm_name] = document
            path_by_arm[arm_name] = path
        if set(by_arm) != set(OFFICIAL_ARM_ORDER):
            raise HarnessError("blind packet does not contain the exact four frozen arms")
        workflows_by_identity = {
            variant: {
                "scenarios": {
                    scenario: public_normalized(
                        by_arm[f"{scenario}-{variant}"]
                    )
                    for scenario in OUTCOME_SCENARIOS
                }
            }
            for variant in ("baseline", "candidate")
        }
        ordered_pairs = sorted(
            workflows_by_identity.items(),
            key=lambda item: sha256_bytes(canonical_json(item[1])),
        )
        packet = {
            "schema_version": SCHEMA_VERSION,
            "comparison_binding": binding,
            "upstream_sha256s": {
                f"normalized_{index + 1}": sha256_file(path_by_arm[arm])
                for index, arm in enumerate(OFFICIAL_ARM_ORDER)
            },
            "runs": {
                f"Run {chr(65 + index)}": value
                for index, (_identity, value) in enumerate(ordered_pairs)
            },
        }
        private_mapping = {
            "schema_version": SCHEMA_VERSION,
            "comparison_binding": binding,
            "blind_packet_sha256": sha256_bytes(canonical_json(packet)),
            "mapping": {
                f"Run {chr(65 + index)}": identity
                for index, (identity, _value) in enumerate(ordered_pairs)
            },
            "arm_normalized_sha256s": {
                arm: sha256_file(path_by_arm[arm]) for arm in OFFICIAL_ARM_ORDER
            },
        }
        assert_identity_blind(packet)
        control = comparison_control(Path(comparison["runtime_root"]))
        packet_path = control / "blind-packet.json"
        mapping_path = control / "private-identity-map.json"
        if state["blind"]["status"] == "frozen":
            require_regular_file(packet_path, "authoritative blind packet")
            require_regular_file(mapping_path, "private identity mapping")
            authoritative_packet = json.loads(packet_path.read_text(encoding="utf-8"))
            authoritative_mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            if (
                packet_path.read_bytes() != canonical_json(authoritative_packet)
                or mapping_path.read_bytes() != canonical_json(authoritative_mapping)
                or authoritative_packet != packet
                or authoritative_mapping != private_mapping
                or state["blind"]["blind_packet_sha256"] != sha256_file(packet_path)
                or state["blind"]["private_mapping_sha256"] != sha256_file(mapping_path)
            ):
                raise HarnessError("frozen blind recovery inputs or bindings drifted")
            packet = authoritative_packet
        else:
            if any(path.exists() or path.is_symlink() for path in (packet_path, mapping_path)):
                raise HarnessError("unregistered authoritative blind artifacts exist")
            published: list[tuple[Path, str]] = []
            try:
                atomic_write_json(packet_path, packet)
                published.append((packet_path, private_mapping["blind_packet_sha256"]))
                atomic_write_json(mapping_path, private_mapping)
                published.append((mapping_path, sha256_file(mapping_path)))
                if (
                    sha256_file(packet_path) != private_mapping["blind_packet_sha256"]
                    or json.loads(packet_path.read_text(encoding="utf-8")) != packet
                    or json.loads(mapping_path.read_text(encoding="utf-8")) != private_mapping
                ):
                    raise HarnessError("authoritative blind artifacts failed to freeze")
                register_blind_packet(
                    comparison_manifest,
                    private_mapping["blind_packet_sha256"],
                    published[-1][1],
                    _comparison=comparison,
                )
            except BaseException as exc:
                for published_path, published_sha256 in reversed(published):
                    if not published_path.exists() and not published_path.is_symlink():
                        continue
                    if (
                        published_path.is_symlink()
                        or not published_path.is_file()
                        or sha256_file(published_path) != published_sha256
                    ):
                        raise HarnessError(
                            "authoritative blind rollback evidence drifted"
                        ) from exc
                    published_path.unlink()
                raise
    assert_identity_blind(packet)
    return packet


def validate_official_normalized(
    path: Path,
    manifest_path: Path,
    expected_arm: str | None = None,
    *,
    _comparison: dict[str, Any] | None = None,
    _state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_regular_file(path, "official normalized output")
    raw = path.read_bytes()
    document = validate_normalized_output(
        json.loads(raw), require_arm_binding=True
    )
    comparison = _comparison or validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    if document["comparison_binding"] != binding:
        raise HarnessError("normalized output belongs to another comparison")
    arm_name = document["arm_binding"]["arm_name"]
    if expected_arm is not None and arm_name != expected_arm:
        raise HarnessError("normalized output is swapped or mislabeled")
    state = _state or validate_attempt_state(
        manifest_path, _comparison=comparison
    )["state"]
    arm_state = state["arms"][arm_name]
    stage_root = safe_path(Path(comparison["runtime_root"]), arm_name)
    output_freeze = safe_path(stage_root, "evaluator/output-freeze.json")
    terminal_seal = safe_path(stage_root, "evaluator/terminal-seal.json")
    if (
        arm_state["status"] != "sealed"
        or arm_state["terminal_seal_sha256"]
        != sha256_file(terminal_seal)
        or document["arm_binding"]["terminal_seal_sha256"]
        != sha256_file(terminal_seal)
        or document["upstream_sha256s"] != {
            "output_freeze": sha256_file(output_freeze),
            "terminal_seal": sha256_file(terminal_seal),
        }
    ):
        raise HarnessError("normalized output does not bind its registered terminal seal")
    expected = normalize_run(
        output_freeze, manifest_path, _comparison=comparison, _state=state
    )
    if raw != canonical_json(document) or document != expected:
        raise HarnessError("official normalized output is not the canonical arm normalization")
    return document


def public_normalized(document: dict[str, Any]) -> dict[str, Any]:
    public = json.loads(json.dumps(document))
    for field in ("arm_binding", "comparison_binding", "upstream_sha256s"):
        public.pop(field, None)
    return public


def validate_blind_packet(
    path: Path, manifest_path: Path, *,
    _comparison: dict[str, Any] | None = None,
    _state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_regular_file(path, "blind packet")
    packet = json.loads(path.read_text(encoding="utf-8"))
    comparison = _comparison or validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    if (
        not isinstance(packet, dict)
        or set(packet) != {
            "schema_version", "comparison_binding", "upstream_sha256s", "runs"
        }
        or packet["schema_version"] != SCHEMA_VERSION
        or packet["comparison_binding"] != binding
        or not exact_digest_map(
            packet["upstream_sha256s"],
            {f"normalized_{index}" for index in range(1, 5)},
        )
        or not isinstance(packet["runs"], dict)
        or set(packet["runs"]) != {"Run A", "Run B"}
    ):
        raise HarnessError("blind packet fields or comparison binding are invalid")
    for workflow in packet["runs"].values():
        if (
            not isinstance(workflow, dict)
            or set(workflow) != {"scenarios"}
            or not isinstance(workflow["scenarios"], dict)
            or set(workflow["scenarios"]) != set(OUTCOME_SCENARIOS)
        ):
            raise HarnessError("blind packet workflow scenarios are invalid")
        for scenario, normalized in workflow["scenarios"].items():
            validated = validate_normalized_output(normalized)
            if validated["scenario_id"] != scenario:
                raise HarnessError("blind packet scenario is mislabeled")
    state = _state or validate_attempt_state(
        manifest_path, require_all_sealed=True, _comparison=comparison
    )["state"]
    authoritative = require_regular_file(
        comparison_control(Path(comparison["runtime_root"])) / "blind-packet.json",
        "authoritative blind packet",
    )
    if (
        state["blind"]["status"] != "frozen"
        or state["blind"]["blind_packet_sha256"] != sha256_file(path)
        or path.read_bytes() != authoritative.read_bytes()
    ):
        raise HarnessError("blind packet does not match frozen comparison state")
    assert_identity_blind(packet)
    return packet


def freeze_judge_record(
    manifest_path: Path, blind_packet_path: Path, decision_path: Path, output: Path
) -> dict[str, object]:
    comparison = validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    state = validate_attempt_state(
        manifest_path, require_all_sealed=True, _comparison=comparison
    )["state"]
    judge_state = state["judge"]
    if (
        judge_state["status"] != "running"
        or judge_state["frozen_record_sha256"] is not None
    ):
        raise HarnessError("judge freeze requires one active unfrozen attempt")
    packet = validate_blind_packet(
        blind_packet_path, manifest_path, _comparison=comparison, _state=state
    )
    require_regular_file(decision_path, "blinded judge decision")
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    if (
        not isinstance(decision, dict)
        or set(decision) != {"verdict", "rationale", "material_correctness_preserved"}
        or decision["verdict"] not in {
            "Run A better", "Run B better", "materially neutral", "inconclusive"
        }
        or not isinstance(decision["rationale"], str)
        or not decision["rationale"].strip()
        or not isinstance(decision["material_correctness_preserved"], bool)
    ):
        raise HarnessError("blinded judge decision fields are invalid")
    if output.exists() or output.is_symlink():
        raise HarnessError("frozen judge record already exists")
    record = {
        "schema_version": SCHEMA_VERSION,
        "comparison_binding": binding,
        "upstream_sha256s": {
            "blind_packet": sha256_file(blind_packet_path),
            "judge_decision": sha256_bytes(canonical_json(decision)),
        },
        **decision,
    }
    atomic_write_json(output, record)
    register_judge_record(
        manifest_path, sha256_file(output), _comparison=comparison
    )
    verify_external_sentinel(comparison["external_sentinel"], Path(comparison["runtime_root"]))
    return record


def validate_judge_record(
    path: Path, manifest_path: Path, blind_packet_path: Path, *,
    _comparison: dict[str, Any] | None = None,
    _state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_regular_file(path, "frozen judge record")
    record = json.loads(path.read_text(encoding="utf-8"))
    comparison = _comparison or validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    decision = {
        key: record.get(key)
        for key in ("verdict", "rationale", "material_correctness_preserved")
    }
    if (
        not isinstance(record, dict)
        or set(record) != {
            "schema_version", "comparison_binding", "upstream_sha256s",
            "verdict", "rationale", "material_correctness_preserved",
        }
        or record["schema_version"] != SCHEMA_VERSION
        or record["comparison_binding"] != binding
        or not exact_digest_map(
            record["upstream_sha256s"], {"blind_packet", "judge_decision"}
        )
        or record["upstream_sha256s"]["blind_packet"]
        != sha256_file(blind_packet_path)
        or record["upstream_sha256s"]["judge_decision"]
        != sha256_bytes(canonical_json(decision))
        or record["verdict"] not in {
            "Run A better", "Run B better", "materially neutral", "inconclusive"
        }
        or not isinstance(record["rationale"], str)
        or not record["rationale"].strip()
        or not isinstance(record["material_correctness_preserved"], bool)
    ):
        raise HarnessError("frozen judge record or upstream digests are invalid")
    state = _state or validate_attempt_state(
        manifest_path, require_all_sealed=True, _comparison=comparison
    )["state"]
    if (
        state["judge"]["status"] != "frozen"
        or state["judge"]["frozen_record_sha256"] != sha256_file(path)
    ):
        raise HarnessError("judge record does not match frozen comparison state")
    return record


def reveal_identities(
    manifest_path: Path,
    blind_packet_path: Path,
    judge_record_path: Path,
    *,
    _comparison: dict[str, Any] | None = None,
    _state: dict[str, Any] | None = None,
    _packet: dict[str, Any] | None = None,
    _judge: dict[str, Any] | None = None,
) -> dict[str, object]:
    comparison = _comparison or validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    state = _state or validate_attempt_state(
        manifest_path, require_all_sealed=True, _comparison=comparison
    )["state"]
    packet = _packet or validate_blind_packet(
        blind_packet_path, manifest_path, _comparison=comparison, _state=state
    )
    judge = _judge or validate_judge_record(
        judge_record_path, manifest_path, blind_packet_path,
        _comparison=comparison, _state=state,
    )
    if (
        state["judge"].get("status") != "frozen"
        or state["judge"].get("frozen_record_sha256") != sha256_file(judge_record_path)
    ):
        raise HarnessError("judge record does not match the frozen comparison state")
    mapping_path = comparison_control(
        Path(comparison["runtime_root"])
    ) / "private-identity-map.json"
    require_regular_file(mapping_path, "private identity mapping")
    private_mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping = private_mapping.get("mapping")
    normalized_sha256s = private_mapping.get("arm_normalized_sha256s")
    if (
        not isinstance(private_mapping, dict)
        or set(private_mapping) != {
            "schema_version", "comparison_binding", "blind_packet_sha256",
            "mapping", "arm_normalized_sha256s",
        }
        or private_mapping["schema_version"] != SCHEMA_VERSION
        or private_mapping["comparison_binding"] != binding
        or private_mapping["blind_packet_sha256"] != sha256_file(blind_packet_path)
        or not isinstance(mapping, dict)
        or set(mapping) != {"Run A", "Run B"}
        or set(mapping.values()) != {"baseline", "candidate"}
        or not exact_digest_map(normalized_sha256s, set(OFFICIAL_ARM_ORDER))
        or packet["upstream_sha256s"] != {
            f"normalized_{index + 1}": normalized_sha256s[arm]
            for index, arm in enumerate(OFFICIAL_ARM_ORDER)
        }
        or state["blind"]["private_mapping_sha256"] != sha256_file(mapping_path)
    ):
        raise HarnessError("private identity mapping is invalid or not frozen")
    return {
        "schema_version": SCHEMA_VERSION,
        "comparison_binding": binding,
        "upstream_sha256s": {
            "blind_packet": sha256_file(blind_packet_path),
            "judge_record": sha256_file(judge_record_path),
            "private_identity_mapping": sha256_file(mapping_path),
        },
        "mapping": mapping,
        "baseline_run": next(run for run, identity in mapping.items() if identity == "baseline"),
        "candidate_run": next(run for run, identity in mapping.items() if identity == "candidate"),
    }


def validate_identity_reveal(
    path: Path,
    manifest_path: Path,
    blind_packet_path: Path,
    judge_record_path: Path,
    *,
    _comparison: dict[str, Any] | None = None,
    _state: dict[str, Any] | None = None,
    _packet: dict[str, Any] | None = None,
    _judge: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_regular_file(path, "identity reveal")
    reveal = json.loads(path.read_text(encoding="utf-8"))
    if reveal != reveal_identities(
        manifest_path, blind_packet_path, judge_record_path,
        _comparison=_comparison, _state=_state, _packet=_packet, _judge=_judge,
    ):
        raise HarnessError("identity reveal or upstream digests are invalid")
    return reveal


def check_candidate_compliance_bound(
    manifest_path: Path,
    report_path: Path,
    reveal_path: Path,
    blind_packet_path: Path,
    judge_record_path: Path,
) -> dict[str, object]:
    comparison = validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    validate_identity_reveal(
        reveal_path, manifest_path, blind_packet_path, judge_record_path,
        _comparison=comparison,
    )
    require_regular_file(report_path, "candidate compliance report")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    result = check_candidate_compliance(report_path)
    return {
        "schema_version": SCHEMA_VERSION,
        "comparison_binding": binding,
        "upstream_sha256s": {
            "identity_reveal": sha256_file(reveal_path),
            "candidate_report": sha256_bytes(canonical_json(report)),
        },
        "candidate_report": report,
        **result,
    }


def validate_candidate_compliance_result(
    path: Path,
    manifest_path: Path,
    reveal_path: Path,
    blind_packet_path: Path,
    judge_record_path: Path,
    *,
    _comparison: dict[str, Any] | None = None,
    _reveal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_regular_file(path, "candidate compliance result")
    result = json.loads(path.read_text(encoding="utf-8"))
    comparison = _comparison or validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    if _reveal is None:
        validate_identity_reveal(
            reveal_path, manifest_path, blind_packet_path, judge_record_path,
            _comparison=comparison,
        )
    if (
        not isinstance(result, dict)
        or set(result) != {
            "schema_version", "comparison_binding", "upstream_sha256s",
            "candidate_report", "compliant", "violations",
        }
        or result["schema_version"] != SCHEMA_VERSION
        or result["comparison_binding"] != binding
        or not exact_digest_map(
            result["upstream_sha256s"], {"identity_reveal", "candidate_report"}
        )
        or result["upstream_sha256s"]["identity_reveal"] != sha256_file(reveal_path)
        or result["upstream_sha256s"]["candidate_report"]
        != sha256_bytes(canonical_json(result["candidate_report"]))
        or not isinstance(result["compliant"], bool)
        or not isinstance(result["violations"], list)
        or any(not isinstance(item, str) for item in result["violations"])
    ):
        raise HarnessError("candidate compliance result or upstream digests are invalid")
    expected = check_candidate_compliance_document(result["candidate_report"])
    if {
        "compliant": result["compliant"], "violations": result["violations"]
    } != expected:
        raise HarnessError("candidate compliance result does not match embedded report")
    return result


def gate_official_outcomes(
    manifest_path: Path,
    baseline_paths: list[Path],
    candidate_paths: list[Path],
    blind_packet_path: Path,
    judge_record_path: Path,
    reveal_path: Path,
    compliance_path: Path,
    *,
    _comparison: dict[str, Any] | None = None,
) -> dict[str, object]:
    comparison = _comparison or validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    state = validate_attempt_state(
        manifest_path, require_all_sealed=True, _comparison=comparison
    )["state"]
    path_by_arm: dict[str, Path] = {}
    expected_groups = (
        (baseline_paths, "baseline"), (candidate_paths, "candidate")
    )
    for paths, variant in expected_groups:
        if len(paths) != len(OUTCOME_SCENARIOS):
            raise HarnessError(f"official {variant} gate requires both scenarios")
        for path in paths:
            document = validate_official_normalized(
                path, manifest_path, _comparison=comparison, _state=state
            )
            arm_name = document["arm_binding"]["arm_name"]
            if not arm_name.endswith(f"-{variant}") or arm_name in path_by_arm:
                raise HarnessError("official gate normalized arms are duplicate or mislabeled")
            path_by_arm[arm_name] = path
    if set(path_by_arm) != set(OFFICIAL_ARM_ORDER):
        raise HarnessError("official gate requires the exact four registered arms")
    packet = validate_blind_packet(
        blind_packet_path, manifest_path, _comparison=comparison, _state=state
    )
    expected_packet_upstreams = {
        f"normalized_{index + 1}": sha256_file(path_by_arm[arm])
        for index, arm in enumerate(OFFICIAL_ARM_ORDER)
    }
    if packet["upstream_sha256s"] != expected_packet_upstreams:
        raise HarnessError("blind packet normalized upstream digests drifted")
    judge = validate_judge_record(
        judge_record_path, manifest_path, blind_packet_path,
        _comparison=comparison, _state=state,
    )
    reveal = validate_identity_reveal(
        reveal_path, manifest_path, blind_packet_path, judge_record_path,
        _comparison=comparison, _state=state, _packet=packet, _judge=judge,
    )
    compliance = validate_candidate_compliance_result(
        compliance_path, manifest_path, reveal_path,
        blind_packet_path, judge_record_path,
        _comparison=comparison, _reveal=reveal,
    )
    outcome = gate_outcomes(baseline_paths, candidate_paths)
    winning_run = (
        f"Run {judge['verdict'].split()[1]}"
        if judge.get("verdict") in {"Run A better", "Run B better"}
        else None
    )
    blind_candidate_better = winning_run == reveal.get("candidate_run")
    correctness = bool(judge.get("material_correctness_preserved"))
    compliant = compliance.get("compliant") is True
    non_preference_hard_gates = bool(outcome["passed"] and correctness and compliant)
    outcome.update({
        "comparison_binding": binding,
        "upstream_sha256s": {
            "blind_packet": sha256_file(blind_packet_path),
            "judge_record": sha256_file(judge_record_path),
            "identity_reveal": sha256_file(reveal_path),
            "candidate_compliance": sha256_file(compliance_path),
            **{
                f"normalized_{index + 1}": sha256_file(path)
                for index, path in enumerate(
                    path_by_arm[arm] for arm in OFFICIAL_ARM_ORDER
                )
            },
        },
        "correctness_gate_evaluated": True,
        "correctness_preserved": correctness,
        "judge_verdict_evaluated": True,
        "judge_verdict": judge["verdict"],
        "blind_candidate_better": blind_candidate_better,
        "candidate_compliant": compliant,
        "non_preference_hard_gates_passed": non_preference_hard_gates,
    })
    outcome["passed"] = bool(non_preference_hard_gates and blind_candidate_better)
    return outcome


def validate_official_outcome_gate(
    path: Path,
    manifest_path: Path,
    baseline_paths: list[Path],
    candidate_paths: list[Path],
    blind_packet_path: Path,
    judge_record_path: Path,
    reveal_path: Path,
    compliance_path: Path,
    *,
    _comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_regular_file(path, "official outcome gate")
    gate = json.loads(path.read_text(encoding="utf-8"))
    expected = gate_official_outcomes(
        manifest_path, baseline_paths, candidate_paths, blind_packet_path,
        judge_record_path, reveal_path, compliance_path,
        _comparison=_comparison,
    )
    if gate != expected:
        raise HarnessError("official outcome gate or an upstream digest drifted")
    return gate


def final_transition(
    failure_class: str | None,
    gate: dict[str, Any],
    judge: dict[str, Any],
) -> tuple[str, str, bool]:
    if failure_class in {
        "evaluator_defect", "baseline_terminal", "ambiguous", "incomparable"
    }:
        return "inconclusive", "uncomparable_runs", False
    if failure_class in {
        "candidate_unscorable", "candidate_hard_gate", "blinded_regression"
    }:
        return "candidate_regression", "candidate_regression", False
    if failure_class == "candidate_not_exposed":
        return "inconclusive", "inconclusive_scenario", False
    if failure_class is not None:
        raise HarnessError("final verdict failure class is invalid")
    if judge.get("verdict") == "inconclusive":
        return "inconclusive", "uncomparable_runs", False
    if gate.get("passed") is True:
        return "candidate_better", "clean_benefit", True
    if (
        judge.get("verdict") == "materially neutral"
        and gate.get("non_preference_hard_gates_passed") is True
    ):
        return "candidate_neutral", "candidate_neutral", False
    return "candidate_regression", "candidate_regression", False


def validate_failure_evidence(
    path: Path, binding: dict[str, object], state: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    require_regular_file(path, "failure evidence")
    raw = path.read_bytes()
    evidence = json.loads(raw)
    if (
        not isinstance(evidence, dict)
        or set(evidence) != {
            "schema_version", "comparison_binding", "attempt_state_sha256",
            "observations",
        }
        or evidence["schema_version"] != SCHEMA_VERSION
        or evidence["comparison_binding"] != binding
        or evidence["attempt_state_sha256"] != attempt_state_sha256(state)
        or raw != canonical_json(evidence)
        or not isinstance(evidence["observations"], list)
        or not evidence["observations"]
    ):
        raise HarnessError("failure evidence identity or shape is invalid")
    if not any(state["arms"][arm]["attempts"] for arm in OFFICIAL_ARM_ORDER):
        raise HarnessError("failure evidence is invalid before the first arm starts")
    bound_digests: set[str] = set()

    def collect(value: object) -> None:
        if is_digest(value):
            bound_digests.add(value)
        elif isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    collect({"arms": state["arms"], "blind": state["blind"], "judge": state["judge"]})
    observed: set[str] = set()
    for observation in evidence["observations"]:
        fact = (
            observation.get("event"), observation.get("subject")
        ) if isinstance(observation, dict) else (None, None)
        condition = FAILURE_FACTS.get(fact)
        if (
            not isinstance(observation, dict)
            or set(observation) != {
                "event", "subject", "evidence_sha256", "summary"
            }
            or condition is None
            or observation["evidence_sha256"] not in bound_digests
            or not isinstance(observation["summary"], str)
            or not observation["summary"].strip()
            or condition in observed
        ):
            raise HarnessError("failure evidence observation is invalid or unbound")
        observed.add(condition)
    return evidence, next(
        condition for condition in FAILURE_PRECEDENCE if condition in observed
    )


def copy_final_evidence(
    comparison: dict[str, Any],
    sources: dict[str, Path],
    contract: tuple[tuple[str, str], ...],
) -> dict[str, Path]:
    if set(sources) != {label for label, _relative in contract}:
        raise HarnessError("final evidence sources are not exact")
    control = comparison_control(Path(comparison["runtime_root"]))
    evidence_root = control / "final-evidence"
    if evidence_root.exists() or evidence_root.is_symlink():
        raise HarnessError("final evidence is already frozen")
    evidence_root.mkdir(mode=0o700)
    copied: dict[str, Path] = {}
    for label, relative in contract:
        source = require_regular_file(sources[label], label.replace("_", " "))
        try:
            document = json.loads(source.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HarnessError(f"{label} is not canonical JSON evidence") from exc
        if source.read_bytes() != canonical_json(document):
            raise HarnessError(f"{label} is not canonical JSON evidence")
        target = safe_path(control, relative, must_exist=False)
        atomic_write_json(target, document)
        copied[label] = target
    return copied


def validate_cleanup_receipt(
    comparison: dict[str, Any],
    state: dict[str, Any],
    final_path: Path,
) -> dict[str, Any] | None:
    receipt_sha256 = state["cleanup_receipt_sha256"]
    if receipt_sha256 is None:
        return None
    control = comparison_control(Path(comparison["runtime_root"]))
    receipt_path = require_regular_file(
        control / "cleanup-receipt.json", "cleanup receipt"
    )
    sentinel = verify_external_sentinel(
        comparison["external_sentinel"], Path(comparison["runtime_root"])
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected = {
        "schema_version": SCHEMA_VERSION,
        "comparison_binding": binding_from_comparison(comparison),
        "attempt_state_sha256": attempt_state_sha256(state),
        "action": "sentinel_retained_through_merge_rereview",
        "upstream_sha256s": {
            "final_verdict": sha256_file(final_path),
            "external_sentinel": sha256_file(sentinel),
        },
    }
    if sha256_file(receipt_path) != receipt_sha256 or receipt != expected:
        raise HarnessError("cleanup receipt or retained sentinel binding drifted")
    return receipt


def validate_final_verdict(manifest_path: Path) -> dict[str, Any]:
    comparison = validate_comparison_manifest(
        manifest_path, recompute_packages=True
    )
    binding = binding_from_comparison(comparison)
    state = validate_attempt_state(
        manifest_path, _comparison=comparison
    )["state"]
    control = comparison_control(Path(comparison["runtime_root"]))
    final_path = require_regular_file(control / "final-verdict.json", "final verdict")
    result = json.loads(final_path.read_text(encoding="utf-8"))
    fields = {
        "schema_version", "comparison_binding", "evidence_paths",
        "upstream_sha256s", "verdict", "stop_reason", "merge_ready",
        "failure_class", "attempt_state_sha256",
    }
    if (
        not isinstance(result, dict) or set(result) != fields
        or result["schema_version"] != SCHEMA_VERSION
        or result["comparison_binding"] != binding
        or state["final_verdict_sha256"] != sha256_file(final_path)
        or result["attempt_state_sha256"] != attempt_state_sha256(state)
    ):
        raise HarnessError("final verdict identity or frozen state drifted")
    contract = FINAL_FAILURE_FILES if result["failure_class"] else FINAL_CHAIN_FILES
    expected_paths = dict(contract)
    if (
        result["evidence_paths"] != expected_paths
        or not exact_digest_map(
            result["upstream_sha256s"], set(expected_paths)
        )
    ):
        raise HarnessError("final verdict evidence contract is invalid")
    evidence: dict[str, Path] = {}
    for label, relative in contract:
        path = require_regular_file(
            safe_path(control, relative), f"final {label.replace('_', ' ')}"
        )
        if result["upstream_sha256s"][label] != sha256_file(path):
            raise HarnessError("final verdict evidence digest drifted")
        evidence[label] = path
    gate: dict[str, Any] = {}
    judge: dict[str, Any] = {}
    if result["failure_class"] is None:
        baseline = [
            evidence["normalized_retry_failed_baseline"],
            evidence["normalized_preflight_remediation_holdout_baseline"],
        ]
        candidate = [
            evidence["normalized_retry_failed_candidate"],
            evidence["normalized_preflight_remediation_holdout_candidate"],
        ]
        gate = validate_official_outcome_gate(
            evidence["outcome_gate"], manifest_path, baseline, candidate,
            evidence["blind_packet"], evidence["judge_record"],
            evidence["identity_reveal"], evidence["candidate_compliance"],
            _comparison=comparison,
        )
        judge = {"verdict": gate["judge_verdict"]}
    else:
        _failure_evidence, derived_failure = validate_failure_evidence(
            evidence["failure_evidence"], binding, state
        )
        if result["failure_class"] != derived_failure:
            raise HarnessError("final failure class does not match structured evidence")
    if (result["verdict"], result["stop_reason"], result["merge_ready"]) != (
        final_transition(result["failure_class"], gate, judge)
    ):
        raise HarnessError("final verdict does not replay from frozen evidence")
    validate_cleanup_receipt(comparison, state, final_path)
    return result


def freeze_final_verdict(
    manifest_path: Path,
    outcome_gate_path: Path | None,
    judge_record_path: Path | None,
    compliance_path: Path | None,
    baseline_paths: list[Path] | None = None,
    candidate_paths: list[Path] | None = None,
    blind_packet_path: Path | None = None,
    reveal_path: Path | None = None,
    *,
    failure_evidence_path: Path | None = None,
) -> dict[str, object]:
    comparison = validate_comparison_manifest(manifest_path)
    binding = binding_from_comparison(comparison)
    state = validate_attempt_state(
        manifest_path, _comparison=comparison
    )["state"]
    if failure_evidence_path is not None:
        _failure_evidence, failure_class = validate_failure_evidence(
            failure_evidence_path, binding, state
        )
        sources = {"failure_evidence": failure_evidence_path}
        gate: dict[str, Any] = {}
        judge: dict[str, Any] = {}
        contract = FINAL_FAILURE_FILES
    else:
        failure_class = None
        if (
            outcome_gate_path is None or judge_record_path is None
            or compliance_path is None
            or baseline_paths is None
            or candidate_paths is None
            or blind_packet_path is None
            or reveal_path is None
        ):
            raise HarnessError("normal final verdict requires the complete frozen chain")
        gate = validate_official_outcome_gate(
            outcome_gate_path, manifest_path, baseline_paths, candidate_paths,
            blind_packet_path, judge_record_path, reveal_path, compliance_path,
            _comparison=comparison,
        )
        judge = {"verdict": gate["judge_verdict"]}
        normalized_by_arm: dict[str, Path] = {}
        for normalized_path in [*baseline_paths, *candidate_paths]:
            normalized = validate_normalized_output(
                json.loads(require_regular_file(
                    normalized_path, "final normalized source"
                ).read_text(encoding="utf-8")),
                require_arm_binding=True,
            )
            arm_name = normalized["arm_binding"]["arm_name"]
            if arm_name in normalized_by_arm:
                raise HarnessError("final normalized sources contain a duplicate arm")
            normalized_by_arm[arm_name] = normalized_path
        if set(normalized_by_arm) != set(OFFICIAL_ARM_ORDER):
            raise HarnessError("final normalized sources do not contain the exact four arms")
        sources = {
            "normalized_retry_failed_baseline": normalized_by_arm["retry-failed-baseline"],
            "normalized_preflight_remediation_holdout_baseline": normalized_by_arm[
                "preflight-remediation-holdout-baseline"
            ],
            "normalized_retry_failed_candidate": normalized_by_arm["retry-failed-candidate"],
            "normalized_preflight_remediation_holdout_candidate": normalized_by_arm[
                "preflight-remediation-holdout-candidate"
            ],
            "blind_packet": blind_packet_path,
            "judge_record": judge_record_path,
            "identity_reveal": reveal_path,
            "candidate_compliance": compliance_path,
            "outcome_gate": outcome_gate_path,
        }
        contract = FINAL_CHAIN_FILES
    verdict, stop_reason, merge_ready = final_transition(failure_class, gate, judge)
    evidence = copy_final_evidence(comparison, sources, contract)
    result = {
        "schema_version": SCHEMA_VERSION,
        "comparison_binding": binding,
        "attempt_state_sha256": attempt_state_sha256(state),
        "evidence_paths": dict(contract),
        "upstream_sha256s": {
            name: sha256_file(path) for name, path in evidence.items()
        },
        "verdict": verdict,
        "stop_reason": stop_reason,
        "merge_ready": merge_ready,
        "failure_class": failure_class,
    }
    final_path = comparison_control(Path(comparison["runtime_root"])) / "final-verdict.json"
    if final_path.exists() or final_path.is_symlink():
        raise HarnessError("final verdict is already frozen")
    atomic_write_json(final_path, result)
    register_final_verdict(
        manifest_path, sha256_file(final_path),
        require_judge=failure_class is None,
        _comparison=comparison,
    )
    frozen_state = validate_attempt_state(
        manifest_path, _comparison=comparison
    )["state"]
    if (
        frozen_state["final_verdict_sha256"] != sha256_file(final_path)
        or result["attempt_state_sha256"] != attempt_state_sha256(frozen_state)
        or json.loads(final_path.read_text(encoding="utf-8")) != result
    ):
        raise HarnessError("final verdict publication or state binding drifted")
    return result


def cleanup_comparison(manifest_path: Path) -> None:
    validate_final_verdict(manifest_path)
    comparison = validate_comparison_manifest(
        manifest_path, recompute_evaluator=False
    )
    state = validate_attempt_state(
        manifest_path, _comparison=comparison
    )["state"]
    if not is_digest(state.get("final_verdict_sha256")):
        raise HarnessError("comparison cleanup requires a frozen final verdict")
    if state.get("cleanup_receipt_sha256") is not None:
        raise HarnessError("comparison cleanup receipt is already frozen")
    runtime_root = Path(comparison["runtime_root"])
    sentinel = verify_external_sentinel(comparison["external_sentinel"], runtime_root)
    final_path = comparison_control(runtime_root) / "final-verdict.json"
    require_regular_file(final_path, "final verdict")
    if sha256_file(final_path) != state["final_verdict_sha256"]:
        raise HarnessError("cleanup final verdict binding drifted")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "comparison_binding": binding_from_comparison(comparison),
        "attempt_state_sha256": attempt_state_sha256(state),
        "action": "sentinel_retained_through_merge_rereview",
        "upstream_sha256s": {
            "final_verdict": sha256_file(final_path),
            "external_sentinel": sha256_file(sentinel),
        },
    }
    receipt_path = comparison_control(runtime_root) / "cleanup-receipt.json"
    if receipt_path.exists() or receipt_path.is_symlink():
        raise HarnessError("cleanup receipt already exists")
    atomic_write_json(receipt_path, receipt)
    with locked_attempt_state(
        manifest_path, _comparison=comparison
    ) as (_comparison, mutable):
        if mutable["cleanup_receipt_sha256"] is not None:
            raise HarnessError("cleanup receipt already registered")
        mutable["cleanup_receipt_sha256"] = sha256_file(receipt_path)
    cleaned_state = validate_attempt_state(
        manifest_path, _comparison=comparison
    )["state"]
    validate_cleanup_receipt(comparison, cleaned_state, final_path)


def validate_ledger() -> None:
    ledger = json.loads(OUTCOME_LEDGER.read_text(encoding="utf-8"))
    entries = ledger["entries"]
    dispositions = {entry["test_disposition"] for entry in entries}
    scopes = {entry.get("rereview_scope") for entry in entries}
    if dispositions != {"permanent", "table_case", "probe_only", "no_test"}:
        raise HarnessError("outcome ledger does not span all frozen test dispositions")
    if not {"targeted", "full"}.issubset(scopes):
        raise HarnessError("outcome ledger does not span both rereview scopes")
    required_topics = {
        "mixed_offset_selection",
        "grouped_malformed_boundaries",
        "rare_integer_and_deep_structure",
        "unreachable_helper",
        "isolated_repair",
        "operational_boundary",
    }
    if {entry["topic"] for entry in entries} != required_topics:
        raise HarnessError("outcome ledger topics drifted")


def load_normalized_arm(
    paths: list[Path], label: str
) -> tuple[dict[str, dict[str, object]], dict[str, str]]:
    if len(paths) != len(OUTCOME_SCENARIOS):
        raise HarnessError(f"{label} must contain exactly two normalized scenario outputs")
    documents: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise HarnessError(f"{label} normalized output must be a regular file")
        document = validate_normalized_output(json.loads(path.read_text(encoding="utf-8")))
        scenario_id = document["scenario_id"]
        if scenario_id in documents:
            raise HarnessError(f"{label} contains duplicate scenario output: {scenario_id}")
        documents[scenario_id] = document
        hashes[scenario_id] = sha256_file(path)
    if set(documents) != set(OUTCOME_SCENARIOS):
        raise HarnessError(f"{label} must contain both frozen scenarios exactly once")
    outcomes = {
        action["finding_id"]: {
            "test_disposition": action["test_disposition"],
            "rereview_scope": action["rereview_scope"],
        }
        for scenario_id in OUTCOME_SCENARIOS
        for action in documents[scenario_id]["behavior"]["review_actions"]
    }
    return outcomes, hashes


def gate_outcomes(
    baseline_paths: list[Path], candidate_paths: list[Path]
) -> dict[str, object]:
    validate_ledger()
    ledger_document = json.loads(OUTCOME_LEDGER.read_text(encoding="utf-8"))
    ledger = {entry["finding_id"]: entry for entry in ledger_document["entries"]}
    ledger_ids = set(ledger)
    baseline, baseline_hashes = load_normalized_arm(baseline_paths, "baseline")
    candidate, candidate_hashes = load_normalized_arm(candidate_paths, "candidate")
    if set(baseline) != ledger_ids or set(candidate) != ledger_ids:
        raise HarnessError("normalized outcome inputs do not exactly cover the frozen ledger")

    regressions: list[dict[str, object]] = []
    for finding_id in sorted(ledger_ids & set(candidate)):
        expected = ledger[finding_id]
        actual = candidate[finding_id]
        for field in ("test_disposition", "rereview_scope"):
            if actual[field] != expected[field]:
                regressions.append(
                    {
                        "finding_id": finding_id,
                        "field": field,
                        "expected": expected[field],
                        "actual": actual[field],
                    }
                )

    def unjustified_permanent(outcomes: dict[str, dict[str, object]]) -> int:
        return sum(
            1
            for finding_id, outcome in outcomes.items()
            if outcome["test_disposition"] == "permanent"
            and ledger[finding_id]["test_disposition"] in {"table_case", "probe_only", "no_test"}
        )

    def unnecessary_full(outcomes: dict[str, dict[str, object]]) -> int:
        return sum(
            1
            for finding_id, outcome in outcomes.items()
            if outcome["rereview_scope"] == "full"
            and ledger[finding_id]["rereview_scope"] in {"targeted", None}
        )

    baseline_permanent = unjustified_permanent(baseline)
    candidate_permanent = unjustified_permanent(candidate)
    baseline_full = unnecessary_full(baseline)
    candidate_full = unnecessary_full(candidate)
    permanent_improved = candidate_permanent < baseline_permanent
    full_improved = candidate_full < baseline_full
    passed = not regressions and permanent_improved and full_improved
    return {
        "schema_version": SCHEMA_VERSION,
        "gate": "deliver_outcomes",
        "passed": passed,
        "ledger_sha256": sha256_file(OUTCOME_LEDGER),
        "ledger_finding_count": len(ledger),
        "input_sha256s": {
            "baseline": baseline_hashes,
            "candidate": candidate_hashes,
        },
        "axes": {
            "unjustified_permanent_decisions": {
                "baseline": baseline_permanent,
                "candidate": candidate_permanent,
                "strict_improvement": permanent_improved,
            },
            "unnecessary_full_rereviews": {
                "baseline": baseline_full,
                "candidate": candidate_full,
                "strict_improvement": full_improved,
            },
        },
        "candidate_category_regressions": regressions,
        "correctness_gate_evaluated": False,
        "judge_verdict_evaluated": False,
    }


def check_candidate_compliance(report_path: Path) -> dict[str, object]:
    if report_path.is_symlink() or not report_path.is_file():
        raise HarnessError("candidate compliance report must be a regular post-reveal file")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return check_candidate_compliance_document(report)


def check_candidate_compliance_document(report: object) -> dict[str, object]:
    if not isinstance(report, dict) or set(report) != {"revealed_identity", "records"}:
        return {"compliant": False, "violations": ["document fields"]}
    if not isinstance(report["revealed_identity"], str) or report["revealed_identity"] != "candidate":
        return {"compliant": False, "violations": ["revealed_identity"]}
    if not isinstance(report["records"], list):
        return {"compliant": False, "violations": ["records type"]}
    required = {
        "finding_id",
        "test_disposition",
        "test_rationale",
        "repair_authorized",
        "rereview_scope",
        "rereview_rationale",
    }
    violations: list[str] = []
    if len(report["records"]) != 6:
        violations.append("records must contain exactly six findings")
    finding_ids: list[str] = []
    for index, record in enumerate(report["records"]):
        if not isinstance(record, dict) or set(record) != required:
            violations.append(f"record {index} fields")
            continue
        finding_id = record["finding_id"]
        if not isinstance(finding_id, str) or not finding_id.strip():
            violations.append(f"record {index} finding_id")
        else:
            finding_ids.append(finding_id)
        if (
            not isinstance(record["test_disposition"], str)
            or record["test_disposition"]
            not in {"permanent", "table_case", "probe_only", "no_test"}
        ):
            violations.append(f"record {index} test_disposition")
        if not isinstance(record["repair_authorized"], bool):
            violations.append(f"record {index} repair_authorized")
            continue
        expected_scopes = {"targeted", "full"} if record["repair_authorized"] else {None}
        if record["rereview_scope"] not in expected_scopes:
            violations.append(f"record {index} rereview_scope")
        if not isinstance(record["test_rationale"], str) or not record["test_rationale"].strip():
            violations.append(f"record {index} test_rationale")
        if not isinstance(record["rereview_rationale"], str) or (
            record["repair_authorized"] and not record["rereview_rationale"].strip()
        ):
            violations.append(f"record {index} rereview_rationale")
    if len(finding_ids) != len(set(finding_ids)):
        violations.append("duplicate finding IDs")
    ledger = json.loads(OUTCOME_LEDGER.read_text(encoding="utf-8"))
    expected_ids = {entry["finding_id"] for entry in ledger["entries"]}
    actual_ids = set(finding_ids)
    if expected_ids - actual_ids:
        violations.append(
            f"missing ledger findings: {', '.join(sorted(expected_ids - actual_ids))}"
        )
    if actual_ids - expected_ids:
        violations.append(
            f"extra ledger findings: {', '.join(sorted(actual_ids - expected_ids))}"
        )
    return {"compliant": not violations, "violations": violations}


def prompt_from_manifest(stage_root: Path, manifest: dict[str, Any]) -> str:
    sections: list[str] = []
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, list):
        raise HarnessError("runner prompt manifest files are invalid")
    selected: list[dict[str, Any]] = []
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("category"), str):
            raise HarnessError("runner prompt manifest entry is invalid")
        if entry["category"] in {"contract", "scenario_stage"}:
            selected.append(entry)
    for entry in sorted(selected, key=lambda item: item["path"]):
        if (
            not isinstance(entry, dict)
            or set(entry) != {"category", "path", "sha256", "size"}
            or entry["category"] not in {"contract", "scenario_stage"}
            or not isinstance(entry["path"], str)
        ):
            raise HarnessError("runner prompt manifest entry is invalid")
        path = safe_path(stage_root, entry["path"])
        if path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            raise HarnessError(f"runner prompt input digest mismatch: {entry['path']}")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise HarnessError(f"runner prompt input must be UTF-8 text: {entry['path']}") from exc
        sections.append(f"## {entry['path']}\n\n{content.rstrip()}\n")
    if not sections:
        raise HarnessError("runner prompt has no allowlisted contract/scenario inputs")
    return "\n".join(sections)


def assemble_runner_prompt(stage_root: Path, phase: str) -> tuple[str, dict[str, Any]]:
    manifest = verify_manifest(stage_root)
    expected_stage = {"pre-packet": "pre_packet", "remediation": "review_packet"}[phase]
    if manifest["scenario_stage"] != expected_stage:
        raise HarnessError(f"runner phase {phase} requires manifest stage {expected_stage}")
    return FIRST_TOOL_GATE_PROMPT + prompt_from_manifest(stage_root, manifest), manifest


def is_structurally_valid_codex_event(event: object) -> bool:
    if not isinstance(event, dict) or event.get("type") not in CODEX_EVENT_TYPES:
        return False
    event_type = event["type"]
    if event_type == "thread.started":
        return isinstance(event.get("thread_id"), str) and bool(event["thread_id"].strip())
    if event_type.startswith("item."):
        item = event.get("item")
        return (
            isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and bool(item["id"].strip())
            and isinstance(item.get("type"), str)
            and bool(item["type"].strip())
        )
    if event_type == "error":
        return isinstance(event.get("message"), str) and bool(event["message"].strip())
    if event_type == "turn.failed":
        return isinstance(event.get("error"), dict)
    return True


def stop_process_group(process: Any, process_group_id: int) -> None:
    own_group = os.getpgrp()
    if process_group_id <= 0 or process_group_id == own_group:
        if process.poll() is None:
            process.kill()
            process.wait()
        raise HarnessError("refusing to signal the evaluator process group")
    signal_error: OSError | None = None
    try:
        os.killpg(process_group_id, signal.SIGKILL)
    except ProcessLookupError:
        if process.poll() is None:
            process.kill()
    except OSError as exc:
        signal_error = exc
        if process.poll() is None:
            process.kill()
    finally:
        process.wait()
    if signal_error is not None:
        raise HarnessError("unable to stop the runner process group") from signal_error


def parent_stream_paths(
    stage_root: Path, phase: str, attempt: int | None = None
) -> tuple[Path, Path]:
    probe_root = ensure_sibling_probe(stage_root).parent
    streams_root = probe_root / "runner-streams"
    if streams_root.is_symlink():
        raise HarnessError("parent stream root must not be a symlink")
    streams_root.mkdir(mode=0o700, exist_ok=True)
    stream_root = streams_root / stage_root.name
    if attempt is not None:
        stream_root = stream_root / f"attempt-{attempt}"
    stream_root = stream_root / phase
    if stream_root.exists() or stream_root.is_symlink():
        raise HarnessError(f"parent stream artifacts already exist: {phase}")
    stream_root.mkdir(parents=True, mode=0o700)
    return stream_root / "trace.jsonl", stream_root / "stderr.txt"


def publish_captured_stream(
    stream_path: Path, artifact_path: Path, capture: StreamCapture
) -> Path:
    if stream_path.is_symlink() or not stream_path.is_file():
        raise HarnessError("captured output is not a regular parent stream")
    if stream_path.stat().st_size != capture.byte_count:
        raise HarnessError("parent stream capture integrity size mismatch")
    data = stream_path.read_bytes()
    if len(data) != capture.byte_count or sha256_bytes(data) != capture.sha256:
        raise HarnessError("parent stream capture integrity digest mismatch")
    if artifact_path.parent.is_symlink() or not artifact_path.parent.is_dir():
        raise HarnessError("runner artifact parent is not a regular directory")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{artifact_path.name}.",
            dir=artifact_path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(data)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, artifact_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return artifact_path


def monitor_codex_process(
    process: Any,
    trace_path: Path,
    auth_copy: Path,
    *,
    total_timeout_seconds: float,
    inactivity_timeout_seconds: float,
    monotonic: Any = time.monotonic,
    wait_for_readable: Any = select.select,
    process_group_id: int,
    stop_group: Any = stop_process_group,
    capture: StreamCapture | None = None,
) -> int:
    if total_timeout_seconds <= 0 or inactivity_timeout_seconds <= 0:
        raise HarnessError("Codex timeout thresholds must be positive")
    if process.stdout is None:
        raise HarnessError("Codex runner stdout pipe is unavailable")
    started = monotonic()
    last_activity = started
    pending = b""
    capture = capture or StreamCapture()
    with trace_path.open("wb") as trace_file:
        while True:
            now = monotonic()
            total_remaining = total_timeout_seconds - (now - started)
            inactivity_remaining = inactivity_timeout_seconds - (now - last_activity)
            if total_remaining <= 0:
                stop_group(process, process_group_id)
                raise HarnessError(
                    f"codex runner total timeout after {total_timeout_seconds:g} seconds; "
                    f"partial trace preserved at {trace_path}"
                )
            if inactivity_remaining <= 0:
                stop_group(process, process_group_id)
                raise HarnessError(
                    "codex runner inactivity timeout after "
                    f"{inactivity_timeout_seconds:g} seconds; partial trace preserved at "
                    f"{trace_path}"
                )
            readable, _, _ = wait_for_readable(
                [process.stdout], [], [], min(total_remaining, inactivity_remaining)
            )
            if not readable:
                continue
            chunk = process.stdout.read1(64 * 1024)
            if not chunk:
                return process.wait()
            trace_file.write(chunk)
            trace_file.flush()
            capture.update(chunk)
            pending += chunk
            while b"\n" in pending:
                raw_line, pending = pending.split(b"\n", 1)
                try:
                    event = json.loads(raw_line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if is_structurally_valid_codex_event(event):
                    last_activity = monotonic()
                    if event["type"] == "thread.started":
                        auth_copy.unlink(missing_ok=True)


def bind_executor_output(path: Path, output: str) -> None:
    expected = output.encode()
    if path.exists():
        if path.read_bytes() != expected:
            raise HarnessError(f"streamed executor output drifted: {path}")
    else:
        path.write_bytes(expected)


def execute_codex(
    command: list[str],
    prompt: str,
    repo: Path,
    *,
    trace_path: Path,
    stderr_path: Path,
    trace_stream_path: Path,
    stderr_stream_path: Path,
    total_timeout_seconds: float,
    inactivity_timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    try:
        profile = Path(command[command.index("-f") + 1])
        env_start = command.index("-i") + 1
    except (ValueError, IndexError) as exc:
        raise HarnessError("Codex command is missing its isolated environment") from exc
    sentinel_entries = [
        item.split("=", 1)[1]
        for item in command[env_start:]
        if item.startswith(f"{EXTERNAL_SENTINEL_ENV}=")
    ]
    if len(sentinel_entries) != 1:
        raise HarnessError("Codex command is missing its external sentinel binding")
    environment = runner_environment(profile, Path(sentinel_entries[0]))
    if command[env_start:env_start + len(environment)] != environment:
        raise HarnessError("Codex command environment is not the fixed allowlist")
    child_env = dict(item.split("=", 1) for item in environment)
    state_home = Path(child_env["CODEX_HOME"])
    auth_copy = state_home / "auth.json"
    process: subprocess.Popen[bytes] | None = None
    process_group_id: int | None = None
    capture = StreamCapture()
    execution_error: BaseException | None = None
    cleanup_error: BaseException | None = None
    returncode: int | None = None
    try:
        with tempfile.TemporaryFile(mode="w+b") as prompt_file, stderr_stream_path.open(
            "w+b"
        ) as stderr_file:
            prompt_file.write(prompt.encode())
            prompt_file.seek(0)
            process = subprocess.Popen(
                command, cwd=repo, stdin=prompt_file, stdout=subprocess.PIPE,
                stderr=stderr_file, text=False, env=child_env, start_new_session=True,
            )
            process_group_id = process.pid
            try:
                actual_process_group_id = os.getpgid(process.pid)
            except ProcessLookupError as exc:
                process.wait()
                process_group_id = None
                raise HarnessError("Codex runner exited before process-group setup") from exc
            if actual_process_group_id != process_group_id:
                process.kill()
                process.wait()
                process_group_id = None
                raise HarnessError("Codex runner did not start in an isolated process group")
            try:
                returncode = monitor_codex_process(
                    process,
                    trace_stream_path,
                    auth_copy,
                    total_timeout_seconds=total_timeout_seconds,
                    inactivity_timeout_seconds=inactivity_timeout_seconds,
                    process_group_id=process_group_id,
                    capture=capture,
                )
            except BaseException as exc:
                execution_error = exc
            finally:
                try:
                    stop_process_group(process, process_group_id)
                except BaseException as exc:
                    cleanup_error = exc
            stderr_file.flush()
        publish_captured_stream(trace_stream_path, trace_path, capture)
        stderr_capture = StreamCapture()
        stderr_capture.update(stderr_stream_path.read_bytes())
        publish_captured_stream(stderr_stream_path, stderr_path, stderr_capture)
        if cleanup_error is not None:
            raise cleanup_error from execution_error
        if execution_error is not None:
            raise execution_error.with_traceback(execution_error.__traceback__)
        if returncode is None:
            raise HarnessError("Codex runner ended without a return code")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
        stdout = trace_path.read_text(encoding="utf-8")
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)
    finally:
        auth_copy.unlink(missing_ok=True)
        if process is not None and process_group_id is not None:
            stop_process_group(process, process_group_id)
        if process is not None and process.stdout is not None:
            process.stdout.close()


def runner_identity() -> dict[str, str]:
    try:
        path = BUNDLED_CODEX.resolve(strict=True)
    except FileNotFoundError as exc:
        raise HarnessError(f"bundled Codex is unavailable: {BUNDLED_CODEX}") from exc
    if path != BUNDLED_CODEX or not path.is_file() or not os.access(path, os.X_OK):
        raise HarnessError("bundled Codex path must be the executable inside ChatGPT.app")
    result = subprocess.run(
        [str(path), "--version"], capture_output=True, text=True, check=False
    )
    version = result.stdout.strip()
    if result.returncode or not version:
        raise HarnessError("bundled Codex --version failed")
    return {"path": str(path), "version": version, "sha256": sha256_file(path)}


def seatbelt_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace('"', '\\"')


def sandbox_profile(stage_root: Path) -> str:
    stage_root = stage_root.resolve()
    traversal_rules = "".join(
        f'(allow file-read-metadata (literal "{seatbelt_path(path)}"))\n'
        for path in (STAGE_ROOT, stage_root.parent)
    )
    existing = {
        path.name for path in stage_root.parent.iterdir() if path.is_dir()
    } if stage_root.parent.is_dir() else set()
    sibling_names = sorted(
        (set((*ARM_NAMES, PREFLIGHT_ARM, SIBLING_PROBE, COMPARISON_CONTROL)) | existing)
        - {stage_root.name}
    )
    sibling_rules = "".join(
        f'(deny file-read* file-write* (subpath "{seatbelt_path(stage_root.parent / name)}"))\n'
        for name in sibling_names
    )
    return (
        '(version 1)\n(allow default)\n'
        '(deny file-read* file-write* (subpath "/Users/fromdarkness"))\n'
        '(deny file-read* file-write* (subpath "/Volumes"))\n'
        '(deny file-read* file-write* (subpath "/private/tmp"))\n'
        f"{traversal_rules}"
        f'(allow file-read* file-write* (subpath "{seatbelt_path(stage_root)}"))\n'
        f"{sibling_rules}"
    )


def runner_environment(profile: Path, external_sentinel: Path | None = None) -> list[str]:
    state_root = profile.parent / "codex-state"
    state_home = state_root / "home"
    if external_sentinel is None:
        stage_candidates = [
            parent for parent in profile.parents
            if parent.name in set((*ARM_NAMES, PREFLIGHT_ARM))
        ]
        if len(stage_candidates) != 1:
            raise HarnessError("runner profile is not nested under one canonical stage")
        external_sentinel = Path(
            ensure_external_sentinel(stage_candidates[0].parent)["path"]
        )
    return [
        f"CODEX_HOME={state_home}",
        f"HOME={state_home}",
        f"TMPDIR={profile.parent / 'tmp'}",
        f"{EXTERNAL_SENTINEL_ENV}={external_sentinel}",
        "PATH=/usr/bin:/bin",
        "LANG=en_US.UTF-8",
        "LC_ALL=en_US.UTF-8",
        "TERM=dumb",
    ]


def codex_command(
    repo: Path, profile: Path, external_sentinel: Path | None = None
) -> list[str]:
    state_root = profile.parent / "codex-state"
    return [
        str(SANDBOX_EXEC), "-f", str(profile), "/usr/bin/env", "-i",
        *runner_environment(profile, external_sentinel), str(BUNDLED_CODEX), "exec", "--json",
        "--ephemeral", "--ignore-user-config", "--strict-config", "--model",
        "gpt-5.6-sol", "--config", 'model_reasoning_effort="xhigh"',
        "--config", f'sqlite_home="{state_root}"',
        "--config", f'log_dir="{state_root / "logs"}"',
        "--dangerously-bypass-approvals-and-sandbox",
        "--cd", str(repo), "-",
    ]


def prepare_codex_state(profile: Path) -> Path:
    state_home = profile.parent / "codex-state/home"
    state_home.mkdir(parents=True, exist_ok=True)
    (profile.parent / "tmp").mkdir(mode=0o700)
    if CODEX_AUTH.is_symlink() or not CODEX_AUTH.is_file():
        raise HarnessError("bundled Codex authentication file is unavailable")
    auth_copy = state_home / "auth.json"
    if auth_copy.exists() or auth_copy.is_symlink():
        raise HarnessError("isolated Codex authentication copy already exists")
    fd = os.open(auth_copy, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as target, CODEX_AUTH.open("rb") as source:
            shutil.copyfileobj(source, target)
    except Exception:
        auth_copy.unlink(missing_ok=True)
        raise
    return auth_copy


def validate_runner_preflight(path: Path, *, check_binary: bool = True) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise HarnessError("runner preflight must be a regular evaluator artifact")
    data = json.loads(path.read_text(encoding="utf-8"))
    fields = {
        "schema_version", "binary_path", "binary_version", "binary_sha256",
        "arm_timeout_policy", "smoke",
    }
    if "comparison_binding" in data:
        fields.add("comparison_binding")
    smoke_fields = {
        "command", "environment", "prompt_sha256", "profile", "profile_sha256", "trace",
        "trace_sha256", "stderr", "stderr_sha256", "exit_code", "timeout_policy",
    }
    if not isinstance(data, dict) or set(data) != fields or data["schema_version"] != SCHEMA_VERSION:
        raise HarnessError("runner preflight fields are not exact")
    identity = {
        "path": data["binary_path"], "version": data["binary_version"],
        "sha256": data["binary_sha256"],
    }
    if (
        not isinstance(identity["path"], str)
        or Path(identity["path"]) != BUNDLED_CODEX
        or not isinstance(identity["version"], str)
        or not identity["version"].strip()
        or not is_digest(identity["sha256"])
        or data["arm_timeout_policy"] != ARM_TIMEOUT_POLICY
        or not isinstance(data["smoke"], dict)
        or set(data["smoke"]) != smoke_fields
    ):
        raise HarnessError("runner preflight identity or smoke fields are invalid")
    smoke = data["smoke"]
    command = smoke["command"]
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise HarnessError("runner preflight command is invalid")
    try:
        repo = Path(command[command.index("--cd") + 1])
        profile_path = Path(command[command.index("-f") + 1])
    except (AttributeError, ValueError, IndexError) as exc:
        raise HarnessError("runner preflight command is invalid") from exc
    profile, trace, stderr = smoke["profile"], smoke["trace"], smoke["stderr"]
    sentinel_entries = [
        item.split("=", 1)[1] for item in smoke["environment"]
        if isinstance(item, str) and item.startswith(f"{EXTERNAL_SENTINEL_ENV}=")
    ] if isinstance(smoke["environment"], list) else []
    if len(sentinel_entries) != 1:
        raise HarnessError("runner preflight sentinel environment is invalid")
    external_sentinel = Path(sentinel_entries[0])
    if (
        command != codex_command(repo, profile_path, external_sentinel)
        or smoke["environment"] != runner_environment(profile_path, external_sentinel)
        or not all(isinstance(value, str) for value in (profile, trace, stderr))
        or profile != sandbox_profile(repo.parent)
        or smoke["profile_sha256"] != sha256_bytes(profile.encode())
        or smoke["prompt_sha256"] != sha256_bytes(PREFLIGHT_PROMPT.encode())
        or smoke["trace_sha256"] != sha256_bytes(trace.encode())
        or smoke["stderr_sha256"] != sha256_bytes(stderr.encode())
        or smoke["timeout_policy"] != PREFLIGHT_TIMEOUT_POLICY
        or isinstance(smoke["exit_code"], bool)
        or smoke["exit_code"] != 0
    ):
        raise HarnessError("runner preflight smoke evidence is invalid")
    validate_runner_trace(trace.encode())
    if check_binary and runner_identity() != identity:
        raise HarnessError("bundled Codex identity drifted from runner preflight")
    if "comparison_binding" in data:
        binding = data["comparison_binding"]
        if (
            not isinstance(binding, dict)
            or set(binding) != {"comparison_manifest_sha256", "evaluator_identity"}
            or not is_digest(binding.get("comparison_manifest_sha256"))
        ):
            raise HarnessError("runner preflight comparison binding is invalid")
        validate_evaluator_identity(binding["evaluator_identity"], recompute=False)
    return data


def preflight_runner(output: Path, comparison_manifest: Path | None = None) -> Path:
    identity = runner_identity()
    comparison = (
        validate_comparison_manifest(comparison_manifest, recompute_packages=True)
        if comparison_manifest is not None
        else None
    )
    binding = binding_from_comparison(comparison) if comparison is not None else None
    with tempfile.TemporaryDirectory(
        prefix="deliver-eval-preflight-", dir=STAGE_ROOT
    ) as temporary:
        root = Path(temporary)
        stage_root = root / PREFLIGHT_ARM
        stage_root.mkdir()
        ensure_sibling_probe(stage_root)
        sentinel_binding = (
            comparison["external_sentinel"]
            if comparison is not None
            else ensure_external_sentinel(root)
        )
        external_sentinel = Path(sentinel_binding["path"])
        repo, profile_path = stage_root / "repo", stage_root / "runner.sb"
        repo.mkdir()
        run(["git", "init", "-q", "-b", "eval"], cwd=repo)
        profile = sandbox_profile(stage_root)
        profile_path.write_text(profile, encoding="utf-8")
        trace_path, stderr_path = stage_root / "trace.jsonl", stage_root / "stderr.txt"
        trace_stream_path, stderr_stream_path = parent_stream_paths(
            stage_root, "preflight"
        )
        auth_copy = prepare_codex_state(profile_path)
        try:
            command = codex_command(repo, profile_path, external_sentinel)
            result = execute_codex(
                command,
                PREFLIGHT_PROMPT,
                repo,
                trace_path=trace_path,
                stderr_path=stderr_path,
                trace_stream_path=trace_stream_path,
                stderr_stream_path=stderr_stream_path,
                total_timeout_seconds=PREFLIGHT_TIMEOUT_POLICY["total_seconds"],
                inactivity_timeout_seconds=PREFLIGHT_TIMEOUT_POLICY["inactivity_seconds"],
            )
        finally:
            auth_copy.unlink(missing_ok=True)
        bind_executor_output(trace_path, result.stdout)
        bind_executor_output(stderr_path, result.stderr)
        if result.returncode:
            raise HarnessError(
                f"bundled Codex preflight failed with exit {result.returncode}: {result.stderr}"
            )
        validate_runner_trace(result.stdout.encode())
        verify_external_sentinel(
            sentinel_binding,
            Path(comparison["runtime_root"]) if comparison is not None else root,
        )
        artifact = {
            "schema_version": SCHEMA_VERSION,
            "binary_path": identity["path"],
            "binary_version": identity["version"],
            "binary_sha256": identity["sha256"],
            "arm_timeout_policy": ARM_TIMEOUT_POLICY,
            "smoke": {
                "command": command, "prompt_sha256": sha256_bytes(PREFLIGHT_PROMPT.encode()),
                "environment": runner_environment(profile_path, external_sentinel),
                "profile": profile, "profile_sha256": sha256_bytes(profile.encode()),
                "trace": result.stdout, "trace_sha256": sha256_bytes(result.stdout.encode()),
                "stderr": result.stderr, "stderr_sha256": sha256_bytes(result.stderr.encode()),
                "exit_code": result.returncode,
                "timeout_policy": PREFLIGHT_TIMEOUT_POLICY,
            },
        }
        if binding is not None:
            artifact["comparison_binding"] = binding
    write_json(output, artifact)
    validate_runner_preflight(output, check_binary=False)
    return output


def rollback_new_runner_artifacts(path: Path, boundary: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or not path.is_dir() or path == boundary:
        raise HarnessError("runner setup rollback path is invalid")
    try:
        path.relative_to(boundary)
    except ValueError as exc:
        raise HarnessError("runner setup rollback escaped its boundary") from exc
    shutil.rmtree(path)
    parent = path.parent
    while parent != boundary:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def run_scenario(stage_root: Path, phase: str) -> Path:
    stage_root = require_stage_root(stage_root)
    ensure_sibling_probe(stage_root)
    comparison_manifest = comparison_for_stage(stage_root)
    comparison = (
        validate_comparison_manifest(comparison_manifest)
        if comparison_manifest is not None
        else None
    )
    sentinel_binding = (
        comparison["external_sentinel"]
        if comparison is not None
        else ensure_external_sentinel(stage_root.parent)
    )
    external_sentinel = Path(sentinel_binding["path"])
    prompt, manifest = assemble_runner_prompt(stage_root, phase)
    preflight_path = safe_path(stage_root, "evidence/runner-preflight.json")
    preflight = validate_runner_preflight(preflight_path)
    arm_attempt: int | None = None
    attempt_action: str | None = None
    attempt_input: str | None = None
    comparison_state: dict[str, Any] | None = None
    if comparison_manifest is not None:
        binding = binding_from_comparison(comparison)
        if preflight.get("comparison_binding") != binding:
            raise HarnessError("runner phase belongs to a different comparison")
        repo_for_input = safe_path(stage_root, "repo")
        initial = manifest["initial_snapshot"]["commit"]
        code_diff, test_diff = repository_diffs(repo_for_input, initial)
        attempt_input = sha256_bytes(canonical_json({
            "comparison_binding": binding,
            "runner_preflight_sha256": sha256_file(preflight_path),
            "runner_manifest_sha256": sha256_file(stage_root / "runner-manifest.json"),
            "arm_name": stage_root.name,
            "phase": phase,
            "head": run(["git", "rev-parse", "HEAD"], cwd=repo_for_input).strip(),
            "status": run(
                ["git", "status", "--short", "--untracked-files=all"],
                cwd=repo_for_input,
            ),
            "implementation_diff_sha256": sha256_bytes(code_diff.encode()),
            "test_diff_sha256": sha256_bytes(test_diff.encode()),
        }))
        comparison_state = validate_attempt_state(
            comparison_manifest, _comparison=comparison
        )["state"]
        arm_state = comparison_state["arms"][stage_root.name]
        if arm_state["status"] in {"pending", "interrupted"}:
            arm_attempt = len(arm_state["attempts"]) + 1
            attempt_action = "begin"
        elif arm_state["status"] == "running" and arm_state["attempts"]:
            arm_attempt = arm_state["attempts"][-1]["attempt"]
            attempt_action = "bind"
        else:
            raise HarnessError("runner phase requires an active or restartable arm")
    identity = {
        "path": preflight["binary_path"], "version": preflight["binary_version"],
        "sha256": preflight["binary_sha256"],
    }
    repo = safe_path(stage_root, "repo")
    elapsed_before_milliseconds = 0
    if phase == "remediation":
        prior = validate_runner_bundles(
            runner_paths(
                stage_root, phases=("pre-packet",),
                _comparison=comparison, _state=comparison_state,
            ),
            phases=("pre-packet",),
            repo=repo,
            stage_root=stage_root,
        )
        elapsed_before_milliseconds = prior["pre-packet"]["metadata"][
            "duration_milliseconds"
        ]
    remaining_milliseconds = (
        ARM_TIMEOUT_POLICY["arm_total_seconds"] * 1000
        - elapsed_before_milliseconds
    )
    if remaining_milliseconds <= 0:
        raise HarnessError("codex runner arm total timeout before phase start")
    profile_text = sandbox_profile(stage_root)
    runner_root = stage_root / "runner"
    if arm_attempt is not None:
        runner_root = runner_root / f"attempt-{arm_attempt}"
    runner_root = runner_root / phase
    if runner_root.exists():
        raise HarnessError(f"runner phase artifacts already exist: {phase}")
    stream_root: Path | None = None
    auth_copy: Path | None = None
    attempt_registered = comparison_manifest is None
    try:
        runner_root.mkdir(parents=True)
        trace_stream_path, stderr_stream_path = parent_stream_paths(
            stage_root, phase, arm_attempt
        )
        stream_root = trace_stream_path.parent
        profile = runner_root / RUNNER_FILES["profile"]
        profile.write_text(profile_text, encoding="utf-8")
        auth_copy = prepare_codex_state(profile)
        command = codex_command(repo, profile, external_sentinel)
        (runner_root / "prompt.txt").write_text(prompt, encoding="utf-8")
        (runner_root / "input-manifest.json").write_bytes(
            (stage_root / "runner-manifest.json").read_bytes()
        )
        trace = runner_root / RUNNER_FILES["trace"]
        stderr = runner_root / RUNNER_FILES["stderr"]
        if comparison_manifest is not None:
            if attempt_action == "begin":
                registered_attempt = begin_arm_attempt(
                    comparison_manifest, stage_root.name, attempt_input, phase,
                    _comparison=comparison,
                )["attempt"]
            else:
                registered_attempt = bind_arm_phase_input(
                    comparison_manifest, stage_root.name, phase, attempt_input,
                    _comparison=comparison,
                )
            attempt_registered = True
            if registered_attempt != arm_attempt:
                raise HarnessError("runner setup attempt no longer matches locked state")
        started = time.monotonic_ns()
        result = execute_codex(
            command,
            prompt,
            repo,
            trace_path=trace,
            stderr_path=stderr,
            trace_stream_path=trace_stream_path,
            stderr_stream_path=stderr_stream_path,
            total_timeout_seconds=remaining_milliseconds / 1000,
            inactivity_timeout_seconds=ARM_TIMEOUT_POLICY["inactivity_seconds"],
        )
    except BaseException:
        if not attempt_registered:
            rollback_new_runner_artifacts(runner_root, stage_root / "runner")
            if stream_root is not None:
                stream_boundary = (
                    stream_root.parents[1]
                    if arm_attempt is not None else stream_root.parent
                )
                rollback_new_runner_artifacts(stream_root, stream_boundary)
        raise
    finally:
        if auth_copy is not None:
            auth_copy.unlink(missing_ok=True)
    ensure_sibling_probe(stage_root)
    verify_external_sentinel(sentinel_binding, stage_root.parent)
    duration_milliseconds = max(1, math.ceil((time.monotonic_ns() - started) / 1_000_000))
    bind_executor_output(trace, result.stdout)
    bind_executor_output(stderr, result.stderr)
    if elapsed_before_milliseconds + duration_milliseconds > (
        ARM_TIMEOUT_POLICY["arm_total_seconds"] * 1000
    ):
        raise HarnessError("codex runner arm total timeout after phase completion")
    validate_runner_trace(trace.read_bytes())
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "phase": phase,
        "command": command,
        "environment": runner_environment(profile, external_sentinel),
        "model": "gpt-5.6-sol",
        "reasoning": "xhigh",
        "execution_boundary": "outer_sandbox_only",
        "prompt_sha256": sha256_bytes(prompt.encode()),
        "input_manifest_sha256": sha256_file(stage_root / "runner-manifest.json"),
        "initial_snapshot": manifest["initial_snapshot"],
        "exit_code": result.returncode,
        "trace_sha256": sha256_file(trace),
        "stderr_sha256": sha256_file(stderr),
        "profile_sha256": sha256_file(profile),
        "runner_preflight_sha256": sha256_file(preflight_path),
        "runner_binary_path": identity["path"],
        "runner_binary_version": identity["version"],
        "runner_binary_sha256": identity["sha256"],
        "duration_milliseconds": duration_milliseconds,
        "timeout_policy": ARM_TIMEOUT_POLICY,
        "arm_elapsed_before_milliseconds": elapsed_before_milliseconds,
    }
    if "comparison_binding" in preflight:
        metadata["comparison_binding"] = preflight["comparison_binding"]
        metadata["arm_attempt"] = arm_attempt
    write_json(runner_root / "metadata.json", metadata)
    if result.returncode:
        raise HarnessError(f"codex runner failed with exit {result.returncode}")
    return trace


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    initialize = commands.add_parser("initialize-comparison")
    initialize.add_argument("--runtime-root", type=Path, required=True)
    initialize.add_argument("--baseline-package", type=Path, required=True)
    initialize.add_argument("--candidate-package", type=Path, required=True)
    initialize.add_argument("--comparison-id")

    prepare = commands.add_parser("prepare")
    prepare.add_argument("--scenario", required=True)
    prepare.add_argument("--contract", type=Path, required=True)
    prepare.add_argument("--destination", type=Path, required=True)
    prepare.add_argument("--runner-preflight", type=Path, required=True)
    prepare.add_argument("--comparison-manifest", type=Path)

    preflight = commands.add_parser("preflight-runner")
    preflight.add_argument("--output", type=Path, required=True)
    preflight.add_argument("--comparison-manifest", type=Path)

    verify = commands.add_parser("verify-manifest")
    verify.add_argument("stage_root", type=Path)

    freeze = commands.add_parser("freeze-pre-packet")
    freeze.add_argument("stage_root", type=Path)
    freeze.add_argument("--validation", type=Path, required=True)

    packet = commands.add_parser("stage-review-packet")
    packet.add_argument("stage_root", type=Path)

    finalize = commands.add_parser("finalize-arm")
    finalize.add_argument("stage_root", type=Path)
    finalize.add_argument("--record", type=Path, required=True)

    runner = commands.add_parser("run-scenario")
    runner.add_argument("stage_root", type=Path)
    runner.add_argument("--phase", choices=("pre-packet", "remediation"), required=True)

    normalize = commands.add_parser("normalize")
    normalize.add_argument("output_freeze", type=Path)
    normalize.add_argument("--output", type=Path, required=True)
    normalize.add_argument("--comparison-manifest", type=Path)

    blind = commands.add_parser("blind-packet")
    blind.add_argument("runs", type=Path, nargs="+")
    blind.add_argument("--output", type=Path, required=True)
    blind.add_argument("--comparison-manifest", type=Path)

    interruption = commands.add_parser("record-external-interruption")
    interruption.add_argument("--comparison-manifest", type=Path, required=True)
    interruption.add_argument("--arm", choices=OFFICIAL_ARM_ORDER, required=True)
    interruption.add_argument("--phase", choices=RUNNER_PHASES, required=True)
    interruption.add_argument("--reason", required=True)

    begin_judge = commands.add_parser("begin-judge")
    begin_judge.add_argument("--comparison-manifest", type=Path, required=True)
    begin_judge.add_argument("--blind-packet", type=Path, required=True)

    judge_interruption = commands.add_parser("record-judge-interruption")
    judge_interruption.add_argument("--comparison-manifest", type=Path, required=True)
    judge_interruption.add_argument("--reason", required=True)

    judge = commands.add_parser("freeze-judge")
    judge.add_argument("--comparison-manifest", type=Path, required=True)
    judge.add_argument("--blind-packet", type=Path, required=True)
    judge.add_argument("--decision", type=Path, required=True)
    judge.add_argument("--output", type=Path, required=True)

    reveal = commands.add_parser("reveal-identities")
    reveal.add_argument("--comparison-manifest", type=Path, required=True)
    reveal.add_argument("--blind-packet", type=Path, required=True)
    reveal.add_argument("--judge-record", type=Path, required=True)
    reveal.add_argument("--output", type=Path, required=True)

    compliance = commands.add_parser("check-candidate-compliance")
    compliance.add_argument("report", type=Path)
    compliance.add_argument("--output", type=Path, required=True)
    compliance.add_argument("--comparison-manifest", type=Path)
    compliance.add_argument("--identity-reveal", type=Path)
    compliance.add_argument("--blind-packet", type=Path)
    compliance.add_argument("--judge-record", type=Path)

    outcomes = commands.add_parser("gate-outcomes")
    outcomes.add_argument("--baseline", type=Path, nargs=2, required=True)
    outcomes.add_argument("--candidate", type=Path, nargs=2, required=True)
    outcomes.add_argument("--output", type=Path, required=True)

    official_gate = commands.add_parser("gate-official")
    official_gate.add_argument("--comparison-manifest", type=Path, required=True)
    official_gate.add_argument("--baseline", type=Path, nargs=2, required=True)
    official_gate.add_argument("--candidate", type=Path, nargs=2, required=True)
    official_gate.add_argument("--blind-packet", type=Path, required=True)
    official_gate.add_argument("--judge-record", type=Path, required=True)
    official_gate.add_argument("--identity-reveal", type=Path, required=True)
    official_gate.add_argument("--candidate-compliance", type=Path, required=True)
    official_gate.add_argument("--output", type=Path, required=True)

    final = commands.add_parser("freeze-final-verdict")
    final.add_argument("--comparison-manifest", type=Path, required=True)
    final.add_argument("--outcome-gate", type=Path)
    final.add_argument("--judge-record", type=Path)
    final.add_argument("--candidate-compliance", type=Path)
    final.add_argument("--failure-evidence", type=Path)
    final.add_argument("--baseline", type=Path, nargs=2)
    final.add_argument("--candidate", type=Path, nargs=2)
    final.add_argument("--blind-packet", type=Path)
    final.add_argument("--identity-reveal", type=Path)
    final.add_argument("--output", type=Path, required=True)

    replay = commands.add_parser("validate-final-verdict")
    replay.add_argument("--comparison-manifest", type=Path, required=True)

    cleanup = commands.add_parser("cleanup-comparison")
    cleanup.add_argument("--comparison-manifest", type=Path, required=True)

    commands.add_parser("validate-ledger")
    return root


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == "initialize-comparison":
        print(initialize_comparison(
            arguments.runtime_root, arguments.baseline_package,
            arguments.candidate_package, comparison_id=arguments.comparison_id,
        ))
    elif arguments.command == "prepare":
        print(json.dumps(prepare_scenario(
            arguments.scenario, arguments.contract, arguments.destination,
            arguments.runner_preflight, arguments.comparison_manifest,
        ), sort_keys=True))
    elif arguments.command == "preflight-runner":
        print(preflight_runner(arguments.output, arguments.comparison_manifest))
    elif arguments.command == "verify-manifest":
        verify_manifest(arguments.stage_root)
    elif arguments.command == "freeze-pre-packet":
        print(freeze_pre_packet(arguments.stage_root, arguments.validation))
    elif arguments.command == "stage-review-packet":
        stage_review_packet(arguments.stage_root)
    elif arguments.command == "finalize-arm":
        print(finalize_arm(arguments.stage_root, arguments.record))
    elif arguments.command == "run-scenario":
        print(run_scenario(arguments.stage_root, arguments.phase))
    elif arguments.command == "normalize":
        write_json(arguments.output, normalize_run(
            arguments.output_freeze, arguments.comparison_manifest
        ))
    elif arguments.command == "blind-packet":
        write_json(arguments.output, build_blind_packet(
            arguments.runs, arguments.comparison_manifest
        ))
    elif arguments.command == "record-external-interruption":
        record_external_interruption(
            arguments.comparison_manifest, arguments.arm, arguments.reason,
            arguments.phase,
        )
    elif arguments.command == "begin-judge":
        begin_judge_attempt(
            arguments.comparison_manifest, sha256_file(arguments.blind_packet)
        )
    elif arguments.command == "record-judge-interruption":
        record_judge_interruption(arguments.comparison_manifest, arguments.reason)
    elif arguments.command == "freeze-judge":
        freeze_judge_record(
            arguments.comparison_manifest, arguments.blind_packet,
            arguments.decision, arguments.output,
        )
    elif arguments.command == "reveal-identities":
        write_json(arguments.output, reveal_identities(
            arguments.comparison_manifest, arguments.blind_packet,
            arguments.judge_record,
        ))
    elif arguments.command == "check-candidate-compliance":
        bound_values = (
            arguments.comparison_manifest, arguments.identity_reveal,
            arguments.blind_packet, arguments.judge_record,
        )
        if any(value is None for value in bound_values) and any(
            value is not None for value in bound_values
        ):
            raise HarnessError("bound compliance requires the complete revealed chain")
        result = (
            check_candidate_compliance_bound(
                arguments.comparison_manifest, arguments.report,
                arguments.identity_reveal, arguments.blind_packet,
                arguments.judge_record,
            )
            if arguments.comparison_manifest is not None
            else check_candidate_compliance(arguments.report)
        )
        write_json(arguments.output, result)
        if not result["compliant"]:
            return 1
    elif arguments.command == "gate-outcomes":
        result = gate_outcomes(arguments.baseline, arguments.candidate)
        write_json(arguments.output, result)
        if not result["passed"]:
            return 1
    elif arguments.command == "gate-official":
        result = gate_official_outcomes(
            arguments.comparison_manifest, arguments.baseline, arguments.candidate,
            arguments.blind_packet, arguments.judge_record, arguments.identity_reveal,
            arguments.candidate_compliance,
        )
        write_json(arguments.output, result)
        if not result["passed"]:
            return 1
    elif arguments.command == "freeze-final-verdict":
        result = freeze_final_verdict(
            arguments.comparison_manifest, arguments.outcome_gate,
            arguments.judge_record, arguments.candidate_compliance,
            failure_evidence_path=arguments.failure_evidence,
            baseline_paths=arguments.baseline,
            candidate_paths=arguments.candidate,
            blind_packet_path=arguments.blind_packet,
            reveal_path=arguments.identity_reveal,
        )
        write_json(arguments.output, result)
        if not result["merge_ready"]:
            return 1
    elif arguments.command == "validate-final-verdict":
        validate_final_verdict(arguments.comparison_manifest)
    elif arguments.command == "cleanup-comparison":
        cleanup_comparison(arguments.comparison_manifest)
    elif arguments.command == "validate-ledger":
        validate_ledger()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
