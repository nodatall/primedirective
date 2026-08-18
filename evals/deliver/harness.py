#!/usr/bin/env python3
"""Deterministic preparation and evaluator-side checks for the Deliver eval."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
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
INHERITED_SENTINEL = "DELIVER_EVAL_INHERITED_SENTINEL"
FIRST_TOOL_GATE_OUTPUT = "deliver-eval-first-tool-gate-ok"
FIRST_TOOL_GATE_COMMAND = (
    '/bin/test ! -e "$CODEX_HOME/auth.json" && '
    f'/bin/test -z "${{{INHERITED_SENTINEL}+x}}" && '
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


class HarnessError(RuntimeError):
    """Raised when an eval isolation or evidence invariant is violated."""


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
                child.name not in set((*ARM_NAMES, SIBLING_PROBE))
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
    scenario_id: str, contract: Path, destination: Path, runner_preflight: Path
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
    return {"head": head, "tree": initial_snapshot["tree"], "fixture_source": fixture_source}


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
        except json.JSONDecodeError as exc:
            raise HarnessError(f"trace line {number} is not JSON") from exc
        if not isinstance(event, dict):
            raise HarnessError(f"trace line {number} must be a JSON object")
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


def runner_paths(stage_root: Path, phases: tuple[str, ...] = RUNNER_PHASES) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for phase in phases:
        root, prefix = safe_path(stage_root, Path("runner") / phase), phase.replace("-", "_")
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
        "runner_binary_sha256",
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
        if (
            command != codex_command(expected_repo, expected_profile)
            or metadata["environment"] != runner_environment(expected_profile)
            or actual != fixed
            or actual_identity != identity
            or metadata["runner_preflight_sha256"] != expected_preflight
        ):
            raise HarnessError(f"{phase} runner metadata violates fixed conditions")
        duration = metadata["duration_milliseconds"]
        if isinstance(duration, bool) or not isinstance(duration, int) or duration < 1:
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
    if not isinstance(seal, dict) or set(seal) != {"schema_version", "event", "output_freeze_sha256", "phase_bindings"}:
        raise HarnessError("evaluator terminal seal fields are not exact")
    if (
        seal["schema_version"] != SCHEMA_VERSION
        or seal["event"] != TERMINAL_SEAL_EVENT
        or seal["output_freeze_sha256"] != sha256_file(output_freeze)
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
    manifest = verify_manifest(stage_root, allow_repo_changes=True)
    if manifest["scenario_stage"] != "review_packet":
        raise HarnessError("arm finalization requires the staged review packet")
    if record.is_symlink() or not record.is_file():
        raise HarnessError("run record must be a regular evaluator input")
    current_manifest = stage_root / "runner-manifest.json"
    repo = safe_path(stage_root, "repo")
    snapshot_data = validate_pre_packet_snapshot(stage_root, manifest)
    runner_sources = runner_paths(stage_root)
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
    write_json(evaluator_root / "terminal-seal.json", seal)
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
    if not isinstance(freeze, dict) or set(freeze) != {
        "schema_version",
        "scenario_id",
        "input_manifest_sha256",
        "initial_snapshot",
        "snapshots",
        "repository_state",
        "artifacts",
    }:
        raise HarnessError("output freeze fields are not exact")
    if freeze["schema_version"] != SCHEMA_VERSION:
        raise HarnessError("output freeze schema version is invalid")
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


def validate_normalized_output(output: object) -> dict[str, Any]:
    if not isinstance(output, dict) or set(output) != {
        "schema_version",
        "scenario_id",
        "snapshots",
        "behavior",
        "measurements",
        "source_hashes",
    }:
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


def normalize_run(output_freeze: Path) -> dict[str, object]:
    freeze, paths = frozen_artifacts(output_freeze)
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
    validate_normalized_output(output)
    assert_identity_blind(output, clues)
    return output


def build_blind_packet(run_paths: list[Path]) -> dict[str, object]:
    if len(run_paths) != 2:
        raise HarnessError("the binary skill review requires exactly two runs")
    runs = [
        validate_normalized_output(json.loads(path.read_text(encoding="utf-8")))
        for path in run_paths
    ]
    ordered = sorted(runs, key=lambda value: sha256_bytes(canonical_json(value)))
    packet = {
        "schema_version": SCHEMA_VERSION,
        "runs": {f"Run {chr(65 + index)}": value for index, value in enumerate(ordered)},
    }
    assert_identity_blind(packet)
    return packet


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


def execute_codex(command: list[str], prompt: str, repo: Path) -> subprocess.CompletedProcess[str]:
    try:
        profile = Path(command[command.index("-f") + 1])
        env_start = command.index("-i") + 1
    except (ValueError, IndexError) as exc:
        raise HarnessError("Codex command is missing its isolated environment") from exc
    environment = runner_environment(profile)
    if command[env_start:env_start + len(environment)] != environment:
        raise HarnessError("Codex command environment is not the fixed allowlist")
    child_env = dict(item.split("=", 1) for item in environment)
    state_home = Path(child_env["CODEX_HOME"])
    auth_copy = state_home / "auth.json"
    stdout: list[str] = []
    process: subprocess.Popen[str] | None = None
    try:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr_file:
            process = subprocess.Popen(
                command, cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=stderr_file, text=True, env=child_env,
            )
            assert process.stdin is not None and process.stdout is not None
            process.stdin.write(prompt)
            process.stdin.close()
            for line in process.stdout:
                stdout.append(line)
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict) and event.get("type") == "thread.started":
                    auth_copy.unlink(missing_ok=True)
            returncode = process.wait()
            stderr_file.seek(0)
            stderr = stderr_file.read()
        return subprocess.CompletedProcess(command, returncode, "".join(stdout), stderr)
    finally:
        auth_copy.unlink(missing_ok=True)
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()


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
    existing = {
        path.name for path in stage_root.parent.iterdir() if path.is_dir()
    } if stage_root.parent.is_dir() else set()
    sibling_names = sorted(
        (set((*ARM_NAMES, PREFLIGHT_ARM, SIBLING_PROBE)) | existing) - {stage_root.name}
    )
    sibling_rules = "".join(
        f'(deny file-read* file-write* (subpath "{seatbelt_path(stage_root.parent / name)}"))\n'
        for name in sibling_names
    )
    return (
        '(version 1)\n(allow default)\n'
        '(deny file-read* file-write* (subpath "/Users/fromdarkness"))\n'
        '(deny file-read* file-write* (subpath "/Volumes"))\n'
        f"{sibling_rules}"
    )


def runner_environment(profile: Path) -> list[str]:
    state_root = profile.parent / "codex-state"
    state_home = state_root / "home"
    return [
        f"CODEX_HOME={state_home}",
        f"HOME={state_home}",
        f"TMPDIR={profile.parent / 'tmp'}",
        "PATH=/usr/bin:/bin",
        "LANG=en_US.UTF-8",
        "LC_ALL=en_US.UTF-8",
        "TERM=dumb",
    ]


def codex_command(repo: Path, profile: Path) -> list[str]:
    state_root = profile.parent / "codex-state"
    return [
        str(SANDBOX_EXEC), "-f", str(profile), "/usr/bin/env", "-i",
        *runner_environment(profile), str(BUNDLED_CODEX), "exec", "--json",
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
    fields = {"schema_version", "binary_path", "binary_version", "binary_sha256", "smoke"}
    smoke_fields = {
        "command", "environment", "prompt_sha256", "profile", "profile_sha256", "trace",
        "trace_sha256", "stderr", "stderr_sha256", "exit_code",
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
    if (
        command != codex_command(repo, profile_path)
        or smoke["environment"] != runner_environment(profile_path)
        or not all(isinstance(value, str) for value in (profile, trace, stderr))
        or profile != sandbox_profile(repo.parent)
        or smoke["profile_sha256"] != sha256_bytes(profile.encode())
        or smoke["prompt_sha256"] != sha256_bytes(PREFLIGHT_PROMPT.encode())
        or smoke["trace_sha256"] != sha256_bytes(trace.encode())
        or smoke["stderr_sha256"] != sha256_bytes(stderr.encode())
        or isinstance(smoke["exit_code"], bool)
        or smoke["exit_code"] != 0
    ):
        raise HarnessError("runner preflight smoke evidence is invalid")
    validate_runner_trace(trace.encode())
    if check_binary and runner_identity() != identity:
        raise HarnessError("bundled Codex identity drifted from runner preflight")
    return data


def preflight_runner(output: Path) -> Path:
    identity = runner_identity()
    with tempfile.TemporaryDirectory(
        prefix="deliver-eval-preflight-", dir=STAGE_ROOT
    ) as temporary:
        root = Path(temporary)
        stage_root = root / PREFLIGHT_ARM
        stage_root.mkdir()
        ensure_sibling_probe(stage_root)
        repo, profile_path = stage_root / "repo", stage_root / "runner.sb"
        repo.mkdir()
        run(["git", "init", "-q", "-b", "eval"], cwd=repo)
        profile = sandbox_profile(stage_root)
        profile_path.write_text(profile, encoding="utf-8")
        auth_copy = prepare_codex_state(profile_path)
        try:
            command = codex_command(repo, profile_path)
            result = execute_codex(command, PREFLIGHT_PROMPT, repo)
        finally:
            auth_copy.unlink(missing_ok=True)
        if result.returncode:
            raise HarnessError(
                f"bundled Codex preflight failed with exit {result.returncode}: {result.stderr}"
            )
        validate_runner_trace(result.stdout.encode())
        artifact = {
            "schema_version": SCHEMA_VERSION,
            "binary_path": identity["path"],
            "binary_version": identity["version"],
            "binary_sha256": identity["sha256"],
            "smoke": {
                "command": command, "prompt_sha256": sha256_bytes(PREFLIGHT_PROMPT.encode()),
                "environment": runner_environment(profile_path),
                "profile": profile, "profile_sha256": sha256_bytes(profile.encode()),
                "trace": result.stdout, "trace_sha256": sha256_bytes(result.stdout.encode()),
                "stderr": result.stderr, "stderr_sha256": sha256_bytes(result.stderr.encode()),
                "exit_code": result.returncode,
            },
        }
    write_json(output, artifact)
    validate_runner_preflight(output, check_binary=False)
    return output


def run_scenario(stage_root: Path, phase: str) -> Path:
    stage_root = require_stage_root(stage_root)
    ensure_sibling_probe(stage_root)
    prompt, manifest = assemble_runner_prompt(stage_root, phase)
    preflight_path = safe_path(stage_root, "evidence/runner-preflight.json")
    preflight = validate_runner_preflight(preflight_path)
    identity = {
        "path": preflight["binary_path"], "version": preflight["binary_version"],
        "sha256": preflight["binary_sha256"],
    }
    repo = safe_path(stage_root, "repo")
    runner_root = stage_root / "runner" / phase
    if runner_root.exists():
        raise HarnessError(f"runner phase artifacts already exist: {phase}")
    runner_root.mkdir(parents=True)
    profile = runner_root / RUNNER_FILES["profile"]
    profile.write_text(sandbox_profile(stage_root), encoding="utf-8")
    auth_copy = prepare_codex_state(profile)
    try:
        command = codex_command(repo, profile)
        (runner_root / "prompt.txt").write_text(prompt, encoding="utf-8")
        (runner_root / "input-manifest.json").write_bytes(
            (stage_root / "runner-manifest.json").read_bytes()
        )
        started = time.monotonic_ns()
        result = execute_codex(command, prompt, repo)
    finally:
        auth_copy.unlink(missing_ok=True)
    ensure_sibling_probe(stage_root)
    duration_milliseconds = max(1, math.ceil((time.monotonic_ns() - started) / 1_000_000))
    trace = runner_root / "trace.jsonl"
    trace.write_text(result.stdout, encoding="utf-8")
    (runner_root / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    validate_runner_trace(trace.read_bytes())
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "phase": phase,
        "command": command,
        "environment": runner_environment(profile),
        "model": "gpt-5.6-sol",
        "reasoning": "xhigh",
        "execution_boundary": "outer_sandbox_only",
        "prompt_sha256": sha256_bytes(prompt.encode()),
        "input_manifest_sha256": sha256_file(stage_root / "runner-manifest.json"),
        "initial_snapshot": manifest["initial_snapshot"],
        "exit_code": result.returncode,
        "trace_sha256": sha256_file(trace),
        "stderr_sha256": sha256_file(runner_root / "stderr.txt"),
        "profile_sha256": sha256_file(profile),
        "runner_preflight_sha256": sha256_file(preflight_path),
        "runner_binary_path": identity["path"],
        "runner_binary_version": identity["version"],
        "runner_binary_sha256": identity["sha256"],
        "duration_milliseconds": duration_milliseconds,
    }
    write_json(runner_root / "metadata.json", metadata)
    if result.returncode:
        raise HarnessError(f"codex runner failed with exit {result.returncode}")
    return trace


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare")
    prepare.add_argument("--scenario", required=True)
    prepare.add_argument("--contract", type=Path, required=True)
    prepare.add_argument("--destination", type=Path, required=True)
    prepare.add_argument("--runner-preflight", type=Path, required=True)

    preflight = commands.add_parser("preflight-runner")
    preflight.add_argument("--output", type=Path, required=True)

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

    blind = commands.add_parser("blind-packet")
    blind.add_argument("runs", type=Path, nargs=2)
    blind.add_argument("--output", type=Path, required=True)

    compliance = commands.add_parser("check-candidate-compliance")
    compliance.add_argument("report", type=Path)
    compliance.add_argument("--output", type=Path, required=True)

    outcomes = commands.add_parser("gate-outcomes")
    outcomes.add_argument("--baseline", type=Path, nargs=2, required=True)
    outcomes.add_argument("--candidate", type=Path, nargs=2, required=True)
    outcomes.add_argument("--output", type=Path, required=True)

    commands.add_parser("validate-ledger")
    return root


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == "prepare":
        print(json.dumps(prepare_scenario(
            arguments.scenario, arguments.contract, arguments.destination,
            arguments.runner_preflight,
        ), sort_keys=True))
    elif arguments.command == "preflight-runner":
        print(preflight_runner(arguments.output))
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
        write_json(arguments.output, normalize_run(arguments.output_freeze))
    elif arguments.command == "blind-packet":
        write_json(arguments.output, build_blind_packet(arguments.runs))
    elif arguments.command == "check-candidate-compliance":
        result = check_candidate_compliance(arguments.report)
        write_json(arguments.output, result)
        if not result["compliant"]:
            return 1
    elif arguments.command == "gate-outcomes":
        result = gate_outcomes(arguments.baseline, arguments.candidate)
        write_json(arguments.output, result)
        if not result["passed"]:
            return 1
    elif arguments.command == "validate-ledger":
        validate_ledger()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
