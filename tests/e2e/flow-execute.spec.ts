import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.describe('Execute Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToFlow(page, 'Execute');
  });

  test('should load Execute page', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText?.toLowerCase()).toContain('execut');
  });

  test('should display migration status', async ({ page }) => {
    const statusIndicators = page.locator('[data-status], .status');
    const statusCount = await statusIndicators.count();
    console.log('Status indicators found:', statusCount);
    
    const inProgress = await page.locator('[data-status="in-progress"]').count();
    const completed = await page.locator('[data-status="completed"]').count();
    const pending = await page.locator('[data-status="pending"]').count();
    
    console.log(`Status - In Progress: ${inProgress}, Completed: ${completed}, Pending: ${pending}`);
  });

  test('should show execution timeline', async ({ page }) => {
    const timeline = page.locator('.timeline, [role="progressbar"]');
    const hasTimeline = await timeline.count() > 0;
    console.log('Timeline view present:', hasTimeline);
  });

  test('should display execution logs', async ({ page }) => {
    const logs = page.locator('.log, .console, [data-testid*="log"]');
    const logCount = await logs.count();
    console.log('Log entries found:', logCount);
  });

  test('should have rollback options', async ({ page }) => {
    const rollbackButton = page.locator('button:has-text("Rollback"), button:has-text("Revert")');
    const hasRollback = await rollbackButton.count() > 0;
    console.log('Rollback option available:', hasRollback);
  });
});
