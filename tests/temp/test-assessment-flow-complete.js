import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // Enable all console logging for debugging
  page.on('console', msg => console.log('CONSOLE:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText));

  try {
    console.log('=== ASSESSMENT FLOW COMPLETE TEST ===');
    
    console.log('1. Navigating to login page...');
    await page.goto('http://localhost:8081/login', { timeout: 30000 });
    await page.waitForTimeout(2000);

    console.log('2. Logging in...');
    await page.fill('input[type="email"], input[name="email"], input[id="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"], input[name="password"], input[id="password"]', 'Password123!');
    await page.click('button:has-text("Login"), button[type="submit"]');
    await page.waitForTimeout(3000);

    console.log('3. Navigating to assessment flow...');
    await page.goto('http://localhost:8081/assessment', { timeout: 10000 });
    await page.waitForTimeout(3000);

    // Look for assessment initialization form
    console.log('4. Looking for assessment initialization form...');
    const initializeButton = await page.$('button:has-text("Initialize"), button:has-text("Start"), button:has-text("Begin")').catch(() => null);
    const appCheckboxes = await page.$$('input[type="checkbox"]').catch(() => []);
    const selectAllButton = await page.$('button:has-text("Select All")').catch(() => null);

    console.log(`Found: ${appCheckboxes.length} checkboxes, Initialize button: ${!!initializeButton}, Select All: ${!!selectAllButton}`);

    if (appCheckboxes.length > 0) {
      console.log('5. Selecting applications for assessment...');
      
      // Select first few applications
      for (let i = 0; i < Math.min(2, appCheckboxes.length); i++) {
        await appCheckboxes[i].check();
        await page.waitForTimeout(100);
      }

      if (initializeButton) {
        console.log('6. Clicking initialize button...');
        await initializeButton.click();
        await page.waitForTimeout(5000);

        // Check if we were redirected to a flow page
        const currentUrl = page.url();
        console.log('7. Current URL after initialization:', currentUrl);

        if (currentUrl.includes('/assessment/') && currentUrl !== 'http://localhost:8081/assessment') {
          console.log('8. ✅ Assessment flow initialized! Redirected to flow page.');
          
          // Look for progress indicators or phase indicators
          const progressText = await page.textContent('body');
          const hasProgress = progressText.includes('Architecture') || 
                            progressText.includes('Tech Debt') ||
                            progressText.includes('6R') ||
                            progressText.includes('Progress');
          
          if (hasProgress) {
            console.log('9. ✅ Assessment flow phase content detected!');
          } else {
            console.log('9. ⚠️ Assessment flow initialized but no phase content visible yet.');
          }

          // Test navigation between phases if buttons exist
          const nextButton = await page.$('button:has-text("Next"), button:has-text("Continue")').catch(() => null);
          if (nextButton) {
            console.log('10. Testing phase navigation...');
            await nextButton.click();
            await page.waitForTimeout(2000);
            console.log('11. ✅ Phase navigation button clicked successfully!');
          } else {
            console.log('10. No navigation buttons found - flow may be waiting for input.');
          }

        } else {
          console.log('8. ⚠️ Assessment flow initialization may have failed - not redirected to flow page');
        }
      } else {
        console.log('6. ⚠️ No initialize button found after selecting applications');
      }
    } else {
      console.log('5. ⚠️ No application checkboxes found - may need data or different initialization flow');
      
      // Look for other initialization options
      const formInputs = await page.$$('input, select, textarea');
      console.log(`Found ${formInputs.length} form inputs on the page`);
      
      if (formInputs.length > 0) {
        console.log('6. Form inputs detected - assessment flow may have different initialization pattern');
      }
    }

    // Take final screenshot
    await page.screenshot({ path: 'assessment-flow-complete-test.png', fullPage: true });
    console.log('12. Screenshot saved as assessment-flow-complete-test.png');

    console.log('=== TEST COMPLETE ===');

  } catch (error) {
    console.error('Error during complete assessment flow test:', error.message);
    await page.screenshot({ path: 'assessment-flow-error.png', fullPage: true });
  } finally {
    await page.waitForTimeout(5000); // Keep browser open to see result
    await browser.close();
  }
})();