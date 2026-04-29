import { mkdirSync } from 'node:fs';
import { basename, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

export interface WorktreeSpec { cardId: string; repoId: string; repoPath: string; workspaceRoot: string }
export interface WorktreeRecord { branch: string; path: string }
export interface ExistingOwnership { cardId: string; branch: string; path: string; dirty?: boolean }

export function deterministicWorktree(spec: WorktreeSpec): WorktreeRecord {
  const safeRepo = basename(spec.repoPath).replace(/[^a-zA-Z0-9._-]/g, '-');
  const safeCard = spec.cardId.replace(/[^a-zA-Z0-9._-]/g, '-');
  return {
    branch: `agent-board/${safeRepo}/${safeCard}`,
    path: resolve(spec.workspaceRoot, `${safeRepo}-${safeCard}`)
  };
}

export function assertInsideWorkspace(workspaceRoot: string, path: string): void {
  const root = resolve(workspaceRoot);
  const target = resolve(path);
  if (!(target === root || target.startsWith(`${root}/`))) throw new Error('worktree path escapes workspace root');
}

export function assertCodexCwd(worktreePath: string, cwd: string): void {
  if (resolve(worktreePath) !== resolve(cwd)) throw new Error('Codex cwd must equal card worktree path');
}

export function collisionCheck(target: WorktreeRecord, existing: ExistingOwnership | undefined, cardId: string): void {
  if (!existing) return;
  if (existing.cardId !== cardId) throw new Error('collision_detected: branch/worktree owned by another card');
  if (existing.branch !== target.branch || resolve(existing.path) !== resolve(target.path)) throw new Error('collision_detected: same-card ownership mismatch');
  if (existing.dirty) throw new Error('collision_detected: existing worktree is dirty');
}

export function ensureRuntimeDirs(root: string): void {
  mkdirSync(root, { recursive: true });
}

export function removeCleanWorktree(repoPath: string, path: string, clean: boolean, merged: boolean): void {
  if (!clean || !merged) throw new Error('cleanup_blocked');
  const status = spawnSync('git', ['-C', path, 'status', '--porcelain'], { encoding: 'utf8' });
  if (status.status !== 0 || status.stdout.trim()) throw new Error('cleanup_blocked');
  const result = spawnSync('git', ['worktree', 'remove', path], { cwd: repoPath, encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout || 'cleanup_blocked');
}
