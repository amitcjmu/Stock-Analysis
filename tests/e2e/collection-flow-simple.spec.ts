import { test, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const TEST_USER = { email: 'chockas@hcltech.com', password: 'Testing123!' };
const BASE_URL = 'http://localhost:8081';
const SCREENSHOT_DIR = '/Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

test.describe('Collection Flow Simple Test', () => {
  let page: Page;

  test.setTimeout(300000); // 5 minutes

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext();
    page = await context.newPage();

    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`[BROWSER ERROR]: ${msg.text()}`);
      }
    });
    page.on('pageerror', error => {
      console.error('[PAGE ERROR]:', error.message);
    });
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('Login and Navigate to Collection', async () => {
    console.log('\n=== LOGIN ===');
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-01-login.png'), fullPage: true });

    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-02-dashboard.png'), fullPage: true });
    console.log('✓ Logged in');

    console.log('\n=== CLICK COLLECTION IN SIDEBAR ===');
    // Use simple text locator for Collection
    await page.click('text=Collection');
    await page.waitForTimeout(3000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-03-collection-menu.png'), fullPage: true });
    console.log('✓ Clicked Collection');
    console.log('URL:', page.url());

    console.log('\n=== LOOKING FOR SUBMENU OR CONTENT ===');
    // Check if there's an expanded menu or if we need to navigate further
    const pageContent = await page.textContent('body');
    const hasOverview = pageContent?.includes('Overview');
    const hasFlows = pageContent?.includes('Flows');
    const hasAssets = pageContent?.includes('Assets') || pageContent?.includes('assets');

    console.log(`Content check: Overview=${hasOverview}, Flows=${hasFlows}, Assets=${hasAssets}`);

    // Try clicking Overview if it exists
    if (hasOverview) {
      try {
        await page.click('text=Overview', { timeout: 5000 });
        await page.waitForTimeout(3000);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-04-overview.png'), fullPage: true });
        console.log('✓ Clicked Overview');
      } catch (e) {
        console.log('⚠ Could not click Overview');
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-05-current-page.png'), fullPage: true });

    console.log('\n=== SEARCHING FOR START/CREATE BUTTONS ===');
    // Look for any button that might start a collection flow
    const allButtons = await page.locator('button').all();
    console.log(`Found ${allButtons.length} buttons on page`);

    for (let i = 0; i < Math.min(allButtons.length, 10); i++) {
      try {
        const text = await allButtons[i].textContent({ timeout: 1000 });
        const isVisible = await allButtons[i].isVisible();
        if (isVisible && text) {
          console.log(`Button ${i + 1}: "${text.trim()}"`);
        }
      } catch (e) {
        // Skip if button is not accessible
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-06-buttons-found.png'), fullPage: true });

    console.log('\n=== TRYING TO START A COLLECTION FLOW ===');
    // Try various button text patterns
    const startPatterns = ['Start', 'New', 'Create', 'Begin', 'Add'];

    for (const pattern of startPatterns) {
      try {
        const button = page.locator(`button:has-text("${pattern}")`).first();
        if (await button.isVisible({ timeout: 2000 })) {
          const buttonText = await button.textContent();
          console.log(`Found button: "${buttonText}" - clicking...`);

          await button.click();
          await page.waitForTimeout(5000);

          await page.screenshot({
            path: path.join(SCREENSHOT_DIR, `s-07-clicked-${pattern.toLowerCase()}.png`),
            fullPage: true
          });

          console.log('✓ Clicked start button');
          break;
        }
      } catch (e) {
        // Pattern not found, continue
      }
    }

    console.log('\n=== MONITORING FOR FLOW ACTIVITY ===');
    const maxWait = 120000; // 2 minutes
    const interval = 10000; // 10 seconds
    let elapsed = 0;
    let count = 0;

    while (elapsed < maxWait) {
      await page.waitForTimeout(interval);
      elapsed += interval;
      count++;

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `s-08-monitor-${count}.png`),
        fullPage: true
      });

      const body = await page.textContent('body');
      const hasRunning = body?.toLowerCase().includes('running') || body?.toLowerCase().includes('processing');
      const hasError = body?.toLowerCase().includes('error') && body?.toLowerCase().includes('failed');
      const hasComplete = body?.toLowerCase().includes('complete') || body?.toLowerCase().includes('success');
      const hasPhase = body?.toLowerCase().includes('gap') || body?.toLowerCase().includes('questionnaire') || body?.toLowerCase().includes('awareness');

      console.log(`[${elapsed/1000}s] running=${hasRunning}, error=${hasError}, complete=${hasComplete}, phase=${hasPhase}`);

      if (hasError) {
        console.log('❌ ERROR DETECTED');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-09-error.png'), fullPage: true });
        break;
      }

      if (hasComplete) {
        console.log('✓ COMPLETION DETECTED');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-10-complete.png'), fullPage: true });
        break;
      }

      if (!hasRunning && !hasPhase && elapsed >= 30000) {
        console.log('⚠ No activity detected after 30s');
        break;
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 's-11-final.png'), fullPage: true });
    console.log('\n✓ TEST COMPLETE');
    console.log(`Final URL: ${page.url()}`);
    console.log(`Screenshots: ${SCREENSHOT_DIR}`);
  });
});
