/**
 * Diagnostic Test - Login Flow
 * This test helps identify the actual selectors present after login
 */

import { test, expect } from '@playwright/test';

test('diagnostic: inspect login flow', async ({ page }) => {
  console.log('🔍 Starting login diagnostic...');

  // Navigate to login
  await page.goto('http://localhost:8081/login', { waitUntil: 'load' });
  await page.waitForTimeout(1000);

  console.log('📍 On login page');

  // Fill login form
  await page.fill('input[type="email"]', 'demo@demo-corp.com');
  await page.fill('input[type="password"]', 'Demo123!');

  console.log('✅ Filled credentials');

  // Click submit
  await page.click('button[type="submit"]');

  console.log('🔄 Submitted login');

  // Wait a bit for any navigation
  await page.waitForTimeout(3000);

  // Check current URL
  const currentUrl = page.url();
  console.log(`📍 Current URL: ${currentUrl}`);

  // Take screenshot
  await page.screenshot({ path: 'test-results/after-login.png', fullPage: true });
  console.log('📸 Screenshot saved to test-results/after-login.png');

  // Get page HTML to inspect
  const pageContent = await page.content();
  console.log(`📄 Page length: ${pageContent.length} characters`);

  // Try to find various elements
  const selectors = [
    'img',
    'button',
    'nav',
    '[data-testid]',
    '[class*="user"]',
    '[class*="profile"]',
    '[aria-label]',
    'text=Demo',
    'text=User',
    'text=Democorp',
  ];

  console.log('\n🔎 Checking for elements:');
  for (const selector of selectors) {
    try {
      const elements = await page.$$(selector);
      if (elements.length > 0) {
        console.log(`✅ Found ${elements.length} element(s) matching: ${selector}`);

        // Get details of first element
        const firstElement = elements[0];
        const tagName = await firstElement.evaluate(el => el.tagName);
        const className = await firstElement.evaluate(el => el.className);
        const id = await firstElement.evaluate(el => el.id);
        const testId = await firstElement.evaluate(el => el.getAttribute('data-testid'));

        console.log(`   Tag: ${tagName}, Class: ${className}, ID: ${id}, TestID: ${testId}`);
      } else {
        console.log(`❌ No elements found for: ${selector}`);
      }
    } catch (e) {
      console.log(`⚠️  Error checking ${selector}: ${e.message}`);
    }
  }

  // Get all data-testid attributes
  const allTestIds = await page.evaluate(() => {
    const elements = document.querySelectorAll('[data-testid]');
    return Array.from(elements).map(el => el.getAttribute('data-testid'));
  });

  if (allTestIds.length > 0) {
    console.log('\n📋 All data-testid attributes found:');
    allTestIds.forEach(id => console.log(`   - ${id}`));
  } else {
    console.log('\n⚠️  No data-testid attributes found on page');
  }

  // Check if still on login page
  if (currentUrl.includes('/login')) {
    console.log('\n❌ ISSUE: Still on login page after submit!');
    console.log('   This means login failed or redirect did not happen');

    // Check for error messages
    const errorText = await page.textContent('body');
    if (errorText.toLowerCase().includes('error') || errorText.toLowerCase().includes('invalid')) {
      console.log('   Found error text on page');
    }
  } else {
    console.log('\n✅ Successfully navigated away from login page');
  }

  // Keep test passing for diagnostic purposes
  expect(true).toBe(true);
});
