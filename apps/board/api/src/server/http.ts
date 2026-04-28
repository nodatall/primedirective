import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { randomUUID } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SqliteStore } from '../db/sqliteStore.js';
import { rejectUnsafeOrigin, resolveHost } from './security.js';
import { autoMergeCard, cleanupMergedCard, createCard, drainQueuedCards, manualMoveCard, pollPrState, resumeCard } from '../orchestrator/cardLifecycle.js';
import { reconcileStartup } from '../orchestrator/reconcile.js';
import type { CardDTO, RepoDTO } from '@prime-board/shared';

const boardRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const defaultDbPath = resolve(boardRoot, 'data/board.sqlite');

async function readJson<T>(req: IncomingMessage): Promise<T> { const chunks: Buffer[] = []; for await (const chunk of req) chunks.push(Buffer.from(chunk)); return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}') as T; }
function send(res: ServerResponse, status: number, body: unknown): void { res.statusCode = status; res.setHeader('content-type', 'application/json'); res.end(JSON.stringify(body)); }

export function makeBoardServer(store = new SqliteStore(process.env.BOARD_DB_PATH ?? defaultDbPath)) {
  reconcileStartup(store);
  drainQueuedCards(store);
  return createServer(async (req, res) => {
    if (rejectUnsafeOrigin(req, res)) return;
    const url = new URL(req.url ?? '/', 'http://127.0.0.1');
    if (req.method === 'GET' && url.pathname === '/health') return send(res, 200, { ok: true });
    if (req.method === 'GET' && url.pathname === '/api/snapshot') return send(res, 200, store.read());
    if (req.method === 'POST' && url.pathname === '/api/repos') {
      const body = await readJson<Partial<RepoDTO>>(req);
      const repo: RepoDTO = { id: body.id ?? randomUUID(), name: body.name ?? 'Repo', path: body.path ?? '', defaultBranch: body.defaultBranch ?? 'main', remoteUrl: body.remoteUrl };
      store.upsertRepo(repo);
      return send(res, 201, { repo });
    }
    if (req.method === 'POST' && url.pathname === '/api/cards') return send(res, 201, { card: createCard(store, await readJson<Partial<CardDTO>>(req)) });
    const actionMatch = url.pathname.match(/^\/api\/cards\/([^/]+)\/(resume|move|poll|automerge|cleanup)$/);
    if (req.method === 'POST' && actionMatch) {
      const [, cardId, action] = actionMatch;
      const body = await readJson<{ note?: string; status?: CardDTO['status'] }>(req);
      const result = action === 'resume' ? resumeCard(store, cardId, body.note ?? '')
        : action === 'move' ? manualMoveCard(store, cardId, body.status ?? 'Blocked')
        : action === 'poll' ? pollPrState(store, cardId)
        : action === 'automerge' ? await autoMergeCard(store, cardId)
        : await cleanupMergedCard(store, cardId);
      return send(res, result.ok ? 200 : 409, result);
    }
    send(res, 404, { error: 'not_found' });
  });
}

export function startBoardServer(port = Number(process.env.BOARD_PORT ?? 4782), host = resolveHost()) { const server = makeBoardServer(); server.listen(port, host); return server; }
