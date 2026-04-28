import type { CardDTO, RepoDTO } from '../../contracts';

export const repos: RepoDTO[] = [{ id: 'prime', name: 'primedirective', path: '/Volumes/Code/primedirective', defaultBranch: 'main' }];

export const cards: CardDTO[] = [
  { id: 'quick-color', repoId: 'prime', title: 'Change button accent', instructions: 'Small localized UI change', taskType: 'Quick', autoMerge: true, status: 'Queued', updatedAt: new Date().toISOString() },
  { id: 'planned-board', repoId: 'prime', title: 'Agent Board vertical slice', instructions: '$plan-and-execute --refine-plan', taskType: 'Planned', autoMerge: false, status: 'Running', branch: 'agent-board/primedirective/planned-board', worktreePath: 'apps/board/worktrees/primedirective-planned-board', updatedAt: new Date().toISOString() },
  { id: 'blocked-risk', repoId: 'prime', title: 'Billing copy cleanup', instructions: 'Touches billing surface', taskType: 'Quick', autoMerge: false, status: 'Blocked', blockerReason: 'protected_risk', blockerSummary: 'Quick Track touched protected billing/auth areas.', updatedAt: new Date().toISOString() }
];
