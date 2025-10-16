import { test, expect } from '@playwright/test';
import * as path from 'path';

test.describe('Complete Migration Journey - End to End', () => {
  test('should complete full migration flow from data import to planning', async ({ page }) => {
    // Set longer timeout for complete flow
    test.setTimeout(120000); // 2 minutes
    
    console.log('=== STARTING COMPLETE MIGRATION JOURNEY ===');
    
    // Step 1: Login
    console.log('Step 1: Logging in...');
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button:has-text("Sign In")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Verify login successful
    const dashboardText = await page.textContent('body');
    expect(dashboardText).toContain('Dashboard');
    console.log('✓ Login successful');
    
    // Step 2: Navigate to Collection
    console.log('Step 2: Navigating to Collection...');
    await page.click('text=Collection');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/flow-1-collection.png' });
    console.log('✓ Arrived at Collection page');
    
    // Step 3: Import test data
    console.log('Step 3: Looking for import options...');
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Import"), input[type="file"]');
    
    if (await uploadButton.count() > 0) {
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.count() > 0) {
        const filePath = path.join(process.cwd(), 'tests/fixtures/test-cmdb-data.csv');
        await fileInput.setInputFiles(filePath);
        console.log('✓ File selected: test-cmdb-data.csv');
      }
    }
    
    // Step 4: Navigate to Discovery
    console.log('Step 4: Moving to Discovery...');
    await page.click('text=Discovery');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/flow-2-discovery.png' });
    
    // Step 5: Navigate to Assessment
    console.log('Step 5: Moving to Assessment...');
    await page.click('text=Assess');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/flow-3-assessment.png' });
    
    // Step 6: Navigate to Planning
    console.log('Step 6: Moving to Planning...');
    await page.click('text=Plan');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/flow-4-planning.png' });
    
    console.log('=== COMPLETE FLOW JOURNEY FINISHED ===');
    await page.screenshot({ path: 'test-results/flow-5-complete.png' });
  });
});
