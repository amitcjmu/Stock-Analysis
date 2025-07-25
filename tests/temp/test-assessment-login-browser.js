import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => {
    if (msg.text().includes('Assessment') || msg.text().includes('error') || msg.text().includes('ERROR')) {
      console.log('CONSOLE:', msg.text());
    }
  });
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  try {
    console.log('1. Navigating to login page...');
    await page.goto('http://localhost:8081/login', { timeout: 30000 });
    await page.waitForTimeout(2000);

    console.log('2. Filling login form...');
    const emailField = await page.$('input[type="email"], input[name="email"], input[id="email"]');
    if (emailField) {
      await emailField.fill('chocka@gmail.com');

      const passwordField = await page.$('input[type="password"], input[name="password"], input[id="password"]');
      if (passwordField) {
        await passwordField.fill('Password123!');

        const loginButton = await page.$('button:has-text("Login"), button[type="submit"]');
        if (loginButton) {
          await loginButton.click();
          console.log('3. Submitted login form...');
          await page.waitForTimeout(3000);
        }
      }
    }

    // Check if we're logged in
    const currentUrl = page.url();
    console.log('4. Current URL after login:', currentUrl);

    if (!currentUrl.includes('/login')) {
      console.log('5. Login successful! Now testing assessment flow navigation...');

      // Try to navigate to assessment flow
      console.log('6. Attempting to navigate to /assessment...');
      await page.goto('http://localhost:8081/assessment', { timeout: 10000 });
      await page.waitForTimeout(2000);

      const finalUrl = page.url();
      console.log('7. Final URL:', finalUrl);

      // Check for assessment content
      const pageTitle = await page.title();
      console.log('8. Page title:', pageTitle);

      // Look for any assessment-related text
      const bodyText = await page.textContent('body');
      const hasAssessmentContent = bodyText.toLowerCase().includes('assessment') ||
                                  bodyText.toLowerCase().includes('architecture') ||
                                  bodyText.toLowerCase().includes('initialize');

      if (hasAssessmentContent) {
        console.log('9. ✅ Assessment content found on page!');
      } else {
        console.log('9. ❌ No assessment content found. Page might need route configuration.');

        // Check what routes are available by looking at navigation
        const navLinks = await page.$$eval('nav a, .nav a, a[href^="/"]', elements => {
          return elements.map(el => ({ text: el.textContent.trim(), href: el.href }))
                        .filter(link => link.text && link.href)
                        .slice(0, 10);
        });

        console.log('10. Available navigation links:', navLinks);
      }

      await page.screenshot({ path: 'assessment-flow-logged-in.png', fullPage: true });
      console.log('11. Screenshot saved as assessment-flow-logged-in.png');
    } else {
      console.log('5. Login failed - still on login page');

      // Check for error messages
      const errorElements = await page.$$('*');
      const errors = [];
      for (const el of errorElements) {
        const text = await el.textContent();
        if (text && text.toLowerCase().includes('error')) {
          errors.push(text.trim());
        }
      }

      if (errors.length > 0) {
        console.log('Login errors found:', errors.slice(0, 3));
      }
    }

  } catch (error) {
    console.error('Error during test:', error.message);
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }
})();
