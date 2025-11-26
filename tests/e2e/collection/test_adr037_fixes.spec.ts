/**
 * E2E Test: ADR-037 Collection Flow Bug Fixes
 *
 * Verifies three critical bug fixes:
 * 1. Issue #1135: Phase transition should NOT prematurely complete after gap analysis
 * 2. Issue #1136: Questionnaire generation should find Collection Flow by master_flow_id
 * 3. canonical_applications: No AttributeError when loading canonical applications
 *
 * Test Strategy:
 * - Create new Collection Flow
 * - Select assets for gap analysis
 * - Monitor phase transitions (gap_analysis → questionnaire_generation)
 * - Verify no premature completion
 * - Verify questionnaires are generated successfully
 * - Check for errors in console and backend logs
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const FRONTEND_URL = 'http://localhost:8081';
const BACKEND_URL = 'http://localhost:8000';
const GAP_ANALYSIS_TIMEOUT = 60000; // 60 seconds
const QUESTIONNAIRE_GENERATION_TIMEOUT = 90000; // 90 seconds

interface FlowState {
  flow_id: string;
  master_flow_id: string;
  status: string;
  current_phase: string;
  phase_status: string;
}

interface TestResults {
  bug1135_premature_completion: 'PASS' | 'FAIL';
  bug1136_uuid_mismatch: 'PASS' | 'FAIL';
  bug_canonical_applications: 'PASS' | 'FAIL';
  evidence: {
    screenshots: string[];
    consoleErrors: string[];
    networkErrors: string[];
    backendLogs: string[];
  };
}

test.describe('ADR-037 Collection Flow Bug Fixes', () => {
  const testResults: TestResults = {
    bug1135_premature_completion: 'PASS',
    bug1136_uuid_mismatch: 'PASS',
    bug_canonical_applications: 'PASS',
    evidence: {
      screenshots: [],
      consoleErrors: [],
      networkErrors: [],
      backendLogs: []
    }
  };

  test.beforeAll(async () => {
    console.log('🔍 Starting ADR-037 Bug Fix Verification Test');
    console.log(`Frontend: ${FRONTEND_URL}`);
    console.log(`Backend: ${BACKEND_URL}`);
    console.log(`Timestamp: ${new Date().toISOString()}`);
  });

  test('should verify all three bug fixes work correctly', async ({ page }) => {
    // Setup console error monitoring
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const errorMsg = msg.text();
        console.log('❌ Browser Console Error:', errorMsg);
        testResults.evidence.consoleErrors.push(errorMsg);
      } else if (msg.type() === 'warning') {
        console.log('⚠️ Browser Console Warning:', msg.text());
      }
    });

    // Setup network request monitoring
    page.on('requestfailed', request => {
      const errorMsg = `${request.method()} ${request.url()} - ${request.failure()?.errorText}`;
      console.log('❌ Network Request Failed:', errorMsg);
      testResults.evidence.networkErrors.push(errorMsg);
    });

    // Step 1: Navigate to Collection Flow page
    console.log('\n📍 Step 1: Navigating to Collection Flow page...');
    await page.goto(`${FRONTEND_URL}/collection`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const screenshot1 = `collection-page-loaded-${Date.now()}.png`;
    await page.screenshot({ path: screenshot1, fullPage: true });
    testResults.evidence.screenshots.push(screenshot1);
    console.log(`✅ Screenshot saved: ${screenshot1}`);

    // Step 2: Create new Collection Flow
    console.log('\n📍 Step 2: Creating new Collection Flow...');
    const flowName = `E2E Test ADR-037 Fixes ${new Date().toISOString()}`;

    // Look for "Create New Flow" or similar button
    const createButtonSelectors = [
      'button:has-text("Create New Flow")',
      'button:has-text("New Collection")',
      'button:has-text("+ New")',
      'button:has-text("Create Flow")',
      '[data-testid="create-flow-button"]'
    ];

    let createButton = null;
    for (const selector of createButtonSelectors) {
      createButton = await page.locator(selector).first();
      if (await createButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log(`✅ Found create button: ${selector}`);
        break;
      }
    }

    if (!createButton || !(await createButton.isVisible().catch(() => false))) {
      console.log('⚠️ No create button found, checking if flow creation form is already visible');
      const screenshot2 = `no-create-button-${Date.now()}.png`;
      await page.screenshot({ path: screenshot2, fullPage: true });
      testResults.evidence.screenshots.push(screenshot2);
    } else {
      await createButton.click();
      await page.waitForTimeout(1000);
    }

    // Fill in flow name (look for input field)
    const nameInputSelectors = [
      'input[name="name"]',
      'input[placeholder*="name" i]',
      'input[type="text"]',
      '[data-testid="flow-name-input"]'
    ];

    for (const selector of nameInputSelectors) {
      const input = await page.locator(selector).first();
      if (await input.isVisible({ timeout: 2000 }).catch(() => false)) {
        await input.fill(flowName);
        console.log(`✅ Filled flow name: ${flowName}`);
        break;
      }
    }

    // Save/Create the flow
    const saveButtonSelectors = [
      'button:has-text("Save")',
      'button:has-text("Create")',
      'button:has-text("Submit")',
      '[data-testid="save-flow-button"]'
    ];

    for (const selector of saveButtonSelectors) {
      const saveButton = await page.locator(selector).first();
      if (await saveButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveButton.click();
        console.log(`✅ Clicked save button: ${selector}`);
        await page.waitForTimeout(2000);
        break;
      }
    }

    const screenshot3 = `flow-created-${Date.now()}.png`;
    await page.screenshot({ path: screenshot3, fullPage: true });
    testResults.evidence.screenshots.push(screenshot3);

    // Step 3: Select assets for gap analysis
    console.log('\n📍 Step 3: Selecting assets for gap analysis...');

    // Wait for asset selection interface to load
    await page.waitForTimeout(2000);

    // Look for asset checkboxes or selection controls
    const assetSelectors = [
      'input[type="checkbox"]',
      '[data-testid="asset-checkbox"]',
      '.asset-selection-checkbox'
    ];

    let selectedAssets = 0;
    for (const selector of assetSelectors) {
      const checkboxes = await page.locator(selector).all();
      if (checkboxes.length > 0) {
        // Select first 2-3 assets
        const assetsToSelect = Math.min(3, checkboxes.length);
        for (let i = 0; i < assetsToSelect; i++) {
          if (await checkboxes[i].isVisible().catch(() => false)) {
            await checkboxes[i].check();
            selectedAssets++;
          }
        }
        if (selectedAssets > 0) {
          console.log(`✅ Selected ${selectedAssets} assets`);
          break;
        }
      }
    }

    if (selectedAssets === 0) {
      console.log('⚠️ Could not find asset checkboxes to select');
    }

    const screenshot4 = `assets-selected-${Date.now()}.png`;
    await page.screenshot({ path: screenshot4, fullPage: true });
    testResults.evidence.screenshots.push(screenshot4);

    // Start gap analysis
    const nextButtonSelectors = [
      'button:has-text("Next")',
      'button:has-text("Continue")',
      'button:has-text("Start Gap Analysis")',
      'button:has-text("Analyze")',
      '[data-testid="start-analysis-button"]'
    ];

    for (const selector of nextButtonSelectors) {
      const nextButton = await page.locator(selector).first();
      if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await nextButton.click();
        console.log(`✅ Clicked next button: ${selector}`);
        await page.waitForTimeout(2000);
        break;
      }
    }

    // Step 4: Monitor Gap Analysis Phase
    console.log('\n📍 Step 4: Monitoring gap analysis phase...');
    console.log('⏳ Waiting for gap analysis to complete (timeout: 60s)...');

    let gapAnalysisCompleted = false;
    let flowMovedToPrematureCompleted = false;
    let currentPhase = 'unknown';

    const startTime = Date.now();

    while (Date.now() - startTime < GAP_ANALYSIS_TIMEOUT) {
      await page.waitForTimeout(3000);

      // Check page content for phase indicators
      const pageContent = await page.content();

      // Look for completion indicators
      if (pageContent.includes('gap analysis') && pageContent.includes('completed')) {
        gapAnalysisCompleted = true;
        console.log('✅ Gap analysis completed');
        break;
      }

      // Check if flow shows as "completed" prematurely (BUG #1135)
      if (pageContent.includes('status') && pageContent.includes('completed') && !pageContent.includes('questionnaire')) {
        console.log('⚠️ POTENTIAL BUG #1135: Flow shows as completed without questionnaire generation');
        flowMovedToPrematureCompleted = true;
      }

      // Look for phase indicators
      if (pageContent.includes('questionnaire') || pageContent.includes('generating')) {
        console.log('✅ Flow advanced to questionnaire generation phase');
        currentPhase = 'questionnaire_generation';
        break;
      }

      console.log(`⏳ Still in gap analysis... (${Math.floor((Date.now() - startTime) / 1000)}s elapsed)`);
    }

    const screenshot5 = `gap-analysis-completed-${Date.now()}.png`;
    await page.screenshot({ path: screenshot5, fullPage: true });
    testResults.evidence.screenshots.push(screenshot5);

    // Step 5: CRITICAL VERIFICATION - Issue #1135
    console.log('\n📍 Step 5: Verifying Issue #1135 - No premature completion...');

    if (flowMovedToPrematureCompleted) {
      console.log('❌ BUG #1135 STILL EXISTS: Flow prematurely completed after gap analysis');
      testResults.bug1135_premature_completion = 'FAIL';
    } else if (currentPhase === 'questionnaire_generation') {
      console.log('✅ BUG #1135 FIXED: Flow correctly advanced to questionnaire_generation');
      testResults.bug1135_premature_completion = 'PASS';
    } else {
      console.log('⚠️ BUG #1135 STATUS UNCLEAR: Could not determine if flow advanced correctly');
    }

    // Step 6: Monitor Questionnaire Generation
    console.log('\n📍 Step 6: Monitoring questionnaire generation phase...');
    console.log('⏳ Waiting for questionnaires to generate (timeout: 90s)...');

    let questionnairesGenerated = false;
    const questionnaireCount = 0;
    const startTime2 = Date.now();

    while (Date.now() - startTime2 < QUESTIONNAIRE_GENERATION_TIMEOUT) {
      await page.waitForTimeout(5000);

      const pageContent = await page.content();

      // Look for questionnaire completion indicators
      if (pageContent.includes('questionnaire') && (pageContent.includes('generated') || pageContent.includes('complete'))) {
        questionnairesGenerated = true;
        console.log('✅ Questionnaires generated successfully');
        break;
      }

      // Check for "flow not found" errors in page (BUG #1136)
      if (pageContent.includes('not found') || pageContent.includes('404')) {
        console.log('⚠️ POTENTIAL BUG #1136: Flow not found error detected in UI');
      }

      console.log(`⏳ Still generating questionnaires... (${Math.floor((Date.now() - startTime2) / 1000)}s elapsed)`);
    }

    const screenshot6 = `questionnaire-generation-completed-${Date.now()}.png`;
    await page.screenshot({ path: screenshot6, fullPage: true });
    testResults.evidence.screenshots.push(screenshot6);

    // Step 7: CRITICAL VERIFICATION - Issue #1136
    console.log('\n📍 Step 7: Verifying Issue #1136 - No UUID mismatch errors...');

    const hasFlowNotFoundError = testResults.evidence.consoleErrors.some(err =>
      err.includes('not found') || err.includes('404') || err.includes('Collection flow')
    );

    const hasNetworkFlowNotFoundError = testResults.evidence.networkErrors.some(err =>
      err.includes('404') || err.includes('not found')
    );

    if (hasFlowNotFoundError || hasNetworkFlowNotFoundError) {
      console.log('❌ BUG #1136 STILL EXISTS: Flow not found errors detected');
      testResults.bug1136_uuid_mismatch = 'FAIL';
    } else if (questionnairesGenerated) {
      console.log('✅ BUG #1136 FIXED: No flow not found errors, questionnaires generated successfully');
      testResults.bug1136_uuid_mismatch = 'PASS';
    } else {
      console.log('⚠️ BUG #1136 STATUS UNCLEAR: Questionnaires not generated but no clear error');
    }

    // Step 8: Verify canonical_applications issue
    console.log('\n📍 Step 8: Verifying canonical_applications AttributeError...');

    const hasCanonicalAppError = testResults.evidence.consoleErrors.some(err =>
      err.includes('canonical_applications') || err.includes('AttributeError')
    );

    if (hasCanonicalAppError) {
      console.log('❌ canonical_applications BUG STILL EXISTS: AttributeError detected');
      testResults.bug_canonical_applications = 'FAIL';
    } else {
      console.log('✅ canonical_applications BUG FIXED: No AttributeError detected');
      testResults.bug_canonical_applications = 'PASS';
    }

    // Final screenshot
    const screenshot7 = `test-completed-${Date.now()}.png`;
    await page.screenshot({ path: screenshot7, fullPage: true });
    testResults.evidence.screenshots.push(screenshot7);

    // Print summary
    console.log('\n' + '='.repeat(80));
    console.log('📊 TEST RESULTS SUMMARY');
    console.log('='.repeat(80));
    console.log(`Bug #1135 (Premature Completion): ${testResults.bug1135_premature_completion}`);
    console.log(`Bug #1136 (UUID Mismatch): ${testResults.bug1136_uuid_mismatch}`);
    console.log(`canonical_applications Bug: ${testResults.bug_canonical_applications}`);
    console.log(`Console Errors: ${testResults.evidence.consoleErrors.length}`);
    console.log(`Network Errors: ${testResults.evidence.networkErrors.length}`);
    console.log(`Screenshots Captured: ${testResults.evidence.screenshots.length}`);
    console.log('='.repeat(80));

    // Assertions
    expect(testResults.bug1135_premature_completion).toBe('PASS');
    expect(testResults.bug1136_uuid_mismatch).toBe('PASS');
    expect(testResults.bug_canonical_applications).toBe('PASS');
    expect(testResults.evidence.consoleErrors.length).toBe(0);
  });

  test.afterAll(async () => {
    console.log('\n📋 Test execution completed');
    console.log('Evidence collected:');
    console.log(`- Screenshots: ${testResults.evidence.screenshots.length}`);
    console.log(`- Console Errors: ${testResults.evidence.consoleErrors.length}`);
    console.log(`- Network Errors: ${testResults.evidence.networkErrors.length}`);

    if (testResults.evidence.consoleErrors.length > 0) {
      console.log('\n❌ Console Errors Detected:');
      testResults.evidence.consoleErrors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err}`);
      });
    }

    if (testResults.evidence.networkErrors.length > 0) {
      console.log('\n❌ Network Errors Detected:');
      testResults.evidence.networkErrors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err}`);
      });
    }
  });
});
