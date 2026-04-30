import React from 'react';
import { describe, expect, it } from 'vitest';
import { renderToString } from 'react-dom/server';
import { BoardApp } from '../src/features/board/BoardApp';
import { BoardCard } from '../src/features/board/BoardCard';
import { CardDetail } from '../src/features/card-detail/CardDetail';

it('renders the Voidgrid-inspired board cockpit and card form', () => {
  const html = renderToString(<BoardApp />);
  expect(html).toContain('Agent Board');
  expect(html).toContain('New agent card');
  expect(html).toContain('Quick');
  expect(html).toContain('Planned');
});

it('renders the Rose Three loader for running cards', () => {
  const html = renderToString(
    <BoardCard
      card={{ id: 'card', repoId: 'repo', title: 'Running card', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Running', branch: 'agent-board/repo/card', updatedAt: new Date().toISOString() }}
      onOpen={() => undefined}
    />
  );
  expect(html).toContain('card__running-loader');
  expect(html).toContain('aria-label="Running"');
});

it('renders card status and branch in the detail metadata block', () => {
  const html = renderToString(
    <CardDetail
      card={{ id: 'card', repoId: 'repo', title: 'Task', instructions: 'Do it', taskType: 'Quick', autoMerge: false, status: 'Inbox', branch: 'agent-board/repo/card', updatedAt: new Date().toISOString() }}
      events={[]}
      onClose={() => undefined}
    />
  );
  expect(html).toContain('detail__metadata');
  expect(html).toContain('Status');
  expect(html).toContain('Branch');
  expect(html).toContain('agent-board/repo/card');
});
