import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    // Ignore HTTPS errors since we're using Docker
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => console.log('CONSOLE:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure()));

  try {
    console.log('1. Navigating to localhost:8081...');
    await page.goto('http://localhost:8081', { timeout: 30000 });

    console.log('2. Waiting for page to load...');
    await page.waitForTimeout(3000);

    // Check if login is needed
    const loginButton = await page.$('button:has-text("Login")').catch(() => null);
    if (loginButton) {
      console.log('3. Login required - logging in...');

      // Try to find email field
      const emailField = await page.$('input[type="email"], input[name="email"], input[id="email"]').catch(() => null);
      if (emailField) {
        await emailField.fill('chocka@gmail.com');

        const passwordField = await page.$('input[type="password"], input[name="password"], input[id="password"]').catch(() => null);
        if (passwordField) {
          await passwordField.fill('Password123!');
          await loginButton.click();
          await page.waitForTimeout(3000);
        }
      }
    }

    console.log('4. Looking for assessment flow navigation...');

    // Look for assessment-related links or buttons
    const assessmentLinks = await page.$$eval('a, button', elements => {
      return elements
        .filter(el => el.textContent.toLowerCase().includes('assess'))
        .map(el => ({ text: el.textContent.trim(), href: el.href || '', type: el.tagName }));
    });

    console.log('Found assessment-related elements:', assessmentLinks);

    // Try to navigate to assessment flow
    const assessmentPath = '/assessment';
    console.log(`5. Attempting to navigate to ${assessmentPath}...`);
    await page.goto(`http://localhost:8081${assessmentPath}`, { timeout: 10000 });
    await page.waitForTimeout(2000);

    // Check current URL and page content
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);

    // Look for any error messages
    const errors = await page.$$eval('*', elements => {
      return elements
        .filter(el => el.textContent.toLowerCase().includes('error') ||
                     el.textContent.toLowerCase().includes('not found') ||
                     el.textContent.toLowerCase().includes('404'))
        .map(el => el.textContent.trim())
        .slice(0, 5); // Limit to first 5 errors
    });

    if (errors.length > 0) {
      console.log('Found errors on page:', errors);
    }

    // Check for assessment flow initialization
    const assessmentContent = await page.$$eval('*', elements => {
      return elements
        .filter(el => el.textContent.toLowerCase().includes('assessment') ||
                     el.textContent.toLowerCase().includes('initialize') ||
                     el.textContent.toLowerCase().includes('architecture'))
        .map(el => ({ tag: el.tagName, text: el.textContent.trim().substring(0, 100) }))
        .slice(0, 10);
    });

    if (assessmentContent.length > 0) {
      console.log('Found assessment-related content:', assessmentContent);
    } else {
      console.log('No assessment-related content found on this page');
    }

    // Take a screenshot for debugging
    await page.screenshot({ path: 'assessment-flow-test.png', fullPage: true });
    console.log('Screenshot saved as assessment-flow-test.png');

    console.log('6. Browser test complete!');

  } catch (error) {
    console.error('Error during browser test:', error.message);
    await page.screenshot({ path: 'assessment-flow-error.png', fullPage: true });
  } finally {
    await page.waitForTimeout(5000); // Keep browser open for 5 seconds to see result
    await browser.close();
  }
})();
