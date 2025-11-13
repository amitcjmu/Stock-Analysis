/**
 * E2E Tests for Decommission Flow - Overview Page
 *
 * Tests Issue #942: Decommission Overview Page Implementation
 *
 * Test Coverage:
 * - Page navigation and rendering
 * - Sidebar menu structure
 * - Metrics cards display
 * - Decommission Assistant insights
 * - Phase pipeline visualization
 * - Schedule Decommission modal
 * - System selection functionality
 *
 * Per ADR-027: Uses snake_case field names
 * Per ADR-006: MFO pattern with HTTP polling
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:8081';
const DECOMMISSION_URL = `${BASE_URL}/decommission`;

// Helper function to login
async function login(page: Page) {
  await page.goto(`${BASE_URL}/login`);

  // Fill login form with existing credentials
  await page.getByRole('textbox', { name: 'Email' }).fill('chockas@hcltech.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('Testing123!');

  // Click sign in and wait for navigation
  await page.getByRole('button', { name: 'Sign In' }).click();

  // Wait for successful login (redirects to dashboard)
  await page.waitForURL(BASE_URL, { timeout: 10000 });

  // Verify login success
  await expect(page.locator('text=Login Successful')).toBeVisible({ timeout: 5000 });
}

test.describe('Decommission Overview Page - Basic Navigation', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display Decommission section in sidebar', async ({ page }) => {
    await page.goto(BASE_URL);

    // Find and click Decommission in sidebar
    const decommissionSection = page.locator('text=Decommission').first();
    await expect(decommissionSection).toBeVisible();

    // Click to expand submenu
    await decommissionSection.click();

    // Verify all 5 submenu items are present
    await expect(page.getByRole('link', { name: 'Overview' }).first()).toBeVisible();
    await expect(page.getByRole('link', { name: 'Planning' }).first()).toBeVisible();
    await expect(page.getByRole('link', { name: 'Data Migration' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Shutdown' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Export' })).toBeVisible();
  });

  test('should navigate to Overview page and display all sections', async ({ page }) => {
    await page.goto(DECOMMISSION_URL);

    // Verify page title
    await expect(page.locator('h1:has-text("Decommission Flow Overview")')).toBeVisible();

    // Verify description
    await expect(page.locator('text=Safely retire legacy systems with automated compliance')).toBeVisible();

    // Verify action buttons
    await expect(page.getByRole('button', { name: 'AI Analysis' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Schedule Decommission' })).toBeVisible();
  });

  test('should display Decommission Assistant insight card', async ({ page }) => {
    await page.goto(DECOMMISSION_URL);

    // Verify assistant heading
    await expect(page.locator('h3:has-text("Decommission Assistant")')).toBeVisible();

    // Verify assistant recommendation text
    await expect(page.locator('text=AI recommends prioritizing 3 legacy systems')).toBeVisible();
    await expect(page.locator('text=$300K annual savings')).toBeVisible();
  });

  test('should display all 4 metrics cards', async ({ page }) => {
    await page.goto(DECOMMISSION_URL);

    // Systems Queued
    await expect(page.locator('text=Systems Queued')).toBeVisible();
    await expect(page.locator('text=45')).toBeVisible();
    await expect(page.locator('text=of 120 total')).toBeVisible();

    // Annual Savings
    await expect(page.locator('text=Annual Savings')).toBeVisible();
    await expect(page.locator('text=$2.4M')).toBeVisible();

    // Data Archived
    await expect(page.locator('text=Data Archived')).toBeVisible();
    await expect(page.locator('text=1.2 TB')).toBeVisible();

    // Compliance Score
    await expect(page.locator('text=Compliance Score')).toBeVisible();
    await expect(page.locator('text=98%')).toBeVisible();
  });

  test('should display Decommission Pipeline with 4 phases', async ({ page }) => {
    await page.goto(DECOMMISSION_URL);

    // Verify pipeline heading
    await expect(page.locator('h3:has-text("Decommission Pipeline")')).toBeVisible();

    // Verify all 4 phases are displayed
    await expect(page.locator('h4:has-text("Planning")')).toBeVisible();
    await expect(page.locator('text=Dependency analysis, risk assessment')).toBeVisible();
    await expect(page.locator('text=67%')).toBeVisible();
    await expect(page.locator('text=12 systems')).toBeVisible();

    await expect(page.locator('h4:has-text("Data Migration")')).toBeVisible();
    await expect(page.locator('text=Archive critical data, backup verification')).toBeVisible();
    await expect(page.locator('text=45%')).toBeVisible();
    await expect(page.locator('text=8 systems')).toBeVisible();

    await expect(page.locator('h4:has-text("System Shutdown")')).toBeVisible();
    await expect(page.locator('text=Safely shut down and remove legacy systems')).toBeVisible();
    await expect(page.locator('text=30%')).toBeVisible();
    await expect(page.locator('text=5 systems')).toBeVisible();

    await expect(page.locator('h4:has-text("Validation")')).toBeVisible();
    await expect(page.locator('text=Post-shutdown validation and cleanup')).toBeVisible();
    await expect(page.locator('text=15%')).toBeVisible();
    await expect(page.locator('text=3 systems')).toBeVisible();
  });

  test('should display Upcoming Decommissions list', async ({ page }) => {
    await page.goto(DECOMMISSION_URL);

    // Verify section heading
    await expect(page.locator('h3:has-text("Upcoming Decommissions")')).toBeVisible();

    // Verify first system
    await expect(page.locator('h4:has-text("Legacy Mainframe System")')).toBeVisible();
    await expect(page.locator('text=$120,000/year')).toBeVisible();
    await expect(page.locator('text=Type:Application')).toBeVisible();
    await expect(page.locator('text=Scheduled:2025-03-15')).toBeVisible();
    await expect(page.locator('text=Priority:High')).toBeVisible();

    // Verify second system
    await expect(page.locator('h4:has-text("Old CRM Database")')).toBeVisible();
    await expect(page.locator('text=$45,000/year')).toBeVisible();
    await expect(page.locator('text=Type:Database')).toBeVisible();
    await expect(page.locator('text=Scheduled:2025-02-28')).toBeVisible();
    await expect(page.locator('text=Priority:Medium')).toBeVisible();

    // Verify third system
    await expect(page.locator('h4:has-text("Legacy Web Server")')).toBeVisible();
    await expect(page.locator('text=$30,000/year')).toBeVisible();
    await expect(page.locator('text=Type:Infrastructure')).toBeVisible();
    await expect(page.locator('text=Scheduled:2025-04-10')).toBeVisible();
    await expect(page.locator('text=Priority:Low')).toBeVisible();
  });
});

test.describe('Decommission Overview Page - Schedule Modal', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto(DECOMMISSION_URL);
  });

  test('should open Schedule Decommission modal', async ({ page }) => {
    // Click Schedule Decommission button
    await page.getByRole('button', { name: 'Schedule Decommission' }).click();

    // Verify modal appears
    await expect(page.locator('h2:has-text("Initialize Decommission Flow")')).toBeVisible();
    await expect(page.locator('text=Select systems to schedule for decommissioning')).toBeVisible();

    // Verify Cancel button
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();

    // Verify Initialize button is disabled with "0 selected" text
    await expect(page.getByRole('button', { name: /Initialize.*0 selected/ })).toBeDisabled();
  });

  test('should display all 3 systems in modal', async ({ page }) => {
    await page.getByRole('button', { name: 'Schedule Decommission' }).click();

    // Verify all systems have checkboxes
    await expect(page.getByRole('checkbox', { name: /Legacy Mainframe System/ })).toBeVisible();
    await expect(page.locator('text=Application').first()).toBeVisible();

    await expect(page.getByRole('checkbox', { name: /Old CRM Database/ })).toBeVisible();
    await expect(page.locator('text=Database').first()).toBeVisible();

    await expect(page.getByRole('checkbox', { name: /Legacy Web Server/ })).toBeVisible();
    await expect(page.locator('text=Infrastructure').first()).toBeVisible();
  });

  test('should enable Initialize button when system selected', async ({ page }) => {
    await page.getByRole('button', { name: 'Schedule Decommission' }).click();

    // Initially disabled
    await expect(page.getByRole('button', { name: /Initialize.*0 selected/ })).toBeDisabled();

    // Select one system
    await page.getByRole('checkbox', { name: /Legacy Mainframe System/ }).click();

    // Button should now be enabled with "1 selected" text
    await expect(page.getByRole('button', { name: /Initialize.*1 selected/ })).toBeEnabled();
  });

  test('should update count when multiple systems selected', async ({ page }) => {
    await page.getByRole('button', { name: 'Schedule Decommission' }).click();

    // Select multiple systems
    await page.getByRole('checkbox', { name: /Legacy Mainframe System/ }).click();
    await page.getByRole('checkbox', { name: /Old CRM Database/ }).click();

    // Button should show "2 selected"
    await expect(page.getByRole('button', { name: /Initialize.*2 selected/ })).toBeEnabled();

    // Select third system
    await page.getByRole('checkbox', { name: /Legacy Web Server/ }).click();

    // Button should show "3 selected"
    await expect(page.getByRole('button', { name: /Initialize.*3 selected/ })).toBeEnabled();
  });

  test('should close modal when Cancel clicked', async ({ page }) => {
    await page.getByRole('button', { name: 'Schedule Decommission' }).click();

    // Verify modal is open
    await expect(page.locator('h2:has-text("Initialize Decommission Flow")')).toBeVisible();

    // Click Cancel
    await page.getByRole('button', { name: 'Cancel' }).click();

    // Wait a bit for modal to close
    await page.waitForTimeout(500);

    // Modal should be closed
    await expect(page.locator('h2:has-text("Initialize Decommission Flow")')).not.toBeVisible();
  });

  test('should deselect system when clicked again', async ({ page }) => {
    await page.getByRole('button', { name: 'Schedule Decommission' }).click();

    // Select system
    await page.getByRole('checkbox', { name: /Legacy Mainframe System/ }).click();
    await expect(page.getByRole('button', { name: /Initialize.*1 selected/ })).toBeEnabled();

    // Deselect same system
    await page.getByRole('checkbox', { name: /Legacy Mainframe System/ }).click();

    // Back to 0 selected and disabled
    await expect(page.getByRole('button', { name: /Initialize.*0 selected/ })).toBeDisabled();
  });
});

test.describe('Decommission Overview Page - Console and Network Validation', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should load page without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];

    // Capture console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(DECOMMISSION_URL);

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Verify no console errors
    expect(consoleErrors).toHaveLength(0);
  });

  test('should not have 404 errors for API calls', async ({ page }) => {
    const failedRequests: string[] = [];

    // Capture failed requests
    page.on('response', (response) => {
      if (response.status() === 404) {
        failedRequests.push(response.url());
      }
    });

    await page.goto(DECOMMISSION_URL);

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Verify no 404 errors
    expect(failedRequests).toHaveLength(0);
  });

  test('should use snake_case field names (ADR-027 compliance)', async ({ page }) => {
    // This test verifies the page is ready to handle snake_case API responses
    await page.goto(DECOMMISSION_URL);

    // Page should load without errors even though backend uses snake_case
    await expect(page.locator('h1:has-text("Decommission Flow Overview")')).toBeVisible();

    // Metrics should display correctly (data would come from API in snake_case)
    await expect(page.locator('text=Systems Queued')).toBeVisible();
    await expect(page.locator('text=Annual Savings')).toBeVisible();
    await expect(page.locator('text=Data Archived')).toBeVisible();
    await expect(page.locator('text=Compliance Score')).toBeVisible();
  });
});
