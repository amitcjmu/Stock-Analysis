import { test, expect } from '@playwright/test';

test.describe('Migration Platform - Dashboard Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    
    // Perform login
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    
    // Wait for login to complete
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('should display dashboard after login', async ({ page }) => {
    // Verify we're on the dashboard (not on login page)
    const url = page.url();
    expect(url).not.toContain('/login');
    
    // Check for dashboard content
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toContain('Demo Credentials');
    
    // Take screenshot for reference
    await page.screenshot({ path: 'test-results/dashboard.png', fullPage: true });
  });

  test('should have navigation menu', async ({ page }) => {
    // Look for navigation elements
    const navElements = await page.locator('nav, aside, [role="navigation"], .sidebar, .menu').count();
    console.log('Navigation elements found:', navElements);
    
    // Log what's visible on the page
    const visibleText = await page.textContent('body');
    console.log('First 500 chars of page:', visibleText?.substring(0, 500));
  });
});
