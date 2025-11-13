import { test, expect } from '@playwright/test';

test.describe('Check Login Response', () => {
  test('capture backend login response', async ({ page }) => {
    // Go to login page
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    
    // Set up response listener before clicking login
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/api/v1/auth/login')
    );
    
    // Fill credentials
    await page.fill('input[type="email"]', 'demo@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    
    // Click Sign In
    await page.click('button:has-text("Sign In")');
    
    // Wait for the response
    const response = await responsePromise;
    console.log('Login response status:', response.status());
    console.log('Login response URL:', response.url());
    
    // Try to get response body
    try {
      const responseBody = await response.json();
      console.log('Login response body:', JSON.stringify(responseBody, null, 2));
    } catch (e) {
      const responseText = await response.text();
      console.log('Login response text:', responseText);
    }
    
    // Also check browser console for errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('Browser console error:', msg.text());
      }
    });
    
    await page.waitForTimeout(2000);
  });
});
