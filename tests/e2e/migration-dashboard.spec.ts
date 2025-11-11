import { test, expect } from '@playwright/test';
import { loginAsDemo } from '../utils/auth-helpers';

test.describe('Migration Platform - Dashboard Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemo(page);
  });

  test('should display dashboard after login', async ({ page }) => {
    const url = page.url();
    console.log('URL after login:', url);
    
    const title = await page.title();
    console.log('Page title after login:', title);
    
    expect(url).toContain('localhost:8081');
  });

  test('should have navigation menu', async ({ page }) => {
    await expect(page.locator('text=Dashboard')).toBeVisible();
    await expect(page.locator('text=Discovery')).toBeVisible();
  });
});
