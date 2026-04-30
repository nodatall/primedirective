import { existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { chromium } from 'playwright';

const args = new Map();
for (let index = 2; index < process.argv.length; index += 2) args.set(process.argv[index], process.argv[index + 1]);

const worktree = args.get('--worktree');
const cardId = args.get('--card-id');
if (!worktree || !cardId) {
  console.error('usage: capture-visual-evidence.mjs --worktree PATH --card-id ID');
  process.exit(2);
}

const boardRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const target = resolve(worktree, 'apps/board/web');
if (!existsSync(resolve(target, 'package.json'))) {
  console.error(`No supported visual evidence target found in ${worktree}`);
  process.exit(2);
}

const artifactDir = resolve(boardRoot, 'artifacts/cards', cardId, 'visual');
mkdirSync(artifactDir, { recursive: true });

const server = await createServer({
  root: target,
  configFile: false,
  logLevel: 'silent',
  plugins: [react(), tailwindcss()],
  server: {
    host: '127.0.0.1',
    port: 0,
    proxy: {
      '/api': 'http://127.0.0.1:4782',
      '/health': 'http://127.0.0.1:4782'
    }
  },
  resolve: {
    alias: {
      '@prime-board/shared': resolve(worktree, 'apps/board/shared/src/index.ts')
    }
  }
});

let browser;
try {
  await server.listen();
  const url = server.resolvedUrls?.local?.[0];
  if (!url) throw new Error('Vite server did not expose a local URL.');
  browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  });

  const viewports = [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'mobile', width: 390, height: 844 }
  ];
  const artifacts = [];
  for (const viewport of viewports) {
    const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } });
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(1000);
    const path = resolve(artifactDir, `${viewport.name}.png`);
    await page.screenshot({ path, fullPage: true });
    await page.close();
    artifacts.push({ kind: 'screenshot', name: viewport.name, path, viewport: { width: viewport.width, height: viewport.height }, url });
  }
  process.stdout.write(JSON.stringify({ artifacts }));
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await server.close();
}
