import { test, expect, Page } from '@playwright/test';

const FLOW_ID = '220b9eb7-5ff4-46f3-9608-bbad9d3335b3';
const BASE_URL = 'http://localhost:8081';

test.describe('Collection Flow Bug #21 - Batched LLM Processing', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('Step 1: Login to application', async () => {
    console.log('🔐 Navigating to login page...');
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: 'screenshots/01-login-page.png', fullPage: true });

    // Enter credentials
    console.log('📝 Entering credentials...');
    await page.fill('input[type="email"], input[name="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"], input[name="password"]', 'Demo123!');

    await page.screenshot({ path: 'screenshots/02-credentials-entered.png', fullPage: true });

    // Click login
    console.log('🚀 Clicking login button...');
    await page.click('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")');

    // Wait for dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    await page.screenshot({ path: 'screenshots/03-dashboard.png', fullPage: true });
    console.log('✅ Login successful');
  });

  test('Step 2: Navigate to Collection Flow', async () => {
    console.log('📋 Navigating to collection page...');
    await page.goto(`${BASE_URL}/collection`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Allow data to load

    await page.screenshot({ path: 'screenshots/04-collection-page.png', fullPage: true });

    // Look for the flow
    console.log('🔍 Looking for running flow or Canada Life engagement...');

    // Try to find the specific flow or any running flow
    const flowCard = await page.locator('div:has-text("Canada Life"), div:has-text("running"), div:has-text("Continue Collection")').first();

    if (await flowCard.count() > 0) {
      console.log('✅ Found flow card');
      await page.screenshot({ path: 'screenshots/05-flow-found.png', fullPage: true });

      // Click to continue
      const continueButton = await page.locator('button:has-text("Continue Collection"), button:has-text("Continue"), a:has-text("View Details")').first();
      await continueButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      await page.screenshot({ path: 'screenshots/06-flow-details.png', fullPage: true });
      console.log('✅ Navigated to flow details');
    } else {
      console.log('⚠️  Flow card not found, trying direct URL navigation...');
      await page.goto(`${BASE_URL}/collection/${FLOW_ID}`);
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'screenshots/06-flow-direct-url.png', fullPage: true });
    }
  });

  test('Step 3: Trigger Gap Analysis → Questionnaire Generation', async () => {
    console.log('🎯 Checking current phase...');

    // Wait for page to load
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshots/07-current-phase.png', fullPage: true });

    // Look for buttons to proceed (various possible button texts)
    const proceedButtons = [
      'Generate Questionnaire',
      'Continue to Questionnaire',
      'Next',
      'Proceed',
      'Generate Questions',
      'Start Questionnaire Generation'
    ];

    let buttonClicked = false;
    for (const buttonText of proceedButtons) {
      const button = page.locator(`button:has-text("${buttonText}")`);
      if (await button.count() > 0 && await button.isVisible()) {
        console.log(`🎯 Found button: "${buttonText}"`);
        await button.click();
        buttonClicked = true;
        console.log('✅ Clicked proceed button');
        break;
      }
    }

    if (!buttonClicked) {
      console.log('⚠️  No proceed button found, checking if already in questionnaire generation...');
    }

    await page.screenshot({ path: 'screenshots/08-after-proceed-click.png', fullPage: true });

    // Wait for processing to start
    console.log('⏳ Waiting for questionnaire generation to start (10 seconds)...');
    await page.waitForTimeout(10000);
    await page.screenshot({ path: 'screenshots/09-processing-10s.png', fullPage: true });

    console.log('⏳ Continuing to wait (20 more seconds)...');
    await page.waitForTimeout(20000);
    await page.screenshot({ path: 'screenshots/10-processing-30s.png', fullPage: true });

    console.log('⏳ Final wait period (30 more seconds)...');
    await page.waitForTimeout(30000);
    await page.screenshot({ path: 'screenshots/11-processing-60s.png', fullPage: true });

    console.log('✅ Waited 60 seconds for processing');
  });

  test('Step 4: Capture Final State', async () => {
    console.log('📸 Capturing final state...');
    await page.screenshot({ path: 'screenshots/12-final-state.png', fullPage: true });

    // Check for any error messages on page
    const errorElements = await page.locator('div:has-text("error"), div:has-text("Error"), div[role="alert"]').count();
    if (errorElements > 0) {
      console.log('⚠️  Error messages found on page');
      const errorText = await page.locator('div:has-text("error"), div:has-text("Error"), div[role="alert"]').first().textContent();
      console.log(`Error text: ${errorText}`);
    } else {
      console.log('✅ No error messages visible on page');
    }

    // Check console logs
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`❌ Browser console error: ${msg.text()}`);
      }
    });

    console.log('✅ Test sequence complete');
  });
});
