import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  // Enable console log capture
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error' && !text.includes('process is not defined')) {
      console.log('CONSOLE ERROR:', text);
    }
  });
  
  // Capture any page errors
  page.on('pageerror', error => {
    if (!error.message.includes('process is not defined')) {
      console.log('PAGE ERROR:', error.message);
    }
  });

  console.log('Opening http://localhost:8081...');
  
  try {
    // Navigate to the application
    await page.goto('http://localhost:8081', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    console.log('Page loaded successfully!');
    
    // Check if we're on login page
    const loginButton = await page.$('button:has-text("Sign In")');
    if (loginButton) {
      console.log('Found login page, attempting to login...');
      
      // Fill in login form
      await page.fill('input[type="email"]', 'chocka@gmail.com');
      await page.fill('input[type="password"]', 'Password123!');
      await loginButton.click();
      
      // Wait for navigation
      await page.waitForTimeout(3000);
    }
    
    // Look for the Assess menu
    console.log('Looking for Assess menu...');
    const assessMenu = await page.$('text=/Assess/i');
    
    if (assessMenu) {
      console.log('Found Assess menu, clicking it...');
      await assessMenu.click();
      await page.waitForTimeout(1000);
      
      // Look for Assessment Flow submenu
      const assessmentFlowLink = await page.$('text=/Assessment Flow/i');
      if (assessmentFlowLink) {
        console.log('Found Assessment Flow link, clicking it...');
        await assessmentFlowLink.click();
        await page.waitForTimeout(2000);
        
        // Check current URL
        const currentUrl = page.url();
        console.log('Current URL:', currentUrl);
        
        // Take screenshot of assessment flow page
        await page.screenshot({ path: 'assessment-flow-initialize.png', fullPage: true });
        console.log('Screenshot saved as assessment-flow-initialize.png');
        
        // Check for any errors on the page
        const errorElements = await page.$$('[class*="error"], [class*="Error"]');
        if (errorElements.length > 0) {
          console.log(`Found ${errorElements.length} error elements`);
          for (const element of errorElements) {
            const text = await element.textContent();
            console.log('ERROR:', text);
          }
        } else {
          console.log('✅ No errors found on Assessment Flow page!');
        }
      } else {
        console.log('❌ Assessment Flow link not found in submenu');
      }
    } else {
      console.log('❌ Assess menu not found');
      
      // Take screenshot of current state
      await page.screenshot({ path: 'navigation-issue.png', fullPage: true });
      console.log('Screenshot saved as navigation-issue.png');
    }
    
    console.log('\nTest complete! Browser will remain open.');
    console.log('Press Ctrl+C to close...');
    
    // Keep the script running
    await new Promise(() => {});
    
  } catch (error) {
    console.error('Error during test:', error);
    await page.screenshot({ path: 'error-screenshot.png' });
    console.log('Error screenshot saved');
  }
})();