import React from 'react';
import { describe, expect, it } from 'vitest';
import { renderToString } from 'react-dom/server';
import { BoardApp } from '../src/features/board/BoardApp';

it('renders the Voidgrid-inspired board cockpit and card form', () => {
  const html = renderToString(<BoardApp />);
  expect(html).toContain('Agent Board');
  expect(html).toContain('New agent card');
  expect(html).toContain('Quick');
  expect(html).toContain('Planned');
  expect(html).toContain('protected_risk');
});
