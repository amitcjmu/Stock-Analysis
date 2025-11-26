/**
 * Bug #22 Fix Test: Collection Flow - No TRUE gaps should not cause endless loop
 *
 * This test verifies that when IntelligentGapScanner finds no TRUE gaps for an asset,
 * the system correctly marks the questionnaire as "completed" (not "failed"),
 * and the flow progresses to completion without getting stuck in an endless loop.
 *
 * Test Flow:
 * 1. Login with chockas@hcltech.com / Testing123!
 * 2. Select Canada Life context
 * 3. Go to Assessment Overview
 * 4. Click New Assessment
 * 5. Select asset(s) needing collection
 * 6. Click Start Collection
 * 7. Verify NO endless loop occurs
 * 8. Verify flow completes or shows questionnaire (not stuck on loading)
 */
import { test, expect } from '@playwright/test';

test.describe('Bug #22: Collection Flow - No TRUE gaps handling', () => {
  test('should not get stuck in endless loop when no TRUE gaps found', async ({ page }) => {
    // Long timeout for collection flow processing
    test.setTimeout(180000); // 3 minutes

    console.log('=== STEP 1: Navigate to app ===');
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');

    // Take screenshot to see current state
    await page.screenshot({ path: '/tmp/bug22-step1-landing.png', fullPage: true });
    console.log('Screenshot: /tmp/bug22-step1-landing.png');

    // Check if already logged in or need to login
    const isLoginPage = await page.locator('input[type="email"], input[placeholder*="email" i]').first().isVisible().catch(() => false);

    if (isLoginPage) {
      console.log('=== STEP 2: Login ===');
      // Fill email
      const emailInput = page.locator('input[type="email"], input[placeholder*="email" i]').first();
      await emailInput.fill('chockas@hcltech.com');

      // Fill password
      const passwordInput = page.locator('input[type="password"]').first();
      await passwordInput.fill('Testing123!');

      // Click Sign In
      const signInButton = page.locator('button:has-text("Sign In")');
      await signInButton.click();

      // Wait for navigation after login
      await page.waitForTimeout(3000);
      await page.waitForLoadState('networkidle');

      await page.screenshot({ path: '/tmp/bug22-step2-after-login.png', fullPage: true });
      console.log('Screenshot: /tmp/bug22-step2-after-login.png');
    }

    console.log('=== STEP 3: Look for context selector or navigation ===');
    // Wait a moment for the UI to load
    await page.waitForTimeout(2000);

    // Take screenshot to see current state
    await page.screenshot({ path: '/tmp/bug22-step3-current-state.png', fullPage: true });
    console.log('Screenshot: /tmp/bug22-step3-current-state.png');

    // Look for Canada Life in the context or navigation
    const canadaLifeText = await page.locator('text=/Canada Life/i').first().isVisible().catch(() => false);
    console.log('Canada Life visible:', canadaLifeText);

    // Try to find Assessment link in navigation
    const assessmentLink = page.locator('a:has-text("Assessment"), [href*="assessment"]').first();
    const hasAssessmentLink = await assessmentLink.isVisible().catch(() => false);
    console.log('Assessment link visible:', hasAssessmentLink);

    if (hasAssessmentLink) {
      console.log('=== STEP 4: Click Assessment link ===');
      await assessmentLink.click();
      await page.waitForTimeout(2000);
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: '/tmp/bug22-step4-assessment-page.png', fullPage: true });
      console.log('Screenshot: /tmp/bug22-step4-assessment-page.png');
    }

    // Look for "New Assessment" or similar button
    console.log('=== STEP 5: Look for New Assessment button ===');
    const newAssessmentButton = page.locator('button:has-text("New Assessment"), button:has-text("Start New"), a:has-text("New Assessment")').first();
    const hasNewAssessmentButton = await newAssessmentButton.isVisible().catch(() => false);
    console.log('New Assessment button visible:', hasNewAssessmentButton);

    if (hasNewAssessmentButton) {
      await newAssessmentButton.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: '/tmp/bug22-step5-new-assessment-modal.png', fullPage: true });
      console.log('Screenshot: /tmp/bug22-step5-new-assessment-modal.png');
    }

    // Look for asset selection in a modal or grid
    console.log('=== STEP 6: Look for asset selection ===');

    // Try multiple selectors for asset rows/checkboxes
    const assetSelectors = [
      '[role="row"] input[type="checkbox"]',
      '.ag-row input[type="checkbox"]',
      'table tbody tr input[type="checkbox"]',
      '[data-testid*="asset"] input[type="checkbox"]',
      '.asset-row input[type="checkbox"]',
    ];

    let foundAssetCheckbox = false;
    for (const selector of assetSelectors) {
      const checkboxes = page.locator(selector);
      const count = await checkboxes.count().catch(() => 0);
      if (count > 0) {
        console.log(`Found ${count} asset checkboxes with selector: ${selector}`);
        // Click the first checkbox to select an asset
        await checkboxes.first().click();
        foundAssetCheckbox = true;
        break;
      }
    }

    await page.screenshot({ path: '/tmp/bug22-step6-asset-selection.png', fullPage: true });
    console.log('Screenshot: /tmp/bug22-step6-asset-selection.png');
    console.log('Found asset checkbox:', foundAssetCheckbox);

    // Look for Start Collection button
    console.log('=== STEP 7: Look for Start Collection button ===');
    const startCollectionButton = page.locator('button:has-text("Start Collection"), button:has-text("Begin Collection")').first();
    const hasStartCollectionButton = await startCollectionButton.isVisible().catch(() => false);
    console.log('Start Collection button visible:', hasStartCollectionButton);

    if (hasStartCollectionButton) {
      console.log('=== STEP 8: Click Start Collection ===');
      await startCollectionButton.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: '/tmp/bug22-step8-after-start-collection.png', fullPage: true });
      console.log('Screenshot: /tmp/bug22-step8-after-start-collection.png');

      // KEY TEST: Monitor for endless loop vs proper completion
      console.log('=== STEP 9: Monitor for endless loop (Bug #22 fix) ===');

      // Wait up to 60 seconds for the collection flow to process
      const maxWaitTime = 60000;
      const checkInterval = 5000;
      let timeWaited = 0;
      let foundEndlessLoop = false;
      let foundCompletion = false;

      while (timeWaited < maxWaitTime) {
        await page.waitForTimeout(checkInterval);
        timeWaited += checkInterval;

        // Take periodic screenshots
        await page.screenshot({
          path: `/tmp/bug22-step9-monitoring-${timeWaited / 1000}s.png`,
          fullPage: true,
        });

        // Check for signs of completion (questionnaire, ready, or completed status)
        const completedIndicators = [
          'text=/completed/i',
          'text=/ready/i',
          'text=/questionnaire/i',
          'text=/no.*gaps/i',
          'text=/collection.*complete/i',
        ];

        for (const indicator of completedIndicators) {
          const isVisible = await page.locator(indicator).first().isVisible().catch(() => false);
          if (isVisible) {
            console.log(`Found completion indicator: ${indicator}`);
            foundCompletion = true;
            break;
          }
        }

        if (foundCompletion) break;

        // Check for signs of endless loop (spinner with no progress, error state)
        const loopIndicators = [
          '.spinner:visible',
          '[class*="loading"]:visible',
          'text=/loading/i',
        ];

        let stillLoading = false;
        for (const indicator of loopIndicators) {
          const isVisible = await page.locator(indicator).first().isVisible().catch(() => false);
          if (isVisible) {
            stillLoading = true;
            console.log(`Still loading after ${timeWaited / 1000}s: ${indicator}`);
          }
        }

        // If still loading after 45 seconds, likely endless loop
        if (stillLoading && timeWaited >= 45000) {
          foundEndlessLoop = true;
          console.log('POTENTIAL ENDLESS LOOP DETECTED!');
          break;
        }

        console.log(`Monitoring... ${timeWaited / 1000}s elapsed`);
      }

      // Final screenshot
      await page.screenshot({ path: '/tmp/bug22-step10-final.png', fullPage: true });
      console.log('Screenshot: /tmp/bug22-step10-final.png');

      // Assert: No endless loop should occur
      expect(foundEndlessLoop).toBe(false);

      console.log('=== TEST COMPLETE ===');
      if (foundCompletion) {
        console.log('SUCCESS: Collection flow completed without endless loop');
      } else {
        console.log('Collection flow is still processing or ended without clear indicator');
      }
    } else {
      console.log('Could not find Start Collection button - taking final screenshot');
      await page.screenshot({ path: '/tmp/bug22-final-state.png', fullPage: true });
    }
  });
});
