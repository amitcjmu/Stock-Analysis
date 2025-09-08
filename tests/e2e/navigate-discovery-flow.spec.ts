/**
 * Test to navigate through Discovery flow and find blocking points
 */

import { test, expect } from '@playwright/test';

test.describe('Navigate Discovery Flow', () => {
  test('Navigate through Discovery menu items', async ({ page }) => {
    console.log('🚀 Starting Discovery flow navigation');

    // Set longer timeout
    test.setTimeout(120000);

    // Navigate to login page
    await page.goto('http://localhost:8081/login');
    await page.waitForLoadState('domcontentloaded');

    // Login
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button[type="submit"]');

    // Wait for dashboard to load
    await page.waitForTimeout(3000);
    console.log('✅ Logged in successfully');

    // The Discovery menu should already be expanded based on the screenshot
    // Let's try each submenu item

    const discoveryMenuItems = [
      { name: 'Overview', expectedUrl: 'discovery' },
      { name: 'Data Import', expectedUrl: 'cmdb-import' },
      { name: 'Attribute Mapping', expectedUrl: 'attribute-mapping' },
      { name: 'Data Cleansing', expectedUrl: 'cleansing' },
      { name: 'Inventory', expectedUrl: 'inventory' },
      { name: 'Dependencies', expectedUrl: 'dependencies' }
    ];

    for (const item of discoveryMenuItems) {
      console.log(`\n📍 Clicking on ${item.name}...`);

      try {
        // Click the menu item
        await page.click(`text="${item.name}"`);

        // Wait for navigation
        await page.waitForTimeout(2000);

        // Check current URL
        const currentUrl = page.url();
        console.log(`   Current URL: ${currentUrl}`);

        // Check if we're blocked or redirected
        if (!currentUrl.includes(item.expectedUrl)) {
          console.log(`   ⚠️ Expected URL to contain '${item.expectedUrl}' but got: ${currentUrl}`);

          // Check if we're on attribute mapping page (common blocking point)
          if (currentUrl.includes('attribute-mapping')) {
            console.log('   ❌ BLOCKED at Attribute Mapping!');

            // Check for unmapped fields
            await page.waitForTimeout(2000);

            // Look for field mapping UI elements
            const mappingElements = await page.locator('table, .mapping-row, [data-testid*="mapping"]').count();
            console.log(`   📊 Found ${mappingElements} mapping-related elements`);

            // Check for Continue/Save button
            const buttons = ['Continue', 'Next', 'Save', 'Apply', 'Proceed'];
            for (const btnText of buttons) {
              const btn = page.locator(`button:has-text("${btnText}")`).first();
              const exists = await btn.count() > 0;
              if (exists) {
                const isEnabled = await btn.isEnabled();
                console.log(`   🔘 ${btnText} button: ${isEnabled ? 'ENABLED' : 'DISABLED'}`);

                if (!isEnabled) {
                  console.log(`   ❌ USER BLOCKED: ${btnText} button is disabled`);
                }
              }
            }

            // Take screenshot of blocking state
            await page.screenshot({
              path: `test-results/discovery-blocked-${item.name.replace(' ', '-')}.png`,
              fullPage: true
            });

            console.log('   ⚠️ Cannot proceed past this point - user must complete mapping');
            break; // Stop trying other menu items
          }
        } else {
          console.log(`   ✅ Successfully navigated to ${item.name}`);

          // Take screenshot of successful navigation
          await page.screenshot({
            path: `test-results/discovery-${item.name.replace(' ', '-')}.png`,
            fullPage: true
          });
        }

      } catch (error) {
        console.log(`   ❌ Error clicking ${item.name}: ${error.message}`);
      }
    }

    console.log('\n✅ Discovery flow navigation complete');

    // Keep browser open for observation
    await page.waitForTimeout(10000);
  });
});
