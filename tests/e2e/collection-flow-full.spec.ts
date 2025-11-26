import { test, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const TEST_USER = { email: 'chockas@hcltech.com', password: 'Testing123!' };
const BASE_URL = 'http://localhost:8081';
const SCREENSHOT_DIR = '/Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

test.describe('Collection Flow - Full Journey', () => {
  let page: Page;
  const consoleErrors: string[] = [];
  const apiErrors: Array<{ status: number; url: string }> = [];

  test.setTimeout(600000); // 10 minutes for full flow

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext();
    page = await context.newPage();

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log(`[BROWSER ERROR]: ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      consoleErrors.push(error.message);
      console.error('[PAGE ERROR]:', error.message);
    });

    page.on('response', async response => {
      if (response.status() >= 400) {
        apiErrors.push({ status: response.status(), url: response.url() });
        console.error(`[HTTP ${response.status()}]: ${response.url()}`);
      }
    });
  });

  test.afterAll(async () => {
    console.log('\n' + '='.repeat(70));
    console.log('TEST SUMMARY');
    console.log('='.repeat(70));
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`API Errors: ${apiErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\nConsole Errors:');
      consoleErrors.slice(0, 10).forEach((err, i) => console.log(`  ${i + 1}. ${err.substring(0, 150)}`));
    }

    if (apiErrors.length > 0) {
      console.log('\nAPI Errors:');
      apiErrors.slice(0, 10).forEach((err, i) => console.log(`  ${i + 1}. HTTP ${err.status}: ${err.url}`));
    }

    await page.close();
  });

  test('Complete Collection Flow with Asset Selection', async () => {
    // STEP 1: Login
    console.log('\n' + '='.repeat(70));
    console.log('STEP 1: LOGIN');
    console.log('='.repeat(70));

    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-01-logged-in.png'), fullPage: true });
    console.log('✓ Login successful');

    // STEP 2: Navigate to Collection
    console.log('\n' + '='.repeat(70));
    console.log('STEP 2: NAVIGATE TO COLLECTION');
    console.log('='.repeat(70));

    await page.click('text=Collection');
    await page.waitForTimeout(2000);
    await page.click('text=Overview');
    await page.waitForTimeout(3000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-02-collection-overview.png'), fullPage: true });
    console.log('✓ On Collection Overview');

    // STEP 3: Start New Collection
    console.log('\n' + '='.repeat(70));
    console.log('STEP 3: START NEW COLLECTION');
    console.log('='.repeat(70));

    await page.click('button:has-text("Start New")');
    await page.waitForTimeout(2000);

    // Select Adaptive Forms option
    await page.click('text=1-50 applications');
    await page.waitForTimeout(1000);

    // Click Start Collection
    await page.click('button:has-text("Start Collection")');
    await page.waitForTimeout(5000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-03-asset-selection.png'), fullPage: true });
    console.log('✓ On Asset Selection page');
    console.log('  URL:', page.url());

    // STEP 4: Select Assets
    console.log('\n' + '='.repeat(70));
    console.log('STEP 4: SELECT ASSETS');
    console.log('='.repeat(70));

    // Select the first 3 applications
    const applicationCheckboxes = await page.locator('input[type="checkbox"]').all();
    console.log(`Found ${applicationCheckboxes.length} checkboxes`);

    let selectedCount = 0;
    for (let i = 0; i < Math.min(applicationCheckboxes.length, 4); i++) {
      try {
        const checkbox = applicationCheckboxes[i];
        if (await checkbox.isVisible()) {
          await checkbox.click();
          selectedCount++;
          await page.waitForTimeout(500);
        }
      } catch (e) {
        console.log(`Could not click checkbox ${i + 1}`);
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-04-assets-selected.png'), fullPage: true });
    console.log(`✓ Selected ${selectedCount} assets`);

    // STEP 5: Continue with Selected Assets
    console.log('\n' + '='.repeat(70));
    console.log('STEP 5: CONTINUE WITH SELECTED ASSETS');
    console.log('='.repeat(70));

    const continueButton = page.locator('button:has-text("Continue with")');
    await continueButton.click();
    await page.waitForTimeout(10000); // Wait longer for backend processing

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-05-flow-executing.png'), fullPage: true });
    console.log('✓ Continue clicked - flow executing');
    console.log('  URL:', page.url());

    // STEP 6: Monitor Flow Execution (Extended)
    console.log('\n' + '='.repeat(70));
    console.log('STEP 6: MONITOR COLLECTION FLOW EXECUTION');
    console.log('='.repeat(70));

    const maxMonitorTime = 300000; // 5 minutes
    const checkInterval = 15000; // 15 seconds
    let elapsed = 0;
    let monitorCount = 0;
    let lastPhase = '';

    while (elapsed < maxMonitorTime) {
      await page.waitForTimeout(checkInterval);
      elapsed += checkInterval;
      monitorCount++;

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `full-06-monitor-${String(monitorCount).padStart(2, '0')}.png`),
        fullPage: true
      });

      const bodyText = await page.textContent('body');
      const lower = bodyText?.toLowerCase() || '';

      // Detect phases
      const currentPhase =
        lower.includes('gap analysis') || lower.includes('gap scanning') ? 'Gap Analysis' :
        lower.includes('data awareness') || lower.includes('data map') ? 'Data Awareness' :
        lower.includes('questionnaire') || lower.includes('generation') ? 'Questionnaire' :
        lower.includes('collection complete') || lower.includes('success') ? 'Completed' :
        'Unknown';

      if (currentPhase !== lastPhase && currentPhase !== 'Unknown') {
        console.log(`  → Phase: ${currentPhase}`);
        lastPhase = currentPhase;
      }

      // Check status indicators
      const hasError = (lower.includes('error') && (lower.includes('failed') || lower.includes('occurred')));
      const hasComplete = lower.includes('completed') || lower.includes('collection complete') || lower.includes('success');
      const hasQuestionnaire = lower.includes('questionnaire ready') || lower.includes('answer questions');

      console.log(`[${elapsed/1000}s] Phase=${currentPhase}, Error=${hasError}, Complete=${hasComplete}, Questionnaire=${hasQuestionnaire}`);

      if (hasError) {
        console.log('❌ ERROR DETECTED');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-07-error.png'), fullPage: true });

        // Try to capture error details
        const errorElements = await page.locator('[class*="error"], [role="alert"]').all();
        for (let i = 0; i < Math.min(errorElements.length, 3); i++) {
          const text = await errorElements[i].textContent();
          console.log(`  Error: ${text}`);
        }
        break;
      }

      if (hasComplete) {
        console.log('✓ FLOW COMPLETED SUCCESSFULLY');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-08-completed.png'), fullPage: true });
        break;
      }

      if (hasQuestionnaire && elapsed > 60000) {
        console.log('✓ QUESTIONNAIRE READY');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-09-questionnaire.png'), fullPage: true });
        // Continue monitoring a bit longer to see if there are issues
        if (elapsed > 120000) break;
      }
    }

    // Final State
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'full-10-final.png'), fullPage: true });

    console.log('\n' + '='.repeat(70));
    console.log('FINAL STATE');
    console.log('='.repeat(70));
    console.log('URL:', page.url());
    console.log('Title:', await page.title());
    console.log('Total Monitoring Time:', elapsed / 1000, 'seconds');
    console.log('\n✓ TEST COMPLETE');
  });
});
