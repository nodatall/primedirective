import { describe, expect, it } from 'vitest';
import { deterministicWorktree, assertInsideWorkspace, collisionCheck } from '../src/worktrees/manager.js';
import { classifyProtectedRisk } from '../src/quick-track/protectedRisk.js';
import { planQuickFinalization } from '../src/quick-track/finalize.js';
import { Scheduler } from '../src/orchestrator/scheduler.js';
import { findExistingPrForBranch, canAutoMerge } from '../src/github/gh.js';
import { reconcileActiveRunner } from '../src/orchestrator/reconcile.js';

it('creates deterministic collision-safe worktree names', () => {
  const target = deterministicWorktree({ cardId: 'card-1', repoId: 'repo', repoPath: '/Volumes/Code/example', workspaceRoot: '/tmp/board' });
  expect(target.branch).toBe('agent-board/example/card-1');
  assertInsideWorkspace('/tmp/board', target.path);
  expect(() => assertInsideWorkspace('/tmp/board', '/tmp/elsewhere/card')).toThrow(/escapes/);
  expect(() => collisionCheck(target, { cardId: 'other', branch: target.branch, path: target.path }, 'card-1')).toThrow(/collision_detected/);
});

it('classifies protected risk by path diff and task intent', () => {
  expect(classifyProtectedRisk(['src/Button.tsx'], '', 'change a color').risky).toBe(false);
  expect(classifyProtectedRisk(['src/AuthView.tsx'], '', 'change copy').risky).toBe(true);
  expect(classifyProtectedRisk(['src/ui.ts'], 'DROP TABLE users', 'small change').risky).toBe(true);
});

it('blocks zero-diff quick track without PR actions', () => {
  expect(planQuickFinalization({ changedFiles: [], diffText: '', taskText: 'do it', checksPresent: false })).toMatchObject({ status: 'blocked', reason: 'no_changes_detected', actions: [] });
});

it('allows five same-repo active cards and blocks sixth by default', () => {
  const scheduler = new Scheduler();
  for (let i = 0; i < 5; i += 1) expect(scheduler.start({ id: `c${i}`, repoId: 'repo' })).toBe(true);
  expect(scheduler.start({ id: 'c6', repoId: 'repo' })).toBe(false);
});

it('blocks ambiguous planned PR association and enforces automerge guards', () => {
  expect(findExistingPrForBranch([{ number: 1, url: 'u', state: 'OPEN' }, { number: 2, url: 'u2', state: 'OPEN' }])).toEqual({ ambiguous: true });
  expect(canAutoMerge({ number: 1, url: 'u', state: 'OPEN', headRefOid: 'abc', mergeable: 'MERGEABLE', checksState: 'passed' }, { enabled: true, protectedRisk: false, unresolvedBlocker: false, allowNoCheck: false, taskType: 'Quick' })).toBe(true);
  expect(canAutoMerge({ number: 1, url: 'u', state: 'OPEN', headRefOid: 'abc', mergeable: 'MERGEABLE', checksState: 'absent' }, { enabled: true, protectedRisk: false, unresolvedBlocker: false, allowNoCheck: true, taskType: 'Planned' })).toBe(false);
});

it('quarantines ambiguous active runners after restart', () => {
  expect(reconcileActiveRunner({ pid: 123, worktreePath: '/tmp/wt', startedAt: new Date().toISOString() })).toMatchObject({ status: 'blocked', reason: 'restart_quarantined' });
});

import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { SqliteStore } from '../src/db/sqliteStore.js';

it('persists lifecycle tables across SQLite store restart', () => {
  const dbPath = join(mkdtempSync(join(tmpdir(), 'board-store-')), 'board.sqlite');
  const store = new SqliteStore(dbPath);
  store.upsertRepo({ id: 'repo', name: 'Repo', path: '/tmp/repo', defaultBranch: 'main' });
  store.upsertCard({ id: 'card', repoId: 'repo', title: 'Card', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Queued', updatedAt: new Date().toISOString() });
  store.upsertRun({ id: 'run-card', cardId: 'card', attempt: 1, phase: 'codex', status: 'running' });
  store.upsertWorktree({ id: 'wt-card', cardId: 'card', repoId: 'repo', path: '/tmp/wt', branch: 'agent-board/repo/card', status: 'active' });
  store.upsertPullRequest({ id: 'pr-card', cardId: 'card', repoId: 'repo', number: 1, url: 'https://example.test/pr/1', state: 'OPEN' });
  store.upsertIntegrationJob({ id: 'job-card', cardId: 'card', repoId: 'repo', type: 'pr_create', status: 'succeeded', lockKey: 'repo', attempts: 1 });
  const restarted = new SqliteStore(dbPath).read();
  expect(restarted.runs).toHaveLength(1);
  expect(restarted.worktrees).toHaveLength(1);
  expect(restarted.pullRequests).toHaveLength(1);
  expect(restarted.integrationJobs).toHaveLength(1);
});

it('rejects protected risk from untracked secret-like files', () => {
  const result = classifyProtectedRisk(['src/new.ts'], 'diff --git a/src/new.ts b/src/new.ts\nAPI_KEY=abc123\n', 'add config');
  expect(result.risky).toBe(true);
});

it('does not treat unknown mergeability as mergeable', () => {
  expect(canAutoMerge({ number: 2, url: 'u', state: 'OPEN', headRefOid: 'abc', mergeable: 'UNKNOWN', checksState: 'passed' }, { enabled: true, protectedRisk: false, unresolvedBlocker: false, allowNoCheck: false, taskType: 'Quick' })).toBe(false);
});

import { classifyRemoteBranchLookup, pickOpenPrForBranch } from '../src/github/gh.js';

it('classifies remote branch lookup without failing open', () => {
  expect(classifyRemoteBranchLookup(0)).toBe('exists');
  expect(classifyRemoteBranchLookup(2)).toBe('absent');
  expect(classifyRemoteBranchLookup(128)).toBe('error');
});

it('requires a single open Planned PR and treats stale-only PRs as ambiguous', () => {
  expect(pickOpenPrForBranch([{ number: 1, url: 'u', state: 'CLOSED' }])).toEqual({ stale: true, state: 'CLOSED' });
  expect(pickOpenPrForBranch([{ number: 1, url: 'u', state: 'MERGED' }])).toEqual({ stale: true, state: 'MERGED' });
  expect(pickOpenPrForBranch([{ number: 1, url: 'u', state: 'OPEN' }, { number: 2, url: 'u2', state: 'CLOSED' }])).toMatchObject({ number: 1 });
  expect(pickOpenPrForBranch([{ number: 1, url: 'u', state: 'OPEN' }, { number: 2, url: 'u2', state: 'OPEN' }])).toEqual({ ambiguous: true });
});

import { reconcileStartup } from '../src/orchestrator/reconcile.js';

it('quarantines persisted running cards on startup reconciliation', () => {
  const dbPath = join(mkdtempSync(join(tmpdir(), 'board-reconcile-')), 'board.sqlite');
  const store = new SqliteStore(dbPath);
  store.upsertCard({ id: 'running-card', repoId: 'repo', title: 'Running', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Running', updatedAt: new Date().toISOString() });
  reconcileStartup(store);
  expect(store.findCard('running-card')).toMatchObject({ status: 'Blocked', blockerReason: 'restart_quarantined' });
});
