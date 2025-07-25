import { test, expect } from '@playwright/test';

test.describe('Simple Browser Test', () => {
  test('Frontend loads and basic functionality works', async ({ page }) => {
    console.log('🔍 Starting browser test...');

    // Set longer timeout for network operations
    test.setTimeout(60000);

    try {
      // Navigate to the main page first
      console.log('📍 Navigating to main page...');
      await page.goto('http://localhost:8081/', { waitUntil: 'domcontentloaded' });

      // Wait for page to be somewhat loaded
      await page.waitForTimeout(3000);

      // Take screenshot of main page
      await page.screenshot({ path: 'main-page.png', fullPage: true });

      console.log('📍 Navigating to attribute mapping...');
      // Navigate to attribute mapping page
      await page.goto('http://localhost:8081/discovery/attribute-mapping', {
        waitUntil: 'domcontentloaded'
      });

      // Wait for page to load
      await page.waitForTimeout(5000);

      // Take a screenshot to see what's actually rendered
      await page.screenshot({ path: 'attribute-mapping-page.png', fullPage: true });

      // Check if page loaded without major errors
      const pageTitle = await page.title();
      console.log(`📄 Page title: ${pageTitle}`);

      // Check for basic page elements
      const bodyContent = await page.locator('body').textContent();
      console.log(`📝 Page has content: ${bodyContent ? 'Yes' : 'No'}`);

      // Look for main heading
      const heading = page.locator('h1');
      const headingCount = await heading.count();
      console.log(`📋 Found ${headingCount} h1 headings`);

      if (headingCount > 0) {
        const headingText = await heading.first().textContent();
        console.log(`📋 Main heading: ${headingText}`);
      }

      // Look for Field Mapping tab
      const fieldMappingTab = page.locator('text=Field Mapping, text=Field Mappings, button:has-text("Field")').first();
      const hasFieldMappingTab = await fieldMappingTab.count() > 0;
      console.log(`🏷️ Field Mapping tab found: ${hasFieldMappingTab}`);

      if (hasFieldMappingTab) {
        console.log('🔥 Clicking Field Mapping tab...');
        await fieldMappingTab.click();
        await page.waitForTimeout(3000);

        // Take screenshot after clicking tab
        await page.screenshot({ path: 'field-mapping-tab.png', fullPage: true });

        // Look for field mapping content
        const mappingContent = page.locator('text=Field Mapping, text=mapping, text=source, text=target');
        const mappingContentCount = await mappingContent.count();
        console.log(`📊 Found ${mappingContentCount} mapping-related content elements`);

        // Look for dropdowns or buttons
        const interactiveElements = page.locator('button, select, [role="button"]');
        const interactiveCount = await interactiveElements.count();
        console.log(`🔘 Found ${interactiveCount} interactive elements`);

        // Look for specific field mapping elements
        const arrowElements = page.locator('text=→');
        const arrowCount = await arrowElements.count();
        console.log(`➡️ Found ${arrowCount} arrow elements (potential mappings)`);
      }

      // Check for any error messages
      const errorElements = page.locator('text=error, text=Error, .error, [class*="error"]');
      const errorCount = await errorElements.count();
      console.log(`❌ Found ${errorCount} potential error elements`);

      if (errorCount > 0) {
        for (let i = 0; i < Math.min(errorCount, 3); i++) {
          const errorText = await errorElements.nth(i).textContent();
          console.log(`❌ Error ${i + 1}: ${errorText}`);
        }
      }

      // Check console for errors
      const consoleLogs: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleLogs.push(msg.text());
        }
      });

      await page.waitForTimeout(2000);
      console.log(`🖥️ Console errors: ${consoleLogs.length}`);
      consoleLogs.forEach((log, i) => {
        console.log(`🖥️ Console error ${i + 1}: ${log}`);
      });

      // Basic test - page should load and have some content
      expect(bodyContent).toBeTruthy();

    } catch (error) {
      console.error('❌ Test failed with error:', error);
      await page.screenshot({ path: 'error-screenshot.png', fullPage: true });
      throw error;
    }
  });
});
