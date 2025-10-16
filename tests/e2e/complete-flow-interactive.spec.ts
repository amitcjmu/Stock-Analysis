import { test, expect } from '@playwright/test';
import * as path from 'path';

test.describe('Complete Migration Journey - Interactive', () => {
  test('should perform interactive operations across all flows', async ({ page }) => {
    test.setTimeout(180000); // 3 minutes for detailed interactions
    
    console.log('=== STARTING INTERACTIVE MIGRATION JOURNEY ===');
    
    // Login
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // COLLECTION PHASE
    console.log('\n--- COLLECTION PHASE ---');
    await page.click('text=Collection');
    await page.waitForTimeout(2000);
    
    // Try to interact with any buttons or inputs
    const collectionButtons = await page.locator('button:visible').all();
    console.log(`Found ${collectionButtons.length} buttons in Collection`);
    
    // Click first actionable button if exists
    if (collectionButtons.length > 2) {
      const buttonText = await collectionButtons[1].textContent();
      console.log(`Clicking button: ${buttonText}`);
      await collectionButtons[1].click();
      await page.waitForTimeout(1000);
    }
    
    // DISCOVERY PHASE
    console.log('\n--- DISCOVERY PHASE ---');
    await page.click('text=Discovery');
    await page.waitForTimeout(2000);
    
    // Check for any data grid or table
    const tables = await page.locator('table, [role="grid"]').count();
    console.log(`Found ${tables} data grids in Discovery`);
    
    // Try to interact with search/filter
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i], input[placeholder*="filter" i]');
    if (await searchInput.count() > 0) {
      await searchInput.first().fill('test-app');
      console.log('Applied search filter: test-app');
      await page.waitForTimeout(1000);
    }
    
    // ASSESSMENT PHASE
    console.log('\n--- ASSESSMENT PHASE ---');
    await page.click('text=Assess');
    await page.waitForTimeout(2000);
    
    // Look for metrics or scores
    const metrics = await page.locator('.metric, .score, .percentage').count();
    console.log(`Found ${metrics} metrics in Assessment`);
    
    // PLANNING PHASE
    console.log('\n--- PLANNING PHASE ---');
    await page.click('text=Plan');
    await page.waitForTimeout(2000);
    
    // Check for planning elements
    const planElements = await page.locator('.wave, .phase, .timeline').count();
    console.log(`Found ${planElements} planning elements`);
    
    // EXECUTION PHASE
    console.log('\n--- EXECUTION PHASE ---');
    await page.click('text=Execute');
    await page.waitForTimeout(2000);
    
    const statusElements = await page.locator('.status, [data-status]').count();
    console.log(`Found ${statusElements} status indicators in Execute`);
    
    console.log('\n=== INTERACTIVE JOURNEY COMPLETED ===');
    
    // Final screenshot
    await page.screenshot({ path: 'test-results/interactive-complete.png', fullPage: true });
  });
});
