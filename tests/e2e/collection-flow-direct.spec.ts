import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const TEST_USER = {
  email: 'chockas@hcltech.com',
  password: 'Testing123!'
};

const BASE_URL = 'http://localhost:8081';
const SCREENSHOT_DIR = '/Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

test.describe('Collection Flow Direct Navigation', () => {
  let page: Page;
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const apiErrors: string[] = [];

  test.setTimeout(240000); // 4 minutes

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext();
    page = await context.newPage();

    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error') {
        console.log(`[BROWSER ERROR]: ${text}`);
        consoleErrors.push(text);
      }
    });

    page.on('pageerror', error => {
      console.error('[PAGE ERROR]:', error.message);
      pageErrors.push(error.message);
    });

    page.on('response', async response => {
      if (response.status() >= 400) {
        const url = response.url();
        console.error(`[HTTP ${response.status()}]: ${url}`);
        apiErrors.push(`${response.status()} ${url}`);
      }
    });
  });

  test.afterAll(async () => {
    console.log('\n=== TEST SUMMARY ===');
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`Page Errors: ${pageErrors.length}`);
    console.log(`API Errors: ${apiErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\nConsole Errors:');
      consoleErrors.forEach((err, i) => console.log(`${i + 1}. ${err}`));
    }
    if (pageErrors.length > 0) {
      console.log('\nPage Errors:');
      pageErrors.forEach((err, i) => console.log(`${i + 1}. ${err}`));
    }
    if (apiErrors.length > 0) {
      console.log('\nAPI Errors:');
      apiErrors.forEach((err, i) => console.log(`${i + 1}. ${err}`));
    }

    await page.close();
  });

  test('Navigate to Collection and Test Flow', async () => {
    // STEP 1: Login
    console.log('\n=== STEP 1: LOGIN ===');
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'direct-01-login.png'),
      fullPage: true
    });

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');

    await page.waitForSelector('text=AI Force Assess', { timeout: 15000 });
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'direct-02-logged-in.png'),
      fullPage: true
    });

    console.log('✓ Login successful');

    // STEP 2: Navigate directly to Collection via sidebar
    console.log('\n=== STEP 2: NAVIGATE TO COLLECTION ===');

    // Find and click the Collection menu item in sidebar
    const collectionMenuItem = page.locator('nav a, nav button, aside a, aside button').filter({ hasText: 'Collection' }).first();
    await collectionMenuItem.click();
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'direct-03-collection-clicked.png'),
      fullPage: true
    });

    console.log('✓ Clicked Collection menu');
    console.log('Current URL:', page.url());

    // STEP 3: Look for collection flows or assets
    console.log('\n=== STEP 3: EXAMINE COLLECTION PAGE ===');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Get page content to analyze
    const pageText = await page.textContent('body');
    console.log('Page contains "asset":', pageText?.toLowerCase().includes('asset'));
    console.log('Page contains "flow":', pageText?.toLowerCase().includes('flow'));
    console.log('Page contains "collection":', pageText?.toLowerCase().includes('collection'));

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'direct-04-collection-page.png'),
      fullPage: true
    });

    // Look for any grid, table, or list of items
    const hasTable = await page.locator('table').count();
    const hasGrid = await page.locator('[class*="grid"]').count();
    const hasRows = await page.locator('[class*="row"]').count();

    console.log(`Found: ${hasTable} tables, ${hasGrid} grids, ${hasRows} rows`);

    // STEP 4: Try to interact with collection items
    console.log('\n=== STEP 4: INTERACT WITH COLLECTION ITEMS ===');

    // Try clicking on any visible button or link
    const actionButtons = await page.locator('button, a[href*="collection"]').all();
    console.log(`Found ${actionButtons.length} potential action buttons/links`);

    // Take screenshot showing all available buttons
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'direct-05-looking-for-actions.png'),
      fullPage: true
    });

    // Try clicking first actionable item if it exists
    if (actionButtons.length > 0) {
      for (let i = 0; i < Math.min(actionButtons.length, 5); i++) {
        const button = actionButtons[i];
        const buttonText = await button.textContent().catch(() => '');
        console.log(`Button ${i + 1}: "${buttonText}"`);

        if (buttonText && (
          buttonText.toLowerCase().includes('start') ||
          buttonText.toLowerCase().includes('create') ||
          buttonText.toLowerCase().includes('new') ||
          buttonText.toLowerCase().includes('begin')
        )) {
          console.log(`Clicking: "${buttonText}"`);
          await button.click();
          await page.waitForTimeout(3000);

          await page.screenshot({
            path: path.join(SCREENSHOT_DIR, 'direct-06-clicked-action.png'),
            fullPage: true
          });
          break;
        }
      }
    }

    // STEP 5: Check if there's a submenu we need to click
    console.log('\n=== STEP 5: CHECK FOR SUBMENUS ===');

    // Look for Overview, Flows, or similar submenu items
    const submenuItems = ['Overview', 'Flows', 'All', 'List', 'Active'];
    for (const itemText of submenuItems) {
      const submenu = page.locator(`a:has-text("${itemText}"), button:has-text("${itemText}")`).first();
      if (await submenu.isVisible().catch(() => false)) {
        console.log(`Found submenu: ${itemText}`);
        await submenu.click();
        await page.waitForTimeout(3000);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, `direct-07-submenu-${itemText.toLowerCase()}.png`),
          fullPage: true
        });
        break;
      }
    }

    // STEP 6: Monitor for any flow activity
    console.log('\n=== STEP 6: MONITOR FOR FLOW ACTIVITY ===');

    const maxMonitorTime = 60000; // 1 minute
    const checkInterval = 10000; // 10 seconds
    let elapsed = 0;
    let monitorCount = 0;

    while (elapsed < maxMonitorTime) {
      await page.waitForTimeout(checkInterval);
      elapsed += checkInterval;
      monitorCount++;

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `direct-08-monitor-${monitorCount}.png`),
        fullPage: true
      });

      // Check for flow indicators
      const indicators = {
        running: await page.locator('text=/running|processing|in progress/i').count(),
        error: await page.locator('text=/error|failed/i').count(),
        complete: await page.locator('text=/complete|success|done/i').count(),
        phase: await page.locator('text=/gap analysis|data awareness|questionnaire/i').count()
      };

      console.log(`Monitor ${monitorCount}: running=${indicators.running}, error=${indicators.error}, complete=${indicators.complete}, phase=${indicators.phase}`);

      if (indicators.error > 0) {
        console.log('❌ Error detected');
        const errorText = await page.locator('text=/error|failed/i').first().textContent();
        console.log('Error:', errorText);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'direct-09-error.png'),
          fullPage: true
        });
        break;
      }

      if (indicators.complete > 0) {
        console.log('✓ Completion detected');
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'direct-10-complete.png'),
          fullPage: true
        });
        break;
      }

      if (indicators.phase > 0) {
        console.log('⏳ Flow phase detected');
      }

      // If no activity after 30s, stop monitoring
      if (elapsed >= 30000 && indicators.running === 0 && indicators.phase === 0) {
        console.log('⚠ No activity detected');
        break;
      }
    }

    // Final screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'direct-11-final.png'),
      fullPage: true
    });

    console.log('\n=== FINAL STATE ===');
    console.log('URL:', page.url());
    console.log('Title:', await page.title());
    console.log('\n✓ Test Complete');
  });
});
