import { test, expect } from '@playwright/test';

test.describe('Debug Login Process', () => {
  test('debug login step by step', async ({ page }) => {
    // Go to login page
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    
    // Check if email field exists and fill it
    const emailInput = page.locator('input[type="email"]');
    const emailCount = await emailInput.count();
    console.log('Email inputs found:', emailCount);
    
    if (emailCount > 0) {
      await emailInput.fill('demo@demo-corp.com');
      const emailValue = await emailInput.inputValue();
      console.log('Email field value:', emailValue);
    }
    
    // Check if password field exists and fill it
    const passwordInput = page.locator('input[type="password"]');
    const passwordCount = await passwordInput.count();
    console.log('Password inputs found:', passwordCount);
    
    if (passwordCount > 0) {
      await passwordInput.fill('Demo123!');
      const passwordValue = await passwordInput.inputValue();
      console.log('Password field filled:', passwordValue.length > 0 ? 'Yes' : 'No');
    }
    
    // Find and check the Sign In button
    const signInButton = page.locator('button:has-text("Sign In")');
    const buttonCount = await signInButton.count();
    console.log('Sign In buttons found:', buttonCount);
    
    // Check if button is enabled
    if (buttonCount > 0) {
      const isDisabled = await signInButton.isDisabled();
      console.log('Button is disabled:', isDisabled);
      
      // Listen for network requests
      page.on('request', request => {
        if (request.url().includes('login') || request.url().includes('auth')) {
          console.log('Login request made to:', request.url());
        }
      });
      
      // Try clicking the button
      await signInButton.click();
      console.log('Button clicked');
      
      // Wait and check for any errors
      await page.waitForTimeout(3000);
      
      // Check for error messages
      const errorMessage = page.locator('.error, .alert, [role="alert"], .text-red-500');
      const errorCount = await errorMessage.count();
      if (errorCount > 0) {
        const errorText = await errorMessage.first().textContent();
        console.log('Error message found:', errorText);
      }
      
      // Check final URL
      console.log('Final URL:', page.url());
    }
  });
});
