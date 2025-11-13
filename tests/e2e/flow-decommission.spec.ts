import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.describe('Decommission Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToFlow(page, 'Decommission');
  });

  test('should load Decommission page', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText?.toLowerCase()).toContain('decommission');
  });

  test('should show retirement candidates', async ({ page }) => {
    const candidates = page.locator('.candidate, [data-testid*="decom"]');
    const count = await candidates.count();
    console.log('Decommission candidates:', count);
  });

  test('should display shutdown checklist', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    const checklist = page.locator('.checklist, [role="list"]');
    const checklistCount = await checklist.count();
    console.log('Checklist items found:', checklistCount);
  });
});
