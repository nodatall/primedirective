import { randomUUID } from 'node:crypto';
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, readFileSync, realpathSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { deriveCardTitle, type CardDTO, type RepoDTO, type RunEventDTO } from '@prime-board/shared';
import type { SqliteStore } from '../db/sqliteStore.js';
import { canTransition } from '../domain/stateMachine.js';
import { canAutoMerge, classifyRemoteBranchLookup, pickOpenPrForBranch } from '../github/gh.js';
import { preflightPlannedSkill } from '../repos/preflight.js';
import { deterministicWorktree, ensureRuntimeDirs, removeCleanWorktree } from '../worktrees/manager.js';
import { planQuickFinalization } from '../quick-track/finalize.js';
import { captureVisualEvidence, copyVisualEvidenceForPr, formatVisualEvidenceMarkdown, type PullRequestVisualArtifact } from '../visual/evidence.js';
import { KeyedSerialQueue } from './locks.js';
import { Scheduler } from './scheduler.js';

const gitQueue = new KeyedSerialQueue();
const scheduler = new Scheduler();
const boardRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
function workspaceRoot(): string { return process.env.BOARD_WORKSPACE_ROOT ?? resolve(boardRoot, 'worktrees'); }

export function createCard(store: SqliteStore, draft: Partial<CardDTO>): CardDTO {
  const now = new Date().toISOString();
  const instructions = draft.instructions ?? '';
  const card: CardDTO = { id: draft.id ?? randomUUID(), repoId: draft.repoId ?? '', title: deriveCardTitle({ title: draft.title, instructions }), instructions, taskType: draft.taskType ?? 'Quick', autoMerge: Boolean(draft.autoMerge), status: 'Inbox', updatedAt: now };
  store.upsertCard(card);
  append(store, card, 'system', 'Card added to inbox');
  return card;
}

export function updateInboxCard(store: SqliteStore, cardId: string, patch: Partial<Pick<CardDTO, 'title' | 'instructions'>>): { ok: true; card: CardDTO } | { ok: false; error: string } {
  const card = store.findCard(cardId);
  if (!card) return { ok: false, error: 'card not found' };
  if (card.status !== 'Inbox') return { ok: false, error: 'edit_blocked: card has already started' };
  const instructions = patch.instructions ?? card.instructions;
  const title = patch.title === undefined ? card.title : deriveCardTitle({ title: patch.title, instructions });
  const updated: CardDTO = { ...card, title, instructions, updatedAt: new Date().toISOString() };
  store.upsertCard(updated);
  append(store, updated, 'system', 'Inbox card edited', { titleChanged: title !== card.title, instructionsChanged: instructions !== card.instructions });
  return { ok: true, card: updated };
}

export function scheduleCard(store: SqliteStore, card: CardDTO): void {
  if (!scheduler.start({ id: card.id, repoId: card.repoId })) return;
  void runQueuedCard(store, card)
    .catch((error: unknown) => block(store, card, 'runner_failed', error instanceof Error ? error.message : String(error)))
    .finally(() => { scheduler.finish(card.id); drainQueuedCards(store); });
}

export function drainQueuedCards(store: SqliteStore): void {
  for (const card of store.read().cards.filter((candidate) => candidate.status === 'Queued' && !candidate.overridePaused)) {
    if (!scheduler.canStart({ id: card.id, repoId: card.repoId })) return;
    scheduleCard(store, card);
  }
}

export async function runQueuedCard(store: SqliteStore, card: CardDTO): Promise<void> {
  const repo = store.findRepo(card.repoId);
  if (!repo) return block(store, card, 'runner_failed', `Repo ${card.repoId} is not registered.`);
  if (card.taskType === 'Planned') {
    const planned = preflightPlannedSkill(repo.path);
    if (!planned.ok) return block(store, card, 'planned_skill_unavailable', planned.errors.join('; '));
  }
  const root = workspaceRoot();
  const worktree = deterministicWorktree({ cardId: card.id, repoId: card.repoId, repoPath: repo.path, workspaceRoot: root });
  ensureRuntimeDirs(root);
  const running: CardDTO = { ...card, status: 'Running', branch: worktree.branch, worktreePath: worktree.path, updatedAt: new Date().toISOString() };
  store.upsertCard(running);
  store.upsertWorktree({ id: `wt-${card.id}`, cardId: card.id, repoId: card.repoId, path: worktree.path, branch: worktree.branch, status: 'creating' });
  store.upsertRun({ id: runId(card), cardId: card.id, attempt: 1, phase: 'worktree', status: 'running', runnerLease: JSON.stringify({ worktreePath: worktree.path }) });
  append(store, running, 'status_transition', 'Runner started', { from: 'Queued', to: 'Running', branch: worktree.branch, worktreePath: worktree.path });

  const wt = await gitQueue.run(repo.id, async () => prepareGitWorktree(repo, running, worktree.path, worktree.branch));
  if (!wt.ok) return block(store, running, 'collision_detected', wt.error);
  store.upsertWorktree({ id: `wt-${card.id}`, cardId: card.id, repoId: card.repoId, path: worktree.path, branch: worktree.branch, status: 'active' });
  if (wt.reused) append(store, running, 'system', 'Reusing existing card worktree', { branch: worktree.branch, worktreePath: worktree.path });

  const prompt = card.taskType === 'Planned' ? plannedPrompt(card) : quickPrompt(card);
  append(store, running, 'prompt_preview', prompt.slice(0, 1000), { promptPreview: prompt.slice(0, 1000) });
  store.upsertRun({ id: runId(card), cardId: card.id, attempt: 1, phase: 'codex', status: 'running', runnerLease: JSON.stringify({ worktreePath: worktree.path }) });
  const result = await runCodex(prompt, worktree.path, (message, metadata) => append(store, running, 'log', message, metadata));
  if (result !== 0) return block(store, running, 'runner_failed', `codex exec exited ${result}`);
  store.upsertRun({ id: runId(card), cardId: card.id, attempt: 1, phase: 'post_run_git', status: 'succeeded', exitCode: result });
  if (card.taskType === 'Quick') await finalizeQuick(store, running, repo);
  else await gitQueue.run(repo.id, async () => associatePlannedPrOrBlock(store, running, repo));
}

function prepareGitWorktree(repo: RepoDTO, card: CardDTO, path: string, branch: string): { ok: true; reused: boolean } | { ok: false; error: string } {
  const reusable = findReusableWorktree(repo, card, path, branch);
  if (reusable.ok) return { ok: true, reused: true };
  if (reusable.error) return { ok: false, error: reusable.error };
  const created = createGitWorktree(repo, path, branch);
  return created.ok ? { ok: true, reused: false } : created;
}

function findReusableWorktree(repo: RepoDTO, card: CardDTO, path: string, branch: string): { ok: true } | { ok: false; error?: string } {
  if (card.branch !== branch || card.worktreePath !== path) return { ok: false };
  const listed = spawnSync('git', ['worktree', 'list', '--porcelain'], { cwd: repo.path, encoding: 'utf8' });
  if (listed.status !== 0) return { ok: false, error: listed.stderr || 'git worktree list failed' };
  const match = listed.stdout.split('\n\n').find((entry) => {
    const lines = entry.split('\n');
    const listedPath = lines.find((line) => line.startsWith('worktree '))?.slice('worktree '.length);
    const listedBranch = lines.find((line) => line.startsWith('branch '))?.slice('branch '.length);
    return listedPath && canonicalPath(listedPath) === canonicalPath(path) && listedBranch === `refs/heads/${branch}`;
  });
  if (!match) return { ok: false };
  const status = spawnSync('git', ['status', '--porcelain'], { cwd: path, encoding: 'utf8' });
  if (status.status !== 0) return { ok: false, error: status.stderr || 'existing worktree status check failed' };
  if (status.stdout.trim()) return { ok: false, error: 'collision_detected: existing card worktree is dirty' };
  return { ok: true };
}

function canonicalPath(path: string): string {
  try { return realpathSync.native(path); }
  catch { return resolve(path); }
}

function createGitWorktree(repo: RepoDTO, path: string, branch: string): { ok: true } | { ok: false; error: string } {
  const existing = spawnSync('git', ['show-ref', '--verify', '--quiet', `refs/heads/${branch}`], { cwd: repo.path });
  if (existing.status === 0) return { ok: false, error: `collision_detected: local branch ${branch} already exists` };
  const remote = spawnSync('git', ['ls-remote', '--exit-code', '--heads', 'origin', branch], { cwd: repo.path, encoding: 'utf8' });
  const remoteState = classifyRemoteBranchLookup(remote.status);
  if (remoteState === 'exists') return { ok: false, error: `collision_detected: remote branch ${branch} already exists` };
  if (remoteState === 'error') return { ok: false, error: remote.stderr || `collision_detected: remote branch lookup failed for ${branch}` };
  const result = spawnSync('git', ['worktree', 'add', '-b', branch, path], { cwd: repo.path, encoding: 'utf8' });
  if (result.status !== 0) return { ok: false, error: result.stderr || result.stdout || 'git worktree add failed' };
  return { ok: true };
}

function runCodex(prompt: string, cwd: string, sink: (message: string, metadata?: Record<string, unknown>) => void): Promise<number | null> {
  if (process.env.BOARD_DISABLE_CODEX === '1') { sink('Codex disabled by BOARD_DISABLE_CODEX=1', { stream: 'system' }); return Promise.resolve(0); }
  return new Promise((resolveExit) => {
    const child = spawn('codex', ['exec', '--json', '--full-auto', '--sandbox', 'workspace-write', '-c', 'model_reasoning_effort="high"', prompt], { cwd, shell: false, stdio: ['ignore', 'pipe', 'pipe'] });
    child.stdout.on('data', (chunk: Buffer) => sink(String(chunk), { stream: 'stdout' }));
    child.stderr.on('data', (chunk: Buffer) => sink(String(chunk), { stream: 'stderr' }));
    child.on('exit', (code) => resolveExit(code));
  });
}

async function finalizeQuick(store: SqliteStore, card: CardDTO, repo: RepoDTO): Promise<void> {
  const statusEntries = listChangedFileEntries(card.worktreePath ?? '');
  const cleanPaths = statusEntries.map((entry) => entry.path);
  const diffText = collectDiffText(card.worktreePath ?? '', statusEntries);
  const finalization = planQuickFinalization({ changedFiles: cleanPaths, diffText, taskText: card.instructions, checksPresent: false });
  if (finalization.status === 'blocked') return block(store, card, finalization.reason, finalization.reason === 'no_changes_detected' ? 'Codex completed but produced no file changes.' : 'Quick Track touched protected-risk areas.');
  const visualEvidence = captureVisualEvidence(card, cleanPaths);
  if (visualEvidence.error) return block(store, card, 'visual_evidence_missing', visualEvidence.error);
  let prVisualEvidence: { artifacts: PullRequestVisualArtifact[]; paths: string[] };
  try {
    prVisualEvidence = copyVisualEvidenceForPr(card, visualEvidence.artifacts);
  } catch (error) {
    return block(store, card, 'visual_evidence_missing', error instanceof Error ? error.message : String(error));
  }
  for (const artifact of prVisualEvidence.artifacts.length > 0 ? prVisualEvidence.artifacts : visualEvidence.artifacts) {
    append(store, card, 'visual_artifact', `${artifact.kind}: ${artifact.name}`, { ...artifact });
  }
  const prResult = await gitQueue.run(repo.id, async () => commitPushAndCreatePr(card, repo, [...cleanPaths, ...prVisualEvidence.paths], prVisualEvidence.artifacts));
  if (!prResult.ok) return block(store, card, 'runner_failed', prResult.error);
  const ready: CardDTO = { ...card, status: 'PR Ready', updatedAt: new Date().toISOString() };
  store.upsertCard(ready);
  store.upsertPullRequest({ id: `pr-${card.id}`, cardId: card.id, repoId: repo.id, number: prResult.number, url: prResult.url, state: 'OPEN', checksState: 'pending' });
  store.upsertIntegrationJob({ id: `pr-create-${card.id}`, cardId: card.id, repoId: repo.id, type: 'pr_create', status: 'succeeded', lockKey: repo.id, attempts: 1 });
  append(store, ready, 'pr', prResult.url, { url: prResult.url, number: prResult.number });
}

interface ChangedFileEntry { status: string; path: string }

function listChangedFileEntries(cwd: string): ChangedFileEntry[] {
  return spawnSync('git', ['status', '--porcelain'], { cwd, encoding: 'utf8' }).stdout.split('\n').filter(Boolean).map((line) => ({ status: line.slice(0, 2), path: line.slice(3) }));
}

function collectDiffText(cwd: string, changedFiles: ChangedFileEntry[]): string {
  const tracked = changedFiles.filter((entry) => entry.status !== '??').map((entry) => entry.path);
  const untracked = changedFiles.filter((entry) => entry.status === '??').map((entry) => entry.path);
  const trackedDiff = tracked.length ? spawnSync('git', ['diff', '--', ...tracked], { cwd, encoding: 'utf8' }).stdout : '';
  const untrackedText = untracked.map((file) => {
    try { return `diff --git a/${file} b/${file}\n--- /dev/null\n+++ b/${file}\n${readFileSync(resolve(cwd, file), 'utf8')}\n`; }
    catch { return `diff --git a/${file} b/${file}\n[unreadable untracked file]\n`; }
  }).join('\n');
  return `${trackedDiff}\n${untrackedText}`;
}

function commitPushAndCreatePr(card: CardDTO, repo: RepoDTO, paths: string[], visualArtifacts: PullRequestVisualArtifact[] = []): { ok: true; url: string; number: number } | { ok: false; error: string } {
  const add = spawnSync('git', ['add', ...paths], { cwd: card.worktreePath, encoding: 'utf8' });
  if (add.status !== 0) return { ok: false, error: add.stderr || 'git add failed' };
  const commit = spawnSync('git', ['commit', '-m', `Agent Board: ${card.title}`], { cwd: card.worktreePath, encoding: 'utf8' });
  if (commit.status !== 0) return { ok: false, error: commit.stderr || 'git commit failed' };
  const push = spawnSync('git', ['push', '-u', 'origin', card.branch ?? ''], { cwd: card.worktreePath, encoding: 'utf8' });
  if (push.status !== 0) return { ok: false, error: push.stderr || 'git push failed' };
  const pr = spawnSync('gh', ['pr', 'create', '--title', card.title, '--body', pullRequestBody(card, visualArtifacts), '--base', repo.defaultBranch, '--head', card.branch ?? ''], { cwd: card.worktreePath, encoding: 'utf8' });
  if (pr.status !== 0) return { ok: false, error: pr.stderr || 'gh pr create failed' };
  const url = pr.stdout.trim();
  return { ok: true, url, number: Number(url.match(/\/(\d+)$/)?.[1] ?? 0) };
}

function pullRequestBody(card: CardDTO, visualArtifacts: PullRequestVisualArtifact[]): string {
  const body = card.instructions.trim() || 'Agent Board task.';
  const markdown = formatVisualEvidenceMarkdown(visualArtifacts, { repoUrl: githubRepoUrl(card.worktreePath), branch: card.branch });
  return markdown ? `${body}\n\n${markdown}` : body;
}

function githubRepoUrl(cwd: string | undefined): string | undefined {
  if (!cwd) return undefined;
  const result = spawnSync('gh', ['repo', 'view', '--json', 'url', '--jq', '.url'], { cwd, encoding: 'utf8' });
  if (result.status !== 0) return undefined;
  return result.stdout.trim() || undefined;
}

function associatePlannedPrOrBlock(store: SqliteStore, card: CardDTO, repo: RepoDTO): void {
  const push = spawnSync('git', ['push', '-u', 'origin', card.branch ?? ''], { cwd: card.worktreePath, encoding: 'utf8' });
  if (push.status !== 0) return block(store, card, 'runner_failed', push.stderr || 'Planned Track branch push failed.');
  const list = spawnSync('gh', ['pr', 'list', '--head', card.branch ?? '', '--state', 'all', '--json', 'number,url,state,headRefOid'], { cwd: card.worktreePath, encoding: 'utf8' });
  if (list.status !== 0) return block(store, card, 'existing_pr_ambiguous', list.stderr || 'Planned Track PR list failed.');
  const prs = JSON.parse(list.stdout) as Array<{ number: number; url: string; state: string; headRefOid?: string }>;
  const associated = pickOpenPrForBranch(prs.map((pr) => ({ number: pr.number, url: pr.url, state: pr.state === 'MERGED' ? 'MERGED' : pr.state === 'CLOSED' ? 'CLOSED' : 'OPEN', headRefOid: pr.headRefOid })));
  if (associated && 'ambiguous' in associated) return block(store, card, 'existing_pr_ambiguous', 'Multiple open PRs match the Planned Track branch.');
  if (associated && 'stale' in associated) return block(store, card, 'existing_pr_ambiguous', `Only stale Planned Track PRs exist (${associated.state}); operator review required.`);
  if (associated) return persistAssociatedPr(store, card, associated.number, associated.url, associated.state, associated.headRefOid);
  const create = spawnSync('gh', ['pr', 'create', '--title', card.title, '--body', card.instructions, '--base', repo.defaultBranch, '--head', card.branch ?? ''], { cwd: card.worktreePath, encoding: 'utf8' });
  if (create.status !== 0) return block(store, card, 'existing_pr_ambiguous', create.stderr || 'No Planned Track PR could be created.');
  const url = create.stdout.trim();
  persistAssociatedPr(store, card, Number(url.match(/\/(\d+)$/)?.[1] ?? 0), url, 'OPEN');
}

function persistAssociatedPr(store: SqliteStore, card: CardDTO, number: number, url: string, state: string, headRefOid?: string): void {
  const ready: CardDTO = { ...card, status: 'PR Ready', updatedAt: new Date().toISOString() };
  store.upsertCard(ready);
  store.upsertPullRequest({ id: `pr-${card.id}`, cardId: card.id, repoId: card.repoId, number, url, state, headRefOid });
  append(store, ready, 'pr', url, { number, url, state, headRefOid });
}

export async function cleanupMergedCard(store: SqliteStore, cardId: string): Promise<{ ok: true } | { ok: false; error: string }> {
  const card = store.findCard(cardId);
  if (!card?.worktreePath) return { ok: false, error: 'cleanup_blocked: card/worktree missing' };
  const repo = store.findRepo(card.repoId);
  if (!repo) return { ok: false, error: 'cleanup_blocked: repo missing' };
  const pr = spawnSync('gh', ['pr', 'view', card.branch ?? '', '--json', 'mergedAt,state'], { cwd: card.worktreePath, encoding: 'utf8' });
  if (pr.status !== 0) return { ok: false, error: pr.stderr || 'cleanup_blocked: PR lookup failed' };
  const parsed = JSON.parse(pr.stdout) as { mergedAt?: string | null; state?: string };
  if (!parsed.mergedAt && parsed.state !== 'MERGED') return { ok: false, error: 'cleanup_blocked: PR is not merged' };
  try {
    return await gitQueue.run(repo.id, async () => {
      removeCleanWorktree(repo.path, card.worktreePath!, true, true);
      store.markWorktreeCleaned(card.id);
      store.upsertCard({ ...card, status: 'Done', updatedAt: new Date().toISOString() });
      return { ok: true as const };
    });
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : String(error) };
  }
}

export async function discardCard(store: SqliteStore, cardId: string): Promise<{ ok: true } | { ok: false; error: string }> {
  const card = store.findCard(cardId);
  if (!card) return { ok: false, error: 'card not found' };
  const repo = store.findRepo(card.repoId);
  if (!repo) return { ok: false, error: 'discard_blocked: repo missing' };
  if (!card.branch && !card.worktreePath) {
    store.deleteCard(cardId);
    return { ok: true };
  }
  if (!card.branch || !card.worktreePath) return { ok: false, error: 'discard_blocked: branch/worktree missing' };
  const branch = card.branch;
  const worktreePath = card.worktreePath;
  const pr = store.read().pullRequests.find((candidate) => candidate.cardId === cardId);
  if (pr?.state === 'MERGED') return { ok: false, error: 'discard_blocked: PR is already merged; use merged cleanup' };

  const result = await gitQueue.run(repo.id, async () => {
    let prState = pr?.state;
    const commandCwd = existsSync(worktreePath) ? worktreePath : repo.path;
    if (pr && prState !== 'CLOSED' && process.env.BOARD_SKIP_GH_PR_CLOSE !== '1') {
      const view = spawnSync('gh', ['pr', 'view', String(pr.number), '--json', 'state,mergedAt'], { cwd: commandCwd, encoding: 'utf8' });
      if (view.status !== 0) return view.stderr || view.stdout || 'gh pr view failed';
      const parsed = JSON.parse(view.stdout) as { state?: string; mergedAt?: string | null };
      if (parsed.mergedAt || parsed.state === 'MERGED') return 'discard_blocked: PR is already merged; use merged cleanup';
      prState = parsed.state ?? prState;
    }
    if (pr && prState !== 'CLOSED' && process.env.BOARD_SKIP_GH_PR_CLOSE !== '1') {
      const close = spawnSync('gh', ['pr', 'close', String(pr.number), '--delete-branch'], { cwd: commandCwd, encoding: 'utf8' });
      if (close.status !== 0) return close.stderr || close.stdout || 'gh pr close failed';
    }
    if (existsSync(worktreePath)) {
      const remove = spawnSync('git', ['worktree', 'remove', '--force', worktreePath], { cwd: repo.path, encoding: 'utf8' });
      if (remove.status !== 0) return remove.stderr || remove.stdout || 'git worktree remove failed';
    }
    const branchExists = spawnSync('git', ['show-ref', '--verify', '--quiet', `refs/heads/${branch}`], { cwd: repo.path });
    if (branchExists.status === 0) {
      const deleteBranch = spawnSync('git', ['branch', '-D', branch], { cwd: repo.path, encoding: 'utf8' });
      if (deleteBranch.status !== 0) return deleteBranch.stderr || deleteBranch.stdout || 'git branch delete failed';
    }
    return undefined;
  });
  if (result) return { ok: false, error: result };
  store.deleteCard(cardId);
  return { ok: true };
}

export function resumeCard(store: SqliteStore, cardId: string, note: string): { ok: true; card: CardDTO } | { ok: false; error: string } {
  const card = store.findCard(cardId);
  if (!card) return { ok: false, error: 'card not found' };
  const queued: CardDTO = { ...card, instructions: `${card.instructions}\n\nOperator resume note:\n${note}`, status: 'Queued', blockerReason: undefined, blockerSummary: undefined, overridePaused: false, updatedAt: new Date().toISOString() };
  store.upsertCard(queued);
  append(store, queued, 'system', 'Card resumed with operator note', { note });
  scheduleCard(store, queued);
  return { ok: true, card: queued };
}

export function manualMoveCard(store: SqliteStore, cardId: string, status: CardDTO['status']): { ok: true; card: CardDTO } | { ok: false; error: string } {
  const card = store.findCard(cardId);
  if (!card) return { ok: false, error: 'card not found' };
  const startsRun = status === 'Queued' || status === 'Running';
  const nextStatus = startsRun ? 'Queued' : status;
  if (card.status === nextStatus) return { ok: true, card };
  if (!canTransition(card.status, nextStatus)) return { ok: false, error: `invalid transition ${card.status} -> ${nextStatus}` };
  const moved: CardDTO = { ...card, status: nextStatus, overridePaused: startsRun ? false : true, updatedAt: new Date().toISOString() };
  store.upsertCard(moved);
  append(store, moved, 'status_transition', startsRun ? 'Card queued from board' : 'Manual operator move', { from: card.status, to: nextStatus, overridePaused: moved.overridePaused });
  if (startsRun) {
    store.upsertRun({ id: runId(card), cardId: card.id, attempt: 1, phase: 'preflight', status: 'running', runnerLease: JSON.stringify({ createdAt: new Date().toISOString() }) });
    scheduleCard(store, moved);
  }
  return { ok: true, card: moved };
}

export function pollPrState(store: SqliteStore, cardId: string): { ok: true; card: CardDTO } | { ok: false; error: string } {
  const card = store.findCard(cardId);
  if (!card?.worktreePath || !card.branch) return { ok: false, error: 'PR polling requires branch/worktree' };
  const view = spawnSync('gh', ['pr', 'view', card.branch, '--json', 'number,url,state,mergedAt,headRefOid,statusCheckRollup,isDraft'], { cwd: card.worktreePath, encoding: 'utf8' });
  if (view.status !== 0) return { ok: false, error: view.stderr || 'gh pr view failed' };
  const parsed = JSON.parse(view.stdout) as { number: number; url: string; state: string; mergedAt?: string | null; headRefOid?: string; isDraft?: boolean };
  const nextStatus: CardDTO['status'] = parsed.mergedAt || parsed.state === 'MERGED' ? 'Merged' : 'PR Ready';
  const updated: CardDTO = { ...card, status: nextStatus, updatedAt: new Date().toISOString() };
  store.upsertCard(updated);
  store.upsertPullRequest({ id: `pr-${card.id}`, cardId: card.id, repoId: card.repoId, number: parsed.number, url: parsed.url, state: parsed.state, headRefOid: parsed.headRefOid });
  append(store, updated, 'pr', parsed.url, parsed);
  if (nextStatus === 'Merged') void cleanupMergedCard(store, card.id);
  return { ok: true, card: updated };
}

export async function autoMergeCard(store: SqliteStore, cardId: string): Promise<{ ok: true } | { ok: false; error: string }> {
  const card = store.findCard(cardId);
  if (!card?.worktreePath || !card.branch || !card.autoMerge) return { ok: false, error: 'auto-merge not enabled or PR missing' };
  const view = spawnSync('gh', ['pr', 'view', card.branch, '--json', 'number,url,state,headRefOid,mergeable,isDraft,statusCheckRollup'], { cwd: card.worktreePath, encoding: 'utf8' });
  if (view.status !== 0) return { ok: false, error: view.stderr || 'gh pr view failed' };
  const parsed = JSON.parse(view.stdout) as { number: number; headRefOid?: string; mergeable?: string; isDraft?: boolean; state?: string; statusCheckRollup?: unknown[] };
  const checksState = deriveChecksState(parsed.statusCheckRollup);
  const allowed = canAutoMerge({ number: parsed.number, url: '', state: parsed.state === 'OPEN' ? 'OPEN' : 'CLOSED', headRefOid: parsed.headRefOid, mergeable: parsed.mergeable === 'MERGEABLE' ? 'MERGEABLE' : parsed.mergeable === 'CONFLICTING' ? 'CONFLICTING' : 'UNKNOWN', checksState, isDraft: parsed.isDraft }, { enabled: true, protectedRisk: card.blockerReason === 'protected_risk', unresolvedBlocker: Boolean(card.blockerReason), allowNoCheck: false, taskType: card.taskType });
  if (!allowed || !parsed.headRefOid) return { ok: false, error: 'auto-merge guardrails failed' };
  const repo = store.findRepo(card.repoId);
  if (!repo) return { ok: false, error: 'repo missing for auto-merge' };
  const expectedHead = parsed.headRefOid;
  const mergeError = await gitQueue.run(repo.id, async () => {
    const mergeResult = spawnSync('gh', ['pr', 'merge', String(parsed.number), '--auto', '--squash', '--match-head-commit', expectedHead], { cwd: card.worktreePath, encoding: 'utf8' });
    return mergeResult.status !== 0 ? mergeResult.stderr || 'gh pr merge failed' : undefined;
  });
  if (mergeError) return { ok: false, error: mergeError };
  store.upsertIntegrationJob({ id: `auto-merge-${card.id}`, cardId: card.id, repoId: card.repoId, type: 'auto_merge', status: 'queued', lockKey: card.repoId, attempts: 1 });
  append(store, card, 'pr', 'Auto-merge queued', { number: parsed.number, headRefOid: parsed.headRefOid });
  return { ok: true };
}

function deriveChecksState(rollup: unknown[] | undefined): 'absent' | 'pending' | 'passed' | 'failed' {
  if (!Array.isArray(rollup) || rollup.length === 0) return 'absent';
  const conclusions = rollup.map((item) => typeof item === 'object' && item ? String((item as Record<string, unknown>).conclusion ?? (item as Record<string, unknown>).status ?? '').toUpperCase() : '');
  if (conclusions.some((value) => ['FAILURE', 'FAILED', 'ERROR', 'CANCELLED', 'TIMED_OUT'].includes(value))) return 'failed';
  if (conclusions.every((value) => ['SUCCESS', 'PASSED', 'COMPLETED'].includes(value))) return 'passed';
  return 'pending';
}

function block(store: SqliteStore, card: CardDTO, reason: CardDTO['blockerReason'], summary: string): void {
  const blocked: CardDTO = { ...card, status: 'Blocked', blockerReason: reason, blockerSummary: summary, updatedAt: new Date().toISOString() };
  store.upsertCard(blocked);
  store.upsertRun({ id: runId(card), cardId: card.id, attempt: 1, phase: 'blocked', status: 'blocked', error: summary });
  append(store, blocked, 'blocker', summary, { reason });
}
function append(store: SqliteStore, card: CardDTO, type: RunEventDTO['type'], message: string, metadata?: Record<string, unknown>): void { store.appendEvent({ id: randomUUID(), runId: runId(card), cardId: card.id, timestamp: new Date().toISOString(), type, message, metadata }); }
function runId(card: CardDTO): string { return `run-${card.id}`; }
function quickPrompt(card: CardDTO): string { return `Quick Track Agent Board task. Make the smallest safe change. Do not commit.\n\nTitle: ${card.title}\nInstructions:\n${card.instructions}`; }
function plannedPrompt(card: CardDTO): string { return `$plan-and-execute --refine-plan\n\nAgent Board Planned Track task. Work in this board-created branch/worktree. The board preflight verified the Prime Directive skill file from the spawned Codex context before launch.\n\nTitle: ${card.title}\nInstructions:\n${card.instructions}`; }
