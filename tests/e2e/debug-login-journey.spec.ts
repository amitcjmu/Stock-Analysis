/**
 * Debug test to see the login and user journey in the browser
 */

import { test, expect } from '@playwright/test';

test.describe('Debug User Journey', () => {
  test('Login and check for blocking flows', async ({ page }) => {
    console.log('🚀 Starting debug journey test');

    // Set longer timeout for debugging
    test.setTimeout(120000);

    // Navigate to login page
    console.log('📍 Navigating to login page...');
    await page.goto('http://localhost:8081/login');

    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    console.log('✅ Login page loaded');

    // Take screenshot
    await page.screenshot({ path: 'test-results/debug-1-login-page.png' });

    // Fill login form
    console.log('📝 Filling login form...');
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');

    // Check if inputs are visible
    const emailVisible = await emailInput.isVisible({ timeout: 5000 }).catch(() => false);
    const passwordVisible = await passwordInput.isVisible({ timeout: 5000 }).catch(() => false);

    console.log(`Email input visible: ${emailVisible}`);
    console.log(`Password input visible: ${passwordVisible}`);

    if (emailVisible && passwordVisible) {
      await emailInput.fill('demo@demo-corp.com');
      await passwordInput.fill('Demo123!');

      // Take screenshot before clicking login
      await page.screenshot({ path: 'test-results/debug-2-filled-form.png' });

      // Click login button
      console.log('🔐 Clicking login button...');
      const loginButton = page.locator('button[type="submit"]');
      await loginButton.click();

      // Wait for navigation
      console.log('⏳ Waiting for login to complete...');
      await page.waitForTimeout(5000); // Give it time to process

      // Take screenshot after login
      await page.screenshot({ path: 'test-results/debug-3-after-login.png' });

      // Check current URL
      const currentUrl = page.url();
      console.log(`📍 Current URL after login: ${currentUrl}`);

      // Check for blocking flow banner
      console.log('🔍 Checking for blocking flows...');
      const possibleSelectors = [
        '.blocking-flow-notification',
        '[data-testid="blocking-flow"]',
        '.alert-warning',
        '.flow-resume-banner',
        'text=complete',
        'text=Continue',
        'text=Resume'
      ];

      for (const selector of possibleSelectors) {
        const element = page.locator(selector);
        const isVisible = await element.isVisible({ timeout: 2000 }).catch(() => false);
        if (isVisible) {
          console.log(`✅ Found blocking element with selector: ${selector}`);
          const text = await element.textContent().catch(() => 'Could not get text');
          console.log(`   Text content: ${text}`);
        }
      }

      // Take final screenshot
      await page.screenshot({ path: 'test-results/debug-4-final-state.png' });

      // Check if we can navigate to discovery
      console.log('🚀 Attempting to navigate to discovery...');
      const discoveryLink = page.locator('text=Discovery');
      const discoveryVisible = await discoveryLink.isVisible({ timeout: 3000 }).catch(() => false);

      if (discoveryVisible) {
        await discoveryLink.click();
        await page.waitForTimeout(3000);

        const finalUrl = page.url();
        console.log(`📍 Final URL: ${finalUrl}`);

        await page.screenshot({ path: 'test-results/debug-5-discovery-page.png' });
      }

    } else {
      console.error('❌ Login inputs not found!');
      const pageContent = await page.content();
      console.log('Page content preview:', pageContent.substring(0, 500));
    }

    console.log('✅ Debug journey complete');

    // Keep browser open for 10 seconds so you can see
    await page.waitForTimeout(10000);
  });
});
