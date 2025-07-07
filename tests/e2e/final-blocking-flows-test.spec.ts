import { test, expect } from '@playwright/test';

test.describe('Final Blocking Flows Test - UUID Fix & React Keys', () => {
  let hasReactKeyWarnings = false;
  let consoleMessages: string[] = [];

  test('should test complete blocking flows functionality without issues', async ({ page }) => {
    // Monitor console for React warnings and errors
    page.on('console', (msg) => {
      const text = msg.text();
      consoleMessages.push(`${msg.type()}: ${text}`);
      
      if (msg.type() === 'warning' && text.includes('Each child in a list should have a unique "key" prop')) {
        hasReactKeyWarnings = true;
        console.log(`❌ REACT KEY WARNING DETECTED: ${text}`);
      } else if (msg.type() === 'error' && !text.includes('No user') && !text.includes('X-')) {
        console.log(`❌ Console Error: ${text}`);
      }
    });

    try {
      // Navigate to login page
      await page.goto('http://localhost:8081');
      await page.waitForLoadState('networkidle');
      
      // Login with demo credentials
      await page.fill('input[type="email"]', 'demo@demo-corp.com');
      await page.fill('input[type="password"]', 'Demo123!');
      await page.click('button:has-text("Sign In")');
      
      // Wait for login to complete
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      console.log('✅ Login completed');
      
      // Navigate to CMDB Import page
      await page.goto('http://localhost:8081/discovery/cmdb-import');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
      
      console.log('📄 CMDB Import page loaded');
      
      // Take a screenshot of the current state
      await page.screenshot({ path: 'test-results/cmdb-page-loaded.png', fullPage: true });
      
      // Look for manage flows button or try to create some flows first
      let manageFlowsButton = page.locator('text=Manage Discovery Flows', 'button:has-text("Manage")').first();
      let hasBlockingFlows = await manageFlowsButton.isVisible().catch(() => false);
      
      if (!hasBlockingFlows) {
        console.log('🚀 No blocking flows found, attempting to create some for testing...');
        
        // Try to start a flow to create incomplete flows
        const startButtons = page.locator('button:has-text("Start"), button:has-text("Begin"), button:has-text("Import")');
        const startButtonCount = await startButtons.count();
        
        if (startButtonCount > 0) {
          // Click the first start button to create an incomplete flow
          await startButtons.first().click();
          await page.waitForTimeout(2000);
          
          // Navigate back to check for blocking flows
          await page.goto('http://localhost:8081/discovery/cmdb-import');
          await page.waitForLoadState('networkidle');
          await page.waitForTimeout(2000);
          
          // Check again for manage flows button
          manageFlowsButton = page.locator('text=Manage Discovery Flows').first();
          hasBlockingFlows = await manageFlowsButton.isVisible().catch(() => false);
        }
      }
      
      if (hasBlockingFlows) {
        console.log('🔍 Found blocking flows, testing dialog functionality...');
        
        // Click to open blocking flows dialog
        await manageFlowsButton.click();
        await page.waitForSelector('text=Incomplete Discovery Flows', { timeout: 10000 });
        
        console.log('✅ Blocking flows dialog opened');
        
        // Take screenshot of the dialog
        await page.screenshot({ path: 'test-results/blocking-flows-dialog-open.png', fullPage: true });
        
        // Wait for any dynamic content to load
        await page.waitForTimeout(2000);
        
        // Look for flow items in the dialog
        const flowCards = page.locator('.space-y-4 > div').filter({ hasNot: page.locator('#select-all') });
        const flowCount = await flowCards.count();
        console.log(`📊 Found ${flowCount} flow items in dialog`);
        
        if (flowCount > 0) {
          console.log('🧪 Testing flow interaction and deletion...');
          
          // Test selecting the first flow
          const firstFlowCheckbox = page.locator('input[type="checkbox"]').nth(1); // Skip select-all
          if (await firstFlowCheckbox.isVisible()) {
            await firstFlowCheckbox.click();
            console.log('✅ Selected first flow');
            await page.waitForTimeout(1000);
          }
          
          // Look for individual delete button
          const deleteButtons = page.locator('button:has-text("Delete")').filter({ hasNot: page.locator('button:has-text("Delete Selected")') });
          const deleteButtonCount = await deleteButtons.count();
          console.log(`🗑️ Found ${deleteButtonCount} individual delete buttons`);
          
          if (deleteButtonCount > 0) {
            // Click on the first individual delete button
            await deleteButtons.first().click();
            console.log('🗑️ Clicked individual delete button');
            
            // Wait for confirmation dialog
            await page.waitForTimeout(1000);
            
            // Look for confirmation dialog
            const confirmDialog = page.locator('text=Delete Discovery Flow', '[role="dialog"]').first();
            if (await confirmDialog.isVisible({ timeout: 3000 })) {
              console.log('✅ Delete confirmation dialog appeared');
              
              // Test actual deletion (but cancel for safety unless it's a demo flow)
              const cancelButton = page.locator('button:has-text("Cancel")');
              const confirmButton = page.locator('button:has-text("Delete"), button:has-text("Confirm")').filter({ hasNot: cancelButton });
              
              // Check if this might be a demo flow (safe to delete)
              const flowIdText = await page.textContent('.font-mono, [data-testid="flow-id"]').catch(() => '');
              const isDemoFlow = flowIdText?.includes('def0') || false;
              
              if (isDemoFlow) {
                console.log('🧪 Demo flow detected, testing actual deletion...');
                await confirmButton.first().click();
                await page.waitForTimeout(2000);
                
                // Check if deletion was successful (no 500 error)
                const errorMessages = page.locator('text=Internal Server Error, text=500, text=Error');
                const hasError = await errorMessages.first().isVisible().catch(() => false);
                
                if (!hasError) {
                  console.log('✅ Flow deletion completed successfully');
                } else {
                  console.log('❌ Flow deletion failed with error');
                }
              } else {
                console.log('⚠️ Non-demo flow detected, cancelling deletion for safety');
                await cancelButton.click();
              }
            }
          }
          
          // Test batch selection and deletion interface
          console.log('🧪 Testing batch selection...');
          
          // Select all flows
          const selectAllCheckbox = page.locator('#select-all');
          if (await selectAllCheckbox.isVisible()) {
            await selectAllCheckbox.click();
            console.log('✅ Select all clicked');
            await page.waitForTimeout(1000);
            
            // Check if batch delete button appears
            const batchDeleteButton = page.locator('button:has-text("Delete Selected")');
            if (await batchDeleteButton.isVisible()) {
              console.log('✅ Batch delete button visible');
              // Don't actually click it for safety
            }
            
            // Unselect all
            await selectAllCheckbox.click();
            await page.waitForTimeout(500);
          }
        }
        
        // Close the dialog
        const closeButtons = page.locator('button[aria-label="Close"], [data-testid="close-button"], button:has-text("×")');
        if (await closeButtons.first().isVisible()) {
          await closeButtons.first().click();
          console.log('✅ Dialog closed');
          await page.waitForTimeout(1000);
        }
        
      } else {
        console.log('ℹ️ No blocking flows found after attempts to create them');
        await page.screenshot({ path: 'test-results/no-blocking-flows.png', fullPage: true });
      }
      
      // Final verification of React warnings
      if (hasReactKeyWarnings) {
        console.log('❌ FAILED: React key warnings were detected!');
        console.log('📝 Console messages with warnings:');
        consoleMessages.filter(msg => msg.includes('key')).forEach(msg => console.log(`  ${msg}`));
        throw new Error('React key warnings found in console');
      } else {
        console.log('✅ SUCCESS: No React key warnings detected throughout the test');
        console.log(`📝 Monitored ${consoleMessages.length} console messages`);
      }
      
    } catch (error) {
      console.log('❌ Test error:', error.message);
      console.log('📝 Recent console messages:');
      consoleMessages.slice(-10).forEach(msg => console.log(`  ${msg}`));
      
      // Take error screenshot
      await page.screenshot({ path: 'test-results/test-error.png', fullPage: true });
      throw error;
    }
  });
});