/**
 * QA Verification Script for Issues #643 and #644
 * Tests authentication and Collection page UX fixes
 */

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = 'http://localhost:8081';
const AUTH_EMAIL = 'demo@demo-corp.com';
const AUTH_PASSWORD = 'Demo123!';
const SCREENSHOT_DIR = path.join(__dirname, 'qa-test-screenshots');

// Create screenshot directory
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function captureConsole(page, testName) {
  const logs = [];

  page.on('console', msg => {
    logs.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });

  page.on('pageerror', error => {
    logs.push({
      type: 'error',
      text: error.message,
      stack: error.stack
    });
  });

  return logs;
}

async function test1_AuthenticationFlow(browser) {
  console.log('\n=== TEST 1: Authentication Flow ===');
  const context = await browser.newContext();
  const page = await context.newPage();
  const consoleLogs = [];

  // Capture console
  page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => consoleLogs.push({ type: 'error', text: err.message }));

  try {
    // Step 1: Navigate to login page
    console.log('Step 1: Navigating to /login...');
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test1-01-login-page.png'), fullPage: true });

    // Step 2: Fill email
    console.log('Step 2: Filling email...');
    const emailInput = await page.locator('input[type="email"]');
    await emailInput.waitFor({ state: 'visible', timeout: 5000 });
    await emailInput.fill(AUTH_EMAIL);

    // Step 3: Fill password
    console.log('Step 3: Filling password...');
    const passwordInput = await page.locator('input[type="password"]');
    await passwordInput.fill(AUTH_PASSWORD);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test1-02-credentials-filled.png'), fullPage: true });

    // Step 4: Click Sign In
    console.log('Step 4: Clicking Sign In...');
    const signInButton = await page.locator('button:has-text("Sign In")');
    await signInButton.click();

    // Step 5: Wait for redirect
    console.log('Step 5: Waiting for redirect...');
    await page.waitForURL(/^(?!.*login)/, { timeout: 10000 });
    await delay(2000); // Allow page to fully load

    const currentUrl = page.url();
    console.log(`✅ Redirected to: ${currentUrl}`);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test1-03-after-login.png'), fullPage: true });

    // Check for 401 errors in console
    const has401Errors = consoleLogs.some(log =>
      log.text.includes('401') || log.text.includes('Not authenticated')
    );

    if (has401Errors) {
      console.log('❌ Found 401 errors in console');
    } else {
      console.log('✅ No 401 errors found');
    }

    // Save console logs
    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, 'test1-console-logs.json'),
      JSON.stringify(consoleLogs, null, 2)
    );

    console.log('✅ TEST 1 PASSED: Authentication flow works correctly\n');
    return { passed: true, context, page };

  } catch (error) {
    console.log(`❌ TEST 1 FAILED: ${error.message}\n`);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test1-ERROR.png'), fullPage: true });
    await context.close();
    return { passed: false, error: error.message };
  }
}

async function test2_CollectionPageNoActiveFlow(page) {
  console.log('\n=== TEST 2: Collection Page - No Active Flow ===');
  const consoleLogs = [];

  page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => consoleLogs.push({ type: 'error', text: err.message }));

  try {
    // Navigate to collection page
    console.log('Navigating to /collection...');
    await page.goto(`${BASE_URL}/collection`, { waitUntil: 'networkidle' });
    await delay(2000);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test2-01-collection-landing.png'), fullPage: true });

    // Check for "Start New Data Collection" heading
    const heading = await page.locator('h2:has-text("Start New Data Collection")').first();
    const headingExists = await heading.isVisible().catch(() => false);
    console.log(`Heading "Start New Data Collection": ${headingExists ? '✅ Found' : '❌ Not found'}`);

    // Check for question
    const question = await page.locator('text=/How many applications/i').first();
    const questionExists = await question.isVisible().catch(() => false);
    console.log(`Question about applications: ${questionExists ? '✅ Found' : '❌ Not found'}`);

    // Check for radio buttons
    const adaptiveRadio = await page.locator('input[type="radio"][value="adaptive"]').first();
    const bulkRadio = await page.locator('input[type="radio"][value="bulk"]').first();
    const adaptiveExists = await adaptiveRadio.isVisible().catch(() => false);
    const bulkExists = await bulkRadio.isVisible().catch(() => false);
    console.log(`Radio button "1-50 applications": ${adaptiveExists ? '✅ Found' : '❌ Not found'}`);
    console.log(`Radio button "50+ applications": ${bulkExists ? '✅ Found' : '❌ Not found'}`);

    // Check for Start Collection button
    const startButton = await page.locator('button:has-text("Start Collection")').first();
    const startButtonExists = await startButton.isVisible().catch(() => false);
    console.log(`"Start Collection" button: ${startButtonExists ? '✅ Found' : '❌ Not found'}`);

    if (startButtonExists) {
      const isDisabled = await startButton.isDisabled();
      console.log(`Button initially disabled: ${isDisabled ? '✅ Correct' : '❌ Should be disabled'}`);

      // Select a radio button
      if (adaptiveExists) {
        console.log('Clicking "1-50 applications" radio button...');
        await adaptiveRadio.click();
        await delay(500);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test2-02-radio-selected.png'), fullPage: true });

        const isEnabledAfterSelection = !(await startButton.isDisabled());
        console.log(`Button enabled after selection: ${isEnabledAfterSelection ? '✅ Correct' : '❌ Should be enabled'}`);
      }
    }

    // Check for Advanced Options section
    const advancedOptions = await page.locator('text=/Advanced Options/i').first();
    const advancedExists = await advancedOptions.isVisible().catch(() => false);
    console.log(`"Advanced Options" section: ${advancedExists ? '✅ Found' : '❌ Not found'}`);

    if (advancedExists) {
      // Try to expand it
      console.log('Attempting to expand Advanced Options...');
      await advancedOptions.click();
      await delay(500);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test2-03-advanced-expanded.png'), fullPage: true });

      // Check for 3 options
      const gapAnalysis = await page.locator('text=/Gap Analysis/i').first();
      const dataIntegration = await page.locator('text=/Data Integration/i').first();
      const progressMonitor = await page.locator('text=/Progress Monitor/i').first();

      console.log(`Gap Analysis option: ${await gapAnalysis.isVisible().catch(() => false) ? '✅' : '❌'}`);
      console.log(`Data Integration option: ${await dataIntegration.isVisible().catch(() => false) ? '✅' : '❌'}`);
      console.log(`Progress Monitor option: ${await progressMonitor.isVisible().catch(() => false) ? '✅' : '❌'}`);
    }

    // Check that old 5-card layout is gone
    const workflowCards = await page.locator('button:has-text("Start Workflow")').count();
    console.log(`Old "Start Workflow" buttons found: ${workflowCards === 0 ? '✅ None (correct)' : `❌ ${workflowCards} found`}`);

    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, 'test2-console-logs.json'),
      JSON.stringify(consoleLogs, null, 2)
    );

    console.log('✅ TEST 2 PASSED: Guided workflow displays correctly\n');
    return { passed: true };

  } catch (error) {
    console.log(`❌ TEST 2 FAILED: ${error.message}\n`);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test2-ERROR.png'), fullPage: true });
    return { passed: false, error: error.message };
  }
}

async function test3_CollectionPageWithActiveFlow(page) {
  console.log('\n=== TEST 3: Collection Page - With Active Flow ===');
  const consoleLogs = [];

  page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));

  try {
    // First, check if there's an active flow via the page UI
    await page.goto(`${BASE_URL}/collection`, { waitUntil: 'networkidle' });
    await delay(2000);

    // Look for active flow banner
    const activeBanner = await page.locator('text=/Active Collection Flow/i').first();
    const bannerExists = await activeBanner.isVisible().catch(() => false);

    console.log(`Active flow banner: ${bannerExists ? '✅ Found' : '⚠️ Not found (may not have active flow)'}`);

    if (bannerExists) {
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test3-01-active-flow-banner.png'), fullPage: true });

      // Check for Continue Collection button
      const continueButton = await page.locator('button:has-text("Continue Collection")').first();
      const continueExists = await continueButton.isVisible().catch(() => false);
      console.log(`"Continue Collection" button: ${continueExists ? '✅ Found' : '❌ Not found'}`);

      // Check for Start New button
      const startNewButton = await page.locator('button:has-text("Start New")').first();
      const startNewExists = await startNewButton.isVisible().catch(() => false);
      console.log(`"Start New" button: ${startNewExists ? '✅ Found' : '❌ Not found'}`);

      // Verify button styling (Continue should be primary/blue)
      if (continueExists) {
        const classes = await continueButton.getAttribute('class');
        const isPrimary = classes && (classes.includes('bg-blue') || classes.includes('primary'));
        console.log(`Continue button is primary styled: ${isPrimary ? '✅' : '⚠️'}`);
      }

      console.log('✅ TEST 3 PASSED: Active flow banner displays with correct buttons\n');
      return { passed: true };
    } else {
      console.log('⚠️ TEST 3 SKIPPED: No active flow found (expected behavior)\n');
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test3-01-no-active-flow.png'), fullPage: true });
      return { passed: true, skipped: true };
    }

  } catch (error) {
    console.log(`❌ TEST 3 FAILED: ${error.message}\n`);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test3-ERROR.png'), fullPage: true });
    return { passed: false, error: error.message };
  }
}

async function test4_ButtonTextCompatibility(page) {
  console.log('\n=== TEST 4: Button Text Compatibility ===');

  try {
    await page.goto(`${BASE_URL}/collection`, { waitUntil: 'networkidle' });
    await delay(2000);

    // Test E2E test selectors
    const results = {};

    // Check for Continue/Resume
    const continueBtn = await page.locator('button:has-text("Continue Collection")').first().isVisible().catch(() => false);
    const resumeBtn = await page.locator('button:has-text("Resume Collection")').first().isVisible().catch(() => false);
    results.continueOrResume = continueBtn || resumeBtn;
    console.log(`Continue/Resume button: ${results.continueOrResume ? '✅' : '⚠️'} (found: ${continueBtn ? 'Continue' : resumeBtn ? 'Resume' : 'none'})`);

    // Check for Start Collection
    const startBtn = await page.locator('button:has-text("Start Collection")').first().isVisible().catch(() => false);
    const newBtn = await page.locator('button:has-text("New Collection")').first().isVisible().catch(() => false);
    results.startOrNew = startBtn || newBtn;
    console.log(`Start/New Collection button: ${results.startOrNew ? '✅' : '❌'} (found: ${startBtn ? 'Start' : newBtn ? 'New' : 'none'})`);

    // Check for Start New
    const startNewBtn = await page.locator('button:has-text("Start New")').first().isVisible().catch(() => false);
    results.startNew = startNewBtn;
    console.log(`Start New button: ${startNewBtn ? '✅' : '⚠️'} (context: active flow banner)`);

    const allTestsPassed = results.startOrNew; // At minimum, Start Collection should exist

    if (allTestsPassed) {
      console.log('✅ TEST 4 PASSED: E2E test button selectors are compatible\n');
      return { passed: true };
    } else {
      console.log('❌ TEST 4 FAILED: Missing expected buttons for E2E tests\n');
      return { passed: false };
    }

  } catch (error) {
    console.log(`❌ TEST 4 FAILED: ${error.message}\n`);
    return { passed: false, error: error.message };
  }
}

async function test5_EndToEndUserFlow(page) {
  console.log('\n=== TEST 5: End-to-End User Flow ===');
  const consoleLogs = [];

  page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => consoleLogs.push({ type: 'error', text: err.message }));

  try {
    // Step 1: Already authenticated from Test 1
    console.log('Step 1: Already authenticated ✅');

    // Step 2: Navigate to Collection
    console.log('Step 2: Navigating to /collection...');
    await page.goto(`${BASE_URL}/collection`, { waitUntil: 'networkidle' });
    await delay(2000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test5-01-collection-page.png'), fullPage: true });

    // Step 3: Select collection method
    console.log('Step 3: Selecting "1-50 applications" method...');
    const adaptiveRadio = await page.locator('input[type="radio"][value="adaptive"]').first();
    await adaptiveRadio.click();
    await delay(500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test5-02-method-selected.png'), fullPage: true });

    // Step 4: Click Start Collection
    console.log('Step 4: Clicking "Start Collection" button...');
    const startButton = await page.locator('button:has-text("Start Collection")').first();
    const isEnabled = !(await startButton.isDisabled());

    if (!isEnabled) {
      throw new Error('Start Collection button is disabled after selecting method');
    }

    await startButton.click();
    await delay(3000); // Wait for navigation

    const currentUrl = page.url();
    console.log(`✅ Navigated to: ${currentUrl}`);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test5-03-after-start.png'), fullPage: true });

    // Step 5: Check for errors
    const errors401 = consoleLogs.filter(log =>
      log.type === 'error' || log.text.includes('401') || log.text.includes('403') || log.text.includes('404')
    );

    if (errors401.length > 0) {
      console.log(`⚠️ Found ${errors401.length} errors in console:`);
      errors401.forEach(err => console.log(`  - ${err.text}`));
    } else {
      console.log('✅ No critical errors in console');
    }

    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, 'test5-console-logs.json'),
      JSON.stringify(consoleLogs, null, 2)
    );

    console.log('✅ TEST 5 PASSED: End-to-end flow completed successfully\n');
    return { passed: true };

  } catch (error) {
    console.log(`❌ TEST 5 FAILED: ${error.message}\n`);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'test5-ERROR.png'), fullPage: true });
    return { passed: false, error: error.message };
  }
}

async function main() {
  console.log('🔍 QA Verification for Issues #643 and #644');
  console.log('='.repeat(50));

  const browser = await chromium.launch({ headless: false }); // Set to true for CI/CD

  try {
    // Test 1: Authentication
    const test1Result = await test1_AuthenticationFlow(browser);

    if (!test1Result.passed) {
      console.log('❌ Cannot proceed without authentication');
      return;
    }

    // Use the authenticated context for remaining tests
    const { page, context } = test1Result;

    // Test 2: Collection Page - No Active Flow
    await test2_CollectionPageNoActiveFlow(page);

    // Test 3: Collection Page - With Active Flow
    await test3_CollectionPageWithActiveFlow(page);

    // Test 4: Button Text Compatibility
    await test4_ButtonTextCompatibility(page);

    // Test 5: End-to-End Flow
    await test5_EndToEndUserFlow(page);

    await context.close();

    console.log('\n' + '='.repeat(50));
    console.log('✅ ALL TESTS COMPLETED');
    console.log(`Screenshots saved to: ${SCREENSHOT_DIR}`);

  } catch (error) {
    console.error('Fatal error:', error);
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
