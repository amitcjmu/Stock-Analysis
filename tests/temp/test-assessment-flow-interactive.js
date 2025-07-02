import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // Enable comprehensive console logging
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('Assessment') || text.includes('ERROR') || text.includes('API Call') || text.includes('flow')) {
      console.log('CONSOLE:', text);
    }
  });
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText));
  page.on('response', response => {
    if (response.url().includes('assessment')) {
      console.log('API RESPONSE:', response.status(), response.url());
    }
  });

  try {
    console.log('=== INTERACTIVE ASSESSMENT FLOW TEST ===');
    
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
    await page.waitForTimeout(5000); // Give more time for demo component to load

    console.log('4. Analyzing page content...');
    
    // Check for demo mode indicator
    const hasDemoIndicator = await page.locator('text=Demo Mode').count() > 0;
    console.log('Demo mode indicator found:', hasDemoIndicator);

    // Look for all input elements more broadly
    const allInputs = await page.$$('input');
    console.log(`Found ${allInputs.length} input elements total`);

    // Look for checkboxes specifically  
    const checkboxes = await page.$$('input[type="checkbox"]');
    console.log(`Found ${checkboxes.length} checkboxes`);

    // Look for demo applications by text content
    const appElements = await page.$$eval('*', elements => {
      return elements
        .filter(el => el.textContent && (
          el.textContent.includes('Customer Portal') ||
          el.textContent.includes('Inventory Management') ||
          el.textContent.includes('Payment Processing') ||
          el.textContent.includes('Analytics Dashboard')
        ))
        .map(el => ({ tag: el.tagName, text: el.textContent.trim().substring(0, 100) }))
        .slice(0, 5);
    });
    console.log('Demo applications found:', appElements.length, appElements);

    // Try to find and click Select All button
    const selectAllButton = await page.$('button:has-text("Select All")');
    if (selectAllButton) {
      console.log('5. Clicking Select All button...');
      await selectAllButton.click();
      await page.waitForTimeout(1000);
      
      // Check if checkboxes are now checked
      const checkedBoxes = await page.$$('input[type="checkbox"]:checked');
      console.log(`After Select All: ${checkedBoxes.length} checkboxes are checked`);
      
      // Look for Initialize button
      const initializeButton = await page.$('button:has-text("Start Assessment")');
      if (initializeButton) {
        console.log('6. Clicking Initialize button...');
        await initializeButton.click();
        await page.waitForTimeout(3000);
        
        // Check current URL after initialization
        const currentUrl = page.url();
        console.log('7. URL after initialization:', currentUrl);
        
        if (currentUrl.includes('/assessment/') && currentUrl.length > 'http://localhost:8081/assessment'.length) {
          console.log('8. ✅ Assessment flow initialized successfully! Redirected to flow page.');
          
          // Look for architecture phase content
          const pageContent = await page.textContent('body');
          const hasArchitectureContent = pageContent.includes('Architecture') || 
                                       pageContent.includes('Standards') ||
                                       pageContent.includes('Minimums');
          
          if (hasArchitectureContent) {
            console.log('9. ✅ Architecture phase content detected!');
          } else {
            console.log('9. ⚠️ Flow initialized but no architecture content visible yet.');
          }
        } else {
          console.log('8. ⚠️ Assessment initialization may have failed or is still processing');
          
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
            console.log('Errors found:', errors.slice(0, 3));
          }
        }
      } else {
        console.log('6. ⚠️ Initialize button not found after selecting applications');
      }
    } else {
      console.log('5. ⚠️ Select All button not found');
    }

    // Take final screenshot
    await page.screenshot({ path: 'assessment-flow-interactive-test.png', fullPage: true });
    console.log('10. Screenshot saved as assessment-flow-interactive-test.png');

    console.log('=== INTERACTIVE TEST COMPLETE ===');

  } catch (error) {
    console.error('Error during interactive test:', error.message);
    await page.screenshot({ path: 'assessment-flow-interactive-error.png', fullPage: true });
  } finally {
    await page.waitForTimeout(5000);
    await browser.close();
  }
})();