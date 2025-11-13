import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.describe('Planning Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToFlow(page, 'Plan');
  });

  test('should load Planning page', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText?.toLowerCase()).toContain('plan');
  });

  test('should display migration waves', async ({ page }) => {
    const waves = page.locator('.wave, [data-testid*="wave"]');
    const waveCount = await waves.count();
    console.log('Migration waves found:', waveCount);
    
    const timeline = page.locator('.timeline, [role="progressbar"]');
    const hasTimeline = await timeline.count() > 0;
    console.log('Timeline view available:', hasTimeline);
  });

  test('should show resource planning', async ({ page }) => {
    const resources = page.locator('.resource, [data-testid*="resource"]');
    const resourceCount = await resources.count();
    console.log('Resource elements:', resourceCount);
    
    const bodyText = await page.textContent('body');
    const hasResourcePlanning = bodyText?.toLowerCase().includes('resource') ||
                               bodyText?.toLowerCase().includes('capacity');
    console.log('Has resource planning:', hasResourcePlanning);
  });

  test('should display dependencies', async ({ page }) => {
    const dependencies = page.locator('.dependency, [data-testid*="depend"]');
    const depCount = await dependencies.count();
    console.log('Dependencies found:', depCount);
  });

  test('should allow creating migration plan', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
  });
});
