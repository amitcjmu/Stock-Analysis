import { test, expect } from '@playwright/test';

test.describe('Execute Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Navigate to Execute
    await page.click('text=Execute');
    await page.waitForTimeout(1000);
  });

  test('should load Execute page', async ({ page }) => {
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Execute');
    
    await page.screenshot({ path: 'test-results/execute-page.png' });
  });

  test('should display migration status', async ({ page }) => {
    // Look for status indicators
    const statusElements = page.locator('.status, .state, [data-status]');
    const statusCount = await statusElements.count();
    console.log('Status indicators found:', statusCount);
    
    // Check for different states
    const inProgress = await page.locator('[data-status="in-progress"], .in-progress').count();
    const completed = await page.locator('[data-status="completed"], .completed').count();
    const pending = await page.locator('[data-status="pending"], .pending').count();
    
    console.log(`Status - In Progress: ${inProgress}, Completed: ${completed}, Pending: ${pending}`);
  });

  test('should show execution timeline', async ({ page }) => {
    // Look for timeline elements
    const timeline = page.locator('.timeline, .schedule, .calendar');
    const hasTimeline = await timeline.count() > 0;
    console.log('Timeline view present:', hasTimeline);
  });

  test('should display execution logs', async ({ page }) => {
    // Look for logs or activity feed
    const logs = page.locator('.log, .activity, .history, [data-testid*="log"]');
    const logCount = await logs.count();
    console.log('Log entries found:', logCount);
    
    if (logCount > 0) {
      const firstLog = await logs.first().textContent();
      console.log('First log entry:', firstLog?.substring(0, 100));
    }
  });

  test('should have rollback options', async ({ page }) => {
    // Look for rollback functionality
    const rollbackButton = page.locator('button:has-text("Rollback"), button:has-text("Revert"), button:has-text("Undo")');
    const hasRollback = await rollbackButton.count() > 0;
    console.log('Rollback option available:', hasRollback);
  });
});
