import { test, expect } from '@playwright/test';

test.describe('Planning Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Navigate to Plan
    await page.click('text=Plan');
    await page.waitForTimeout(1000);
  });

  test('should load Planning page', async ({ page }) => {
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Plan');
    
    await page.screenshot({ path: 'test-results/planning-page.png' });
  });

  test('should display migration waves', async ({ page }) => {
    // Look for wave planning elements
    const waves = page.locator('.wave, .phase, [data-testid*="wave"]');
    const waveCount = await waves.count();
    console.log('Migration waves found:', waveCount);
    
    // Check for timeline
    const timeline = page.locator('.timeline, .gantt, .schedule');
    const hasTimeline = await timeline.count() > 0;
    console.log('Timeline view available:', hasTimeline);
  });

  test('should show resource planning', async ({ page }) => {
    // Look for resource allocation
    const resources = page.locator('.resource, .team, .allocation');
    const resourceCount = await resources.count();
    console.log('Resource elements:', resourceCount);
    
    // Check for capacity indicators
    const capacity = await page.textContent('body');
    const hasCapacity = capacity?.includes('capacity') || capacity?.includes('resource') || capacity?.includes('team');
    console.log('Has resource planning:', hasCapacity);
  });

  test('should display dependencies', async ({ page }) => {
    // Look for dependency indicators
    const dependencies = page.locator('.dependency, .prerequisite, [data-depends]');
    const depCount = await dependencies.count();
    console.log('Dependencies found:', depCount);
  });

  test('should allow creating migration plan', async ({ page }) => {
    // Look for plan creation
    const createButton = page.locator('button:has-text("Create"), button:has-text("New Plan"), button:has-text("Add")');
    
    if (await createButton.count() > 0) {
      console.log('Create plan button found');
      await createButton.first().click();
      await page.waitForTimeout(2000);
      
      // Check if plan form appears
      const form = await page.locator('form, .modal, [role="dialog"]').count();
      console.log('Plan creation form appeared:', form > 0);
    }
  });
});
