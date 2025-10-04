import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests
 * Uses Chrome browser (not Chromium) for better compatibility with authentication
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Sequential execution to avoid flow conflicts
  reporter: 'html',
  timeout: 180000, // 3 minutes per test (allow time for questionnaire generation)

  use: {
    baseURL: 'http://localhost:8081',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chrome',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome', // Use actual Chrome browser, not Chromium
      },
    },
  ],

  webServer: {
    command: 'echo "Docker services should already be running"',
    url: 'http://localhost:8081',
    reuseExistingServer: true,
  },
});
