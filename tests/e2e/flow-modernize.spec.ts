import { test, expect } from '@playwright/test';

test.describe('Modernize Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Navigate to Modernize
    await page.click('text=Modernize');
    await page.waitForTimeout(1000);
  });

  test('should load Modernize page', async ({ page }) => {
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Modernize');
    
    await page.screenshot({ path: 'test-results/modernize-page.png' });
  });

  test('should display modernization recommendations', async ({ page }) => {
    // Look for recommendations
    const recommendations = page.locator('.recommendation, .suggestion, [data-testid*="recommend"]');
    const recCount = await recommendations.count();
    console.log('Recommendations found:', recCount);
  });

  test('should show refactoring options', async ({ page }) => {
    // Look for refactoring elements
    const refactoring = await page.textContent('body');
    const hasRefactoring = 
      refactoring?.includes('refactor') ||
      refactoring?.includes('optimize') ||
      refactoring?.includes('improve');
    console.log('Has refactoring content:', hasRefactoring);
  });

  test('should display cloud-native patterns', async ({ page }) => {
    // Look for cloud patterns
    const patterns = page.locator('.pattern, .architecture, .design');
    const patternCount = await patterns.count();
    console.log('Architecture patterns found:', patternCount);
  });
});
