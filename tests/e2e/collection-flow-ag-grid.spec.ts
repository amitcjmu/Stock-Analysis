import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOTS_DIR = '/Users/chocka/CursorProjects/migrate-ui-orchestrator/test-results/collection-flow-screenshots';

// Ensure screenshots directory exists
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

test.describe('Collection Flow - AG Grid Asset Selection Journey', () => {
  test('Complete collection flow with AG Grid checkbox selection', async ({ page }) => {
    const testStartTime = Date.now();
    console.log('\n=== COLLECTION FLOW TEST STARTING ===\n');

    // Step 1: Login
    console.log('Step 1: Logging in...');
    await page.goto('http://localhost:8081/login');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '01-login-page.png'), fullPage: true });

    // Use demo credentials shown on the login page
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '02-credentials-entered.png'), fullPage: true });

    // Click login and wait for navigation away from login page
    await Promise.all([
      page.click('button[type="submit"]'),
      page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 15000 })
    ]);

    console.log(`After login, current URL: ${page.url()}`);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '03-after-login.png'), fullPage: true });

    // Verify we're not on login page
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.error('✗ Still on login page - authentication failed');
      throw new Error('Login failed - still on login page');
    }

    console.log('✓ Login successful - redirected to:', currentUrl);

    // Step 2: Navigate to Collection Flow
    console.log('\nStep 2: Navigating to Collection Flow...');
    await page.goto('http://localhost:8081/collection');

    // Don't wait for networkidle due to polling - wait for content instead
    await page.waitForSelector('h1, h2, .collection-header', { timeout: 10000 });

    // Check if we got redirected back to login
    if (page.url().includes('/login')) {
      console.error('✗ Redirected to login after navigating to collection - session not persisted');
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '04-redirected-to-login.png'), fullPage: true });
      throw new Error('Session not persisted - redirected to login');
    }

    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '04-collection-page.png'), fullPage: true });
    console.log(`Collection page URL: ${page.url()}`);

    // Wait for the page to check for active flows (async operation)
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '04b-after-wait.png'), fullPage: true });

    // Try to wait for "Active Collection Flow Detected" or "Continue Collection" button
    try {
      await page.waitForSelector('button:has-text("Continue Collection")', { timeout: 5000 });
      console.log('✓ Found "Continue Collection" button');

      await page.locator('button:has-text("Continue Collection")').click();
      console.log('✓ Clicked Continue Collection button');

      // Wait for navigation
      await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '05-continue-collection-clicked.png'), fullPage: true });
      console.log(`After Continue Collection, URL: ${page.url()}`);
    } catch (error) {
      console.log('⚠ No "Continue Collection" button found, checking for other options...');

      // Look for "Start New Data Collection" page
      const pageText = await page.textContent('body');
      if (pageText?.includes('Start New Data Collection')) {
        console.log('On "Start New Data Collection" page - selecting Adaptive Forms option');

        // Select the first option (1-50 applications → Adaptive Forms)
        const adaptiveFormsRadio = await page.locator('text=1-50 applications').count();
        if (adaptiveFormsRadio > 0) {
          await page.locator('text=1-50 applications').click();
          await page.waitForTimeout(500);

          // Click Start Collection button
          const startBtn = await page.locator('button:has-text("Start Collection")').count();
          if (startBtn > 0) {
            await page.locator('button:has-text("Start Collection")').click();
            await page.waitForTimeout(2000);
            await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '05-start-new-clicked.png'), fullPage: true });
            console.log('✓ Started new collection flow');
          }
        }
      }
    }

    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '06-flow-page-loaded.png'), fullPage: true });
    console.log(`Current page URL: ${page.url()}`);

    // Step 3: Wait for Asset Selection Page
    console.log('\nStep 3: Waiting for Asset Selection page to load...');

    // Check if page uses AG Grid or card-based layout
    await page.waitForTimeout(2000); // Give time for page to fully render
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '07-asset-selection-page.png'), fullPage: true });

    const hasAgGrid = await page.locator('.ag-root-wrapper').count() > 0;
    const hasCards = await page.locator('text=Select Assets').count() > 0;

    console.log(`Page layout: AG Grid=${hasAgGrid}, Card-based=${hasCards}`);

    if (!hasAgGrid && !hasCards) {
      console.error('✗ Neither AG Grid nor card-based layout found');
      throw new Error('Asset selection page not loaded properly');
    }

    // Step 4: Select Assets
    console.log('\nStep 4: Attempting to select assets...');
    let checkboxSelector = '';
    let selectionSuccess = false;

    if (hasCards) {
      console.log('Using card-based layout - selecting assets with standard checkboxes');

      // Try "Select All" checkbox first
      const selectAllCheckbox = await page.locator('text=Select All').count();
      if (selectAllCheckbox > 0) {
        console.log('Found "Select All" checkbox');
        try {
          await page.locator('text=Select All').click();
          await page.waitForTimeout(1000);
          await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '08-select-all-clicked.png'), fullPage: true });
          console.log('✓ Clicked Select All checkbox');
          checkboxSelector = 'Select All checkbox';
          selectionSuccess = true;
        } catch (error) {
          console.log(`✗ Failed to click Select All: ${error.message}`);
        }
      }

      // If Select All didn't work, try individual asset checkboxes
      if (!selectionSuccess) {
        console.log('Trying individual asset checkboxes...');
        const assetCheckboxes = await page.locator('input[type="checkbox"]').count();
        console.log(`Found ${assetCheckboxes} checkboxes`);

        if (assetCheckboxes > 0) {
          try {
            // Select first 3 assets
            const checkboxesToSelect = Math.min(3, assetCheckboxes);
            for (let i = 0; i < checkboxesToSelect; i++) {
              await page.locator('input[type="checkbox"]').nth(i).click();
              await page.waitForTimeout(500);
              console.log(`✓ Clicked checkbox ${i + 1}`);
            }
            checkboxSelector = 'input[type="checkbox"]';
            selectionSuccess = true;
          } catch (error) {
            console.log(`✗ Failed to click individual checkboxes: ${error.message}`);
          }
        }
      }
    } else if (hasAgGrid) {
      console.log('Using AG Grid layout - trying AG Grid selectors');

      const agGridSelectors = [
        { name: 'AG Grid selection checkbox', selector: '.ag-selection-checkbox' },
        { name: 'AG Grid checkbox input wrapper', selector: '.ag-checkbox-input-wrapper' },
        { name: 'AG Grid header select all', selector: '.ag-header-select-all' },
        { name: 'Row with checkbox role', selector: '[role="row"] [role="checkbox"]' }
      ];

      for (const { name, selector } of agGridSelectors) {
        console.log(`Trying ${name}: ${selector}`);
        const elements = await page.locator(selector).count();
        if (elements > 0) {
          try {
            await page.locator(selector).first().click();
            await page.waitForTimeout(1000);
            checkboxSelector = selector;
            selectionSuccess = true;
            console.log(`✓ Clicked using ${name}`);
            break;
          } catch (error) {
            console.log(`✗ Failed: ${error.message}`);
          }
        }
      }
    }

    if (!selectionSuccess) {
      console.error('✗ All checkbox selection strategies failed');
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '08-checkbox-selection-failed.png'), fullPage: true });

      // Dump page HTML for debugging
      const html = await page.content();
      fs.writeFileSync(path.join(SCREENSHOTS_DIR, 'page-content.html'), html);
      console.log('Page HTML saved to page-content.html');

      throw new Error('Could not select assets - all checkbox selectors failed');
    }

    console.log(`\n✓ Successfully selected assets using: ${checkboxSelector}`);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '09-assets-selected.png'), fullPage: true });

    // Step 5: Capture console logs and network errors
    console.log('\nStep 5: Monitoring browser console and network...');
    const consoleMessages: string[] = [];
    const networkErrors: string[] = [];

    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push(`[${msg.type()}] ${text}`);
      if (msg.type() === 'error') {
        console.log(`Browser Console Error: ${text}`);
      }
    });

    page.on('requestfailed', request => {
      const failure = `${request.method()} ${request.url()} - ${request.failure()?.errorText}`;
      networkErrors.push(failure);
      console.log(`Network Error: ${failure}`);
    });

    // Step 6: Proceed to next step (Continue button)
    console.log('\nStep 6: Looking for Continue/Next button...');

    const buttonSelectors = [
      'button:has-text("Continue")',
      'button:has-text("Next")',
      'button:has-text("Proceed")',
      'button:has-text("Analyze")',
      '[data-testid="continue-button"]',
      '[data-testid="next-button"]'
    ];

    let continueButtonFound = false;
    for (const btnSelector of buttonSelectors) {
      const btnCount = await page.locator(btnSelector).count();
      if (btnCount > 0) {
        console.log(`Found button with selector: ${btnSelector}`);
        await page.locator(btnSelector).first().click();

        // Don't wait for networkidle due to potential polling
        await page.waitForTimeout(3000);
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '10-after-continue-click.png'), fullPage: true });
        continueButtonFound = true;
        console.log('✓ Clicked Continue button');
        console.log(`After Continue, URL: ${page.url()}`);
        break;
      }
    }

    if (!continueButtonFound) {
      console.log('⚠ Continue button not found, checking if already on next page...');
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '10-no-continue-button.png'), fullPage: true });
    }

    // Step 7: Wait for Gap Analysis or Questionnaire page
    console.log('\nStep 7: Waiting for Gap Analysis/Questionnaire generation...');
    await page.waitForTimeout(5000); // Give time for processing
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '11-gap-analysis-page.png'), fullPage: true });

    // Check for common indicators
    const pageTextAfterContinue = await page.textContent('body');
    const hasGapAnalysis = pageTextAfterContinue?.toLowerCase().includes('gap analysis') ||
                           pageTextAfterContinue?.toLowerCase().includes('analyzing');
    const hasQuestionnaire = pageTextAfterContinue?.toLowerCase().includes('questionnaire') ||
                             pageTextAfterContinue?.toLowerCase().includes('questions');
    const hasError = pageTextAfterContinue?.toLowerCase().includes('error') ||
                     pageTextAfterContinue?.toLowerCase().includes('failed');

    console.log('\nPage Content Indicators:');
    console.log(`  Gap Analysis: ${hasGapAnalysis}`);
    console.log(`  Questionnaire: ${hasQuestionnaire}`);
    console.log(`  Error Message: ${hasError}`);

    // Step 8: Check for specific errors
    console.log('\nStep 8: Checking for JSON parsing or backend errors...');

    const jsonErrors = consoleMessages.filter(msg =>
      msg.toLowerCase().includes('json') ||
      msg.toLowerCase().includes('parse') ||
      msg.toLowerCase().includes('syntax')
    );

    const apiErrors = consoleMessages.filter(msg =>
      msg.toLowerCase().includes('api') ||
      msg.toLowerCase().includes('400') ||
      msg.toLowerCase().includes('500')
    );

    if (jsonErrors.length > 0) {
      console.log('\n⚠ JSON Parsing Errors Found:');
      jsonErrors.forEach(err => console.log(`  ${err}`));
    }

    if (apiErrors.length > 0) {
      console.log('\n⚠ API Errors Found:');
      apiErrors.forEach(err => console.log(`  ${err}`));
    }

    if (networkErrors.length > 0) {
      console.log('\n⚠ Network Errors:');
      networkErrors.forEach(err => console.log(`  ${err}`));
    }

    // Step 9: Final status check
    console.log('\nStep 9: Checking final flow status...');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '12-final-state.png'), fullPage: true });

    // Try to find status indicators
    const statusElements = await page.locator('[data-testid*="status"], .status, .state').count();
    console.log(`Found ${statusElements} status elements`);

    const testEndTime = Date.now();
    const testDuration = ((testEndTime - testStartTime) / 1000).toFixed(2);

    // Generate test summary
    const summary = {
      testDuration: `${testDuration} seconds`,
      checkboxSelectorUsed: checkboxSelector,
      selectionSuccess: selectionSuccess,
      continueButtonFound: continueButtonFound,
      pageIndicators: {
        gapAnalysis: hasGapAnalysis,
        questionnaire: hasQuestionnaire,
        errorMessage: hasError
      },
      consoleErrorCount: consoleMessages.filter(m => m.includes('[error]')).length,
      networkErrorCount: networkErrors.length,
      jsonErrorCount: jsonErrors.length,
      apiErrorCount: apiErrors.length,
      totalConsoleMessages: consoleMessages.length
    };

    console.log('\n=== TEST SUMMARY ===');
    console.log(JSON.stringify(summary, null, 2));

    // Save summary to file
    fs.writeFileSync(
      path.join(SCREENSHOTS_DIR, 'test-summary.json'),
      JSON.stringify({
        summary,
        consoleMessages,
        networkErrors,
        jsonErrors,
        apiErrors
      }, null, 2)
    );

    console.log('\n✓ Test completed - check screenshots and test-summary.json for details');

    // Assert basic success criteria
    expect(selectionSuccess).toBeTruthy();
  });
});
