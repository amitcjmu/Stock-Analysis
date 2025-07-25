import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Discovery Flow End-to-End', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:8081/login');

    // Login with provided credentials
    await page.fill('input[type="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Wait for navigation to complete
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test('Upload file and verify attribute mapping flow', async ({ page }) => {
    // Navigate to Discovery
    await page.click('text=Discovery');
    await page.waitForTimeout(1000);

    // Check if there's an active flow and handle flow sync
    const overviewVisible = await page.locator('text=Overview').isVisible();
    if (overviewVisible) {
      // We're on the overview page, check for active flows
      await page.waitForTimeout(2000); // Wait for flow status widget

      // Check if flow intelligence widget shows "flow not found"
      const flowNotFound = await page.locator('text=/flow.*not.*found|Flow not found/i').isVisible();
      if (flowNotFound) {
        console.log('Flow not found detected, navigating to CMDB Import');
        // Click on the recommended action to go to CMDB import
        const cmdbImportButton = page.locator('button').filter({ hasText: /CMDB Import|Data Import|Upload/i }).first();
        if (await cmdbImportButton.isVisible()) {
          await cmdbImportButton.click();
        } else {
          // Manual navigation if button not found
          await page.click('text=Data Import');
        }
      }
    } else {
      // Direct navigation to Data Import
      await page.click('text=Data Import');
    }

    await page.waitForURL('**/discovery/cmdb-import', { timeout: 5000 });

    // Prepare test file
    const testFilePath = path.join(__dirname, '../../fixtures/test-cmdb-data.csv');

    // Find and click the upload area for Application Discovery
    const uploadArea = page.locator('.border-dashed').filter({ hasText: 'Application Discovery' }).first();
    await uploadArea.click();

    // Upload file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    // Wait for upload to complete
    await page.waitForTimeout(2000);

    // Look for success indicators
    const successMessage = page.locator('text=/Upload completed|Processing complete|Data import complete/i');
    await expect(successMessage).toBeVisible({ timeout: 30000 });

    // Check if flow ID is displayed
    const flowIdElement = page.locator('text=/flow-\\d{8}-\\d{6}/');
    const flowIdVisible = await flowIdElement.isVisible();
    if (flowIdVisible) {
      const flowId = await flowIdElement.textContent();
      console.log('Flow ID created:', flowId);
    }

    // Navigate to Attribute Mapping
    await page.click('text=Attribute Mapping');
    await page.waitForURL('**/discovery/attribute-mapping', { timeout: 5000 });

    // Wait for page to load
    await page.waitForTimeout(2000);

    // Check for data presence
    const noDataMessage = page.locator('text=No Field Mapping Available');
    const hasNoDataMessage = await noDataMessage.isVisible();

    if (hasNoDataMessage) {
      console.log('WARNING: No field mapping data found on attribute mapping page');

      // Check if we need to select a flow
      const flowSelector = page.locator('select[id="flow-selector"], .flow-selector');
      if (await flowSelector.isVisible()) {
        console.log('Flow selector found, selecting first available flow');
        const options = await flowSelector.locator('option').all();
        if (options.length > 1) {
          // Select the first non-default option
          await flowSelector.selectOption({ index: 1 });
          await page.waitForTimeout(2000);
        }
      }

      // Re-check for data after potential flow selection
      const stillNoData = await noDataMessage.isVisible();
      if (stillNoData) {
        // Check for active flows
        const activeFlowsDebug = await page.locator('text=/Available Flows: \\d+/').textContent();
        console.log('Active flows debug:', activeFlowsDebug);

        // Take screenshot for debugging
        await page.screenshot({ path: 'attribute-mapping-error.png', fullPage: true });

        throw new Error('Attribute mapping page shows no data after upload');
      }
    }

    // Verify field mappings are visible
    const fieldMappingSection = page.locator('text=/Field Mapping|Critical Attributes/');
    await expect(fieldMappingSection).toBeVisible({ timeout: 10000 });

    console.log('SUCCESS: Attribute mapping page loaded with data');
  });

  test('Handle flow synchronization issues', async ({ page }) => {
    // Navigate to Discovery Overview
    await page.click('text=Discovery');
    await page.waitForTimeout(2000);

    // Check if we're on the overview page
    const overviewPageTitle = page.locator('h1, h2').filter({ hasText: /Discovery Overview|Active Discovery/i });
    if (await overviewPageTitle.isVisible()) {
      console.log('On Discovery Overview page');

      // Wait for flow status widget to load
      await page.waitForTimeout(3000);

      // Check for flow synchronization issues
      const flowNotFoundText = page.locator('text=/flow.*not.*found|doesn.*t exist|No flow analysis/i');
      if (await flowNotFoundText.isVisible()) {
        console.log('Flow synchronization issue detected');

        // Look for navigation button in flow status widget
        const navigationButton = page.locator('button').filter({ hasText: /Navigate|Continue|Start|Upload/i }).first();
        if (await navigationButton.isVisible()) {
          console.log('Found navigation button, clicking...');
          await navigationButton.click();

          // Verify we navigated to the correct page
          await page.waitForURL('**/discovery/cmdb-import', { timeout: 5000 });
          console.log('Successfully navigated to CMDB Import page');
        } else {
          console.log('No navigation button found, manual navigation required');

          // Try clicking on Data Import manually
          const dataImportLink = page.locator('a, button').filter({ hasText: /Data Import|CMDB Import/i }).first();
          if (await dataImportLink.isVisible()) {
            await dataImportLink.click();
            await page.waitForURL('**/discovery/cmdb-import', { timeout: 5000 });
          }
        }
      } else {
        console.log('No flow synchronization issues detected');
      }
    }
  });
});
