import { test, expect } from '@playwright/test';
import { loginAsDemo } from '../utils/auth-helpers';

test.describe('Migration Platform - Authentication Flow', () => {
  test('should login with demo credentials and access dashboard', async ({ page }) => {
    await loginAsDemo(page);

    // Verify we're on dashboard
    await expect(page.locator('text=Dashboard')).toBeVisible();

    const url = page.url();
    console.log('URL after login:', url);
    expect(url).toContain('localhost:8081');
  });
});
