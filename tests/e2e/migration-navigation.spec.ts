import { test, expect } from '@playwright/test';

test.describe('Migration Platform - Navigation Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('should navigate to Discovery section', async ({ page }) => {
    // Click on Discovery
    await page.click('text=Discovery');
    await page.waitForLoadState('networkidle');
    
    const url = page.url();
    console.log('Discovery URL:', url);
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/discovery.png' });
  });

  test('should navigate to Collection section', async ({ page }) => {
    // Click on Collection
    await page.click('text=Collection');
    await page.waitForLoadState('networkidle');
    
    const url = page.url();
    console.log('Collection URL:', url);
    
    await page.screenshot({ path: 'test-results/collection.png' });
  });

  test('should navigate to Assess section', async ({ page }) => {
    // Click on Assess
    await page.click('text=Assess');
    await page.waitForLoadState('networkidle');
    
    const url = page.url();
    console.log('Assess URL:', url);
    
    await page.screenshot({ path: 'test-results/assess.png' });
  });
});
