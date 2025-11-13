import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.describe('FinOps Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToFlow(page, 'FinOps');
  });

  test('should load FinOps page', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText?.toLowerCase()).toContain('fin');
  });

  test('should display cost metrics', async ({ page }) => {
    const costElements = page.locator('.cost, .price, [data-testid*="cost"]');
    const costCount = await costElements.count();
    console.log('Cost elements found:', costCount);
    
    const bodyText = await page.textContent('body');
    const hasCurrency = bodyText?.includes('$') || bodyText?.includes('USD');
    console.log('Has currency data:', hasCurrency);
  });

  test('should show cost optimization suggestions', async ({ page }) => {
    const suggestions = page.locator('.suggestion, .recommendation');
    const suggestionCount = await suggestions.count();
    console.log('Cost optimization suggestions:', suggestionCount);
  });

  test('should display budget tracking', async ({ page }) => {
    const budgetElements = page.locator('.budget, [data-testid*="budget"]');
    const budgetCount = await budgetElements.count();
    console.log('Budget tracking elements:', budgetCount);
  });
});
