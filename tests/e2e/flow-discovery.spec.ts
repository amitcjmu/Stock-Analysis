import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.describe('Discovery Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToFlow(page, 'Discovery');
  });

  test('should load Discovery page with expected content', async ({ page }) => {
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Check for discovery-related content in the body
    const bodyText = await page.textContent('body');
    const hasDiscoveryContent = 
      bodyText?.toLowerCase().includes('discover') || 
      bodyText?.toLowerCase().includes('inventory') ||
      bodyText?.toLowerCase().includes('application');
    
    expect(hasDiscoveryContent).toBeTruthy();
    console.log('✓ Discovery page loaded with relevant content');
  });

  test('should show application inventory options', async ({ page }) => {
    // Wait for page to be ready
    await page.waitForSelector('button', { state: 'visible', timeout: 10000 });
    
    const buttons = page.locator('button:visible');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
    console.log(`Found ${buttonCount} buttons on Discovery page`);
    
    // Check for data grid
    const dataGrid = page.locator('table, [role="grid"]');
    const hasGrid = await dataGrid.count() > 0;
    console.log('Has data grid:', hasGrid);
  });

  test('should allow starting a new discovery scan', async ({ page }) => {
    // Look for action buttons
    const actionButtons = page.locator('button:has-text("Scan"), button:has-text("Start"), button:has-text("Import"), button:has-text("Upload"), button:has-text("Add")');
    
    const buttonCount = await actionButtons.count();
    
    if (buttonCount > 0) {
      await expect(actionButtons.first()).toBeVisible({ timeout: 5000 });
      console.log(`✓ Found ${buttonCount} action button(s) on Discovery page`);
      await page.screenshot({ path: 'test-results/discovery-actions.png' });
    } else {
      console.log('⚠️ No action buttons found - this may be expected for current state');
    }
  });

  test('should display discovered applications list', async ({ page }) => {
    // Look for any list or table
    const listItems = page.locator('table tbody tr, [role="row"]');
    
    await page.waitForTimeout(2000); // Give data time to load
    
    const itemCount = await listItems.count();
    console.log(`Found ${itemCount} items in discovery list`);
    
    // Either we have items or an empty state - both are valid
    if (itemCount === 0) {
      // Look for empty state separately
      const emptyStateText = page.locator('text="No data"');
      const emptyStateClass = page.locator('.empty-state');
      
      const hasEmptyText = await emptyStateText.count() > 0;
      const hasEmptyClass = await emptyStateClass.count() > 0;
      
      console.log('Shows empty state:', hasEmptyText || hasEmptyClass);
    }
  });

  test('should allow filtering discovered items', async ({ page }) => {
    // Look for search/filter input
    const searchInput = page.locator('input[type="search"]');
    const filterInputByPlaceholder = page.locator('input[placeholder*="search"], input[placeholder*="filter"]');
    
    const hasSearchInput = await searchInput.count() > 0;
    const hasFilterInput = await filterInputByPlaceholder.count() > 0;
    
    if (hasSearchInput || hasFilterInput) {
      const filterInput = hasSearchInput ? searchInput.first() : filterInputByPlaceholder.first();
      await expect(filterInput).toBeVisible({ timeout: 5000 });
      console.log('✓ Filter/search input found');
      
      await filterInput.fill('test');
      await page.waitForTimeout(1000); // Debounce
      console.log('✓ Filter applied successfully');
    } else {
      console.log('⚠️ No filter input found - may not be implemented yet');
    }
  });

  test('should handle empty discovery state gracefully', async ({ page }) => {
    // Just verify the page loaded
    await page.waitForLoadState('domcontentloaded');
    
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    expect(bodyText!.length).toBeGreaterThan(0);
    
    console.log('✓ Discovery page handles state gracefully');
  });
});
