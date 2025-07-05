import { test, expect } from '@playwright/test';

test.describe('Simple Test', () => {
  test('Basic page load test', async ({ page }) => {
    await page.goto('http://localhost:8081');
    await expect(page).toHaveTitle(/AI powered Migration Orchestrator/);
  });
});