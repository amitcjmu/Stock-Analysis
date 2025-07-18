import { test, expect } from '@playwright/test';

test.describe('Simple Blocking Flows Test', () => {
  let hasReactKeyWarnings = false;
  const consoleMessages: string[] = [];

  test('should test blocking flows without React key warnings', async ({ page }) => {
    // Monitor console for React warnings and errors
    page.on('console', (msg) => {
      const text = msg.text();
      consoleMessages.push(`${msg.type()}: ${text}`);
      
      if (msg.type() === 'warning' && text.includes('Each child in a list should have a unique "key" prop')) {
        hasReactKeyWarnings = true;
        console.log(`❌ REACT KEY WARNING DETECTED: ${text}`);
      } else if (msg.type() === 'error') {
        console.log(`❌ Console Error: ${text}`);
      } else if (msg.type() === 'warning') {
        console.log(`⚠️ Warning: ${text}`);
      }
    });

    try {
      // Navigate directly to CMDB Import page
      await page.goto('http://localhost:8081/discovery/cmdb-import');
      
      // Wait for either login form or the page content
      await page.waitForLoadState('networkidle');
      
      // Check if we need to login
      const loginForm = await page.locator('input[type="email"]').isVisible();
      
      if (loginForm) {
        console.log('🔐 Login required, authenticating...');
        // Login with demo account
        await page.fill('input[type="email"]', 'demo@hcltech.com');
        await page.fill('input[type="password"]', 'Demo123!');
        await page.click('button[type="submit"]');
        
        // Wait for redirect and page load
        await page.waitForLoadState('networkidle');
        
        // Navigate to CMDB Import again after login
        await page.goto('http://localhost:8081/discovery/cmdb-import');
        await page.waitForLoadState('networkidle');
      }
      
      console.log('📄 Page loaded, looking for CMDB Import content...');
      
      // Wait for the page to fully load and check for blocking flows
      await page.waitForTimeout(3000); // Give time for async operations
      
      // Look for the manage flows button or incomplete flows indicator
      const manageFlowsButton = page.locator('text=Manage Discovery Flows', 'button:has-text("Manage")', 'text=incomplete flow').first();
      const hasBlockingFlows = await manageFlowsButton.isVisible().catch(() => false);
      
      if (hasBlockingFlows) {
        console.log('🔍 Found blocking flows, clicking to open dialog...');
        await manageFlowsButton.click();
        
        // Wait for dialog to appear
        await page.waitForSelector('text=Incomplete Discovery Flows', { timeout: 10000 });
        console.log('✅ Blocking flows dialog opened');
        
        // Take a screenshot
        await page.screenshot({ path: 'test-results/blocking-flows-dialog.png', fullPage: true });
        
        // Look for flow items in the dialog
        const flowItems = page.locator('[data-testid="flow-card"], .space-y-4 > div').filter({ hasText: 'UNKNOWN' });
        const flowCount = await flowItems.count();
        console.log(`📊 Found ${flowCount} flow items in dialog`);
        
        if (flowCount > 0) {
          // Test selecting flows
          const selectAllCheckbox = page.locator('#select-all');
          if (await selectAllCheckbox.isVisible()) {
            await selectAllCheckbox.click();
            console.log('✅ Select all checkbox clicked');
            await page.waitForTimeout(1000); // Wait for UI update
          }
          
          // Check for delete buttons
          const deleteSelectedBtn = page.locator('button:has-text("Delete Selected")');
          if (await deleteSelectedBtn.isVisible()) {
            console.log('✅ Delete Selected button visible');
            // Don't actually click delete in test
          }
          
          // Test individual flow actions
          const deleteButtons = page.locator('button:has-text("Delete")');
          const deleteCount = await deleteButtons.count();
          console.log(`🗑️ Found ${deleteCount} individual delete buttons`);
        }
        
        // Close the dialog
        const closeButtons = page.locator('button[aria-label="Close"], [data-testid="close-button"]');
        if (await closeButtons.first().isVisible()) {
          await closeButtons.first().click();
          console.log('✅ Dialog closed');
        }
        
      } else {
        console.log('ℹ️ No blocking flows found or button not visible');
        
        // Take a screenshot to see what's on the page
        await page.screenshot({ path: 'test-results/cmdb-import-page.png', fullPage: true });
        
        // Try to start a new flow to create some incomplete flows for testing
        const startFlowButton = page.locator('button:has-text("Start"), button:has-text("Begin"), button:has-text("Import")').first();
        if (await startFlowButton.isVisible()) {
          console.log('🚀 Starting a new flow for testing...');
          await startFlowButton.click();
          await page.waitForTimeout(2000);
          
          // Navigate back to check for blocking flows
          await page.goto('http://localhost:8081/discovery/cmdb-import');
          await page.waitForLoadState('networkidle');
          
          const manageFlowsButtonRetry = page.locator('text=Manage Discovery Flows').first();
          if (await manageFlowsButtonRetry.isVisible()) {
            await manageFlowsButtonRetry.click();
            await page.waitForSelector('text=Incomplete Discovery Flows', { timeout: 5000 });
            console.log('✅ Successfully opened blocking flows dialog after creating flow');
          }
        }
      }
      
      // Final check for React warnings
      if (hasReactKeyWarnings) {
        console.log('❌ FAILED: React key warnings were detected!');
        throw new Error('React key warnings found in console');
      } else {
        console.log('✅ SUCCESS: No React key warnings detected');
      }
      
    } catch (error) {
      console.log('❌ Test error:', error.message);
      console.log('📝 Console messages during test:');
      consoleMessages.forEach(msg => console.log(`  ${msg}`));
      throw error;
    }
  });
});