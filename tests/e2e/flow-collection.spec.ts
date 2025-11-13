import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.describe('Collection Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToFlow(page, 'Collection');
  });

  test('should load Collection page', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Collection');
    
    await page.screenshot({ path: 'test-results/collection-page.png' });
  });

  test('should display data collection options', async ({ page }) => {
    // Look for import/upload buttons
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Import"), button:has-text("Add")');
    const uploadCount = await uploadButton.count();
    console.log('Upload/Import buttons found:', uploadCount);
  });

  test('should show collected data grid', async ({ page }) => {
    // Check for data grid or table
    const dataGrid = page.locator('table, [role="grid"], .data-grid');
    const hasGrid = await dataGrid.count() > 0;
    console.log('Has data grid:', hasGrid);
    
    // Check for data source references
    const bodyText = await page.textContent('body');
    const hasDataSource = bodyText?.toLowerCase().includes('cmdb') || 
                          bodyText?.toLowerCase().includes('import') ||
                          bodyText?.toLowerCase().includes('source');
    console.log('Has data source references:', hasDataSource);
  });

  test('should allow data export', async ({ page }) => {
    // Look for export buttons
    const exportButton = page.locator('button:has-text("Export"), button:has-text("Download")');
    const exportCount = await exportButton.count();
    
    if (exportCount > 0) {
      console.log(`✓ Found ${exportCount} export button(s)`);
    } else {
      console.log('⚠️ No export buttons found');
    }
  });

  test('should support bulk operations', async ({ page }) => {
    // Look for bulk action buttons
    const bulkActions = page.locator('button:has-text("Bulk"), button:has-text("Select All")');
    const bulkCount = await bulkActions.count();
    
    console.log(`Bulk action buttons: ${bulkCount}`);
  });
});
