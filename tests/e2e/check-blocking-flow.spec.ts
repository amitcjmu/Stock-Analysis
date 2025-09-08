/**
 * Test to check for blocking flows and follow the user journey
 */

import { test, expect } from '@playwright/test';

test.describe('Check Blocking Flow Journey', () => {
  test('Login and follow blocking flow if present', async ({ page }) => {
    console.log('🚀 Starting blocking flow check');

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

    // Take screenshot of dashboard
    await page.screenshot({ path: 'test-results/blocking-1-dashboard.png', fullPage: true });

    // Check current URL
    console.log(`📍 Current URL: ${page.url()}`);

    // Look for any indication of blocking flow or incomplete tasks
    const blockingIndicators = [
      'text="Resume"',
      'text="Continue"',
      'text="Complete"',
      'text="Pending"',
      'text="Required"',
      'text="blocking"',
      'text="attribute"',
      'text="mapping"'
    ];

    let foundBlockingFlow = false;
    let blockingText = '';

    for (const selector of blockingIndicators) {
      try {
        const element = page.locator(selector).first();
        const isVisible = await element.isVisible({ timeout: 1000 }).catch(() => false);

        if (isVisible) {
          foundBlockingFlow = true;
          const text = await element.textContent().catch(() => '');
          console.log(`⚠️ Found blocking indicator: "${text}" with selector: ${selector}`);
          blockingText = text;

          // Try to click it if it's a button
          const isButton = await element.evaluate(el =>
            el.tagName === 'BUTTON' || el.tagName === 'A' || el.closest('button') !== null
          ).catch(() => false);

          if (isButton) {
            console.log(`🔘 Clicking blocking flow button: "${text}"`);
            await element.click();
            await page.waitForTimeout(3000);

            const newUrl = page.url();
            console.log(`📍 Navigated to: ${newUrl}`);

            await page.screenshot({
              path: 'test-results/blocking-2-after-click.png',
              fullPage: true
            });

            break;
          }
        }
      } catch (e) {
        // Continue checking other selectors
      }
    }

    if (!foundBlockingFlow) {
      console.log('✅ No blocking flow detected');

      // Try to navigate to Discovery directly
      console.log('📍 Navigating to Discovery...');
      await page.click('text=Discovery');
      await page.waitForTimeout(3000);

      await page.screenshot({
        path: 'test-results/blocking-3-discovery.png',
        fullPage: true
      });

      // Check if we're redirected to attribute mapping
      const currentUrl = page.url();
      if (currentUrl.includes('attribute-mapping')) {
        console.log('⚠️ Redirected to attribute mapping - blocking flow active!');

        // Check for unmapped fields
        const unmappedFields = await page.locator('.unmapped-field, [data-status="pending"], text="Not Mapped"').count();
        console.log(`📊 Unmapped fields found: ${unmappedFields}`);

        // Check if Continue/Next button is enabled
        const continueBtn = page.locator('button:has-text("Continue"), button:has-text("Next"), button:has-text("Save")').first();
        const isEnabled = await continueBtn.isEnabled().catch(() => false);
        console.log(`🔘 Continue button enabled: ${isEnabled}`);

        if (!isEnabled) {
          console.log('❌ USER BLOCKED: Cannot proceed without completing attribute mapping');
        }
      }
    }

    // Final state screenshot
    await page.screenshot({
      path: 'test-results/blocking-4-final.png',
      fullPage: true
    });

    console.log('✅ Blocking flow check complete');

    // Keep browser open for observation
    await page.waitForTimeout(10000);
  });
});
