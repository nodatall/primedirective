import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { randomUUID } from 'node:crypto';
import { createReadStream, realpathSync, statSync } from 'node:fs';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SqliteStore } from '../db/sqliteStore.js';
import { rejectUnsafeOrigin, resolveHost } from './security.js';
import { autoMergeCard, cleanupMergedCard, createCard, discardCard, drainQueuedCards, manualMoveCard, pollPrState, resumeCard, updateInboxCard } from '../orchestrator/cardLifecycle.js';
import { reconcileStartup } from '../orchestrator/reconcile.js';
import type { CardDTO, RepoDTO } from '@prime-board/shared';

const boardRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const defaultDbPath = resolve(boardRoot, 'data/board.sqlite');
const artifactRoot = resolve(boardRoot, 'artifacts');

async function readJson<T>(req: IncomingMessage): Promise<T> { const chunks: Buffer[] = []; for await (const chunk of req) chunks.push(Buffer.from(chunk)); return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}') as T; }
function send(res: ServerResponse, status: number, body: unknown): void { res.statusCode = status; res.setHeader('content-type', 'application/json'); res.end(JSON.stringify(body)); }
function sendArtifact(res: ServerResponse, path: string | null): void {
  if (!path) return send(res, 400, { error: 'artifact_path_required' });
  try {
    const target = realpathSync.native(path);
    const root = canonicalPath(artifactRoot);
    if (!(target === root || target.startsWith(`${root}/`))) return send(res, 403, { error: 'artifact_path_forbidden' });
    if (!statSync(target).isFile()) return send(res, 404, { error: 'artifact_not_found' });
    res.statusCode = 200;
    res.setHeader('content-type', contentTypeFor(target));
    createReadStream(target).pipe(res);
  } catch {
    send(res, 404, { error: 'artifact_not_found' });
  }
}

function canonicalPath(path: string): string {
  try { return realpathSync.native(path); }
  catch { return resolve(path); }
}

function contentTypeFor(path: string): string {
  const ext = extname(path).toLowerCase();
  if (ext === '.png') return 'image/png';
  if (ext === '.webm') return 'video/webm';
  if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
  return 'application/octet-stream';
}

export function makeBoardServer(store = new SqliteStore(process.env.BOARD_DB_PATH ?? defaultDbPath)) {
  reconcileStartup(store);
  drainQueuedCards(store);
  return createServer(async (req, res) => {
    if (rejectUnsafeOrigin(req, res)) return;
    const url = new URL(req.url ?? '/', 'http://127.0.0.1');
    if (req.method === 'GET' && url.pathname === '/health') return send(res, 200, { ok: true });
    if (req.method === 'GET' && url.pathname === '/api/snapshot') return send(res, 200, store.read());
    if (req.method === 'GET' && url.pathname === '/api/artifacts') return sendArtifact(res, url.searchParams.get('path'));
    if (req.method === 'POST' && url.pathname === '/api/repos') {
      const body = await readJson<Partial<RepoDTO>>(req);
      const repo: RepoDTO = { id: body.id ?? randomUUID(), name: body.name ?? 'Repo', path: body.path ?? '', defaultBranch: body.defaultBranch ?? 'main', remoteUrl: body.remoteUrl };
      store.upsertRepo(repo);
      return send(res, 201, { repo });
    }
    const repoMatch = url.pathname.match(/^\/api\/repos\/([^/]+)$/);
    if (req.method === 'DELETE' && repoMatch) {
      const repoId = decodeURIComponent(repoMatch[1]);
      if (store.countCardsForRepo(repoId) > 0) return send(res, 409, { error: 'repo_has_cards', message: 'Remove or finish this repo’s cards before removing the repo.' });
      store.deleteRepo(repoId);
      return send(res, 200, { ok: true });
    }
    if (req.method === 'POST' && url.pathname === '/api/cards') return send(res, 201, { card: createCard(store, await readJson<Partial<CardDTO>>(req)) });
    const cardMatch = url.pathname.match(/^\/api\/cards\/([^/]+)$/);
    if (req.method === 'PATCH' && cardMatch) {
      const result = updateInboxCard(store, decodeURIComponent(cardMatch[1]), await readJson<Partial<Pick<CardDTO, 'title' | 'instructions'>>>(req));
      return send(res, result.ok ? 200 : 409, result);
    }
    if (req.method === 'DELETE' && cardMatch) {
      store.deleteCard(cardMatch[1]);
      return send(res, 200, { ok: true });
    }
    const actionMatch = url.pathname.match(/^\/api\/cards\/([^/]+)\/(resume|move|poll|automerge|cleanup|discard)$/);
    if (req.method === 'POST' && actionMatch) {
      const [, cardId, action] = actionMatch;
      const body = await readJson<{ note?: string; status?: CardDTO['status'] }>(req);
      const result = action === 'resume' ? resumeCard(store, cardId, body.note ?? '')
        : action === 'move' ? manualMoveCard(store, cardId, body.status ?? 'Blocked')
        : action === 'poll' ? pollPrState(store, cardId)
        : action === 'automerge' ? await autoMergeCard(store, cardId)
        : action === 'discard' ? await discardCard(store, cardId)
        : await cleanupMergedCard(store, cardId);
      return send(res, result.ok ? 200 : 409, result);
    }
    send(res, 404, { error: 'not_found' });
  });
}

export function startBoardServer(port = Number(process.env.BOARD_PORT ?? 4782), host = resolveHost()) { const server = makeBoardServer(); server.listen(port, host); return server; }
