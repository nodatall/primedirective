import { spawnSync } from 'node:child_process';
import type { PullRequestDTO, WorkflowOverride } from '@prime-board/shared';

export function findExistingPrForBranch(prs: PullRequestDTO[]): PullRequestDTO | { ambiguous: true } | undefined {
  if (prs.length > 1) return { ambiguous: true };
  return prs[0];
}

export function canAutoMerge(pr: PullRequestDTO, options: { enabled: boolean; protectedRisk: boolean; unresolvedBlocker: boolean; allowNoCheck: boolean; taskType: 'Quick' | 'Planned' }): boolean {
  if (!options.enabled || options.protectedRisk || options.unresolvedBlocker) return false;
  if (pr.state !== 'OPEN' || pr.isDraft) return false;
  if (!pr.headRefOid || pr.mergeable !== 'MERGEABLE') return false;
  if (pr.checksState === 'passed') return true;
  return pr.checksState === 'absent' && options.taskType === 'Quick' && options.allowNoCheck;
}

export function resolveNoCheckOverride(config: WorkflowOverride | undefined): boolean {
  return config?.allowQuickNoCheckAutomerge === true;
}

export function mergePrWithExpectedHead(repoPath: string, prNumber: number, expectedHeadSha: string): void {
  const result = spawnSync('gh', ['pr', 'merge', String(prNumber), '--auto', '--squash', '--match-head-commit', expectedHeadSha], { cwd: repoPath, stdio: 'pipe', encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout || 'gh pr merge failed');
}

export function classifyRemoteBranchLookup(status: number | null): 'exists' | 'absent' | 'error' {
  if (status === 0) return 'exists';
  if (status === 2) return 'absent';
  return 'error';
}

export function pickOpenPrForBranch(prs: PullRequestDTO[]): PullRequestDTO | { ambiguous: true } | { stale: true; state: string } | undefined {
  const open = prs.filter((pr) => pr.state === 'OPEN');
  if (open.length > 1) return { ambiguous: true };
  if (open.length === 1) return open[0];
  if (prs.length > 0) return { stale: true, state: prs.map((pr) => pr.state).join(',') };
  return undefined;
}
