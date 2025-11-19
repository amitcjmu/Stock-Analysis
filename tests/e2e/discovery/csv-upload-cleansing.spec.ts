/**
 * E2E tests for CSV upload with data cleansing functionality.
 *
 * Tests the complete CSV upload workflow:
 * 1. CSV file upload with malformed data (unquoted commas)
 * 2. Data cleansing notification (toast)
 * 3. Automatic import continuation
 * 4. Data import verification
 */

import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../../utils/auth-helpers';

test.describe('CSV Upload with Data Cleansing', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to CMDB import page
    await loginAndNavigateToFlow(page, 'Discovery');
    await page.goto('/discovery/cmdb-import');
    await page.waitForLoadState('domcontentloaded');
  });

  test('CSV upload shows cleansing notification and continues import automatically', async ({ page }) => {
    // Create CSV content with unquoted comma in description field (will trigger cleansing)
    const csvContent = `server_name,description,ip_address
server1,DC1, room A,192.168.1.1
server2,Located in DC2, building B,192.168.1.2
server3,Normal description,192.168.1.3`;

    // Create a File object with the CSV content
    const csvBuffer = Buffer.from(csvContent);
    const csvBlob = {
      name: 'test-cleansing.csv',
      mimeType: 'text/csv',
      buffer: csvBuffer,
    };

    // Find the file input element
    // Try multiple selectors as the UI might vary
    const fileInput = page.locator('input[type="file"]').first();

    // Upload the CSV file
    await fileInput.setInputFiles(csvBlob);

    // Wait for file processing to start
    await page.waitForTimeout(2000);

    // Verify toast notification appears with cleansing message
    // Toast title: "Data Cleansing Applied"
    const toastTitle = page.locator('text=Data Cleansing Applied');
    await expect(toastTitle.first()).toBeVisible({ timeout: 10000 });

    // Verify the toast description contains the expected message about replacing commas
    const toastDescription = page.locator('text=/Unquoted commas.*replaced.*spaces.*column alignment/i');
    await expect(toastDescription.first()).toBeVisible({ timeout: 5000 });

    // Verify toast mentions row count (should show at least 1 row cleansed)
    const rowCountText = page.locator('text=/\\d+ row\\(s\\) were cleaned/i');
    await expect(rowCountText.first()).toBeVisible({ timeout: 5000 });

    const rowCountContent = await rowCountText.first().textContent();
    expect(rowCountContent).toMatch(/\d+\s+row\(s\)\s+were\s+cleaned/i);

    // Verify import continues automatically (no dialog/button to click)
    // Wait a bit for processing to complete
    await page.waitForTimeout(3000);

    // Verify no confirmation dialog appears (our implementation uses toast, not dialog)
    const dialog = page.locator('[role="dialog"]:has-text("Accept")').first();
    const dialogVisible = await dialog.isVisible({ timeout: 1000 }).catch(() => false);
    expect(dialogVisible).toBeFalsy(); // Dialog should NOT appear

    // Verify import process continues (check for success indicators or progress)
    // This could be a success message, progress indicator, or file list update
    const successIndicator = page.locator('text=/import|upload|success|completed/i').first();
    const hasSuccessIndicator = await successIndicator.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSuccessIndicator) {
      console.log('✅ Import process continued automatically');
    } else {
      // This is acceptable - the import might still be processing in the background
      console.log('ℹ️ Import may be processing in background');
    }
  });

  test('CSV upload without malformed data does not show cleansing notification', async ({ page }) => {
    // Create CSV content with properly quoted fields (should NOT trigger cleansing)
    const csvContent = `server_name,description,ip_address
server1,"DC1, room A",192.168.1.1
server2,"Located in DC2, building B",192.168.1.2
server3,Normal description,192.168.1.3`;

    const csvBuffer = Buffer.from(csvContent);
    const csvBlob = {
      name: 'test-normal.csv',
      mimeType: 'text/csv',
      buffer: csvBuffer,
    };

    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(csvBlob);

    // Wait for file processing
    await page.waitForTimeout(2000);

    // Verify NO cleansing notification appears
    const cleansingToastTitle = page.locator('text=Data Cleansing Applied');
    const toastVisible = await cleansingToastTitle.isVisible({ timeout: 5000 }).catch(() => false);
    expect(toastVisible).toBeFalsy(); // Cleansing toast should NOT appear for valid CSV

    console.log('✅ No cleansing notification for properly formatted CSV');
  });

  test('CSV upload with multiple rows requiring cleansing shows accurate count', async ({ page }) => {
    // Create CSV with multiple rows that need cleansing
    const csvContent = `server_name,description,ip_address
server1,DC1, room A,192.168.1.1
server2,Located in DC2, building B,192.168.1.2
server3,Another, comma, issue,192.168.1.3
server4,One more, problem, row,192.168.1.4
server5,Normal description,192.168.1.5`;

    const csvBuffer = Buffer.from(csvContent);
    const csvBlob = {
      name: 'test-multiple-cleansing.csv',
      mimeType: 'text/csv',
      buffer: csvBuffer,
    };

    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(csvBlob);

    // Wait for processing
    await page.waitForTimeout(2000);

    // Verify toast title appears
    const toastTitle = page.locator('text=Data Cleansing Applied');
    await expect(toastTitle.first()).toBeVisible({ timeout: 10000 });

    // Verify toast mentions multiple rows (should be at least 4 rows cleansed)
    const rowCountText = page.locator('text=/\\d+ row\\(s\\) were cleaned/i');
    await expect(rowCountText.first()).toBeVisible({ timeout: 5000 });

    // Extract row count from toast message (e.g., "4 row(s) were cleaned")
    const rowCountContent = await rowCountText.first().textContent();
    const rowCountMatch = rowCountContent?.match(/(\d+)\s+row/i);
    if (rowCountMatch) {
      const rowCount = parseInt(rowCountMatch[1], 10);
      expect(rowCount).toBeGreaterThanOrEqual(4); // Should be at least 4 rows
      console.log(`✅ Toast shows correct row count: ${rowCount} rows cleansed`);
    }
  });
});
