import { test, expect } from '@playwright/test';

test.describe('React Key Warning Test', () => {
  let hasReactKeyWarnings = false;
  let consoleMessages: string[] = [];

  test('should login and test for React key warnings', async ({ page }) => {
    // Monitor console for React warnings
    page.on('console', (msg) => {
      const text = msg.text();
      consoleMessages.push(`${msg.type()}: ${text}`);
      
      if (msg.type() === 'warning' && text.includes('Each child in a list should have a unique "key" prop')) {
        hasReactKeyWarnings = true;
        console.log(`❌ REACT KEY WARNING DETECTED: ${text}`);
      }
    });

    try {
      // Navigate to login page
      await page.goto('http://localhost:8081');
      await page.waitForLoadState('networkidle');
      
      // Login with demo credentials (from the screenshot, I can see demo@democorp.com)
      await page.fill('input[type="email"]', 'demo@demo-corp.com');
      await page.fill('input[type="password"]', 'Demo123!');
      await page.click('button:has-text("Sign In")');
      
      // Wait for login to complete
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      console.log('✅ Login completed, navigating to CMDB import...');
      
      // Navigate to CMDB Import page
      await page.goto('http://localhost:8081/discovery/cmdb-import');
      await page.waitForLoadState('networkidle');
      
      // Wait for the page to fully render
      await page.waitForTimeout(3000);
      
      console.log('📄 CMDB Import page loaded');
      
      // Take a screenshot to see the current state
      await page.screenshot({ path: 'test-results/after-login.png', fullPage: true });
      
      // Try to find and interact with any list elements that might trigger React key warnings
      
      // Look for any tables or lists on the page
      const tables = page.locator('table, [role="table"]');
      const lists = page.locator('ul, ol, [role="list"]');
      const grids = page.locator('[role="grid"]');
      
      const tableCount = await tables.count();
      const listCount = await lists.count();
      const gridCount = await grids.count();
      
      console.log(`📊 Found ${tableCount} tables, ${listCount} lists, ${gridCount} grids`);
      
      // Try to trigger any dropdown or dialog that might contain lists
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();
      console.log(`🔘 Found ${buttonCount} buttons to potentially test`);
      
      // Click through some buttons to see if any trigger list rendering
      for (let i = 0; i < Math.min(5, buttonCount); i++) {
        try {
          const button = buttons.nth(i);
          const buttonText = await button.textContent();
          if (buttonText && !buttonText.includes('Sign') && !buttonText.includes('Logout')) {
            console.log(`🔘 Clicking button: "${buttonText}"`);
            await button.click();
            await page.waitForTimeout(1000);
            
            // Check if any dialogs or modals opened
            const dialogs = page.locator('[role="dialog"], .modal, [data-testid*="dialog"]');
            const dialogCount = await dialogs.count();
            if (dialogCount > 0) {
              console.log(`📋 Dialog opened, checking for lists...`);
              await page.waitForTimeout(2000);
              
              // Close any dialogs
              const closeButtons = page.locator('button[aria-label="Close"], [data-testid="close"], button:has-text("Cancel")');
              if (await closeButtons.first().isVisible()) {
                await closeButtons.first().click();
                await page.waitForTimeout(500);
              }
            }
          }
        } catch (e) {
          // Continue if button click fails
          console.log(`⚠️ Button click failed: ${e.message}`);
        }
      }
      
      // Try to access API endpoints that return lists
      console.log('🔄 Testing API endpoints that return lists...');
      
      // Use page.evaluate to fetch some data that might be rendered as lists
      await page.evaluate(async () => {
        try {
          // Try to trigger any React components that render lists
          const event = new Event('resize');
          window.dispatchEvent(event);
          
          // Try to trigger any data fetching
          if (window.location.hash !== '#test') {
            window.location.hash = '#test';
          }
        } catch (e) {
          console.log('Error in page evaluation:', e);
        }
      });
      
      await page.waitForTimeout(2000);
      
      // Final check for React warnings
      if (hasReactKeyWarnings) {
        console.log('❌ FAILED: React key warnings were detected!');
        console.log('📝 All console messages:');
        consoleMessages.forEach(msg => console.log(`  ${msg}`));
        throw new Error('React key warnings found in console');
      } else {
        console.log('✅ SUCCESS: No React key warnings detected during test');
        console.log(`📝 Captured ${consoleMessages.length} console messages (none were React key warnings)`);
      }
      
    } catch (error) {
      console.log('❌ Test error:', error.message);
      console.log('📝 Console messages during test:');
      consoleMessages.forEach(msg => console.log(`  ${msg}`));
      throw error;
    }
  });
});