import { describe, expect, it } from 'vitest';
import { assertTransition, canTransition, blocker } from '../src/domain/stateMachine.js';
import { parseAgentBoardMarkdown } from '../src/workflow/loader.js';
import { resolveHost, isOriginAllowed } from '../src/server/security.js';

it('enforces state transitions and blocker reasons', () => {
  expect(canTransition('Inbox', 'Queued')).toBe(true);
  expect(() => assertTransition('Done', 'Running')).toThrow(/invalid transition/);
  expect(blocker('no_changes_detected', 'No changes').status).toBe('Blocked');
});

it('rejects invariant-weakening workflow overrides', () => {
  const result = parseAgentBoardMarkdown('allowQuickNoCheckAutomerge: true\nallowAdminMerge: true\nunknown: nope');
  expect(result.config.allowQuickNoCheckAutomerge).toBe(true);
  expect(result.errors).toEqual(expect.arrayContaining([expect.stringContaining('allowAdminMerge'), expect.stringContaining('unknown')]));
});

it('binds only to loopback defaults and rejects unsafe origins', () => {
  expect(resolveHost()).toBe('127.0.0.1');
  expect(() => resolveHost('0.0.0.0')).toThrow(/Refusing/);
  expect(isOriginAllowed('http://localhost:5178', true)).toBe(true);
  expect(isOriginAllowed(undefined, true)).toBe(false);
  expect(isOriginAllowed('http://localhost:5173', true)).toBe(false);
  expect(isOriginAllowed('https://evil.example')).toBe(false);
});
