import { describe, expect, it } from 'vitest';
import { deterministicWorktree, assertInsideWorkspace, collisionCheck } from '../src/worktrees/manager.js';
import { classifyProtectedRisk } from '../src/quick-track/protectedRisk.js';
import { planQuickFinalization } from '../src/quick-track/finalize.js';
import { Scheduler } from '../src/orchestrator/scheduler.js';
import { findExistingPrForBranch, canAutoMerge } from '../src/github/gh.js';
import { reconcileActiveRunner } from '../src/orchestrator/reconcile.js';
import { createCard, discardCard, resumeCard, updateInboxCard } from '../src/orchestrator/cardLifecycle.js';
import { captureVisualEvidence, copyVisualEvidenceForPr, formatVisualEvidenceMarkdown, requiresVisualEvidence } from '../src/visual/evidence.js';

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

it('requires visual evidence for frontend implementation files only', () => {
  expect(requiresVisualEvidence(['apps/board/web/src/styles.css'])).toBe(true);
  expect(requiresVisualEvidence(['components/Button.tsx'])).toBe(true);
  expect(requiresVisualEvidence(['apps/board/web/tests/render.test.tsx'])).toBe(false);
  expect(requiresVisualEvidence(['README.md'])).toBe(false);
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

import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { SqliteStore } from '../src/db/sqliteStore.js';
import { spawnSync } from 'node:child_process';

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

it('adds new cards to inbox without starting a run', () => {
  const dbPath = join(mkdtempSync(join(tmpdir(), 'board-inbox-card-')), 'board.sqlite');
  const store = new SqliteStore(dbPath);
  const card = createCard(store, { id: 'card', repoId: 'repo', title: 'New task', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Running' });
  const snapshot = store.read();
  expect(card.status).toBe('Inbox');
  expect(snapshot.cards[0]).toMatchObject({ id: 'card', status: 'Inbox' });
  expect(snapshot.runs).toHaveLength(0);
});

it('derives a title from instructions when omitted', () => {
  const dbPath = join(mkdtempSync(join(tmpdir(), 'board-derived-title-')), 'board.sqlite');
  const store = new SqliteStore(dbPath);
  const card = createCard(store, {
    id: 'card',
    repoId: 'repo',
    title: '',
    instructions: '## Page Feedback: /\n**Viewport:** 2048x1062\n**Feedback:** make the submit button smaller',
    taskType: 'Quick',
    autoMerge: false
  });
  expect(card.title).toBe('make the submit button smaller');
  expect(store.findCard('card')?.title).toBe('make the submit button smaller');
});

it('updates inbox card title and instructions before work starts', () => {
  const dbPath = join(mkdtempSync(join(tmpdir(), 'board-edit-inbox-')), 'board.sqlite');
  const store = new SqliteStore(dbPath);
  createCard(store, { id: 'card', repoId: 'repo', title: 'Old title', instructions: 'Old instructions', taskType: 'Quick', autoMerge: false });

  expect(updateInboxCard(store, 'card', { title: 'New title', instructions: 'New instructions' })).toMatchObject({ ok: true, card: { title: 'New title', instructions: 'New instructions' } });
  expect(store.findCard('card')).toMatchObject({ title: 'New title', instructions: 'New instructions', status: 'Inbox' });
});

it('rejects inbox edits after a card starts', () => {
  const dbPath = join(mkdtempSync(join(tmpdir(), 'board-edit-started-')), 'board.sqlite');
  const store = new SqliteStore(dbPath);
  store.upsertCard({ id: 'card', repoId: 'repo', title: 'Started', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Queued', updatedAt: new Date().toISOString() });

  expect(updateInboxCard(store, 'card', { title: 'Too late' })).toEqual({ ok: false, error: 'edit_blocked: card has already started' });
  expect(store.findCard('card')?.title).toBe('Started');
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

it('resumes a quarantined card by reusing its clean existing worktree', async () => {
  const root = mkdtempSync(join(tmpdir(), 'board-resume-'));
  const repo = join(root, 'repo');
  const worktreeRoot = join(root, 'worktrees');
  const worktreePath = join(worktreeRoot, 'repo-card');
  const branch = 'agent-board/repo/card';
  mkdirSync(repo);
  mkdirSync(worktreeRoot);
  git(['init', '-b', 'main'], repo);
  git(['config', 'user.email', 'board@example.test'], repo);
  git(['config', 'user.name', 'Board Test'], repo);
  writeFileSync(join(repo, 'README.md'), '# fixture\n');
  git(['add', 'README.md'], repo);
  git(['commit', '-m', 'initial'], repo);
  git(['worktree', 'add', '-b', branch, worktreePath], repo);

  const previousDisableCodex = process.env.BOARD_DISABLE_CODEX;
  const previousWorkspaceRoot = process.env.BOARD_WORKSPACE_ROOT;
  process.env.BOARD_DISABLE_CODEX = '1';
  process.env.BOARD_WORKSPACE_ROOT = worktreeRoot;
  try {
    const store = new SqliteStore(join(root, 'board.sqlite'));
    store.upsertRepo({ id: 'repo', name: 'Repo', path: repo, defaultBranch: 'main' });
    store.upsertCard({ id: 'card', repoId: 'repo', title: 'Resume', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Blocked', branch, worktreePath, blockerReason: 'restart_quarantined', blockerSummary: 'restart', updatedAt: new Date().toISOString() });

    expect(resumeCard(store, 'card', 'continue')).toMatchObject({ ok: true });
    const deadline = Date.now() + 5000;
    let card = store.findCard('card');
    while (Date.now() < deadline && card?.blockerReason !== 'no_changes_detected' && card?.blockerReason !== 'collision_detected') {
      await new Promise((resolve) => setTimeout(resolve, 50));
      card = store.findCard('card');
    }

    expect(card).toMatchObject({ status: 'Blocked', blockerReason: 'no_changes_detected' });
    expect(store.read().events.map((event) => event.message)).toContain('Reusing existing card worktree');
  } finally {
    if (previousDisableCodex === undefined) delete process.env.BOARD_DISABLE_CODEX;
    else process.env.BOARD_DISABLE_CODEX = previousDisableCodex;
    if (previousWorkspaceRoot === undefined) delete process.env.BOARD_WORKSPACE_ROOT;
    else process.env.BOARD_WORKSPACE_ROOT = previousWorkspaceRoot;
  }
});

it('produces fake visual artifacts for frontend changes in test mode', () => {
  const root = mkdtempSync(join(tmpdir(), 'board-visual-'));
  const previousMode = process.env.BOARD_VISUAL_EVIDENCE_MODE;
  const previousArtifactRoot = process.env.BOARD_VISUAL_EVIDENCE_ARTIFACT_ROOT;
  process.env.BOARD_VISUAL_EVIDENCE_MODE = 'fake';
  process.env.BOARD_VISUAL_EVIDENCE_ARTIFACT_ROOT = join(root, 'artifacts');
  try {
    const result = captureVisualEvidence({ id: 'card', repoId: 'repo', title: 'Card', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Running', worktreePath: root, updatedAt: new Date().toISOString() }, ['apps/board/web/src/styles.css']);
    expect(result).toMatchObject({ required: true, artifacts: [{ kind: 'screenshot', name: 'desktop' }, { kind: 'screenshot', name: 'mobile' }] });
  } finally {
    if (previousMode === undefined) delete process.env.BOARD_VISUAL_EVIDENCE_MODE;
    else process.env.BOARD_VISUAL_EVIDENCE_MODE = previousMode;
    if (previousArtifactRoot === undefined) delete process.env.BOARD_VISUAL_EVIDENCE_ARTIFACT_ROOT;
    else process.env.BOARD_VISUAL_EVIDENCE_ARTIFACT_ROOT = previousArtifactRoot;
  }
});

it('copies visual screenshots into the branch and formats PR markdown', () => {
  const root = mkdtempSync(join(tmpdir(), 'board-pr-visual-'));
  const worktree = join(root, 'worktree');
  const source = join(root, 'desktop.png');
  mkdirSync(worktree);
  writeFileSync(source, 'fake png\n');

  const prepared = copyVisualEvidenceForPr(
    { id: 'card', repoId: 'repo', title: 'Card', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Running', worktreePath: worktree, branch: 'agent-board/repo/card', updatedAt: new Date().toISOString() },
    [{ kind: 'screenshot', name: 'desktop', path: source, viewport: { width: 1440, height: 900 } }]
  );

  expect(prepared.paths).toEqual(['.agent-board/visual-evidence/card/01-desktop.png']);
  expect(existsSync(join(worktree, prepared.paths[0]))).toBe(true);
  expect(readFileSync(join(worktree, prepared.paths[0]), 'utf8')).toBe('fake png\n');
  expect(formatVisualEvidenceMarkdown(prepared.artifacts, { repoUrl: 'https://github.com/acme/project', branch: 'agent-board/repo/card' })).toContain(
    '![desktop (1440x900)](https://github.com/acme/project/blob/agent-board/repo/card/.agent-board/visual-evidence/card/01-desktop.png?raw=1)'
  );
});

it('discards a card by removing its worktree, local branch, and board records', async () => {
  const root = mkdtempSync(join(tmpdir(), 'board-discard-'));
  const repo = join(root, 'repo');
  const worktreePath = join(root, 'repo-card');
  const branch = 'agent-board/repo/card';
  mkdirSync(repo);
  git(['init', '-b', 'main'], repo);
  git(['config', 'user.email', 'board@example.test'], repo);
  git(['config', 'user.name', 'Board Test'], repo);
  writeFileSync(join(repo, 'README.md'), '# fixture\n');
  git(['add', 'README.md'], repo);
  git(['commit', '-m', 'initial'], repo);
  git(['worktree', 'add', '-b', branch, worktreePath], repo);

  const previousSkipGh = process.env.BOARD_SKIP_GH_PR_CLOSE;
  process.env.BOARD_SKIP_GH_PR_CLOSE = '1';
  try {
    const store = new SqliteStore(join(root, 'board.sqlite'));
    store.upsertRepo({ id: 'repo', name: 'Repo', path: repo, defaultBranch: 'main' });
    store.upsertCard({ id: 'card', repoId: 'repo', title: 'Discard', instructions: 'Discard it', taskType: 'Quick', autoMerge: false, status: 'PR Ready', branch, worktreePath, updatedAt: new Date().toISOString() });
    store.upsertWorktree({ id: 'wt-card', cardId: 'card', repoId: 'repo', path: worktreePath, branch, status: 'active' });
    store.upsertPullRequest({ id: 'pr-card', cardId: 'card', repoId: 'repo', number: 12, url: 'https://example.test/pr/12', state: 'OPEN' });

    await expect(discardCard(store, 'card')).resolves.toEqual({ ok: true });
    expect(store.findCard('card')).toBeUndefined();
    expect(spawnSync('test', ['-d', worktreePath]).status).not.toBe(0);
    expect(spawnSync('git', ['show-ref', '--verify', '--quiet', `refs/heads/${branch}`], { cwd: repo }).status).not.toBe(0);
  } finally {
    if (previousSkipGh === undefined) delete process.env.BOARD_SKIP_GH_PR_CLOSE;
    else process.env.BOARD_SKIP_GH_PR_CLOSE = previousSkipGh;
  }
});

it('discards an inbox card without requiring a branch or worktree', async () => {
  const root = mkdtempSync(join(tmpdir(), 'board-inbox-discard-'));
  const store = new SqliteStore(join(root, 'board.sqlite'));
  store.upsertRepo({ id: 'repo', name: 'Repo', path: root, defaultBranch: 'main' });
  store.upsertCard({ id: 'card', repoId: 'repo', title: 'Inbox card', instructions: 'Not started', taskType: 'Quick', autoMerge: false, status: 'Inbox', updatedAt: new Date().toISOString() });

  await expect(discardCard(store, 'card')).resolves.toEqual({ ok: true });
  expect(store.findCard('card')).toBeUndefined();
});

it('finishes stale discard when the PR is already closed and local cleanup already happened', async () => {
  const root = mkdtempSync(join(tmpdir(), 'board-stale-discard-'));
  const repo = join(root, 'repo');
  const worktreePath = join(root, 'repo-card');
  const branch = 'agent-board/repo/card';
  mkdirSync(repo);
  git(['init', '-b', 'main'], repo);
  git(['config', 'user.email', 'board@example.test'], repo);
  git(['config', 'user.name', 'Board Test'], repo);
  writeFileSync(join(repo, 'README.md'), '# fixture\n');
  git(['add', 'README.md'], repo);
  git(['commit', '-m', 'initial'], repo);

  const store = new SqliteStore(join(root, 'board.sqlite'));
  store.upsertRepo({ id: 'repo', name: 'Repo', path: repo, defaultBranch: 'main' });
  store.upsertCard({ id: 'card', repoId: 'repo', title: 'Stale discard', instructions: 'Discard it', taskType: 'Quick', autoMerge: false, status: 'PR Ready', branch, worktreePath, updatedAt: new Date().toISOString() });
  store.upsertWorktree({ id: 'wt-card', cardId: 'card', repoId: 'repo', path: worktreePath, branch, status: 'active' });
  store.upsertPullRequest({ id: 'pr-card', cardId: 'card', repoId: 'repo', number: 12, url: 'https://example.test/pr/12', state: 'CLOSED' });

  await expect(discardCard(store, 'card')).resolves.toEqual({ ok: true });
  expect(store.findCard('card')).toBeUndefined();
  expect(store.read().pullRequests).toHaveLength(0);
  expect(store.read().worktrees).toHaveLength(0);
});

function git(args: string[], cwd: string): void {
  const result = spawnSync('git', args, { cwd, encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout || `git ${args.join(' ')} failed`);
}
