/**
 * E2E tests for Bulk CSV/JSON Import workflow.
 *
 * Tests the complete user journey:
 * 1. File Upload
 * 2. Field Mapping (with confidence scores)
 * 3. Import Configuration
 * 4. Progress Monitoring
 * 5. Results Summary
 */

import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Bulk CSV Import Workflow', () => {
  const testFilesDir = path.join(__dirname, '../fixtures/import-files');

  test.beforeEach(async ({ page }) => {
    await page.goto('/collection');
    await expect(page).toHaveTitle(/Collection Flow/);
  });

  test('should complete CSV import with automatic field mapping', async ({ page }) => {
    // Step 1: Open import wizard
    await page.click('[data-testid="bulk-import-button"]');
    await expect(page.locator('[data-testid="import-wizard-modal"]')).toBeVisible();

    // Step 2: Upload CSV file
    const fileInput = page.locator('[data-testid="file-upload-input"]');
    await fileInput.setInputFiles(path.join(testFilesDir, 'applications.csv'));

    // Wait for file analysis
    await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible({ timeout: 5000 });

    // Verify detected rows and columns
    await expect(page.locator('[data-testid="detected-rows"]')).toContainText('50 rows');
    await expect(page.locator('[data-testid="detected-columns"]')).toContainText('10 columns');

    // Continue to field mapping
    await page.click('[data-testid="continue-to-mapping-button"]');

    // Step 3: Review suggested field mappings
    await expect(page.locator('[data-testid="field-mapping-table"]')).toBeVisible();

    // High-confidence mappings should be pre-selected
    const highConfidenceMappings = page.locator('[data-testid^="mapping-confidence-high-"]');
    await expect(highConfidenceMappings.first()).toBeVisible();

    // Verify confidence indicators
    await expect(page.locator('[data-testid="confidence-indicator-app_name"]')).toContainText('95%');

    // Manually adjust a low-confidence mapping
    await page.selectOption(
      '[data-testid="mapping-select-prog_lang"]',
      'app_03_language'
    );

    // Continue to configuration
    await page.click('[data-testid="continue-to-config-button"]');

    // Step 4: Configure import options
    await expect(page.locator('[data-testid="import-configuration"]')).toBeVisible();

    // Select overwrite option
    await page.check('[data-testid="overwrite-existing-checkbox"]');

    // Select gap recalculation mode
    await page.selectOption('[data-testid="gap-recalc-mode"]', 'fast');

    // Start import
    await page.click('[data-testid="start-import-button"]');

    // Step 5: Monitor progress
    await expect(page.locator('[data-testid="import-progress-bar"]')).toBeVisible();

    // Wait for stages to progress
    await expect(page.locator('[data-testid="current-stage"]')).toContainText('Creating assets');

    // Wait for completion (with longer timeout for actual import)
    await expect(page.locator('[data-testid="import-complete"]')).toBeVisible({ timeout: 30000 });

    // Step 6: Review results
    await expect(page.locator('[data-testid="assets-created"]')).toContainText('50');
    await expect(page.locator('[data-testid="questions-answered"]')).toContainText('200');

    // No errors
    await expect(page.locator('[data-testid="import-errors"]')).toContainText('0');

    // Close wizard
    await page.click('[data-testid="close-wizard-button"]');
    await expect(page.locator('[data-testid="import-wizard-modal"]')).not.toBeVisible();
  });

  test('should handle JSON import with manual field mapping', async ({ page }) => {
    await page.click('[data-testid="bulk-import-button"]');

    // Upload JSON file
    const fileInput = page.locator('[data-testid="file-upload-input"]');
    await fileInput.setInputFiles(path.join(testFilesDir, 'servers.json'));

    await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible({ timeout: 5000 });

    // JSON should be detected
    await expect(page.locator('[data-testid="file-format"]')).toContainText('JSON');

    await page.click('[data-testid="continue-to-mapping-button"]');

    // Manually map all fields
    await page.selectOption('[data-testid="mapping-select-server_name"]', 'server_01_name');
    await page.selectOption('[data-testid="mapping-select-os_type"]', 'server_02_os');
    await page.selectOption('[data-testid="mapping-select-cpu_count"]', 'server_03_cpu');

    // Verify mapping count
    await expect(page.locator('[data-testid="mapped-fields-count"]')).toContainText('3 of 3');

    await page.click('[data-testid="continue-to-config-button"]');

    // Use thorough gap recalculation for servers
    await page.selectOption('[data-testid="gap-recalc-mode"]', 'thorough');

    await page.click('[data-testid="start-import-button"]');

    // Wait for completion
    await expect(page.locator('[data-testid="import-complete"]')).toBeVisible({ timeout: 30000 });
  });

  test('should show validation warnings for invalid data', async ({ page }) => {
    await page.click('[data-testid="bulk-import-button"]');

    // Upload file with invalid data
    const fileInput = page.locator('[data-testid="file-upload-input"]');
    await fileInput.setInputFiles(path.join(testFilesDir, 'invalid-data.csv'));

    await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible({ timeout: 5000 });

    await page.click('[data-testid="continue-to-mapping-button"]');
    await page.click('[data-testid="continue-to-config-button"]');

    // Should show validation warnings
    await expect(page.locator('[data-testid="validation-warnings"]')).toBeVisible();
    await expect(page.locator('[data-testid="warning-count"]')).toContainText('5 warnings');

    // Expand warnings
    await page.click('[data-testid="expand-warnings-button"]');

    // Should show specific warnings
    await expect(page.locator('[data-testid="warning-invalid-dropdown"]')).toBeVisible();
    await expect(page.locator('[data-testid="warning-missing-required"]')).toBeVisible();

    // User can still proceed
    await page.click('[data-testid="start-import-button"]');

    // Should show confirmation dialog for proceeding with warnings
    await expect(page.locator('[data-testid="warning-confirmation-dialog"]')).toBeVisible();

    await page.click('[data-testid="confirm-proceed-button"]');

    // Import should proceed
    await expect(page.locator('[data-testid="import-progress-bar"]')).toBeVisible();
  });

  test('should handle file upload errors gracefully', async ({ page }) => {
    await page.click('[data-testid="bulk-import-button"]');

    // Upload file that's too large
    const fileInput = page.locator('[data-testid="file-upload-input"]');
    await fileInput.setInputFiles(path.join(testFilesDir, 'too-large.csv'));

    // Should show error message
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="upload-error"]')).toContainText('File size exceeds');

    // Clear error and retry
    await page.click('[data-testid="clear-file-button"]');

    // Upload valid file
    await fileInput.setInputFiles(path.join(testFilesDir, 'applications.csv'));

    // Should succeed
    await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible({ timeout: 5000 });
  });

  test('should allow canceling import during progress', async ({ page }) => {
    await page.click('[data-testid="bulk-import-button"]');

    const fileInput = page.locator('[data-testid="file-upload-input"]');
    await fileInput.setInputFiles(path.join(testFilesDir, 'large-dataset.csv'));

    await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible({ timeout: 5000 });

    await page.click('[data-testid="continue-to-mapping-button"]');
    await page.click('[data-testid="continue-to-config-button"]');
    await page.click('[data-testid="start-import-button"]');

    // Wait for import to start
    await expect(page.locator('[data-testid="import-progress-bar"]')).toBeVisible();

    // Cancel import
    await page.click('[data-testid="cancel-import-button"]');

    // Confirmation dialog
    await expect(page.locator('[data-testid="cancel-confirmation-dialog"]')).toBeVisible();
    await page.click('[data-testid="confirm-cancel-button"]');

    // Import should be canceled
    await expect(page.locator('[data-testid="import-canceled"]')).toBeVisible();

    // Can retry or close
    await expect(page.locator('[data-testid="retry-import-button"]')).toBeVisible();
  });

  test('should show progress stages during import', async ({ page }) => {
    await page.click('[data-testid="bulk-import-button"]');

    const fileInput = page.locator('[data-testid="file-upload-input"]');
    await fileInput.setInputFiles(path.join(testFilesDir, 'applications.csv'));

    await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible({ timeout: 5000 });
    await page.click('[data-testid="continue-to-mapping-button"]');
    await page.click('[data-testid="continue-to-config-button"]');
    await page.click('[data-testid="start-import-button"]');

    // Should show progression through stages
    await expect(page.locator('[data-testid="current-stage"]')).toContainText('Validating data');
    await expect(page.locator('[data-testid="current-stage"]')).toContainText('Creating assets');
    await expect(page.locator('[data-testid="current-stage"]')).toContainText('Answering questions');
    await expect(page.locator('[data-testid="current-stage"]')).toContainText('Recalculating gaps');

    // Progress percentage should increase
    const progressText = await page.locator('[data-testid="progress-percent"]').textContent();
    const progress = parseInt(progressText || '0');
    expect(progress).toBeGreaterThan(0);

    // Wait for 100%
    await expect(page.locator('[data-testid="progress-percent"]')).toContainText('100%');
  });
});
