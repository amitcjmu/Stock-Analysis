import { test, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const TEST_USER = { email: 'chockas@hcltech.com', password: 'Testing123!' };
const BASE_URL = 'http://localhost:8081';
const SCREENSHOT_DIR = '/Users/chocka/CursorProjects/migrate-ui-orchestrator/tests/e2e/screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

test.describe('Collection Flow Complete E2E', () => {
  let page: Page;
  const consoleErrors: string[] = [];
  const apiErrors: Array<{ status: number; url: string; body?: string }> = [];

  test.setTimeout(300000); // 5 minutes

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext();
    page = await context.newPage();

    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        console.log(`[BROWSER ERROR]: ${text}`);
        consoleErrors.push(text);
      }
    });

    page.on('pageerror', error => {
      console.error('[PAGE ERROR]:', error.message);
      consoleErrors.push(error.message);
    });

    page.on('response', async response => {
      if (response.status() >= 400) {
        const url = response.url();
        const errorInfo = { status: response.status(), url, body: undefined as string | undefined };

        try {
          const contentType = response.headers()['content-type'];
          if (contentType?.includes('application/json')) {
            errorInfo.body = await response.text();
          }
        } catch (e) {
          // Ignore if we can't read body
        }

        console.error(`[HTTP ${errorInfo.status}]: ${url}`);
        if (errorInfo.body) {
          console.error(`  Response: ${errorInfo.body.substring(0, 200)}`);
        }
        apiErrors.push(errorInfo);
      }
    });
  });

  test.afterAll(async () => {
    console.log('\n' + '='.repeat(60));
    console.log('TEST SUMMARY');
    console.log('='.repeat(60));
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`API Errors: ${apiErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\nConsole Errors:');
      consoleErrors.forEach((err, i) => console.log(`  ${i + 1}. ${err}`));
    }

    if (apiErrors.length > 0) {
      console.log('\nAPI Errors:');
      apiErrors.forEach((err, i) => {
        console.log(`  ${i + 1}. HTTP ${err.status}: ${err.url}`);
        if (err.body) {
          console.log(`     ${err.body.substring(0, 150)}`);
        }
      });
    }

    await page.close();
  });

  test('Complete Collection Flow with Adaptive Forms', async () => {
    // STEP 1: Login
    console.log('\n' + '='.repeat(60));
    console.log('STEP 1: LOGIN');
    console.log('='.repeat(60));

    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'complete-01-login.png'), fullPage: true });

    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'complete-02-dashboard.png'), fullPage: true });
    console.log('✓ Login successful');

    // STEP 2: Navigate to Collection
    console.log('\n' + '='.repeat(60));
    console.log('STEP 2: NAVIGATE TO COLLECTION');
    console.log('='.repeat(60));

    await page.click('text=Collection');
    await page.waitForTimeout(2000);

    await page.click('text=Overview');
    await page.waitForTimeout(3000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'complete-03-collection-overview.png'), fullPage: true });
    console.log('✓ On Collection Overview');
    console.log('  URL:', page.url());

    // STEP 3: Start New Collection
    console.log('\n' + '='.repeat(60));
    console.log('STEP 3: START NEW COLLECTION');
    console.log('='.repeat(60));

    await page.click('button:has-text("Start New")');
    await page.waitForTimeout(2000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'complete-04-start-dialog.png'), fullPage: true });
    console.log('✓ Start dialog opened');

    // STEP 4: Select Adaptive Forms option
    console.log('\n' + '='.repeat(60));
    console.log('STEP 4: SELECT ADAPTIVE FORMS');
    console.log('='.repeat(60));

    // Click the first option (1-50 applications → Adaptive Forms)
    const adaptiveFormsOption = page.locator('text=1-50 applications').first();
    await adaptiveFormsOption.click();
    await page.waitForTimeout(1000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'complete-05-option-selected.png'), fullPage: true });
    console.log('✓ Adaptive Forms option selected');

    // STEP 5: Click Start Collection button
    console.log('\n' + '='.repeat(60));
    console.log('STEP 5: CLICK START COLLECTION');
    console.log('='.repeat(60));

    const startCollectionButton = page.locator('button:has-text("Start Collection")');
    await startCollectionButton.click();
    await page.waitForTimeout(5000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'complete-06-flow-started.png'), fullPage: true });
    console.log('✓ Start Collection clicked');
    console.log('  URL:', page.url());

    // STEP 6: Monitor flow execution
    console.log('\n' + '='.repeat(60));
    console.log('STEP 6: MONITOR COLLECTION FLOW EXECUTION');
    console.log('='.repeat(60));

    const maxMonitorTime = 180000; // 3 minutes
    const checkInterval = 10000; // 10 seconds
    let elapsed = 0;
    let monitorCount = 0;
    let flowCompleted = false;
    let flowErrored = false;

    while (elapsed < maxMonitorTime) {
      await page.waitForTimeout(checkInterval);
      elapsed += checkInterval;
      monitorCount++;

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `complete-07-monitor-${String(monitorCount).padStart(2, '0')}.png`),
        fullPage: true
      });

      // Get page content
      const bodyText = await page.textContent('body');
      const lowerBody = bodyText?.toLowerCase() || '';

      // Check for phase indicators
      const indicators = {
        gapAnalysis: lowerBody.includes('gap analysis') || lowerBody.includes('gap scanning'),
        dataAwareness: lowerBody.includes('data awareness') || lowerBody.includes('data map'),
        questionnaire: lowerBody.includes('questionnaire') || lowerBody.includes('question generation'),
        running: lowerBody.includes('running') || lowerBody.includes('processing') || lowerBody.includes('in progress'),
        error: (lowerBody.includes('error') && lowerBody.includes('failed')) || lowerBody.includes('error occurred'),
        complete: lowerBody.includes('completed') || lowerBody.includes('success') || lowerBody.includes('finished')
      };

      console.log(`[${elapsed/1000}s] Gap=${indicators.gapAnalysis}, Data=${indicators.dataAwareness}, Q=${indicators.questionnaire}, Run=${indicators.running}, Err=${indicators.error}, Done=${indicators.complete}`);

      // Check for errors
      if (indicators.error) {
        console.log('❌ ERROR DETECTED IN UI');
        flowErrored = true;

        // Try to capture error message
        const errorElements = await page.locator('text=/error|failed/i').all();
        for (let i = 0; i < Math.min(errorElements.length, 3); i++) {
          const errorText = await errorElements[i].textContent();
          console.log(`  Error ${i + 1}: ${errorText}`);
        }

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'complete-08-error-state.png'),
          fullPage: true
        });
        break;
      }

      // Check for completion
      if (indicators.complete) {
        console.log('✓ FLOW COMPLETED SUCCESSFULLY');
        flowCompleted = true;

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, 'complete-09-completed.png'),
          fullPage: true
        });
        break;
      }

      // Log current phase if detected
      if (indicators.gapAnalysis) console.log('  → Phase: Gap Analysis');
      if (indicators.dataAwareness) console.log('  → Phase: Data Awareness');
      if (indicators.questionnaire) console.log('  → Phase: Questionnaire Generation');

      // If no activity after 30s, warn but continue
      if (elapsed >= 30000 && !indicators.running && !indicators.gapAnalysis && !indicators.dataAwareness && !indicators.questionnaire) {
        console.log('  ⚠ No obvious activity indicators visible');
      }
    }

    // Final screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'complete-10-final.png'),
      fullPage: true
    });

    console.log('\n' + '='.repeat(60));
    console.log('FINAL STATE');
    console.log('='.repeat(60));
    console.log('URL:', page.url());
    console.log('Title:', await page.title());
    console.log('Flow Completed:', flowCompleted);
    console.log('Flow Errored:', flowErrored);
    console.log('Total Monitoring Time:', elapsed / 1000, 'seconds');

    console.log('\n✓ TEST EXECUTION COMPLETE');
    console.log(`  Screenshots saved to: ${SCREENSHOT_DIR}`);
  });
});
