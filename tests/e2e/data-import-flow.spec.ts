import { test, expect } from '@playwright/test';

test.describe('Data Import to Attribute Mapping Flow', () => {
  test('should successfully upload a file and navigate to attribute mapping', async ({ page }) => {
    // 1. Navigate to the Data Import page
    await page.goto('http://localhost:8081/discovery/data-import');

    // Wait for the page to load and the upload zones to be visible
    await expect(page.locator('text=Upload Your Data')).toBeVisible();

    // 2. Upload a sample CSV file
    const fileUploadPromise = page.waitForEvent('filechooser');
    await page.locator('div.p-6:has-text("CMDB Data")').first().click();
    const fileChooser = await fileUploadPromise;
    
    // Create a dummy CSV file
    const csvContent = 'asset_name,ip_address,os\nserver1,192.168.1.1,Linux\nserver2,192.168.1.2,Windows';
    await fileChooser.setFiles({
      name: 'test_cmdb_import.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent),
    });

    // 3. Wait for the analysis to complete
    // The analysis triggers a navigation, so we wait for the new page to load
    await page.waitForURL('**/discovery/attribute-mapping', { timeout: 15000 });

    // 4. Verify that the application successfully navigates to the attribute mapping page
    await expect(page).toHaveURL(/.*attribute-mapping/);
    await expect(page.locator('h1:has-text("Attribute Mapping")')).toBeVisible();
    
    console.log('Successfully navigated to Attribute Mapping page.');
  });
}); 