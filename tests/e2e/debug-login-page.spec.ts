import { test, expect } from '@playwright/test';

test.describe('Debug Login Page', () => {
  test('Check login page structure', async ({ page }) => {
    test.setTimeout(30000);

    console.log('🔍 Debugging login page...');
    await page.goto('http://localhost:8081/login');

    // Wait for page to load
    await page.waitForTimeout(3000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/login-page-debug.png', fullPage: true });

    // Check page title
    const title = await page.title();
    console.log('Page title:', title);

    // Look for input fields
    const emailInputs = await page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').count();
    const passwordInputs = await page.locator('input[type="password"], input[name="password"]').count();
    const submitButtons = await page.locator('button[type="submit"], button:has-text("login"), button:has-text("sign in")').count();

    console.log('Email inputs found:', emailInputs);
    console.log('Password inputs found:', passwordInputs);
    console.log('Submit buttons found:', submitButtons);

    // List all form elements
    const formElements = await page.locator('form input, form button').all();
    console.log('Form elements count:', formElements.length);

    for (let i = 0; i < formElements.length; i++) {
      const element = formElements[i];
      const tagName = await element.evaluate(el => el.tagName);
      const type = await element.getAttribute('type');
      const name = await element.getAttribute('name');
      const placeholder = await element.getAttribute('placeholder');
      console.log(`Element ${i}: ${tagName} type="${type}" name="${name}" placeholder="${placeholder}"`);
    }

    // Check if we're actually on a login page
    const hasLoginForm = await page.locator('form').count() > 0;
    const hasLoginText = await page.locator('text=/login|sign in/i').count() > 0;

    console.log('Has form:', hasLoginForm);
    console.log('Has login text:', hasLoginText);

    expect(true).toBe(true); // Always pass, this is just for debugging
  });
});
