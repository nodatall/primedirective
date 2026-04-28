import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './web/playwright',
  timeout: 30_000,
  use: {
    baseURL: 'http://127.0.0.1:5178',
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    }
  },
  webServer: {
    command: 'npm run build --workspace @prime-board/api && node scripts/e2e-server.mjs',
    url: 'http://127.0.0.1:5178',
    reuseExistingServer: false
  }
});
