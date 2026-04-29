import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '127.0.0.1',
    port: 5178,
    proxy: {
      '/api': 'http://127.0.0.1:4782',
      '/health': 'http://127.0.0.1:4782'
    }
  },
  resolve: {
    alias: {
      '@prime-board/shared': new URL('../shared/src/index.ts', import.meta.url).pathname
    }
  }
});
