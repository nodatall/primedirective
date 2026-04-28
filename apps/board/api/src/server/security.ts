import type { IncomingMessage, ServerResponse } from 'node:http';

const loopbackHosts = new Set(['127.0.0.1', 'localhost', '::1']);
const defaultAllowedOrigins = new Set(['http://127.0.0.1:5178', 'http://localhost:5178']);

export function resolveHost(host = process.env.BOARD_HOST ?? '127.0.0.1'): string {
  const normalized = host.replace(/^\[/, '').replace(/\]$/, '');
  if (!loopbackHosts.has(normalized)) throw new Error(`Refusing to bind Agent Board API to non-loopback host ${host}`);
  return host;
}

export function isLoopbackHost(hostHeader: string | undefined): boolean {
  if (!hostHeader) return true;
  const host = hostHeader.split(':')[0]?.replace(/^\[/, '').replace(/\]$/, '');
  return loopbackHosts.has(host);
}

export function isOriginAllowed(origin: string | undefined, requireOrigin = false): boolean {
  if (!origin) return !requireOrigin;
  const allowed = new Set([...(process.env.BOARD_ALLOWED_ORIGINS?.split(',').map((originValue) => originValue.trim()).filter(Boolean) ?? []), ...defaultAllowedOrigins]);
  return allowed.has(origin);
}

export function rejectUnsafeOrigin(req: IncomingMessage, res: ServerResponse): boolean {
  const method = req.method ?? 'GET';
  const stateChanging = !['GET', 'HEAD', 'OPTIONS'].includes(method);
  if (!isLoopbackHost(req.headers.host) || (stateChanging && !isOriginAllowed(req.headers.origin, true))) {
    res.statusCode = 403;
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify({ error: 'origin_rejected' }));
    return true;
  }
  return false;
}
