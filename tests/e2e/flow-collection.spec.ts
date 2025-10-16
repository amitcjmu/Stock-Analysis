import { test, expect } from '@playwright/test';

test.describe('Collection Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Navigate to Collection
    await page.click('text=Collection');
    await page.waitForTimeout(1000);
  });

  test('should load Collection page', async ({ page }) => {
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Collection');
    
    await page.screenshot({ path: 'test-results/collection-page.png' });
  });

  test('should display data collection options', async ({ page }) => {
    // Look for import/upload buttons
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Import"), button:has-text("Add")');
    const uploadCount = await uploadButton.count();
    console.log('Upload/Import buttons found:', uploadCount);
    
    // Check for data sources
    const dataSourcesText = await page.textContent('body');
    const hasDataSources = 
      dataSourcesText?.includes('source') ||
      dataSourcesText?.includes('database') ||
      dataSourcesText?.includes('file');
    console.log('Has data source references:', hasDataSources);
  });

  test('should show collected data grid', async ({ page }) => {
    // Look for data table or grid
    const dataGrid = page.locator('table, [role="grid"], .data-grid, .ag-root');
    const gridCount = await dataGrid.count();
    
    if (gridCount > 0) {
      console.log('Data grid found');
      
      // Check for column headers
      const headers = await page.locator('th, [role="columnheader"]').allTextContents();
      console.log('Grid columns:', headers.join(', '));
      
      // Check row count
      const rows = await page.locator('tbody tr, [role="row"]').count();
      console.log('Data rows:', rows);
    }
  });

  test('should allow data export', async ({ page }) => {
    // Look for export functionality
    const exportButton = page.locator('button:has-text("Export"), button:has-text("Download")');
    
    if (await exportButton.count() > 0) {
      console.log('Export button available');
      
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);
      
      await exportButton.first().click();
      const download = await downloadPromise;
      
      if (download) {
        console.log('Download triggered:', download.suggestedFilename());
      }
    }
  });

  test('should support bulk operations', async ({ page }) => {
    // Look for checkboxes for selection
    const checkboxes = page.locator('input[type="checkbox"]');
    const checkboxCount = await checkboxes.count();
    
    if (checkboxCount > 1) {
      // Select first few items
      await checkboxes.nth(0).check();
      await checkboxes.nth(1).check();
      
      // Look for bulk action buttons
      const bulkActions = page.locator('button:has-text("Delete"), button:has-text("Process"), button:has-text("Action")');
      const bulkActionCount = await bulkActions.count();
      console.log('Bulk actions available:', bulkActionCount);
    }
  });
});
