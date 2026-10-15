#!/usr/bin/env node

import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const VERSION = "deliver-plain-language-v12.32";
const INTERFACE_PATH = "evals/deliver/plain-language-v12/independent-case-bundle-interface.json";
const BUNDLE_SUBDIRECTORY = "private-oracle";
const MANIFEST_NAME = "bundle-manifest.json";
const REQUIRED_FILES = [
  "author-v132.mjs", "bundle-manifest.json", "cases.json", "expected-answers.json",
  "judge-allocation-manifest.json", "projected-arm-packet.json",
  "response-schema.json", "validate-v132.mjs",
];
const IMPORTED_FILES = REQUIRED_FILES.filter((name) => name !== MANIFEST_NAME);
const REQUIRED_FILE_MODES = Object.fromEntries(REQUIRED_FILES.map((name) => [
  name, ["author-v132.mjs", "validate-v132.mjs"].includes(name) ? "100755" : "100644",
]));
const OUTPUT_FIELDS = [
  "bundle_manifest_sha256", "bundle_source_commit", "bundle_source_tree",
  "controller_commit", "controller_tree", "imported_file_sha256",
  "manifest_payload_sha256", "oracle_version", "public_file_sha256",
  "schema_version", "status",
].sort();
const MANIFEST_FIELDS = [
  "approved_removed_behavior_ids", "bundle_file_sha256", "controller_commit",
  "controller_tree", "counts", "freshness", "manifest_payload_sha256", "model",
  "namespace", "oracle_version", "public_file_sha256", "reasoning",
  "required_file_modes", "required_files", "response_schema_public_path",
  "retained_behavior_ids", "schema_version",
].sort();

const sha = (value) => crypto.createHash("sha256").update(value).digest("hex");
const canonical = (value) => Buffer.from(JSON.stringify(value, Object.keys(value).sort()));
const sortedObject = (value) => Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b)));
const deepCanonical = (value) => {
  if (Array.isArray(value)) return value.map(deepCanonical);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, deepCanonical(value[key])]));
  }
  return value;
};
const canonicalJson = (value) => Buffer.from(JSON.stringify(deepCanonical(value)));
const readJson = (bytes, label) => {
  const value = JSON.parse(bytes.toString("utf8"));
  assert(value && typeof value === "object" && !Array.isArray(value), `${label} must be an object`);
  return value;
};
const git = (repo, args, encoding = null) => execFileSync("/usr/bin/git", args, {
  cwd: repo,
  encoding,
  stdio: ["ignore", "pipe", "pipe"],
});
const commit = (repo, ref) => {
  const value = git(repo, ["rev-parse", `${ref}^{commit}`], "utf8").trim();
  assert(/^[0-9a-f]{40}$/.test(value), "commit is malformed");
  return value;
};
const tree = (repo, ref) => {
  const value = git(repo, ["rev-parse", `${ref}^{tree}`], "utf8").trim();
  assert(/^[0-9a-f]{40}$/.test(value), "tree is malformed");
  return value;
};
const blob = (repo, ref, relative) => git(repo, ["cat-file", "blob", `${ref}:${relative}`]);
const mode = (repo, ref, relative) => {
  const lines = git(repo, ["ls-tree", ref, "--", relative], "utf8").trim().split("\n");
  assert.equal(lines.length, 1, `missing Git entry: ${relative}`);
  const [metadata, listed] = lines[0].split("\t");
  const [gitMode, kind, objectId] = metadata.split(" ");
  assert.equal(listed, relative);
  assert.equal(kind, "blob");
  assert(["100644", "100755"].includes(gitMode));
  assert(/^[0-9a-f]{40}$/.test(objectId));
  return gitMode;
};
const parseArgs = () => {
  const names = [
    "--public-repo", "--controller-commit", "--bundle-repo",
    "--bundle-source-commit", "--bundle-root",
  ];
  assert.equal(process.argv.length, 2 + names.length * 2, "argument set is not exact");
  const result = {};
  for (let index = 0; index < names.length; index += 1) {
    assert.equal(process.argv[2 + index * 2], names[index], "argument order is not exact");
    result[names[index].slice(2)] = process.argv[3 + index * 2];
  }
  return result;
};

const args = parseArgs();
const publicRepo = fs.realpathSync(args["public-repo"]);
const bundleRepo = fs.realpathSync(args["bundle-repo"]);
const bundleRoot = fs.realpathSync(args["bundle-root"]);
const controller = commit(publicRepo, args["controller-commit"]);
const bundleSource = commit(bundleRepo, args["bundle-source-commit"]);
const controllerTree = tree(publicRepo, controller);
const bundleTree = tree(bundleRepo, bundleSource);
const interfaceDoc = readJson(blob(publicRepo, controller, INTERFACE_PATH), "bundle interface");
assert.equal(interfaceDoc.oracle_version, VERSION);
assert.equal(interfaceDoc.schema_version, 1);
assert.equal(interfaceDoc.bundle_manifest_schema_version, 2);
assert.equal(interfaceDoc.bundle_subdirectory, BUNDLE_SUBDIRECTORY);
assert.deepEqual(interfaceDoc.required_files, REQUIRED_FILES);
assert.deepEqual(interfaceDoc.manifest_declared_imported_files, IMPORTED_FILES);
assert.deepEqual(interfaceDoc.required_file_modes, REQUIRED_FILE_MODES);
assert.equal(interfaceDoc.expected_model, "gpt-5.6-sol");
assert.equal(interfaceDoc.expected_reasoning, "xhigh");
assert.equal(interfaceDoc.expected_allocation_status, "allocated_not_run");
assert.equal(interfaceDoc.namespace_pattern, "^v1232-[0-9a-f]{20}$");
assert.deepEqual([...interfaceDoc.standalone_validator_output_fields].sort(), OUTPUT_FIELDS);

const publicDigests = {};
for (const relative of interfaceDoc.public_binding_paths) {
  const source = blob(publicRepo, controller, relative);
  assert(fs.statSync(path.join(publicRepo, relative), { throwIfNoEntry: true }).isFile());
  assert(fs.readFileSync(path.join(publicRepo, relative)).equals(source), `public drift: ${relative}`);
  publicDigests[relative] = sha(source);
}

const listed = git(
  bundleRepo,
  ["ls-tree", "-r", "--name-only", bundleSource, "--", BUNDLE_SUBDIRECTORY],
  "utf8",
).trim().split("\n");
const expectedPaths = interfaceDoc.required_files.map((name) => `${BUNDLE_SUBDIRECTORY}/${name}`);
assert.deepEqual(listed, expectedPaths);
const sourceFiles = {};
const sourceModes = {};
for (const name of interfaceDoc.required_files) {
  const relative = `${BUNDLE_SUBDIRECTORY}/${name}`;
  sourceFiles[name] = blob(bundleRepo, bundleSource, relative);
  sourceModes[name] = mode(bundleRepo, bundleSource, relative);
  const staged = path.join(bundleRoot, name);
  assert(fs.lstatSync(staged).isFile() && !fs.lstatSync(staged).isSymbolicLink());
  assert(fs.readFileSync(staged).equals(sourceFiles[name]), `staged bundle drift: ${name}`);
}
assert.deepEqual(sourceModes, interfaceDoc.required_file_modes);

const manifestRaw = sourceFiles[MANIFEST_NAME];
const manifest = readJson(manifestRaw, "bundle manifest");
assert.deepEqual(Object.keys(manifest).sort(), MANIFEST_FIELDS);
assert.equal(manifest.schema_version, 2);
assert.equal(manifest.oracle_version, VERSION);
assert.match(manifest.namespace, /^v1232-[0-9a-f]{20}$/);
assert.equal(manifest.model, interfaceDoc.expected_model);
assert.equal(manifest.reasoning, interfaceDoc.expected_reasoning);
assert.equal(manifest.controller_commit, controller);
assert.equal(manifest.controller_tree, controllerTree);
assert.deepEqual(manifest.required_files, interfaceDoc.required_files);
assert.deepEqual(manifest.required_file_modes, sourceModes);
assert.deepEqual(manifest.public_file_sha256, publicDigests);
assert.deepEqual(manifest.counts, interfaceDoc.expected_counts);
assert.deepEqual(manifest.freshness, interfaceDoc.freshness_contract);
assert.equal(manifest.response_schema_public_path, interfaceDoc.response_schema_binding.public_source);
const inventory = readJson(
  blob(publicRepo, controller, "evals/deliver/plain-language-v12/public-contract-inventory.json"),
  "public contract inventory",
);
const behaviorMap = readJson(
  blob(publicRepo, controller, "evals/deliver/plain-language-v12/candidate-behavior-map.json"),
  "candidate behavior map",
);
const behaviorIds = inventory.behaviors.map((item) => item.behavior_id);
const removed = behaviorMap.intentionally_removed_behavior_ids;
const retained = behaviorIds.filter((behaviorId) => !new Set(removed).has(behaviorId));
assert.equal(behaviorIds.length, 108);
assert.equal(new Set(behaviorIds).size, 108);
assert.equal(retained.length, 103);
assert.deepEqual(removed, [
  "DLV-ACT-005", "DLV-MODE-004", "DLV-PLAN-005", "DLV-PLAN-006", "DLV-STOP-008",
]);
assert.deepEqual(manifest.retained_behavior_ids, retained);
assert.deepEqual(manifest.approved_removed_behavior_ids, removed);
const payload = { ...manifest };
delete payload.manifest_payload_sha256;
assert.equal(manifest.manifest_payload_sha256, sha(canonicalJson(payload)));
const importedDigests = sortedObject(Object.fromEntries(
  interfaceDoc.manifest_declared_imported_files.map((name) => [name, sha(sourceFiles[name])]),
));
assert.deepEqual(manifest.bundle_file_sha256, importedDigests);
assert(sourceFiles[interfaceDoc.response_schema_binding.bundle_file].equals(
  blob(publicRepo, controller, interfaceDoc.response_schema_binding.public_source),
));
assert(sourceFiles[interfaceDoc.standalone_validator_binding.bundle_file].equals(
  blob(publicRepo, controller, interfaceDoc.standalone_validator_binding.public_source),
));

const output = {
  schema_version: 1,
  oracle_version: VERSION,
  status: "pass",
  controller_commit: controller,
  controller_tree: controllerTree,
  bundle_source_commit: bundleSource,
  bundle_source_tree: bundleTree,
  bundle_manifest_sha256: sha(manifestRaw),
  manifest_payload_sha256: manifest.manifest_payload_sha256,
  public_file_sha256: sortedObject(publicDigests),
  imported_file_sha256: importedDigests,
};
assert.deepEqual(Object.keys(output).sort(), OUTPUT_FIELDS);
process.stdout.write(`${JSON.stringify(output)}\n`);
