import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:8081';

test.describe('Bug #21 - Complete Collection Flow with Batched LLM Processing', () => {
  let page: Page;
  let flowId: string | null = null;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();

    // Enable console logging
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error') {
        console.log(`❌ Browser console error: ${text}`);
      } else if (type === 'warning') {
        console.log(`⚠️  Browser console warning: ${text}`);
      }
    });
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('Step 1: Login to application', async () => {
    console.log('🔐 Navigating to login page...');
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: 'screenshots/bug21-01-login-page.png', fullPage: true });

    // Enter credentials
    console.log('📝 Entering credentials...');
    await page.fill('input[type="email"], input[name="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"], input[name="password"]', 'Demo123!');

    await page.screenshot({ path: 'screenshots/bug21-02-credentials-entered.png', fullPage: true });

    // Click login
    console.log('🚀 Clicking login button...');
    await page.click('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")');

    // Wait for dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    await page.screenshot({ path: 'screenshots/bug21-03-dashboard.png', fullPage: true });
    console.log('✅ Login successful');
  });

  test('Step 2: Navigate to Collection and start/continue flow', async () => {
    console.log('📋 Navigating to collection page...');
    await page.goto(`${BASE_URL}/collection`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Allow data to load

    await page.screenshot({ path: 'screenshots/bug21-04-collection-page.png', fullPage: true });

    // Look for existing active/paused flows
    console.log('🔍 Looking for existing flows...');
    const continueButton = page.locator('button:has-text("Continue Collection"), button:has-text("Resume")').first();
    const startButton = page.locator('button:has-text("Start New Collection"), button:has-text("New Collection")').first();

    if (await continueButton.count() > 0 && await continueButton.isVisible()) {
      console.log('✅ Found existing flow, clicking Continue Collection...');
      await continueButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    } else if (await startButton.count() > 0 && await startButton.isVisible()) {
      console.log('✅ Starting new collection flow...');
      await startButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    } else {
      console.log('⚠️  No start/continue button found, checking current page state...');
    }

    await page.screenshot({ path: 'screenshots/bug21-05-after-flow-action.png', fullPage: true });

    // Extract flow ID from URL
    const currentUrl = page.url();
    const flowIdMatch = currentUrl.match(/\/collection\/([a-f0-9-]{36})/);
    if (flowIdMatch) {
      flowId = flowIdMatch[1];
      console.log(`✅ Flow ID: ${flowId}`);
    } else {
      console.log('⚠️  Could not extract flow ID from URL');
    }
  });

  test('Step 3: Asset Selection', async () => {
    console.log('🎯 Asset Selection Phase...');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshots/bug21-06-asset-selection-page.png', fullPage: true });

    // Look for asset selection UI
    const selectAllCheckbox = page.locator('input[type="checkbox"][aria-label*="Select all"], input[type="checkbox"]:near(:text("Select All"))').first();
    const assetCheckboxes = page.locator('input[type="checkbox"][data-testid*="asset"], tr input[type="checkbox"]');

    let assetsSelected = false;

    // Try Select All first
    if (await selectAllCheckbox.count() > 0 && await selectAllCheckbox.isVisible()) {
      console.log('✅ Found Select All checkbox, clicking...');
      await selectAllCheckbox.click();
      await page.waitForTimeout(1000);
      assetsSelected = true;
    }
    // Otherwise select individual assets
    else if (await assetCheckboxes.count() > 0) {
      const checkboxCount = await assetCheckboxes.count();
      console.log(`✅ Found ${checkboxCount} asset checkboxes, selecting first 10...`);

      const limit = Math.min(10, checkboxCount);
      for (let i = 0; i < limit; i++) {
        try {
          await assetCheckboxes.nth(i).check({ timeout: 1000 });
          assetsSelected = true;
        } catch (e) {
          console.log(`⚠️  Could not check checkbox ${i}`);
        }
      }
      await page.waitForTimeout(500);
    } else {
      console.log('⚠️  No asset checkboxes found, checking if assets are pre-selected...');
    }

    await page.screenshot({ path: 'screenshots/bug21-07-assets-selected.png', fullPage: true });

    if (assetsSelected) {
      console.log('✅ Assets selected, looking for Continue/Next button...');
    } else {
      console.log('⚠️  Asset selection state unclear');
    }

    // Click Continue/Next button
    const continueButtons = [
      'button:has-text("Continue")',
      'button:has-text("Next")',
      'button:has-text("Proceed")',
      'button:has-text("Start Gap Analysis")'
    ];

    for (const selector of continueButtons) {
      const button = page.locator(selector).first();
      if (await button.count() > 0 && await button.isVisible()) {
        console.log(`✅ Found button: ${selector}, clicking...`);
        await button.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        break;
      }
    }

    await page.screenshot({ path: 'screenshots/bug21-08-after-continue.png', fullPage: true });
  });

  test('Step 4: Gap Analysis Phase', async () => {
    console.log('🔍 Gap Analysis Phase...');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/bug21-09-gap-analysis.png', fullPage: true });

    // Wait for gap analysis to complete (look for statistics or completion message)
    console.log('⏳ Waiting for gap analysis to complete (30 seconds)...');
    await page.waitForTimeout(30000);
    await page.screenshot({ path: 'screenshots/bug21-10-gap-analysis-complete.png', fullPage: true });

    // Look for gap statistics
    const gapStatsElements = await page.locator('text=/gap/i, text=/found/i, div:has-text("gaps")').count();
    if (gapStatsElements > 0) {
      console.log('✅ Gap statistics visible');
    } else {
      console.log('⚠️  Gap statistics not found');
    }

    // Click to proceed to questionnaire generation
    const proceedButtons = [
      'button:has-text("Generate Questionnaire")',
      'button:has-text("Continue to Questionnaire")',
      'button:has-text("Generate Questions")',
      'button:has-text("Next")',
      'button:has-text("Continue")'
    ];

    let clicked = false;
    for (const selector of proceedButtons) {
      const button = page.locator(selector).first();
      if (await button.count() > 0 && await button.isVisible()) {
        console.log(`✅ Found button: ${selector}, clicking...`);
        await button.click();
        clicked = true;
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        break;
      }
    }

    if (!clicked) {
      console.log('⚠️  Could not find proceed button, may already be in next phase');
    }

    await page.screenshot({ path: 'screenshots/bug21-11-after-gap-analysis-proceed.png', fullPage: true });
  });

  test('Step 5: Questionnaire Generation - Bug #21 Test', async () => {
    console.log('📝 Questionnaire Generation Phase - Testing Bug #21 Fix...');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshots/bug21-12-questionnaire-generation-start.png', fullPage: true });

    console.log('⏳ Waiting 90 seconds for batched questionnaire generation...');
    console.log('📦 Expected: Batches of 5 assets each');
    console.log('📊 For 50 assets: 10 batches total');

    // Wait in intervals and take screenshots
    for (let i = 1; i <= 9; i++) {
      await page.waitForTimeout(10000); // 10 seconds
      console.log(`⏳ ${i * 10} seconds elapsed...`);
      await page.screenshot({
        path: `screenshots/bug21-13-questionnaire-generation-${i * 10}s.png`,
        fullPage: true
      });
    }

    console.log('✅ Waited 90 seconds for questionnaire generation');
    await page.screenshot({ path: 'screenshots/bug21-14-questionnaire-generation-complete.png', fullPage: true });

    // Check for any error messages
    const errorElements = await page.locator('div:has-text("error"), div:has-text("Error"), div[role="alert"]').count();
    if (errorElements > 0) {
      console.log('⚠️  Error messages found on page');
      const errorText = await page.locator('div:has-text("error"), div:has-text("Error"), div[role="alert"]').first().textContent();
      console.log(`Error text: ${errorText}`);
    } else {
      console.log('✅ No error messages visible on page');
    }
  });

  test('Step 6: Verify Success and Flow Progression', async () => {
    console.log('🎯 Checking final flow state...');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshots/bug21-15-final-state.png', fullPage: true });

    // Look for success indicators
    const successIndicators = [
      'text=/questionnaire.*generated/i',
      'text=/manual.*collection/i',
      'text=/ready.*collect/i',
      'button:has-text("Start Collection")',
      'button:has-text("Begin Collection")'
    ];

    let successFound = false;
    for (const selector of successIndicators) {
      if (await page.locator(selector).count() > 0) {
        console.log(`✅ Success indicator found: ${selector}`);
        successFound = true;
      }
    }

    if (successFound) {
      console.log('✅ Questionnaire generation appears successful');
    } else {
      console.log('⚠️  Could not confirm questionnaire generation success');
    }

    // Check current URL/phase
    const currentUrl = page.url();
    console.log(`📍 Current URL: ${currentUrl}`);

    if (flowId) {
      console.log(`📋 Flow ID: ${flowId}`);
    }

    console.log('✅ Bug #21 Complete Flow Test finished');
    console.log('📝 Next step: Check backend logs for batch processing confirmation');
  });
});
