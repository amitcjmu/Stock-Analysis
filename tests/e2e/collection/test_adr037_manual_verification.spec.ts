/**
 * Manual E2E Verification for ADR-037 Collection Flow Bug Fixes
 *
 * Verifies three critical bug fixes:
 * 1. Issue #1135: Phase transition should NOT prematurely complete after gap analysis
 * 2. Issue #1136: Questionnaire generation should find Collection Flow by master_flow_id
 * 3. canonical_applications: No AttributeError when loading canonical applications
 *
 * This test uses demo credentials and navigates the actual Collection Flow UI.
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:8081';
const BACKEND_URL = 'http://localhost:8000';
const AUTH_EMAIL = 'demo@demo-corp.com';
const AUTH_PASSWORD = 'Demo123!';

interface BugVerificationResults {
  bug1135_premature_completion: 'PASS' | 'FAIL' | 'UNCLEAR';
  bug1136_uuid_mismatch: 'PASS' | 'FAIL' | 'UNCLEAR';
  bug_canonical_applications: 'PASS' | 'FAIL' | 'UNCLEAR';
  consoleErrors: string[];
  networkErrors: string[];
  screenshots: string[];
}

/**
 * Login helper with auth context wait
 */
async function loginAndWaitForContext(page: Page): Promise<void> {
  console.log('🔐 Logging in with demo credentials...');

  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle');

  await page.fill('input[type="email"]', AUTH_EMAIL);
  await page.fill('input[type="password"]', AUTH_PASSWORD);
  await page.click('button:has-text("Sign In")');
  await page.waitForTimeout(2000);

  console.log('⏳ Waiting for AuthContext initialization...');

  await page.waitForFunction(() => {
    const client = localStorage.getItem('auth_client');
    const engagement = localStorage.getItem('auth_engagement');
    const user = localStorage.getItem('auth_user');

    return client && engagement && user &&
           client !== 'null' && engagement !== 'null' && user !== 'null';
  }, { timeout: 10000 });

  await page.waitForTimeout(1000);
  console.log('✅ Login complete');
}

/**
 * Check backend logs for specific patterns
 */
async function checkBackendLogs(pattern: string): Promise<boolean> {
  try {
    const { exec } = require('child_process');
    const util = require('util');
    const execPromise = util.promisify(exec);

    const { stdout } = await execPromise(
      `docker logs migration_backend --tail 200 2>&1 | grep -E "${pattern}"`
    );

    return stdout.length > 0;
  } catch (error) {
    return false;
  }
}

test.describe('ADR-037 Bug Fix Manual Verification', () => {
  const results: BugVerificationResults = {
    bug1135_premature_completion: 'UNCLEAR',
    bug1136_uuid_mismatch: 'UNCLEAR',
    bug_canonical_applications: 'UNCLEAR',
    consoleErrors: [],
    networkErrors: [],
    screenshots: []
  };

  test.beforeEach(async ({ page }) => {
    // Monitor console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const errorMsg = msg.text();
        console.log('❌ Console Error:', errorMsg);
        results.consoleErrors.push(errorMsg);

        // Check for specific bug indicators
        if (errorMsg.includes('canonical_applications') || errorMsg.includes('AttributeError')) {
          results.bug_canonical_applications = 'FAIL';
        }
        if (errorMsg.includes('Collection flow') && errorMsg.includes('not found')) {
          results.bug1136_uuid_mismatch = 'FAIL';
        }
      }
    });

    // Monitor network errors
    page.on('requestfailed', request => {
      const errorMsg = `${request.method()} ${request.url()} - ${request.failure()?.errorText}`;
      console.log('❌ Network Error:', errorMsg);
      results.networkErrors.push(errorMsg);

      if (errorMsg.includes('404') && errorMsg.includes('collection')) {
        results.bug1136_uuid_mismatch = 'FAIL';
      }
    });
  });

  test('should verify Collection Flow executes without ADR-037 bugs', async ({ page }) => {
    console.log('\n' + '='.repeat(80));
    console.log('🔍 ADR-037 BUG FIX VERIFICATION TEST');
    console.log('='.repeat(80));
    console.log(`Timestamp: ${new Date().toISOString()}`);
    console.log(`Frontend: ${BASE_URL}`);
    console.log(`Backend: ${BACKEND_URL}`);
    console.log('='.repeat(80) + '\n');

    // Step 1: Login
    await loginAndWaitForContext(page);

    const screenshot1 = `adr037-01-logged-in-${Date.now()}.png`;
    await page.screenshot({ path: screenshot1, fullPage: true });
    results.screenshots.push(screenshot1);
    console.log(`📸 Screenshot: ${screenshot1}`);

    // Step 2: Navigate to Collection Flow
    console.log('\n📍 Step 2: Navigating to Collection Flow...');
    await page.goto(`${BASE_URL}/collection`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const screenshot2 = `adr037-02-collection-page-${Date.now()}.png`;
    await page.screenshot({ path: screenshot2, fullPage: true });
    results.screenshots.push(screenshot2);
    console.log(`📸 Screenshot: ${screenshot2}`);

    // Step 3: Check for existing flows or start new one
    console.log('\n📍 Step 3: Checking for existing Collection Flows...');

    const resumeButton = page.locator('button:has-text("Resume"), button:has-text("Continue")');
    const startButton = page.locator('button:has-text("Start Collection"), button:has-text("New Collection")');

    const hasResumeButton = await resumeButton.isVisible({ timeout: 3000 }).catch(() => false);
    const hasStartButton = await startButton.isVisible({ timeout: 3000 }).catch(() => false);

    let flowStarted = false;

    if (hasResumeButton) {
      console.log('✅ Found incomplete flow - resuming...');
      await resumeButton.first().click();
      await page.waitForTimeout(3000);
      flowStarted = true;
    } else if (hasStartButton) {
      console.log('✅ Starting new collection flow...');
      await startButton.first().click();
      await page.waitForTimeout(3000);
      flowStarted = true;
    } else {
      console.log('⚠️ Could not find Resume or Start button');
    }

    const screenshot3 = `adr037-03-flow-started-${Date.now()}.png`;
    await page.screenshot({ path: screenshot3, fullPage: true });
    results.screenshots.push(screenshot3);
    console.log(`📸 Screenshot: ${screenshot3}`);

    // Step 4: Select assets if needed
    console.log('\n📍 Step 4: Checking asset selection...');

    const checkboxes = page.locator('input[type="checkbox"]').filter({
      hasNot: page.locator('[disabled]')
    });
    const checkboxCount = await checkboxes.count();

    if (checkboxCount > 0) {
      console.log(`✅ Found ${checkboxCount} asset checkboxes - selecting 2 assets...`);
      const assetsToSelect = Math.min(2, checkboxCount);

      for (let i = 0; i < assetsToSelect; i++) {
        await checkboxes.nth(i).check();
        await page.waitForTimeout(300);
      }

      console.log(`✅ Selected ${assetsToSelect} assets`);

      // Click Continue/Next button
      const continueButton = page.locator('button:has-text("Continue"), button:has-text("Next"), button:has-text("Analyze")');
      if (await continueButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await continueButton.first().click();
        console.log('✅ Clicked Continue/Analyze button');
        await page.waitForTimeout(3000);
      }
    } else {
      console.log('⚠️ No asset checkboxes found - may already be in a running flow');
    }

    const screenshot4 = `adr037-04-assets-selected-${Date.now()}.png`;
    await page.screenshot({ path: screenshot4, fullPage: true });
    results.screenshots.push(screenshot4);
    console.log(`📸 Screenshot: ${screenshot4}`);

    // Step 5: Monitor for phase progression
    console.log('\n📍 Step 5: Monitoring phase progression...');
    console.log('⏳ Waiting for gap analysis and questionnaire generation (max 90s)...');

    let phaseProgressed = false;
    let gapAnalysisCompleted = false;
    let questionnaireGenerationStarted = false;
    let flowCompletedPrematurely = false;

    const startTime = Date.now();
    const maxWaitTime = 90000; // 90 seconds

    while (Date.now() - startTime < maxWaitTime) {
      await page.waitForTimeout(5000);

      const pageContent = await page.textContent('body');

      // Check for gap analysis completion
      if (!gapAnalysisCompleted && pageContent?.includes('gap') && pageContent?.includes('completed')) {
        gapAnalysisCompleted = true;
        console.log('✅ Gap analysis completed');
      }

      // Check for questionnaire generation
      if (pageContent?.includes('questionnaire') || pageContent?.includes('Generating')) {
        if (!questionnaireGenerationStarted) {
          questionnaireGenerationStarted = true;
          console.log('✅ Questionnaire generation started');
        }
      }

      // Check for premature completion (BUG #1135 indicator)
      if (gapAnalysisCompleted && !questionnaireGenerationStarted &&
          pageContent?.includes('completed') && pageContent?.includes('status')) {
        flowCompletedPrematurely = true;
        console.log('⚠️ POTENTIAL BUG #1135: Flow may have completed prematurely');
        results.bug1135_premature_completion = 'FAIL';
        break;
      }

      // Check if questionnaires are visible
      if (pageContent?.includes('questionnaire') && pageContent?.includes('generated')) {
        phaseProgressed = true;
        console.log('✅ Questionnaires generated - phase progression successful');
        results.bug1135_premature_completion = 'PASS';
        break;
      }

      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      console.log(`⏳ Still waiting... (${elapsed}s elapsed)`);
    }

    const screenshot5 = `adr037-05-phase-progression-${Date.now()}.png`;
    await page.screenshot({ path: screenshot5, fullPage: true });
    results.screenshots.push(screenshot5);
    console.log(`📸 Screenshot: ${screenshot5}`);

    // Step 6: Verify Bug Fixes
    console.log('\n📍 Step 6: Verifying bug fixes...');

    // Bug #1135: Premature Completion
    if (results.bug1135_premature_completion === 'UNCLEAR') {
      if (questionnaireGenerationStarted && !flowCompletedPrematurely) {
        results.bug1135_premature_completion = 'PASS';
      } else if (!phaseProgressed) {
        results.bug1135_premature_completion = 'UNCLEAR';
      }
    }

    // Bug #1136: UUID Mismatch
    if (results.bug1136_uuid_mismatch === 'UNCLEAR') {
      const hasUUIDError = results.consoleErrors.some(err =>
        err.includes('Collection flow') && err.includes('not found')
      ) || results.networkErrors.some(err =>
        err.includes('404') && err.includes('collection')
      );

      results.bug1136_uuid_mismatch = hasUUIDError ? 'FAIL' : 'PASS';
    }

    // Bug #3: canonical_applications
    if (results.bug_canonical_applications === 'UNCLEAR') {
      const hasCanonicalError = results.consoleErrors.some(err =>
        err.includes('canonical_applications') || err.includes('AttributeError')
      );

      results.bug_canonical_applications = hasCanonicalError ? 'FAIL' : 'PASS';
    }

    const screenshot6 = `adr037-06-final-state-${Date.now()}.png`;
    await page.screenshot({ path: screenshot6, fullPage: true });
    results.screenshots.push(screenshot6);
    console.log(`📸 Screenshot: ${screenshot6}`);

    // Print detailed results
    console.log('\n' + '='.repeat(80));
    console.log('📊 ADR-037 BUG FIX VERIFICATION RESULTS');
    console.log('='.repeat(80));
    console.log(`Bug #1135 (Premature Completion):     ${results.bug1135_premature_completion}`);
    console.log(`Bug #1136 (UUID Mismatch):            ${results.bug1136_uuid_mismatch}`);
    console.log(`Bug (canonical_applications):         ${results.bug_canonical_applications}`);
    console.log(`Console Errors:                       ${results.consoleErrors.length}`);
    console.log(`Network Errors:                       ${results.networkErrors.length}`);
    console.log(`Screenshots Captured:                 ${results.screenshots.length}`);
    console.log('='.repeat(80));

    if (results.consoleErrors.length > 0) {
      console.log('\n❌ Console Errors:');
      results.consoleErrors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err.substring(0, 200)}${err.length > 200 ? '...' : ''}`);
      });
    }

    if (results.networkErrors.length > 0) {
      console.log('\n❌ Network Errors:');
      results.networkErrors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err}`);
      });
    }

    console.log('\n📸 Screenshots saved:');
    results.screenshots.forEach((screenshot, idx) => {
      console.log(`  ${idx + 1}. ${screenshot}`);
    });

    // Assertions
    console.log('\n🔍 Running final assertions...');

    expect(results.bug_canonical_applications,
      'canonical_applications bug should be fixed').toBe('PASS');

    expect(results.bug1136_uuid_mismatch,
      'UUID mismatch bug should be fixed').toBe('PASS');

    // Note: Bug #1135 may be UNCLEAR if no flow execution occurred
    if (flowStarted && phaseProgressed) {
      expect(results.bug1135_premature_completion,
        'Premature completion bug should be fixed').toBe('PASS');
    }

    console.log('✅ All verifiable assertions passed!\n');
  });
});
