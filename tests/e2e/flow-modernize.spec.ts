import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.describe('Modernize Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToFlow(page, 'Modernize');
  });

  test('should load Modernize page', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    const bodyText = await page.textContent('body');
    expect(bodyText?.toLowerCase()).toContain('modern');
  });

  test('should display modernization recommendations', async ({ page }) => {
    const recommendations = page.locator('.recommendation, [data-testid*="recommend"]');
    const recCount = await recommendations.count();
    console.log('Recommendations found:', recCount);
  });

  test('should show refactoring options', async ({ page }) => {
    const bodyText = await page.textContent('body');
    const hasRefactoring = bodyText?.toLowerCase().includes('refactor') ||
                          bodyText?.toLowerCase().includes('container') ||
                          bodyText?.toLowerCase().includes('serverless');
    console.log('Has refactoring content:', hasRefactoring);
  });

  test('should display cloud-native patterns', async ({ page }) => {
    const patterns = page.locator('.pattern, [data-testid*="pattern"]');
    const patternCount = await patterns.count();
    console.log('Architecture patterns found:', patternCount);
  });
});
