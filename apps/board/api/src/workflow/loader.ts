import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { WorkflowOverride } from '@prime-board/shared';

const allowedKeys = new Set(['allowQuickNoCheckAutomerge', 'maxActiveRuns', 'maxActiveCardsPerRepo', 'protectedRiskExtraPatterns']);
const forbidden = new Set(['disableProtectedRisk', 'allowAdminMerge', 'forceCleanup', 'disableCwdContainment', 'disableGitCriticalSections']);

export interface WorkflowLoadResult {
  config: WorkflowOverride;
  errors: string[];
}

export function parseAgentBoardMarkdown(markdown: string): WorkflowLoadResult {
  const config: WorkflowOverride = {};
  const errors: string[] = [];
  for (const raw of markdown.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes(':')) continue;
    const [key, ...rest] = line.split(':');
    const value = rest.join(':').trim();
    if (forbidden.has(key)) {
      errors.push(`${key} weakens immutable board safety invariants`);
      continue;
    }
    if (!allowedKeys.has(key)) {
      errors.push(`${key} is not an allowlisted AGENT_BOARD.md key`);
      continue;
    }
    if (key === 'allowQuickNoCheckAutomerge') config.allowQuickNoCheckAutomerge = value === 'true';
    if (key === 'maxActiveRuns') config.maxActiveRuns = Number(value);
    if (key === 'maxActiveCardsPerRepo') config.maxActiveCardsPerRepo = Number(value);
    if (key === 'protectedRiskExtraPatterns') config.protectedRiskExtraPatterns = value.split(',').map((v) => v.trim()).filter(Boolean);
  }
  if (config.allowQuickNoCheckAutomerge !== undefined && config.allowQuickNoCheckAutomerge !== true && config.allowQuickNoCheckAutomerge !== false) errors.push('allowQuickNoCheckAutomerge must be boolean');
  return { config, errors };
}

export function loadWorkflow(repoPath: string): WorkflowLoadResult {
  const file = join(repoPath, 'AGENT_BOARD.md');
  if (!existsSync(file)) return { config: {}, errors: [] };
  return parseAgentBoardMarkdown(readFileSync(file, 'utf8'));
}
