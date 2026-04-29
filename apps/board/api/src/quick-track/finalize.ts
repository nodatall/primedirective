import { classifyProtectedRisk } from './protectedRisk.js';

export interface QuickFinalizeInput {
  changedFiles: string[];
  diffText: string;
  taskText: string;
  checksPresent: boolean;
}

export function planQuickFinalization(input: QuickFinalizeInput) {
  if (input.changedFiles.length === 0) return { status: 'blocked' as const, reason: 'no_changes_detected' as const, actions: [] as string[] };
  const risk = classifyProtectedRisk(input.changedFiles, input.diffText, input.taskText);
  if (risk.risky) return { status: 'blocked' as const, reason: 'protected_risk' as const, actions: [] as string[], risk };
  return { status: 'ready' as const, actions: ['git add', 'git commit', 'git push', 'gh pr create'] };
}
