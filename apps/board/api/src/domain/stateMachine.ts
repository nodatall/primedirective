import type { BlockerReason, CardStatus } from '@prime-board/shared';

const transitions: Record<CardStatus, CardStatus[]> = {
  Inbox: ['Queued', 'Abandoned'],
  Queued: ['Running', 'Blocked', 'Abandoned'],
  Running: ['Blocked', 'PR Ready', 'Checks Pending', 'Abandoned'],
  Blocked: ['Queued', 'Abandoned'],
  'PR Ready': ['Checks Pending', 'Merging', 'Done', 'Blocked', 'Abandoned'],
  'Checks Pending': ['Merging', 'Blocked', 'PR Ready'],
  Merging: ['Merged', 'Blocked'],
  Merged: ['Done', 'Blocked'],
  Done: [],
  Abandoned: []
};

export function canTransition(from: CardStatus, to: CardStatus): boolean {
  return transitions[from]?.includes(to) ?? false;
}

export function assertTransition(from: CardStatus, to: CardStatus): void {
  if (!canTransition(from, to)) throw new Error(`invalid transition ${from} -> ${to}`);
}

export function manualOverride(status: CardStatus): { status: CardStatus; overridePaused: true } {
  return { status, overridePaused: true };
}

export function blocker(reason: BlockerReason, summary: string) {
  return { status: 'Blocked' as const, blockerReason: reason, blockerSummary: summary };
}
