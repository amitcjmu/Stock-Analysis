/**
 * E2E tests for Multi-Asset Bulk Answer workflow.
 *
 * Tests the complete user journey:
 * 1. Asset Selection
 * 2. Answer Questions
 * 3. Resolve Conflicts (if any)
 * 4. Confirmation & Submit
 */

import { test, expect } from '@playwright/test';

test.describe('Multi-Asset Bulk Answer Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:8081/login', { waitUntil: 'load' });
    await page.waitForTimeout(1000);

    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button[type="submit"]');

    // Wait for login to process
    await page.waitForTimeout(3000);

    // Verify login was successful
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      throw new Error(`Login failed - still on login page: ${currentUrl}`);
    }

    // Navigate to adaptive forms page (where bulk answer button exists)
    await page.goto('/collection/adaptive-forms');
    // Verify we're on the adaptive forms page
    await expect(page).toHaveURL(/.*\/collection\/adaptive-forms/);

    // Wait for flow to auto-initialize (page creates flow automatically if none exists)
    // This may take a few seconds while the flow is created in the backend
    console.log('⏳ Waiting for flow to auto-initialize...');
    await page.waitForTimeout(5000); // Give time for flow creation

    // Wait for the bulk operations bar to appear (indicates flow is active)
    // If this times out, it means either:
    // 1. Flow initialization failed (backend issue)
    // 2. Blocking flows exist (run SQL: DELETE FROM migration.discovery_flows WHERE status NOT IN ('completed','failed','cancelled'))
    await page.waitForSelector('[data-testid="bulk-operations-bar"]', { timeout: 30000 });
    console.log('✅ Flow initialized, bulk operations bar visible');
  });

  test('should complete bulk answer for multiple assets without conflicts', async ({ page }) => {
    // Step 1: Open bulk answer modal
    await page.click('[data-testid="bulk-answer-button"]');
    await expect(page.locator('[data-testid="multi-asset-answer-modal"]')).toBeVisible();

    // Step 2: Select 5 assets
    const assetCheckboxes = page.locator('[data-testid^="asset-checkbox-"]');
    await assetCheckboxes.nth(0).check();
    await assetCheckboxes.nth(1).check();
    await assetCheckboxes.nth(2).check();
    await assetCheckboxes.nth(3).check();
    await assetCheckboxes.nth(4).check();

    // Verify selection count
    await expect(page.locator('[data-testid="selected-count"]')).toContainText('5');

    // Continue to answer questions
    await page.click('[data-testid="continue-to-answers-button"]');

    // Step 3: Answer questions
    await expect(page.locator('[data-testid="bulk-answer-form"]')).toBeVisible();

    // Fill in application name
    await page.fill('[data-testid="question-app_01_name"]', 'Test Application');

    // Select programming language
    await page.selectOption('[data-testid="question-app_02_language"]', 'Python');

    // Select database
    await page.selectOption('[data-testid="question-app_03_database"]', 'PostgreSQL');

    // Continue to preview
    await page.click('[data-testid="preview-answers-button"]');

    // Step 4: Preview should show no conflicts
    await expect(page.locator('[data-testid="conflict-warning"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="preview-summary"]')).toContainText('5 assets');
    await expect(page.locator('[data-testid="preview-summary"]')).toContainText('3 questions');

    // Step 5: Submit
    await page.click('[data-testid="submit-bulk-answers-button"]');

    // Wait for success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Successfully answered');

    // Modal should close
    await expect(page.locator('[data-testid="multi-asset-answer-modal"]')).not.toBeVisible();
  });

  test('should handle conflicts with overwrite strategy', async ({ page }) => {
    // Select assets that have conflicting answers
    await page.click('[data-testid="bulk-answer-button"]');

    // Select 3 assets with existing different answers
    await page.click('[data-testid="asset-checkbox-asset-with-conflict-1"]');
    await page.click('[data-testid="asset-checkbox-asset-with-conflict-2"]');
    await page.click('[data-testid="asset-checkbox-asset-with-conflict-3"]');

    await page.click('[data-testid="continue-to-answers-button"]');

    // Answer question that will conflict
    await page.selectOption('[data-testid="question-app_02_language"]', 'Java');

    // Preview to detect conflicts
    await page.click('[data-testid="preview-answers-button"]');

    // Should show conflict warning
    await expect(page.locator('[data-testid="conflict-warning"]')).toBeVisible();
    await expect(page.locator('[data-testid="conflict-count"]')).toContainText('1 conflict');

    // Show conflict details
    await page.click('[data-testid="view-conflicts-button"]');
    await expect(page.locator('[data-testid="conflict-detail"]')).toBeVisible();

    // Select overwrite strategy
    await page.selectOption('[data-testid="conflict-strategy"]', 'overwrite');

    // Submit with conflict resolution
    await page.click('[data-testid="submit-with-conflicts-button"]');

    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible({ timeout: 10000 });
  });

  test('should handle conflicts with skip strategy', async ({ page }) => {
    await page.click('[data-testid="bulk-answer-button"]');

    // Select conflicting assets
    await page.click('[data-testid="asset-checkbox-asset-with-conflict-1"]');
    await page.click('[data-testid="asset-checkbox-asset-with-conflict-2"]');

    await page.click('[data-testid="continue-to-answers-button"]');
    await page.fill('[data-testid="question-app_01_name"]', 'New Name');
    await page.click('[data-testid="preview-answers-button"]');

    // Conflict detected
    await expect(page.locator('[data-testid="conflict-warning"]')).toBeVisible();

    // Select skip strategy (skip conflicting assets)
    await page.selectOption('[data-testid="conflict-strategy"]', 'skip');

    await page.click('[data-testid="submit-with-conflicts-button"]');

    // Success message should indicate some assets skipped
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="skipped-assets"]')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.click('[data-testid="bulk-answer-button"]');

    // Select assets
    await page.click('[data-testid="asset-checkbox-0"]');
    await page.click('[data-testid="continue-to-answers-button"]');

    // Try to preview without answering required questions
    await page.click('[data-testid="preview-answers-button"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="validation-error"]')).toContainText('required');

    // Submit button should be disabled
    await expect(page.locator('[data-testid="submit-bulk-answers-button"]')).toBeDisabled();
  });

  test('should filter assets by type', async ({ page }) => {
    await page.click('[data-testid="bulk-answer-button"]');

    // Apply asset type filter
    await page.selectOption('[data-testid="asset-type-filter"]', 'Application');

    // Should only show Application assets
    const visibleAssets = page.locator('[data-testid^="asset-row-"]');
    await expect(visibleAssets).toHaveCount(await getApplicationAssetCount());

    // Change filter to Server
    await page.selectOption('[data-testid="asset-type-filter"]', 'Server');

    // Should only show Server assets
    await expect(visibleAssets).toHaveCount(await getServerAssetCount());
  });
});

// Helper functions (would be in a separate utility file)
async function getApplicationAssetCount(): Promise<number> {
  // In real implementation, would query test data
  return 10;
}

async function getServerAssetCount(): Promise<number> {
  return 8;
}
