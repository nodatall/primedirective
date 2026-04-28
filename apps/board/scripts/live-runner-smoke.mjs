#!/usr/bin/env node
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

const fixture = mkdtempSync(join(tmpdir(), 'agent-board-codex-smoke-'));
writeFileSync(join(fixture, 'README.md'), '# Codex smoke fixture\n');
const init = spawnSync('git', ['init'], { cwd: fixture, encoding: 'utf8' });
if (init.status !== 0) {
  console.log(JSON.stringify({ live_runner_smoke: 'skipped', reason: 'git unavailable', fixture }));
  process.exit(0);
}
const result = spawnSync('codex', ['exec', '--json', '--full-auto', '--sandbox', 'workspace-write', 'Inspect this disposable fixture and respond with no file changes.'], { cwd: fixture, encoding: 'utf8', timeout: 120000 });
console.log(JSON.stringify({
  live_runner_smoke: result.status === 0 ? 'passed' : 'failed',
  command: 'codex exec --json --full-auto --sandbox workspace-write <prompt>',
  exitCode: result.status,
  github_pr_creation: 'skipped: disposable local fixture has no remote and PR creation would be unsafe here',
  stderrExcerpt: result.stderr?.slice(0, 500) ?? ''
}, null, 2));
rmSync(fixture, { recursive: true, force: true });
process.exit(result.status === 0 ? 0 : 1);
