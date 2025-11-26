import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const TEST_USER = {
  email: 'chockas@hcltech.com',
  password: 'Testing123!'
};

const BASE_URL = 'http://localhost:8081';
const SCREENSHOT_DIR = '/Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/screenshots';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

test.describe('Collection Flow End-to-End Test', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();

    // Enable console log capturing
    page.on('console', msg => {
      const type = msg.type();
      if (type === 'error' || type === 'warning') {
        console.log(`[BROWSER ${type.toUpperCase()}]:`, msg.text());
      }
    });

    // Capture page errors
    page.on('pageerror', error => {
      console.error('[PAGE ERROR]:', error.message);
    });
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('Step 1: Login to application', async () => {
    console.log('\n=== STEP 1: LOGIN ===');

    // Navigate to login page
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Take screenshot of login page
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '01-login-page.png'),
      fullPage: true
    });

    // Fill in login credentials
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);

    // Take screenshot before login
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '02-credentials-filled.png'),
      fullPage: true
    });

    // Click login button
    await page.click('button[type="submit"]');

    // Wait for navigation to dashboard
    await page.waitForURL(/\/dashboard|\/assess/, { timeout: 10000 });
    await page.waitForTimeout(3000);

    // Take screenshot of dashboard
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '03-logged-in-dashboard.png'),
      fullPage: true
    });

    console.log('✓ Login successful');
  });

  test('Step 2: Navigate to Assessment Overview', async () => {
    console.log('\n=== STEP 2: NAVIGATE TO ASSESSMENT OVERVIEW ===');

    // Click on "Assess" in navigation
    const assessNav = page.locator('text=Assess').first();
    await assessNav.click();
    await page.waitForTimeout(2000);

    // Click on "Overview"
    const overviewNav = page.locator('text=Overview').first();
    await overviewNav.click();
    await page.waitForTimeout(3000);

    // Wait for assets to load
    await page.waitForSelector('[data-testid="asset-card"], .asset-item, [class*="asset"]', {
      timeout: 10000,
      state: 'visible'
    }).catch(() => {
      console.log('No asset cards found with standard selectors, page may still be loading');
    });

    // Take screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '04-assessment-overview.png'),
      fullPage: true
    });

    console.log('✓ Navigated to Assessment Overview');
  });

  test('Step 3: Find and Start Collection Flow', async () => {
    console.log('\n=== STEP 3: START COLLECTION FLOW ===');

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Look for assets that need collection
    // Try multiple selectors to find assets
    const assetSelectors = [
      '[data-testid*="asset"]',
      '[class*="asset-card"]',
      '[class*="AssetCard"]',
      'text=/Asset.*\\d+/',
      'button:has-text("Start Collection")',
      'button:has-text("Collect Data")',
      'button:has-text("Begin Collection")'
    ];

    let foundAsset = false;
    for (const selector of assetSelectors) {
      const elements = await page.locator(selector).count();
      if (elements > 0) {
        console.log(`Found ${elements} elements with selector: ${selector}`);
        foundAsset = true;
      }
    }

    // Take screenshot showing available assets
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '05-assets-before-collection.png'),
      fullPage: true
    });

    // Try to find and click collection button
    const collectionButtonSelectors = [
      'button:has-text("Start Collection")',
      'button:has-text("Collect Data")',
      'button:has-text("Begin Collection")',
      'button[aria-label*="collection"]',
      '[data-testid="start-collection-button"]'
    ];

    let collectionStarted = false;
    for (const selector of collectionButtonSelectors) {
      const button = page.locator(selector).first();
      if (await button.isVisible().catch(() => false)) {
        console.log(`Found collection button: ${selector}`);
        await button.click();
        collectionStarted = true;
        await page.waitForTimeout(2000);
        break;
      }
    }

    if (!collectionStarted) {
      console.log('⚠ No collection button found. Looking for alternative ways to start collection...');

      // Try clicking on an asset card to see options
      const assetCard = page.locator('[class*="asset"], [data-testid*="asset"]').first();
      if (await assetCard.isVisible().catch(() => false)) {
        await assetCard.click();
        await page.waitForTimeout(2000);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '06-asset-clicked.png'),
          fullPage: true
        });
      }
    }

    // Take screenshot of collection initiation
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '07-collection-initiated.png'),
      fullPage: true
    });

    if (collectionStarted) {
      console.log('✓ Collection flow started');
    } else {
      console.log('⚠ Could not automatically start collection flow');
    }
  });

  test('Step 4: Monitor Collection Flow Progress', async () => {
    console.log('\n=== STEP 4: MONITOR COLLECTION FLOW ===');

    // Wait for flow to start processing
    await page.waitForTimeout(5000);

    // Monitor for up to 2 minutes, taking screenshots periodically
    const maxWaitTime = 120000; // 2 minutes
    const screenshotInterval = 10000; // 10 seconds
    let elapsedTime = 0;
    let screenshotCount = 0;

    while (elapsedTime < maxWaitTime) {
      await page.waitForTimeout(screenshotInterval);
      elapsedTime += screenshotInterval;
      screenshotCount++;

      // Take periodic screenshot
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `08-progress-${screenshotCount}.png`),
        fullPage: true
      });

      // Check for completion or error indicators
      const hasError = await page.locator('text=/error|failed/i').isVisible().catch(() => false);
      const hasSuccess = await page.locator('text=/complete|success/i').isVisible().catch(() => false);

      if (hasError) {
        console.log('❌ Error detected in UI');
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '09-error-state.png'),
          fullPage: true
        });
        break;
      }

      if (hasSuccess) {
        console.log('✓ Collection flow completed successfully');
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '10-success-state.png'),
          fullPage: true
        });
        break;
      }

      console.log(`⏳ Monitoring... (${elapsedTime/1000}s elapsed)`);
    }

    // Final screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '11-final-state.png'),
      fullPage: true
    });

    console.log('✓ Collection flow monitoring complete');
  });

  test('Step 5: Capture Final State and Console Errors', async () => {
    console.log('\n=== STEP 5: FINAL STATE CAPTURE ===');

    // Get final page state
    const url = page.url();
    const title = await page.title();

    console.log(`Final URL: ${url}`);
    console.log(`Final Title: ${title}`);

    // Check for any visible error messages
    const errorElements = await page.locator('[class*="error"], [role="alert"], .alert-error').all();
    if (errorElements.length > 0) {
      console.log(`⚠ Found ${errorElements.length} error elements on page`);
      for (let i = 0; i < errorElements.length; i++) {
        const errorText = await errorElements[i].textContent();
        console.log(`Error ${i + 1}: ${errorText}`);
      }
    }

    // Take final comprehensive screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '12-test-complete.png'),
      fullPage: true
    });

    console.log('✓ Final state captured');
    console.log(`\nScreenshots saved to: ${SCREENSHOT_DIR}`);
  });
});
