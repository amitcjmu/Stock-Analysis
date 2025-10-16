import { test, expect } from '@playwright/test';

test.describe('Migration Platform - Authentication Flow', () => {
  test('should login with demo credentials and access dashboard', async ({ page }) => {
    // Go to login page
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    
    // Fill in demo credentials
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    
    // Click Sign In
    await page.click('button:has-text("Sign In")');
    
    // Wait for navigation after login
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Give time for any redirects
    
    // Check if we're logged in (URL should change or dashboard should appear)
    const currentUrl = page.url();
    console.log('URL after login:', currentUrl);
    
    // Take a screenshot to see what page we're on
    await page.screenshot({ path: 'test-results/after-login.png', fullPage: true });
    
    // Log what's on the page
    const pageTitle = await page.title();
    console.log('Page title after login:', pageTitle);
    
    // Check if login was successful (no longer on login page)
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Demo Credentials');
  });
});
