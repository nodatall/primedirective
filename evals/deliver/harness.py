#!/usr/bin/env python3
"""Deterministic preparation and evaluator-side checks for the Deliver eval."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


SUITE_ROOT = Path(__file__).resolve().parent
SCHEMA_VERSION = 1
DENIED_INPUT_PARTS = {"evaluator", "evaluators", "ledger", "hidden"}
DENIED_INPUT_NAMES = {"outcome-ledger.json", "identity-denylist.txt"}
IDENTITY_DENYLIST = SUITE_ROOT / "evaluator" / "identity-denylist.txt"
OUTCOME_LEDGER = SUITE_ROOT / "evaluator" / "outcome-ledger.json"
FIXED_AUTHOR_DATE = "2000-01-01T00:00:00+00:00"


class HarnessError(RuntimeError):
    """Raised when an eval isolation or evidence invariant is violated."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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


def materialize_git_ref(repo_root: Path, ref: str, destination: Path) -> str:
    resolved = run(["git", "rev-parse", f"{ref}^{{commit}}"], cwd=repo_root).strip()
    tree = run(["git", "rev-parse", f"{resolved}^{{tree}}"], cwd=repo_root).strip()
    listing = subprocess.run(
        ["git", "ls-tree", "-rz", resolved],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout
    for record in listing.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, object_id = metadata.decode().split()
        relative = Path(raw_path.decode("utf-8"))
        reject_evaluator_path(relative)
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
    return f"{resolved}:{tree}"


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


def write_manifest(stage_root: Path, descriptor: dict[str, Any], fixture_source: str, stage: str) -> None:
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": descriptor["id"],
        "scenario_stage": stage,
        "fixture_source": fixture_source,
        "fixed_conditions": descriptor["fixed_conditions"],
        "files": list(iter_manifest_files(stage_root)),
    }
    manifest_path = stage_root / "runner-manifest.json"
    write_json(manifest_path, manifest)
    (stage_root / "runner-manifest.sha256").write_text(
        f"{sha256_file(manifest_path)}  runner-manifest.json\n", encoding="ascii"
    )


def prepare_scenario(scenario_id: str, contract: Path, destination: Path) -> dict[str, str]:
    if destination.exists() and any(destination.iterdir()):
        raise HarnessError(f"destination must be absent or empty: {destination}")
    if contract.is_symlink() or not (contract.is_file() or contract.is_dir()):
        raise HarnessError("contract must be a regular extracted file or package directory")
    destination.mkdir(parents=True, exist_ok=True)
    repo = destination / "repo"
    scenario_destination = destination / "scenario"
    contract_destination = destination / "contract"
    repo.mkdir()
    scenario_destination.mkdir()
    contract_destination.mkdir()

    scenario_root, descriptor = scenario_descriptor(scenario_id)
    fixture = descriptor["fixture"]
    if fixture["kind"] == "directory":
        fixture_root = safe_path(scenario_root, fixture["path"])
        copy_directory(fixture_root, repo)
        frozen_tree = tree_hash(fixture_root)
        if frozen_tree != fixture["tree_sha256"]:
            raise HarnessError("tracked directory fixture drifted from its frozen tree hash")
        fixture_source = f"directory:{fixture['path']}:{frozen_tree}"
    elif fixture["kind"] == "git_ref":
        if fixture["repository"] != "repo_root":
            raise HarnessError("historical git fixtures must name the suite repository root")
        repository = SUITE_ROOT.parents[1]
        fixture_source = f"git:{materialize_git_ref(repository, fixture['ref'], repo)}"
        if fixture_source != f"git:{fixture['resolved_commit']}:{fixture['tree']}" :
            raise HarnessError("pinned historical fixture commit or tree drifted")
    else:
        raise HarnessError(f"unknown fixture kind: {fixture['kind']}")

    for relative_name in descriptor["pre_packet_files"]:
        relative = Path(relative_name)
        source = safe_path(scenario_root, relative)
        target = safe_path(scenario_destination, Path(relative.name), must_exist=False)
        target.write_bytes(source.read_bytes())
    if contract.is_dir():
        copy_directory(contract, contract_destination)
        if not any(contract_destination.rglob("SKILL.md")):
            raise HarnessError("extracted contract package contains no SKILL.md")
    else:
        (contract_destination / "SKILL.md").write_bytes(contract.read_bytes())
    head = initialize_snapshot(repo, f"Frozen {scenario_id} fixture")
    write_manifest(destination, descriptor, fixture_source, "pre_packet")
    verify_manifest(destination)
    return {"head": head, "fixture_source": fixture_source}


def tree_hash(root: Path) -> str:
    entries: list[tuple[str, str, int]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_dir() or ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        reject_symlink_chain(root, relative)
        entries.append((relative.as_posix(), sha256_file(path), stat.S_IMODE(path.stat().st_mode)))
    return sha256_bytes(canonical_json(entries))


def verify_manifest(stage_root: Path) -> None:
    manifest_path = safe_path(stage_root, "runner-manifest.json")
    expected_line = safe_path(stage_root, "runner-manifest.sha256").read_text(encoding="ascii")
    expected_hash = expected_line.split()[0]
    if sha256_file(manifest_path) != expected_hash:
        raise HarnessError("runner manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    listed: set[str] = set()
    for entry in manifest["files"]:
        relative = Path(entry["path"])
        reject_evaluator_path(relative)
        path = safe_path(stage_root, relative)
        if not path.is_file() or sha256_file(path) != entry["sha256"]:
            raise HarnessError(f"runner input hash mismatch: {relative}")
        listed.add(relative.as_posix())
    actual = {entry["path"] for entry in iter_manifest_files(stage_root)}
    if listed != actual:
        raise HarnessError("runner manifest allowlist does not match staged inputs")


def freeze_pre_packet(stage_root: Path, validation: Path) -> Path:
    manifest = json.loads((stage_root / "runner-manifest.json").read_text(encoding="utf-8"))
    if manifest["scenario_stage"] != "pre_packet":
        raise HarnessError("pre-packet freeze is only valid before review packet staging")
    if validation.is_symlink() or not validation.is_file():
        raise HarnessError("validation evidence must be a regular file")
    repo = safe_path(stage_root, "repo")
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": manifest["scenario_id"],
        "head": run(["git", "rev-parse", "HEAD"], cwd=repo).strip(),
        "status": run(["git", "status", "--short"], cwd=repo),
        "diff_sha256": sha256_bytes(run(["git", "diff", "--binary", "HEAD"], cwd=repo).encode()),
        "validation_sha256": sha256_file(validation),
    }
    output = stage_root / "evidence" / "pre-packet-snapshot.json"
    write_json(output, evidence)
    return output


def stage_review_packet(stage_root: Path) -> None:
    snapshot = safe_path(stage_root, "evidence/pre-packet-snapshot.json")
    if not snapshot.is_file():
        raise HarnessError("review packet requires a frozen pre-packet snapshot")
    manifest_path = stage_root / "runner-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["scenario_stage"] != "pre_packet":
        raise HarnessError("review packet already staged")
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
    write_manifest(stage_root, descriptor, manifest["fixture_source"], "review_packet")


def freeze_output(stage_root: Path, record: Path, trace: Path) -> Path:
    manifest = json.loads((stage_root / "runner-manifest.json").read_text(encoding="utf-8"))
    if manifest["scenario_stage"] != "review_packet":
        raise HarnessError("output freeze requires the staged review packet")
    if record.is_symlink() or not record.is_file() or trace.is_symlink() or not trace.is_file():
        raise HarnessError("run record and trace must be regular files")
    repo = safe_path(stage_root, "repo")
    code_diff = run(["git", "diff", "--binary", "HEAD", "--", ".", ":(exclude)tests"], cwd=repo)
    test_diff = run(["git", "diff", "--binary", "HEAD", "--", "tests"], cwd=repo)
    output = stage_root / "evidence" / "output-freeze.json"
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": manifest["scenario_id"],
        "head": run(["git", "rev-parse", "HEAD"], cwd=repo).strip(),
        "status": run(["git", "status", "--short"], cwd=repo),
        "implementation_diff_sha256": sha256_bytes(code_diff.encode()),
        "test_diff_sha256": sha256_bytes(test_diff.encode()),
        "run_record_sha256": sha256_file(record),
        "pre_freeze_trace_sha256": sha256_file(trace),
    }
    write_json(output, evidence)
    with trace.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "output_freeze", "evidence_sha256": sha256_file(output)}, sort_keys=True) + "\n")
    return output


def audit_trace(trace: Path) -> None:
    frozen = False
    violations: list[str] = []
    denied = ("/evaluator/", "\\evaluator\\", "outcome-ledger", "hidden_tests", "posthoc")
    for number, line in enumerate(trace.read_text(encoding="utf-8").splitlines(), 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HarnessError(f"trace line {number} is not JSON") from exc
        if event.get("event") == "output_freeze":
            frozen = True
            continue
        if frozen:
            continue
        serialized = json.dumps(event, sort_keys=True).lower()
        if any(token.lower() in serialized for token in denied):
            violations.append(str(number))
    if not frozen:
        raise HarnessError("trace has no output_freeze marker")
    if violations:
        raise HarnessError(f"pre-freeze evaluator trace contamination on lines {', '.join(violations)}")


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


def assert_identity_blind(value: object) -> None:
    text = json.dumps(value, sort_keys=True).lower()
    leaked = [token for token in denylist() if token in text]
    if leaked:
        raise HarnessError(f"identity clue leaked into blind packet: {', '.join(leaked)}")


def evidence_path(record_root: Path, relative: str) -> Path:
    path = safe_path(record_root, relative)
    reject_evaluator_path(path.relative_to(record_root))
    if not path.is_file():
        raise HarnessError(f"missing run evidence: {relative}")
    return path


def normalize_run(record_path: Path) -> dict[str, object]:
    if record_path.is_symlink() or not record_path.is_file():
        raise HarnessError("run record must be a regular file")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if "candidate_compliance" in record:
        raise HarnessError("candidate compliance belongs in the post-reveal packet")
    root = record_path.parent
    required = {"implementation_diff", "test_diff", "probe_results", "review_log"}
    if set(record.get("evidence", {})) != required:
        raise HarnessError("run record must name the four evaluator evidence inputs exactly")
    clues = record.get("identity_clues", [])
    raw: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for name, relative in record["evidence"].items():
        path = evidence_path(root, relative)
        hashes[name] = sha256_file(path)
        raw[name] = normalize_text(path.read_text(encoding="utf-8"), clues)
    implementation = raw["implementation_diff"]
    tests = raw["test_diff"]
    probe_data = json.loads(raw["probe_results"])
    review_data = json.loads(raw["review_log"])
    output: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": record["scenario_id"],
        "snapshots": record["snapshots"],
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
        },
        "measurements": record["measurements"],
        "source_hashes": hashes,
    }
    assert_identity_blind(output)
    return output


def build_blind_packet(run_paths: list[Path]) -> dict[str, object]:
    if len(run_paths) != 2:
        raise HarnessError("the binary skill review requires exactly two runs")
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in run_paths]
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


def load_outcome_record(path: Path, label: str, ledger_ids: set[str]) -> tuple[dict[str, dict[str, object]], list[str]]:
    if path.is_symlink() or not path.is_file():
        raise HarnessError(f"{label} outcome record must be a regular file")
    document = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if set(document) != {"schema_version", "outcomes"} or document.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{label}: invalid document fields or schema_version")
    raw_outcomes = document.get("outcomes", {})
    if not isinstance(raw_outcomes, dict):
        return {}, [*errors, f"{label}: outcomes must be an object"]
    actual_ids = set(raw_outcomes)
    missing = sorted(ledger_ids - actual_ids)
    extra = sorted(actual_ids - ledger_ids)
    if missing:
        errors.append(f"{label}: missing findings: {', '.join(missing)}")
    if extra:
        errors.append(f"{label}: extra findings: {', '.join(extra)}")
    outcomes: dict[str, dict[str, object]] = {}
    for finding_id in sorted(actual_ids & ledger_ids):
        outcome = raw_outcomes[finding_id]
        if not isinstance(outcome, dict) or set(outcome) != {"test_disposition", "rereview_scope"}:
            errors.append(f"{label}: {finding_id} must contain only test_disposition and rereview_scope")
            continue
        if outcome["test_disposition"] not in {"permanent", "table_case", "probe_only", "no_test"}:
            errors.append(f"{label}: {finding_id} has invalid test_disposition")
            continue
        if outcome["rereview_scope"] not in {"targeted", "full", None}:
            errors.append(f"{label}: {finding_id} has invalid rereview_scope")
            continue
        outcomes[finding_id] = outcome
    return outcomes, errors


def gate_outcomes(baseline_path: Path, candidate_path: Path) -> dict[str, object]:
    validate_ledger()
    ledger_document = json.loads(OUTCOME_LEDGER.read_text(encoding="utf-8"))
    ledger = {entry["finding_id"]: entry for entry in ledger_document["entries"]}
    ledger_ids = set(ledger)
    baseline, baseline_errors = load_outcome_record(baseline_path, "baseline", ledger_ids)
    candidate, candidate_errors = load_outcome_record(candidate_path, "candidate", ledger_ids)

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
    errors = [*baseline_errors, *candidate_errors]
    passed = not errors and not regressions and permanent_improved and full_improved
    return {
        "schema_version": SCHEMA_VERSION,
        "gate": "deliver_outcomes",
        "passed": passed,
        "ledger_sha256": sha256_file(OUTCOME_LEDGER),
        "ledger_finding_count": len(ledger),
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
        "record_errors": errors,
        "correctness_gate_evaluated": False,
        "judge_verdict_evaluated": False,
    }


def check_candidate_compliance(report_path: Path) -> dict[str, object]:
    if report_path.is_symlink() or not report_path.is_file():
        raise HarnessError("candidate compliance report must be a regular post-reveal file")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("revealed_identity") != "candidate":
        raise HarnessError("candidate compliance is valid only after identity reveal")
    required = {
        "finding_id",
        "test_disposition",
        "test_rationale",
        "repair_authorized",
        "rereview_scope",
        "rereview_rationale",
    }
    violations: list[str] = []
    for index, record in enumerate(report.get("records", [])):
        if set(record) != required:
            violations.append(f"record {index} fields")
            continue
        if record["test_disposition"] not in {"permanent", "table_case", "probe_only", "no_test"}:
            violations.append(f"record {index} test_disposition")
        expected_scopes = {"targeted", "full"} if record["repair_authorized"] else {None}
        if record["rereview_scope"] not in expected_scopes:
            violations.append(f"record {index} rereview_scope")
        if not str(record["test_rationale"]).strip() or (
            record["repair_authorized"] and not str(record["rereview_rationale"]).strip()
        ):
            violations.append(f"record {index} rationale")
    if not report.get("records"):
        violations.append("missing records")
    return {"compliant": not violations, "violations": violations}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare")
    prepare.add_argument("--scenario", required=True)
    prepare.add_argument("--contract", type=Path, required=True)
    prepare.add_argument("--destination", type=Path, required=True)

    verify = commands.add_parser("verify-manifest")
    verify.add_argument("stage_root", type=Path)

    freeze = commands.add_parser("freeze-pre-packet")
    freeze.add_argument("stage_root", type=Path)
    freeze.add_argument("--validation", type=Path, required=True)

    packet = commands.add_parser("stage-review-packet")
    packet.add_argument("stage_root", type=Path)

    output_freeze = commands.add_parser("freeze-output")
    output_freeze.add_argument("stage_root", type=Path)
    output_freeze.add_argument("--record", type=Path, required=True)
    output_freeze.add_argument("--trace", type=Path, required=True)

    trace = commands.add_parser("audit-trace")
    trace.add_argument("trace", type=Path)

    normalize = commands.add_parser("normalize")
    normalize.add_argument("record", type=Path)
    normalize.add_argument("--output", type=Path, required=True)

    blind = commands.add_parser("blind-packet")
    blind.add_argument("runs", type=Path, nargs=2)
    blind.add_argument("--output", type=Path, required=True)

    compliance = commands.add_parser("check-candidate-compliance")
    compliance.add_argument("report", type=Path)
    compliance.add_argument("--output", type=Path, required=True)

    outcomes = commands.add_parser("gate-outcomes")
    outcomes.add_argument("--baseline", type=Path, required=True)
    outcomes.add_argument("--candidate", type=Path, required=True)
    outcomes.add_argument("--output", type=Path, required=True)

    commands.add_parser("validate-ledger")
    return root


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == "prepare":
        print(json.dumps(prepare_scenario(arguments.scenario, arguments.contract, arguments.destination), sort_keys=True))
    elif arguments.command == "verify-manifest":
        verify_manifest(arguments.stage_root)
    elif arguments.command == "freeze-pre-packet":
        print(freeze_pre_packet(arguments.stage_root, arguments.validation))
    elif arguments.command == "stage-review-packet":
        stage_review_packet(arguments.stage_root)
    elif arguments.command == "freeze-output":
        print(freeze_output(arguments.stage_root, arguments.record, arguments.trace))
    elif arguments.command == "audit-trace":
        audit_trace(arguments.trace)
    elif arguments.command == "normalize":
        write_json(arguments.output, normalize_run(arguments.record))
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
