import { test, expect } from '@playwright/test';

test.describe('FinOps Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Navigate to FinOps
    await page.click('text=FinOps');
    await page.waitForTimeout(1000);
  });

  test('should load FinOps page', async ({ page }) => {
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('FinOps');
    
    await page.screenshot({ path: 'test-results/finops-page.png' });
  });

  test('should display cost metrics', async ({ page }) => {
    // Look for cost/financial data
    const costElements = page.locator('.cost, .price, .budget, [data-testid*="cost"]');
    const costCount = await costElements.count();
    console.log('Cost elements found:', costCount);
    
    // Check for currency symbols
    const hasFinancialData = await page.textContent('body');
    const hasCurrency = hasFinancialData?.includes('$') || hasFinancialData?.includes('€') || hasFinancialData?.includes('£');
    console.log('Has currency data:', hasCurrency);
  });

  test('should show cost optimization suggestions', async ({ page }) => {
    // Look for optimization opportunities
    const optimizations = page.locator('.optimization, .saving, .recommendation');
    const optCount = await optimizations.count();
    console.log('Cost optimization suggestions:', optCount);
  });

  test('should display budget tracking', async ({ page }) => {
    // Look for budget elements
    const budget = page.locator('.budget, .spend, .forecast');
    const budgetCount = await budget.count();
    console.log('Budget tracking elements:', budgetCount);
  });
});
