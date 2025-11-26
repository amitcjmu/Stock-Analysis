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

test.describe('Collection Flow V2 - Navigate via Cards', () => {
  let page: Page;
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

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

  test('Complete Collection Flow via Card Navigation', async () => {
    // STEP 1: Login
    console.log('\n=== STEP 1: LOGIN ===');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'v2-01-login-page.png'),
      fullPage: true
    });

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');

    await page.waitForSelector('text=AI Force Assess', { timeout: 15000 });
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'v2-02-dashboard.png'),
      fullPage: true
    });

    console.log('✓ Login successful');

    // STEP 2: Click on the "Assess" card
    console.log('\n=== STEP 2: CLICK ASSESS CARD ===');

    const assessCard = page.locator('text=Assess').filter({ has: page.locator('text=Understand Tech Debt') });
    if (await assessCard.isVisible().catch(() => false)) {
      await assessCard.click();
      await page.waitForTimeout(3000);
    } else {
      // Try clicking the card container
      console.log('Trying alternative selector for Assess card...');
      const cardContainer = page.locator('[class*="card"]').filter({ hasText: 'Assess' }).first();
      await cardContainer.click();
      await page.waitForTimeout(3000);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'v2-03-assess-page.png'),
      fullPage: true
    });

    console.log('✓ Clicked Assess card');
    console.log('Current URL:', page.url());

    // STEP 3: Look for assets and collection options
    console.log('\n=== STEP 3: EXAMINE ASSETS ===');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'v2-04-assets-view.png'),
      fullPage: true
    });

    // Check if we're on an assets page
    const hasAssets = await page.locator('table, [class*="grid"], [class*="asset"]').isVisible().catch(() => false);
    console.log('Assets visible:', hasAssets);

    // STEP 4: Go back and try Collection card
    console.log('\n=== STEP 4: NAVIGATE TO COLLECTION ===');

    // Click Dashboard to go back
    await page.click('text=Dashboard');
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'v2-05-back-to-dashboard.png'),
      fullPage: true
    });

    // Click on the "Collection" sidebar item
    await page.click('text=Collection');
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'v2-06-collection-section.png'),
      fullPage: true
    });

    console.log('✓ On Collection section');
    console.log('Current URL:', page.url());

    // STEP 5: Try to start a collection flow
    console.log('\n=== STEP 5: START COLLECTION FLOW ===');

    // Look for any clickable elements (buttons, cards, rows)
    const startButtons = await page.locator('button:has-text("Start"), button:has-text("New"), button:has-text("Create"), button:has-text("Begin")').count();
    console.log(`Found ${startButtons} potential start buttons`);

    if (startButtons > 0) {
      const firstButton = page.locator('button:has-text("Start"), button:has-text("New"), button:has-text("Create"), button:has-text("Begin")').first();
      await firstButton.click();
      await page.waitForTimeout(3000);

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, 'v2-07-flow-started.png'),
        fullPage: true
      });

      console.log('✓ Clicked start button');
    } else {
      console.log('⚠ No start button found');

      // Try clicking on an existing row or card
      const rows = await page.locator('tr, [class*="row"], [class*="card"]').count();
      console.log(`Found ${rows} potential clickable rows/cards`);

      if (rows > 1) {  // > 1 to skip header row
        const secondRow = page.locator('tr, [class*="row"]').nth(1);
        if (await secondRow.isVisible().catch(() => false)) {
          await secondRow.click();
          await page.waitForTimeout(3000);

          await page.screenshot({
            path: path.join(SCREENSHOT_DIR, 'v2-07-row-clicked.png'),
            fullPage: true
          });
        }
      }
    }

    // STEP 6: Monitor for collection flow progress
    console.log('\n=== STEP 6: MONITOR COLLECTION FLOW ===');

    const maxWaitTime = 90000; // 90 seconds
    const checkInterval = 10000; // 10 seconds
    let elapsedTime = 0;
    let screenshotCount = 0;

    while (elapsedTime < maxWaitTime) {
      await page.waitForTimeout(checkInterval);
      elapsedTime += checkInterval;
      screenshotCount++;

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `v2-08-monitor-${screenshotCount}.png`),
        fullPage: true
      });

      // Check for phase indicators
      const phaseIndicators = [
        'Gap Analysis',
        'Data Awareness',
        'Questionnaire',
        'Generation',
        'running',
        'processing',
        'completed',
        'error',
        'failed'
      ];

      let foundIndicator = false;
      for (const indicator of phaseIndicators) {
        const hasIndicator = await page.locator(`text=/${indicator}/i`).isVisible().catch(() => false);
        if (hasIndicator) {
          console.log(`⏳ Found indicator: ${indicator} (${elapsedTime/1000}s)`);
          foundIndicator = true;
          break;
        }
      }

      // Check for errors
      const hasError = await page.locator('text=/error|failed/i').isVisible().catch(() => false);
      if (hasError) {
        console.log('❌ Error detected in UI');
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'v2-09-error-state.png'),
          fullPage: true
        });

        // Get error text
        const errorText = await page.locator('text=/error|failed/i').first().textContent();
        console.log('Error text:', errorText);
        break;
      }

      // Check for completion
      const hasComplete = await page.locator('text=/complete|success|done/i').isVisible().catch(() => false);
      if (hasComplete) {
        console.log('✓ Flow completed successfully');
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'v2-10-success-state.png'),
          fullPage: true
        });
        break;
      }

      // If nothing is happening and no indicators found, stop early
      if (elapsedTime >= 30000 && !foundIndicator) {
        console.log('⚠ No activity detected after 30s');
        break;
      }
    }

    // Final screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'v2-11-final-state.png'),
      fullPage: true
    });

    // Get final page URL and title
    console.log('\n=== FINAL STATE ===');
    console.log('Final URL:', page.url());
    console.log('Final Title:', await page.title());

    console.log('\n✓ Test Complete');
    console.log(`Screenshots saved to: ${SCREENSHOT_DIR}`);
  });
});
