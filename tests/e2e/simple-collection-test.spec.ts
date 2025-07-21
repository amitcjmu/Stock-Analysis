import { test, expect } from '@playwright/test';

test('simple collection flow test', async ({ page }) => {
  // Navigate directly to the app
  await page.goto('http://localhost:8081');
  
  // Wait for the page to load with a simple check
  await page.waitForLoadState('domcontentloaded');
  
  // Take a screenshot for debugging
  await page.screenshot({ path: 'test-results/initial-load.png' });
  
  // Check if we're on login page or main page
  const isLoginPage = await page.locator('input[type="email"]').count() > 0;
  
  if (isLoginPage) {
    console.log('On login page, logging in...');
    // Fill login form
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button[type="submit"]');
    
    // Wait for navigation
    await page.waitForURL('http://localhost:8081/', { timeout: 15000 });
  }
  
  // Take another screenshot
  await page.screenshot({ path: 'test-results/after-login.png' });
  
  // Navigate to collection
  await page.goto('http://localhost:8081/collection');
  
  // Wait and refresh twice
  await page.waitForLoadState('networkidle');
  await page.reload();
  await page.waitForLoadState('networkidle');
  await page.reload();
  await page.waitForLoadState('networkidle');
  
  // Take screenshot of collection page
  await page.screenshot({ path: 'test-results/collection-page.png' });
  
  // Simple check - just verify we're on collection page
  const url = page.url();
  expect(url).toContain('/collection');
  
  // Check for any h1 element
  const h1Count = await page.locator('h1').count();
  console.log(`Found ${h1Count} h1 elements`);
  expect(h1Count).toBeGreaterThan(0);
});