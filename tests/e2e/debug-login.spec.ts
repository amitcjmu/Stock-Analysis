import { test, expect } from '@playwright/test';

test('Debug Login Page Structure', async ({ page }) => {
  // Navigate to the application
  await page.goto('http://localhost:8081/');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Take a screenshot
  await page.screenshot({ path: 'login-page-debug.png', fullPage: true });
  
  // Log the page title
  const title = await page.title();
  console.log('Page title:', title);
  
  // Log the current URL
  console.log('Current URL:', page.url());
  
  // Try to find login elements with various selectors
  const emailSelectors = [
    'input[type="email"]',
    'input[name="email"]',
    'input[id="email"]',
    '#email',
    'input[placeholder*="email" i]',
    'input[placeholder*="Email" i]',
    'input[placeholder*="username" i]',
    'input[placeholder*="Username" i]'
  ];
  
  const passwordSelectors = [
    'input[type="password"]',
    'input[name="password"]', 
    'input[id="password"]',
    '#password',
    'input[placeholder*="password" i]',
    'input[placeholder*="Password" i]'
  ];
  
  const submitSelectors = [
    'button[type="submit"]',
    'button:has-text("Login")',
    'button:has-text("Log in")',
    'button:has-text("Sign in")',
    'button:has-text("Sign In")',
    'input[type="submit"]'
  ];
  
  console.log('Looking for email input fields...');
  for (const selector of emailSelectors) {
    const element = page.locator(selector);
    if (await element.isVisible()) {
      console.log(`✅ Found email field with selector: ${selector}`);
      const placeholder = await element.getAttribute('placeholder');
      console.log(`  Placeholder: ${placeholder}`);
    }
  }
  
  console.log('Looking for password input fields...');
  for (const selector of passwordSelectors) {
    const element = page.locator(selector);
    if (await element.isVisible()) {
      console.log(`✅ Found password field with selector: ${selector}`);
      const placeholder = await element.getAttribute('placeholder');
      console.log(`  Placeholder: ${placeholder}`);
    }
  }
  
  console.log('Looking for submit buttons...');
  for (const selector of submitSelectors) {
    const element = page.locator(selector);
    if (await element.isVisible()) {
      console.log(`✅ Found submit button with selector: ${selector}`);
      const text = await element.textContent();
      console.log(`  Text: ${text}`);
    }
  }
  
  // Get all input elements on the page
  const allInputs = await page.locator('input').all();
  console.log(`Found ${allInputs.length} input elements total`);
  
  for (let i = 0; i < allInputs.length; i++) {
    const input = allInputs[i];
    const type = await input.getAttribute('type');
    const name = await input.getAttribute('name');
    const id = await input.getAttribute('id');
    const placeholder = await input.getAttribute('placeholder');
    console.log(`Input ${i}: type="${type}", name="${name}", id="${id}", placeholder="${placeholder}"`);
  }
  
  // Get all buttons on the page
  const allButtons = await page.locator('button').all();
  console.log(`Found ${allButtons.length} button elements total`);
  
  for (let i = 0; i < allButtons.length; i++) {
    const button = allButtons[i];
    const type = await button.getAttribute('type');
    const text = await button.textContent();
    console.log(`Button ${i}: type="${type}", text="${text}"`);
  }
  
  // Check if we're already logged in (redirected to admin)
  if (page.url().includes('/admin')) {
    console.log('🔄 Already logged in - redirected to admin area');
  }
  
  // Check if this is actually the login page
  const loginText = await page.locator('text=Login, text=log in, text=sign in').first();
  if (await loginText.isVisible()) {
    console.log('✅ This appears to be a login page');
  } else {
    console.log('❓ This may not be a login page');
  }
  
  // Get page content for inspection
  const pageContent = await page.content();
  console.log('Page HTML length:', pageContent.length);
  
  // Look for any forms
  const forms = await page.locator('form').all();
  console.log(`Found ${forms.length} form elements`);
}); 