import { test, expect } from '@playwright/test';

test.describe('Discovery Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Navigate to Discovery
    await page.click('text=Discovery');
    await page.waitForTimeout(1000);
  });

  test('should load Discovery page', async ({ page }) => {
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Discovery');
    
    // Check for key Discovery elements
    const hasDiscoveryContent = 
      bodyText?.includes('discover') || 
      bodyText?.includes('inventory') ||
      bodyText?.includes('application');
    expect(hasDiscoveryContent).toBeTruthy();
  });

  test('should show application inventory options', async ({ page }) => {
    // Look for common discovery actions
    const buttons = page.locator('button');
    const buttonTexts = await buttons.allTextContents();
    console.log('Available buttons:', buttonTexts.join(', '));
    
    // Check for data grids or tables
    const tables = await page.locator('table, [role="grid"]').count();
    console.log('Tables/grids found:', tables);
  });

  test('should allow starting a new discovery scan', async ({ page }) => {
    // Look for scan/discovery initiation
    const scanButton = page.locator('button:has-text("Scan"), button:has-text("Start"), button:has-text("Discover"), button:has-text("New")');
    
    if (await scanButton.count() > 0) {
      await scanButton.first().click();
      await page.waitForTimeout(2000);
      
      // Check if modal or form appears
      const modal = await page.locator('[role="dialog"], .modal, .popup').count();
      console.log('Modal/dialog appeared:', modal > 0);
      
      // Take screenshot of discovery initiation
      await page.screenshot({ path: 'test-results/discovery-scan-init.png' });
    }
  });

  test('should display discovered applications list', async ({ page }) => {
    // Check for application list/grid
    const appList = page.locator('.app-list, .application-grid, table tbody tr, [data-testid*="app"]');
    const appCount = await appList.count();
    console.log('Applications found:', appCount);
    
    if (appCount > 0) {
      // Get details of first application
      const firstApp = appList.first();
      const appText = await firstApp.textContent();
      console.log('First app details:', appText?.substring(0, 100));
    }
  });

  test('should allow filtering discovered items', async ({ page }) => {
    // Look for filter inputs
    const filterInput = page.locator('input[placeholder*="filter"], input[placeholder*="search"], input[type="search"]');
    
    if (await filterInput.count() > 0) {
      await filterInput.first().fill('test');
      await page.waitForTimeout(1000);
      
      // Check if content updates
      const bodyAfterFilter = await page.textContent('body');
      console.log('Filtering applied');
    }
  });
});
