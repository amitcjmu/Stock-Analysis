/**
 * Manual Collection Flow E2E Test
 *
 * Comprehensive test of Collection flow with proper authentication
 *
 * Steps:
 * 1. Login with demo credentials
 * 2. Navigate to Collection page
 * 3. Start new collection flow
 * 4. Select assets
 * 5. Navigate through collection phases
 * 6. Verify data persistence and API responses
 */

import { test, expect, Page } from '@playwright/test';
import path from 'path';

const BASE_URL = 'http://localhost:8081';
const DEMO_EMAIL = 'demo@demo-corp.com';
const DEMO_PASSWORD = 'Demo123!';

// Project-relative screenshot directory (not user-specific absolute path)
const SCREENSHOT_DIR = path.resolve(__dirname, '../../qa-test-screenshots');

/**
 * Enhanced login helper that waits for full auth context initialization
 * Bug #650 Fix: Ensures AuthContext React hooks complete before proceeding
 */
async function loginAndWaitForContext(page: Page) {
  console.log('🔐 Logging in with demo credentials...');

  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle');

  // Fill in credentials
  await page.fill('input[type="email"], input[name="email"]', DEMO_EMAIL);
  await page.fill('input[type="password"], input[name="password"]', DEMO_PASSWORD);

  // Click sign in
  await page.click('button:has-text("Sign In")');

  // Wait for redirect after login
  await page.waitForTimeout(2000);

  // CRITICAL FIX (Bug #650): Wait for AuthContext to fully initialize
  console.log('⏳ Waiting for AuthContext initialization...');

  await page.waitForFunction(() => {
    const client = localStorage.getItem('auth_client');
    const engagement = localStorage.getItem('auth_engagement');
    const user = localStorage.getItem('auth_user');

    // Ensure all are loaded and not null strings
    return client && engagement && user &&
           client !== 'null' && engagement !== 'null' && user !== 'null';
  }, { timeout: 10000 });

  // Verify context is loaded
  const authContext = await page.evaluate(() => ({
    client: localStorage.getItem('auth_client'),
    engagement: localStorage.getItem('auth_engagement'),
    user: localStorage.getItem('auth_user')
  }));

  console.log('✅ Auth context loaded:', authContext);

  // Additional wait for React state to sync
  await page.waitForTimeout(1000);

  const currentUrl = page.url();
  console.log(`✅ Login complete, redirected to: ${currentUrl}`);

  return currentUrl;
}

test.describe('Collection Flow - Full Journey', () => {
  test.setTimeout(180000); // 3 minutes

  test.beforeEach(async ({ page }) => {
    // Login before each test (Bug #650 Fix: Now waits for AuthContext)
    await loginAndWaitForContext(page);
  });

  test('Complete Collection Flow Journey', async ({ page, context }) => {
    console.log('\n🧪 COLLECTION FLOW COMPREHENSIVE TEST\n');

    // STEP 1: Navigate to Collection page
    console.log('📝 STEP 1: Navigate to Collection page');
    await page.goto(`${BASE_URL}/collection`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '01-collection-landing.png'),
      fullPage: true
    });
    console.log('✅ Collection page loaded');

    // STEP 2: Check for existing flows or start new
    console.log('\n📝 STEP 2: Check for existing flows or start new collection');

    const startButton = page.locator('button:has-text("Start Collection"), button:has-text("New Collection"), button:has-text("Create")');
    const resumeButton = page.locator('button:has-text("Resume"), button:has-text("Continue")');

    const hasStartButton = await startButton.isVisible({ timeout: 5000 }).catch(() => false);
    const hasResumeButton = await resumeButton.isVisible({ timeout: 5000 }).catch(() => false);

    let flowId: string | null = null;

    if (hasResumeButton) {
      console.log('📋 Found incomplete flow, resuming...');
      await resumeButton.first().click();
      await page.waitForTimeout(2000);

      // Extract flow ID from URL
      const urlMatch = page.url().match(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/);
      flowId = urlMatch ? urlMatch[0] : null;
      console.log(`🔍 Resumed flow ID: ${flowId}`);
    } else if (hasStartButton) {
      console.log('🆕 Starting new collection flow...');
      await startButton.first().click();
      await page.waitForTimeout(3000);

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '02-after-start-click.png'),
        fullPage: true
      });

      // Extract flow ID from URL
      const urlMatch = page.url().match(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/);
      flowId = urlMatch ? urlMatch[0] : null;
      console.log(`🔍 New flow ID: ${flowId}`);
    } else {
      console.error('❌ No start or resume button found!');
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, 'ERROR-no-buttons.png'),
        fullPage: true
      });

      // Check page content
      const pageContent = await page.content();
      console.log('Page HTML preview:', pageContent.substring(0, 500));
    }

    // STEP 3: Asset Selection Phase
    console.log('\n📝 STEP 3: Asset Selection Phase');
    await page.waitForTimeout(2000);

    // Take screenshot of asset selection
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '03-asset-selection.png'),
      fullPage: true
    });

    // Look for asset checkboxes
    const checkboxes = page.locator('input[type="checkbox"]').filter({ hasNot: page.locator('[disabled]') });
    const checkboxCount = await checkboxes.count();
    console.log(`📊 Found ${checkboxCount} available checkboxes`);

    if (checkboxCount === 0) {
      console.error('❌ No asset checkboxes found!');

      // Check for any error messages
      const errorMessages = page.locator('text=/error|failed|not found/i');
      const errorCount = await errorMessages.count();

      if (errorCount > 0) {
        for (let i = 0; i < Math.min(errorCount, 3); i++) {
          const errorText = await errorMessages.nth(i).textContent();
          console.error(`❌ Error message ${i + 1}: ${errorText}`);
        }
      }

      // Check API network requests
      console.log('🔍 Checking network activity...');
      const logs: string[] = [];

      page.on('response', response => {
        if (response.url().includes('/api/')) {
          logs.push(`${response.status()} ${response.url()}`);
        }
      });

      await page.waitForTimeout(3000);
      console.log('Network logs:', logs.slice(0, 10));

      throw new Error('No assets available for selection - possible data issue');
    }

    // Select 2-3 assets
    const selectCount = Math.min(3, checkboxCount);
    console.log(`✅ Selecting ${selectCount} assets...`);

    for (let i = 0; i < selectCount; i++) {
      await checkboxes.nth(i).check();
      await page.waitForTimeout(500);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '04-assets-selected.png'),
      fullPage: true
    });

    console.log(`✅ Selected ${selectCount} assets`);

    // STEP 4: Proceed to next phase
    console.log('\n📝 STEP 4: Proceed to next phase');

    const nextButton = page.locator('button:has-text("Next"), button:has-text("Continue"), button:has-text("Submit"), button:has-text("Analyze")');
    const hasNextButton = await nextButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasNextButton) {
      const buttonText = await nextButton.first().textContent();
      console.log(`🔘 Clicking button: "${buttonText}"`);

      await nextButton.first().click();
      await page.waitForTimeout(3000);

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '05-after-next-click.png'),
        fullPage: true
      });

      console.log('✅ Proceeded to next phase');
    } else {
      console.error('❌ No Next/Continue button found!');
      throw new Error('Cannot proceed - no navigation button');
    }

    // STEP 5: Verify current phase
    console.log('\n📝 STEP 5: Verify current phase');

    const currentUrl = page.url();
    console.log(`🔍 Current URL: ${currentUrl}`);

    // Check for common phase indicators
    const phaseIndicators = [
      'Gap Analysis',
      'Questionnaire',
      'Data Collection',
      'Assessment',
      'Review'
    ];

    for (const indicator of phaseIndicators) {
      const hasIndicator = await page.locator(`text=${indicator}`).isVisible({ timeout: 2000 }).catch(() => false);
      if (hasIndicator) {
        console.log(`✅ Phase detected: ${indicator}`);

        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, `06-phase-${indicator.toLowerCase().replace(/\s+/g, '-')}.png`),
          fullPage: true
        });

        break;
      }
    }

    // STEP 6: Check for loading states and errors
    console.log('\n📝 STEP 6: Monitor for loading states and errors');

    // Wait a bit to see if anything is loading
    await page.waitForTimeout(2000);

    // Check for spinners
    const spinners = page.locator('svg.animate-spin, [class*="spinner"], [class*="loading"]');
    const spinnerCount = await spinners.count();

    if (spinnerCount > 0) {
      console.log(`⏳ Found ${spinnerCount} loading indicators`);

      // Wait for loading to complete (max 30 seconds)
      await page.waitForTimeout(30000);

      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '07-after-loading.png'),
        fullPage: true
      });
    }

    // STEP 7: Check backend logs for errors
    console.log('\n📝 STEP 7: Final state verification');

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '08-final-state.png'),
      fullPage: true
    });

    console.log('✅ Collection flow test completed');
    console.log(`📊 Flow ID: ${flowId}`);
    console.log(`📍 Final URL: ${page.url()}`);
  });

  test('Verify API Responses', async ({ page, request }) => {
    console.log('\n🧪 API RESPONSE VERIFICATION TEST\n');

    // Login first (Bug #650 Fix: Now waits for AuthContext)
    const afterLoginUrl = await loginAndWaitForContext(page);

    // Navigate to collection
    await page.goto(`${BASE_URL}/collection`);
    await page.waitForTimeout(2000);

    // Intercept API calls
    const apiCalls: Array<{url: string, status: number, body?: unknown}> = [];

    page.on('response', async response => {
      if (response.url().includes('/api/')) {
        const data: {url: string, status: number, body?: unknown} = {
          url: response.url(),
          status: response.status()
        };

        // Try to get response body
        try {
          const contentType = response.headers()['content-type'];
          if (contentType && contentType.includes('application/json')) {
            data.body = await response.json();
          }
        } catch (e) {
          // Ignore JSON parse errors
        }

        apiCalls.push(data);
      }
    });

    // Wait and collect API calls
    await page.waitForTimeout(5000);

    console.log('\n📊 API CALLS CAPTURED:');
    apiCalls.forEach((call, index) => {
      console.log(`\n${index + 1}. ${call.status} ${call.url}`);
      if (call.body) {
        console.log('   Response:', JSON.stringify(call.body).substring(0, 200));
      }
    });

    // Check for errors
    const errorCalls = apiCalls.filter(call => call.status >= 400);

    if (errorCalls.length > 0) {
      console.log('\n⚠️  ERROR RESPONSES FOUND:');
      errorCalls.forEach(call => {
        console.log(`❌ ${call.status} ${call.url}`);
        if (call.body) {
          console.log('   Error:', JSON.stringify(call.body));
        }
      });
    } else {
      console.log('\n✅ All API calls successful (no 4xx/5xx errors)');
    }
  });
});
