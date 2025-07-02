const { chromium } = require('playwright');

(async () => {
  // Launch browser in headed mode so we can see what's happening
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
    if (msg.type() === 'error') {
      console.log('CONSOLE ERROR:', msg.text());
    }
  });
  
  // Capture any page errors
  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    console.log('REQUEST FAILED:', request.url(), request.failure().errorText);
  });

  console.log('Opening http://localhost:8081...');
  
  try {
    // Navigate to the application
    await page.goto('http://localhost:8081', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    console.log('Page loaded successfully!');
    
    // Wait a bit to see if there are any delayed errors
    await page.waitForTimeout(3000);
    
    // Check for any error messages in the UI
    const errorElements = await page.$$('[class*="error"], [class*="Error"]');
    if (errorElements.length > 0) {
      console.log(`Found ${errorElements.length} error elements on the page`);
      
      for (const element of errorElements) {
        const text = await element.textContent();
        console.log('ERROR ELEMENT:', text);
      }
    }
    
    // Take a screenshot
    await page.screenshot({ path: 'assessment-flow-homepage.png', fullPage: true });
    console.log('Screenshot saved as assessment-flow-homepage.png');
    
    // Check if we can find any assessment-related links or buttons
    const assessmentElements = await page.$$('text=/assess/i');
    console.log(`Found ${assessmentElements.length} assessment-related elements`);
    
    // Keep browser open for manual inspection
    console.log('\nBrowser will remain open for manual inspection.');
    console.log('Press Ctrl+C to close...');
    
    // Keep the script running
    await new Promise(() => {});
    
  } catch (error) {
    console.error('Error during page load:', error);
    await page.screenshot({ path: 'error-screenshot.png' });
    console.log('Error screenshot saved');
  }
})();