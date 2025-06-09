import { test, expect, Page } from '@playwright/test';

const TEST_BASE_URL = 'http://localhost:8081';

async function loginAsAdmin(page: Page) {
  await page.goto(`${TEST_BASE_URL}/login`);
  await page.evaluate(() => localStorage.clear());
  await page.goto(`${TEST_BASE_URL}/login`, { waitUntil: 'networkidle' });
  
  await page.fill('input[type="email"]', 'admin@democorp.com');
  await page.fill('input[type="password"]', 'admin123');
  
  await page.click('button[type="submit"]');
  try {
    await page.waitForURL(`${TEST_BASE_URL}/admin`, { timeout: 15000 });
    console.log('Successfully navigated to admin page.');
  } catch(e) {
    console.error("Failed to navigate to admin page after login.", e);
    await page.screenshot({ path: 'playwright-debug/simple-login-failure.png' });
    throw e;
  }
}

test.describe('Simple Login Test', () => {
  test('Should log in and redirect to admin dashboard', async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page.locator('h1:has-text("Admin Console")')).toBeVisible();
  });
}); 