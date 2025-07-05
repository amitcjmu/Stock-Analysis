import { test, expect } from '@playwright/test';

test.describe('Login Test', () => {
  test('User can login successfully', async ({ page }) => {
    test.setTimeout(60000); // 1 minute timeout
    
    console.log('🔐 Testing user login...');
    await page.goto('http://localhost:8081/login');
    
    // Fill login form
    await page.fill('input[type="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    
    // Wait for successful login
    await page.waitForURL('**/dashboard', { timeout: 30000 });
    
    // Verify we're on the dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    console.log('✅ Login successful!');
  });
});