#!/usr/bin/env node
import { spawn } from 'node:child_process';
import { rmSync } from 'node:fs';

const dbPath = new URL('../data/e2e.sqlite', import.meta.url).pathname;
rmSync(dbPath, { force: true });
const env = { ...process.env, BOARD_DISABLE_CODEX: '1', BOARD_SKIP_PLANNED_SKILL_PROBE: '1', BOARD_DB_PATH: dbPath, BOARD_WORKSPACE_ROOT: new URL('../worktrees', import.meta.url).pathname, BOARD_ALLOWED_ORIGINS: 'http://127.0.0.1:5178,http://localhost:5178' };
const api = spawn('npm', ['run', 'start', '--workspace', '@prime-board/api'], { stdio: 'inherit', env });
const web = spawn('npm', ['run', 'dev', '--workspace', '@prime-board/web', '--', '--host', '127.0.0.1', '--port', '5178'], { stdio: 'inherit', env });
function shutdown() { api.kill('SIGTERM'); web.kill('SIGTERM'); }
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
api.on('exit', (code) => { if (code && code !== 143) process.exit(code); });
web.on('exit', (code) => { if (code && code !== 143) process.exit(code); });
