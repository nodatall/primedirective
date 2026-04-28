import { expect, request, test } from '@playwright/test';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

function makeRepo(): string {
  const repo = mkdtempSync(join(tmpdir(), 'agent-board-e2e-repo-'));
  const remote = mkdtempSync(join(tmpdir(), 'agent-board-e2e-remote-'));
  spawnSync('git', ['init', '--bare'], { cwd: remote, stdio: 'ignore' });
  spawnSync('git', ['init', '-b', 'main'], { cwd: repo, stdio: 'ignore' });
  spawnSync('git', ['config', 'user.email', 'board@example.test'], { cwd: repo, stdio: 'ignore' });
  spawnSync('git', ['config', 'user.name', 'Board Test'], { cwd: repo, stdio: 'ignore' });
  writeFileSync(join(repo, 'README.md'), '# fixture\n');
  spawnSync('git', ['add', 'README.md'], { cwd: repo, stdio: 'ignore' });
  spawnSync('git', ['commit', '-m', 'initial'], { cwd: repo, stdio: 'ignore' });
  spawnSync('git', ['remote', 'add', 'origin', remote], { cwd: repo, stdio: 'ignore' });
  spawnSync('git', ['push', '-u', 'origin', 'main'], { cwd: repo, stdio: 'ignore' });
  return repo;
}

test('creates a card through the real API-backed board and observes backend state', async ({ page }) => {
  const api = await request.newContext({ baseURL: 'http://127.0.0.1:4782', extraHTTPHeaders: { origin: 'http://127.0.0.1:5178' } });
  await api.post('/api/repos', { data: { id: 'prime', name: 'fixture', path: makeRepo(), defaultBranch: 'main' } });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Agent Board' })).toBeVisible();
  await page.getByLabel('Title').fill('No-op quick card');
  await page.getByLabel('Repo').fill('prime');
  await page.getByLabel('Instructions').fill('Inspect only and make no changes.');
  await page.getByRole('button', { name: 'Queue card' }).click();
  await expect(page.getByText('No-op quick card')).toBeVisible();
  await expect(page.getByText('Codex completed but produced no file changes.')).toBeVisible({ timeout: 10_000 });
  await page.getByText('No-op quick card').click();
  await expect(page.getByLabel('Card detail')).toContainText('no_changes_detected');
});
