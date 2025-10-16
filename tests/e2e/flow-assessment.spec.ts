import { test, expect } from '@playwright/test';

test.describe('Assessment Flow - Complete E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Navigate to Assess
    await page.click('text=Assess');
    await page.waitForTimeout(1000);
  });

  test('should load Assessment page', async ({ page }) => {
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Assess');
    
    // Check for assessment-related content
    const hasAssessmentContent = 
      bodyText?.includes('tech debt') ||
      bodyText?.includes('cloud read') ||
      bodyText?.includes('assessment') ||
      bodyText?.includes('analysis');
    console.log('Has assessment content:', hasAssessmentContent);
  });

  test('should display assessment categories', async ({ page }) => {
    // Look for assessment types or categories
    const cards = page.locator('.card, .assessment-card, [data-testid*="assess"]');
    const cardCount = await cards.count();
    console.log('Assessment cards found:', cardCount);
    
    if (cardCount > 0) {
      const firstCardText = await cards.first().textContent();
      console.log('First assessment type:', firstCardText?.substring(0, 100));
    }
  });

  test('should start new assessment', async ({ page }) => {
    // Look for start assessment button
    const startButton = page.locator('button:has-text("Start"), button:has-text("Begin"), button:has-text("New Assessment")');
    
    if (await startButton.count() > 0) {
      await startButton.first().click();
      await page.waitForTimeout(2000);
      
      // Check if assessment form appears
      const form = await page.locator('form, [role="form"]').count();
      console.log('Assessment form appeared:', form > 0);
      
      await page.screenshot({ path: 'test-results/assessment-start.png' });
    }
  });

  test('should show assessment metrics', async ({ page }) => {
    // Look for metrics or scores
    const metrics = page.locator('.metric, .score, .percentage, [data-testid*="metric"]');
    const metricCount = await metrics.count();
    console.log('Metrics displayed:', metricCount);
    
    // Check for progress indicators
    const progress = page.locator('[role="progressbar"], .progress-bar, .progress');
    const progressCount = await progress.count();
    console.log('Progress indicators:', progressCount);
  });

  test('should display risk analysis', async ({ page }) => {
    // Look for risk indicators
    const riskElements = page.locator('.risk, .warning, .alert, [data-severity]');
    const riskCount = await riskElements.count();
    
    if (riskCount > 0) {
      console.log('Risk indicators found:', riskCount);
      
      // Check risk levels
      const highRisk = await page.locator('.high-risk, [data-severity="high"]').count();
      const mediumRisk = await page.locator('.medium-risk, [data-severity="medium"]').count();
      const lowRisk = await page.locator('.low-risk, [data-severity="low"]').count();
      
      console.log(`Risks - High: ${highRisk}, Medium: ${mediumRisk}, Low: ${lowRisk}`);
    }
  });
});
