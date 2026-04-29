import type { BlockerReason, CardDTO } from '@prime-board/shared';
import type { SqliteStore } from '../db/sqliteStore.js';

export interface RunnerLease { pid?: number; worktreePath: string; startedAt: string }

export function reconcileActiveRunner(lease: RunnerLease | undefined): { status: 'ok' | 'blocked'; reason?: BlockerReason; summary?: string } {
  if (!lease) return { status: 'ok' };
  return { status: 'blocked', reason: 'restart_quarantined', summary: `Runner lease for ${lease.worktreePath} requires operator review after restart.` };
}

export function reconcileStartup(store: SqliteStore): void {
  for (const card of store.read().cards.filter((candidate) => candidate.status === 'Running')) {
    const summary = `Card was Running during API startup and was quarantined for operator review.`;
    const blocked: CardDTO = { ...card, status: 'Blocked', blockerReason: 'restart_quarantined', blockerSummary: summary, updatedAt: new Date().toISOString() };
    store.upsertCard(blocked);
  }
}
