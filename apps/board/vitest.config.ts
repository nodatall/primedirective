import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['api/tests/**/*.test.ts', 'web/tests/**/*.test.ts'],
    environment: 'node'
  },
  resolve: {
    alias: {
      '@prime-board/shared': new URL('./shared/src/index.ts', import.meta.url).pathname
    }
  }
});
