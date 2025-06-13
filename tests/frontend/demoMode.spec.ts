import { test, expect } from '@playwright/test';

test('Demo Mode: login, dashboard, and navigation', async ({ page }) => {
  // 1. Go to login page
  await page.goto('http://localhost:8081/login');

  // 2. Attempt a failed login
  await page.fill('input[type="email"]', 'fail@fail.com');
  await page.fill('input[type="password"]', 'wrongpassword');
  await page.click('button:has-text("Sign In")');

  // 3. Wait for error and Try Demo Mode button
  await expect(page.locator('button', { hasText: 'Try Demo Mode' })).toBeVisible();
  await page.click('button:has-text("Try Demo Mode")');

  // 4. Verify demo mode banner is visible
  await expect(page.locator('text=Demo Mode')).toBeVisible();

  // 5. Navigate to home/dashboard (should be redirected automatically)
  await expect(page).toHaveURL(/\/$|\/dashboard/);

  // 6. Click a few links in the sidebar (simulate navigation)
  // Example: Discovery Dashboard
  await page.click('a:has-text("Discovery")');
  await expect(page).toHaveURL(/discovery/);

  // Example: Asset Inventory
  await page.click('a:has-text("Asset Inventory")');
  await expect(page).toHaveURL(/asset-inventory/);

  // Example: Plan
  await page.click('a:has-text("Plan")');
  await expect(page).toHaveURL(/plan/);

  // 7. Assert no error banners or critical errors are shown
  await expect(page.locator('text=Error')).not.toBeVisible();
  await expect(page.locator('text=404')).not.toBeVisible();
}); 