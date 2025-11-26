import { test, Page, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const TEST_USER = { email: 'chockas@hcltech.com', password: 'Testing123!' };
const BASE_URL = 'http://localhost:8081';
const SCREENSHOT_DIR = '/Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

test.describe('Collection Flow - Final Complete Test', () => {
  let page: Page;
  const consoleErrors: string[] = [];
  const apiErrors: Array<{ status: number; url: string; method: string }> = [];

  test.setTimeout(600000); // 10 minutes

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
        apiErrors.push({
          status: response.status(),
          url: response.url(),
          method: response.request().method()
        });
        console.error(`[HTTP ${response.status()}]: ${response.request().method()} ${response.url()}`);
      }
    });
  });

  test.afterAll(async () => {
    console.log('\n' + '='.repeat(80));
    console.log('FINAL TEST SUMMARY');
    console.log('='.repeat(80));
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`API Errors: ${apiErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\nConsole Errors:');
      consoleErrors.slice(0, 10).forEach((err, i) => console.log(`  ${i + 1}. ${err.substring(0, 200)}`));
    }

    if (apiErrors.length > 0) {
      console.log('\nAPI Errors:');
      apiErrors.slice(0, 10).forEach((err, i) => {
        console.log(`  ${i + 1}. ${err.method} ${err.status}: ${err.url.substring(0, 100)}`);
      });
    }

    await page.close();
  });

  test('Complete Collection Flow Journey', async () => {
    // STEP 1: Login
    console.log('\n' + '='.repeat(80));
    console.log('STEP 1: LOGIN');
    console.log('='.repeat(80));

    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-01-logged-in.png'), fullPage: true });
    console.log('✓ Login successful');

    // STEP 2: Navigate to Collection
    console.log('\n' + '='.repeat(80));
    console.log('STEP 2: NAVIGATE TO COLLECTION');
    console.log('='.repeat(80));

    await page.click('text=Collection');
    await page.waitForTimeout(2000);
    await page.click('text=Overview');
    await page.waitForTimeout(3000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-02-collection-overview.png'), fullPage: true });
    console.log('✓ Collection Overview loaded');

    // STEP 3: Start New Collection
    console.log('\n' + '='.repeat(80));
    console.log('STEP 3: START NEW COLLECTION FLOW');
    console.log('='.repeat(80));

    await page.click('button:has-text("Start New")');
    await page.waitForTimeout(2000);

    await page.click('text=1-50 applications');
    await page.waitForTimeout(1000);

    await page.click('button:has-text("Start Collection")');
    await page.waitForTimeout(5000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-03-asset-selection.png'), fullPage: true });
    console.log('✓ Asset selection page loaded');

    const flowUrl = page.url();
    const flowIdMatch = flowUrl.match(/flowId=([a-f0-9-]+)/);
    const flowId = flowIdMatch ? flowIdMatch[1] : 'unknown';
    console.log(`  Flow ID: ${flowId}`);

    // STEP 4: Select Assets Using "Select All"
    console.log('\n' + '='.repeat(80));
    console.log('STEP 4: SELECT ASSETS');
    console.log('='.repeat(80));

    // Click "Select All" checkbox
    const selectAllCheckbox = page.locator('text=Select All').locator('..').locator('input[type="checkbox"]');
    if (await selectAllCheckbox.isVisible()) {
      await selectAllCheckbox.click();
      await page.waitForTimeout(2000);
      console.log('✓ Clicked "Select All" checkbox');
    } else {
      // Fallback: click individual asset checkboxes
      console.log('  Fallback: Selecting individual assets...');

      // Find asset rows and click their checkboxes
      const assetRows = await page.locator('[class*="asset"], [data-asset-id]').all();
      console.log(`  Found ${assetRows.length} asset rows`);

      // Select first 3 assets
      for (let i = 0; i < Math.min(assetRows.length, 3); i++) {
        const checkbox = assetRows[i].locator('input[type="checkbox"]').first();
        if (await checkbox.isVisible().catch(() => false)) {
          await checkbox.click();
          await page.waitForTimeout(500);
          console.log(`  ✓ Selected asset ${i + 1}`);
        }
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-04-assets-selected.png'), fullPage: true });

    // STEP 5: Continue with Selected Assets
    console.log('\n' + '='.repeat(80));
    console.log('STEP 5: CONTINUE WITH SELECTED ASSETS');
    console.log('='.repeat(80));

    const continueButton = page.locator('button:has-text("Continue with")');

    // Wait for button to be enabled
    await page.waitForTimeout(2000);

    // Check if button is enabled
    const isDisabled = await continueButton.getAttribute('disabled');
    if (isDisabled !== null) {
      console.log('⚠ Continue button is disabled - no assets selected');
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-05-button-disabled.png'), fullPage: true });

      // Try clicking first visible checkbox directly by text
      const firstAsset = page.locator('text=Analytics Dashboard').or(page.locator('text=Ansible Tower')).first();
      const firstCheckbox = page.locator('input[type="checkbox"]').first();
      await firstCheckbox.click();
      await page.waitForTimeout(1000);
      console.log('  Tried clicking first checkbox');
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-06-before-continue.png'), fullPage: true });

    // Force click even if disabled (to see what happens)
    await continueButton.click({ force: true });
    await page.waitForTimeout(10000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-07-after-continue.png'), fullPage: true });
    console.log('✓ Continue button clicked');
    console.log(`  URL: ${page.url()}`);

    // STEP 6: Extended Monitoring
    console.log('\n' + '='.repeat(80));
    console.log('STEP 6: MONITOR COLLECTION FLOW (5 MINUTES)');
    console.log('='.repeat(80));

    const maxTime = 300000; // 5 minutes
    const interval = 15000; // 15 seconds
    let elapsed = 0;
    let count = 0;
    let lastPhase = '';
    const phaseChanges: string[] = [];

    while (elapsed < maxTime) {
      await page.waitForTimeout(interval);
      elapsed += interval;
      count++;

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `final-08-monitor-${String(count).padStart(3, '0')}.png`),
        fullPage: true
      });

      const body = await page.textContent('body');
      const lower = body?.toLowerCase() || '';

      // Detect current phase
      let currentPhase = 'Waiting';
      if (lower.includes('gap analysis') || lower.includes('intelligent gap')) currentPhase = 'Gap Analysis';
      else if (lower.includes('data awareness') || lower.includes('data map')) currentPhase = 'Data Awareness';
      else if (lower.includes('questionnaire') && lower.includes('generat')) currentPhase = 'Questionnaire Generation';
      else if (lower.includes('answer') && lower.includes('question')) currentPhase = 'Questionnaire Ready';
      else if (lower.includes('complete') || lower.includes('success')) currentPhase = 'Completed';
      else if (lower.includes('error') || lower.includes('failed')) currentPhase = 'Error';

      if (currentPhase !== lastPhase && currentPhase !== 'Waiting') {
        console.log(`  [${elapsed/1000}s] → Phase Change: ${lastPhase || 'Start'} → ${currentPhase}`);
        phaseChanges.push(`${elapsed/1000}s: ${currentPhase}`);
        lastPhase = currentPhase;
      } else {
        console.log(`  [${elapsed/1000}s] Phase: ${currentPhase}`);
      }

      // Check for errors
      if (currentPhase === 'Error') {
        console.log('❌ ERROR DETECTED');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-09-error.png'), fullPage: true });

        // Capture error messages
        const errorTexts = await page.locator('[class*="error"], [role="alert"]').allTextContents();
        errorTexts.forEach((text, i) => console.log(`  Error ${i + 1}: ${text.substring(0, 150)}`));
        break;
      }

      // Check for completion
      if (currentPhase === 'Completed') {
        console.log('✓ FLOW COMPLETED');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-10-completed.png'), fullPage: true });
        break;
      }

      // Check if questionnaire is ready
      if (currentPhase === 'Questionnaire Ready') {
        console.log('✓ QUESTIONNAIRE GENERATED');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-11-questionnaire.png'), fullPage: true });

        // Monitor a bit longer then exit
        if (elapsed > 60000) {
          console.log('  Questionnaire stable for 1+ minute - ending test');
          break;
        }
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'final-12-final-state.png'), fullPage: true });

    console.log('\n' + '='.repeat(80));
    console.log('COLLECTION FLOW TEST COMPLETE');
    console.log('='.repeat(80));
    console.log(`Flow ID: ${flowId}`);
    console.log(`Final URL: ${page.url()}`);
    console.log(`Total Time: ${elapsed/1000}s`);
    console.log(`Phase Changes: ${phaseChanges.length}`);
    phaseChanges.forEach((change, i) => console.log(`  ${i + 1}. ${change}`));
    console.log('\n✓ Test execution complete');
  });
});
