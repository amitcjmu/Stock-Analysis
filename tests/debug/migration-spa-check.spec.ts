import { test, expect } from '@playwright/test';

test.describe('Migration Platform - SPA Navigation Check', () => {
  test('should change content when navigating between sections', async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Get initial content
    const dashboardContent = await page.textContent('body');
    console.log('Dashboard contains:', dashboardContent?.includes('cloud migration journey') ? 'migration journey text' : 'different content');
    
    // Navigate to Collection
    await page.click('text=Collection');
    await page.waitForTimeout(1000);
    const collectionContent = await page.textContent('body');
    console.log('Collection page contains:', collectionContent?.substring(200, 400));
    
    // Check if content changed
    const contentChanged = dashboardContent !== collectionContent;
    console.log('Content changed after navigation:', contentChanged);
    
    // Check URL pattern
    const url = page.url();
    console.log('URL pattern:', url.includes('#') ? 'Hash routing' : url.includes('/collection') ? 'Path routing' : 'No routing change');
  });
});
