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

test.describe('Collection Flow E2E Test - Fixed', () => {
  let page: Page;
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext();
    page = await context.newPage();

    // Capture console logs
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error') {
        console.log(`[BROWSER ERROR]: ${text}`);
        consoleErrors.push(text);
      } else if (type === 'warning') {
        console.log(`[BROWSER WARNING]: ${text}`);
      }
    });

    // Capture page errors
    page.on('pageerror', error => {
      console.error('[PAGE ERROR]:', error.message);
      pageErrors.push(error.message);
    });

    // Capture failed requests
    page.on('requestfailed', request => {
      console.error('[REQUEST FAILED]:', request.url(), request.failure()?.errorText);
    });
  });

  test.afterAll(async () => {
    console.log('\n=== TEST SUMMARY ===');
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`Page Errors: ${pageErrors.length}`);
    if (consoleErrors.length > 0) {
      console.log('\nConsole Errors:');
      consoleErrors.forEach((err, i) => console.log(`${i + 1}. ${err}`));
    }
    if (pageErrors.length > 0) {
      console.log('\nPage Errors:');
      pageErrors.forEach((err, i) => console.log(`${i + 1}. ${err}`));
    }
    await page.close();
  });

  test('Complete Collection Flow Journey', async () => {
    // STEP 1: Login
    console.log('\n=== STEP 1: LOGIN ===');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'fixed-01-login-page.png'),
      fullPage: true
    });

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Wait for dashboard to load (it stays at root URL)
    await page.waitForSelector('text=AI Force Assess', { timeout: 15000 });
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'fixed-02-dashboard.png'),
      fullPage: true
    });

    console.log('✓ Login successful - Dashboard loaded');

    // STEP 2: Navigate to Assess section
    console.log('\n=== STEP 2: NAVIGATE TO ASSESS SECTION ===');

    // Click on "Assess" in the sidebar
    await page.click('text=Assess');
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'fixed-03-assess-menu.png'),
      fullPage: true
    });

    // Click on "Overview" submenu
    const overviewLink = page.locator('a:has-text("Overview")').first();
    await overviewLink.click();
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'fixed-04-assessment-overview.png'),
      fullPage: true
    });

    console.log('✓ Navigated to Assessment Overview');

    // STEP 3: Find assets and look for Collection option
    console.log('\n=== STEP 3: EXAMINE ASSETS ===');

    // Wait for content to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Take screenshot of current page
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'fixed-05-assets-page.png'),
      fullPage: true
    });

    // Look for assets - they might be in a table or card layout
    const pageContent = await page.content();
    console.log('Page URL:', page.url());

    // Try to find asset elements
    const assetElements = await page.locator('[class*="asset"], [data-testid*="asset"], tr, .ag-row').count();
    console.log(`Found ${assetElements} potential asset elements`);

    // Look for buttons or links related to collection
    const collectionButtons = await page.locator('button:has-text("Collect"), button:has-text("Collection"), a:has-text("Collection")').count();
    console.log(`Found ${collectionButtons} collection-related buttons`);

    // STEP 4: Navigate to Collection section directly
    console.log('\n=== STEP 4: NAVIGATE TO COLLECTION SECTION ===');

    // Click on "Collection" in the sidebar
    await page.click('text=Collection');
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'fixed-06-collection-menu.png'),
      fullPage: true
    });

    // Look for Overview or similar submenu
    const collectionOverviewExists = await page.locator('a:has-text("Overview")').count();
    if (collectionOverviewExists > 0) {
      await page.locator('a:has-text("Overview")').first().click();
      await page.waitForTimeout(3000);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'fixed-07-collection-page.png'),
      fullPage: true
    });

    console.log('✓ On Collection section');
    console.log('Current URL:', page.url());

    // STEP 5: Look for ways to start collection flow
    console.log('\n=== STEP 5: FIND START COLLECTION OPTION ===');

    // Try various button text patterns
    const buttonPatterns = [
      'Start Collection',
      'New Collection',
      'Create Collection',
      'Begin Collection',
      'Start Flow',
      'New Flow',
      'Add Collection'
    ];

    let flowStarted = false;
    for (const pattern of buttonPatterns) {
      const button = page.locator(`button:has-text("${pattern}")`).first();
      if (await button.isVisible().catch(() => false)) {
        console.log(`Found button: "${pattern}"`);
        await button.click();
        flowStarted = true;
        await page.waitForTimeout(3000);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'fixed-08-flow-started.png'),
          fullPage: true
        });
        break;
      }
    }

    if (!flowStarted) {
      console.log('⚠ No collection start button found. Checking for existing flows...');

      // Look for existing flows or assets in the collection view
      const flowRows = await page.locator('tr, [class*="flow"], [class*="row"]').count();
      console.log(`Found ${flowRows} potential flow/asset rows`);

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, 'fixed-08-no-start-button.png'),
        fullPage: true
      });

      // Try clicking on the first row to see if it opens a collection flow
      const firstRow = page.locator('tr, [class*="row"]').first();
      if (await firstRow.isVisible().catch(() => false)) {
        await firstRow.click();
        await page.waitForTimeout(3000);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'fixed-09-row-clicked.png'),
          fullPage: true
        });
      }
    }

    // STEP 6: Monitor for collection flow activity
    console.log('\n=== STEP 6: MONITOR FOR COLLECTION FLOW ===');

    // Wait and check for progress indicators
    const maxWaitTime = 60000; // 1 minute
    const checkInterval = 5000; // 5 seconds
    let elapsedTime = 0;
    let screenshotCount = 0;

    while (elapsedTime < maxWaitTime) {
      await page.waitForTimeout(checkInterval);
      elapsedTime += checkInterval;
      screenshotCount++;

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `fixed-10-monitor-${screenshotCount}.png`),
        fullPage: true
      });

      // Check for status indicators
      const hasRunning = await page.locator('text=/running|processing|in progress/i').isVisible().catch(() => false);
      const hasError = await page.locator('text=/error|failed/i').isVisible().catch(() => false);
      const hasComplete = await page.locator('text=/complete|success|done/i').isVisible().catch(() => false);

      if (hasRunning) {
        console.log(`⏳ Flow is running (${elapsedTime/1000}s)`);
      }

      if (hasError) {
        console.log('❌ Error detected in UI');
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'fixed-11-error-state.png'),
          fullPage: true
        });
        break;
      }

      if (hasComplete) {
        console.log('✓ Flow completed successfully');
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'fixed-12-success-state.png'),
          fullPage: true
        });
        break;
      }

      // If nothing is happening, break early
      if (elapsedTime >= 30000 && !hasRunning) {
        console.log('⚠ No activity detected after 30s');
        break;
      }
    }

    // Final screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'fixed-13-final-state.png'),
      fullPage: true
    });

    console.log('\n✓ Collection Flow Test Complete');
    console.log(`Screenshots saved to: ${SCREENSHOT_DIR}`);
  });
});
