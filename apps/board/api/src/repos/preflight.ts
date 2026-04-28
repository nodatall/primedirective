import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

export interface PreflightResult { ok: boolean; errors: string[] }

const boardRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');

function hasCommand(command: string): boolean {
  const result = spawnSync(command, ['--version'], { stdio: 'ignore' });
  return result.status === 0;
}

export function preflightRepo(repoPath: string): PreflightResult {
  const errors: string[] = [];
  const abs = resolve(repoPath);
  if (!existsSync(abs)) errors.push('repo path does not exist');
  if (!existsSync(join(abs, '.git'))) errors.push('repo path is not a git worktree root');
  if (!hasCommand('git')) errors.push('git CLI unavailable');
  if (!hasCommand('gh')) errors.push('gh CLI unavailable');
  if (!hasCommand('codex')) errors.push('Codex CLI unavailable');
  return { ok: errors.length === 0, errors };
}

export function preflightPlannedSkill(repoPath: string): PreflightResult {
  if (process.env.BOARD_SKIP_PLANNED_SKILL_PROBE === '1') return { ok: true, errors: [] };
  const localSkill = join(boardRoot, '..', '..', 'skills', 'plan-and-execute', 'SKILL.md');
  if (!existsSync(localSkill)) return { ok: false, errors: ['planned_skill_unavailable: Prime Directive plan-and-execute skill file is missing'] };
  const prompt = [
    'Read-only Agent Board Planned Track preflight.',
    `Inspect this exact Prime Directive skill file from the spawned Codex session cwd: ${localSkill}`,
    'Do not modify files.',
    'Reply with exactly PLAN_AND_EXECUTE_AVAILABLE only if that file is readable, its frontmatter name is plan-and-execute, and it documents the --refine-plan modifier.',
    'If any check fails, reply with exactly PLAN_AND_EXECUTE_UNAVAILABLE.'
  ].join('\n');
  const result = spawnSync('codex', ['exec', '--json', '--full-auto', '--sandbox', 'read-only', prompt], { cwd: resolve(repoPath), encoding: 'utf8', timeout: 120000 });
  if (result.status !== 0) return { ok: false, errors: [`planned_skill_unavailable: Codex skill resolution probe failed: ${result.stderr || result.stdout}`] };
  if (!result.stdout.includes('PLAN_AND_EXECUTE_AVAILABLE')) return { ok: false, errors: ['planned_skill_unavailable: spawned Codex session did not confirm plan-and-execute availability'] };
  return { ok: true, errors: [] };
}
