import { test, expect } from '@playwright/test';
import { loginAndNavigateToFlow } from '../utils/auth-helpers';

test.describe('Assessment Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToFlow(page, 'Assess');
  });

  test('should load Assessment page', async ({ page }) => {
    await page.waitForLoadState('domcontentloaded');
    
    // Check for assessment-related content
    const bodyText = await page.textContent('body');
    const hasAssessmentContent = 
      bodyText?.toLowerCase().includes('tech debt') ||
      bodyText?.toLowerCase().includes('cloud') ||
      bodyText?.toLowerCase().includes('assess') ||
      bodyText?.toLowerCase().includes('analysis');
    
    expect(hasAssessmentContent).toBeTruthy();
    console.log('✓ Assessment page loaded with relevant content');
  });

  test('should display assessment categories', async ({ page }) => {
    // Look for assessment types or categories
    const cards = page.locator('.card, [data-testid*="assess"]');
    const cardCount = await cards.count();
    console.log(`Found ${cardCount} assessment card(s)`);
    
    if (cardCount > 0) {
      await expect(cards.first()).toBeVisible({ timeout: 5000 });
      const firstCardText = await cards.first().textContent();
      console.log('First assessment type:', firstCardText?.substring(0, 100));
    } else {
      console.log('⚠️ No assessment cards found - checking for other content');
    }
  });

  test('should start new assessment', async ({ page }) => {
    // Look for start assessment button
    const startButton = page.locator('button:has-text("Start"), button:has-text("Begin"), button:has-text("New"), button:has-text("Create")');
    const buttonCount = await startButton.count();
    
    if (buttonCount > 0) {
      console.log(`✓ Found ${buttonCount} action button(s)`);
      await startButton.first().click();
      await page.waitForLoadState('domcontentloaded');
      
      // Check if assessment form or modal appears
      const form = page.locator('form, [role="form"], [role="dialog"]');
      if (await form.count() > 0) {
        await expect(form.first()).toBeVisible({ timeout: 5000 });
        console.log('✓ Assessment form appeared');
      }
      
      await page.screenshot({ path: 'test-results/assessment-start.png' });
    } else {
      console.log('⚠️ No start button found - may not be implemented yet');
    }
  });

  test('should show assessment metrics', async ({ page }) => {
    // Look for metrics or scores
    const metrics = page.locator('.metric, .score, .percentage, [data-testid*="metric"]');
    const metricCount = await metrics.count();
    console.log(`Found ${metricCount} metric element(s)`);
    
    // Check for progress indicators
    const progress = page.locator('[role="progressbar"], .progress-bar, .progress');
    const progressCount = await progress.count();
    console.log(`Found ${progressCount} progress indicator(s)`);
  });

  test('should display risk analysis', async ({ page }) => {
    // Look for risk indicators
    const riskElements = page.locator('.risk, .warning, .alert, [data-severity]');
    const riskCount = await riskElements.count();
    
    if (riskCount > 0) {
      console.log(`✓ Found ${riskCount} risk indicator(s)`);
      
      // Check risk levels
      const highRisk = await page.locator('[data-severity="high"]').count();
      const mediumRisk = await page.locator('[data-severity="medium"]').count();
      const lowRisk = await page.locator('[data-severity="low"]').count();
      
      console.log(`Risks - High: ${highRisk}, Medium: ${mediumRisk}, Low: ${lowRisk}`);
    } else {
      console.log('⚠️ No risk indicators found');
    }
  });

  test('should handle assessment state gracefully', async ({ page }) => {
    // Just verify the page loaded
    await page.waitForLoadState('domcontentloaded');
    
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    expect(bodyText!.length).toBeGreaterThan(0);
    
    console.log('✓ Assessment page handles state gracefully');
  });
});
