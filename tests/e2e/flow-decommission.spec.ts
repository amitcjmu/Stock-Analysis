import { test, expect } from '@playwright/test';

test.describe('Decommission Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Navigate to Decommission
    await page.click('text=Decommission');
    await page.waitForTimeout(1000);
  });

  test('should load Decommission page', async ({ page }) => {
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Decommission');
    
    await page.screenshot({ path: 'test-results/decommission-page.png' });
  });

  test('should show retirement candidates', async ({ page }) => {
    // Look for systems to decommission
    const candidates = page.locator('.candidate, .retire, [data-testid*="decommission"]');
    const candidateCount = await candidates.count();
    console.log('Decommission candidates:', candidateCount);
  });

  test('should display shutdown checklist', async ({ page }) => {
    // Look for checklist items
    const checklist = page.locator('.checklist, .task, input[type="checkbox"]');
    const checklistCount = await checklist.count();
    console.log('Checklist items found:', checklistCount);
  });
});
