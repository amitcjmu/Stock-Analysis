import { test, expect } from '@playwright/test';

test.describe('Debug Discovery Page', () => {
  test('Investigate discovery page structure and upload areas', async ({ page }) => {
    test.setTimeout(90000);

    // Login first
    console.log('🔐 Logging in...');
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"]', 'analyst@demo-corp.com');
    await page.fill('input[type="password"]', 'Demo123!');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    console.log('✅ Logged in, current URL:', page.url());

    // Navigate to discovery
    console.log('📁 Navigating to discovery...');
    await page.goto('http://localhost:8081/discovery');
    await page.waitForTimeout(3000);

    console.log('📄 On discovery page, URL:', page.url());

    // Take full page screenshot
    await page.screenshot({ path: 'test-results/discovery-page-full.png', fullPage: true });

    // Check page title and main content
    const title = await page.title();
    console.log('Page title:', title);

    // Look for main navigation/tabs
    const tabs = await page.locator('button[role="tab"], .tab, [data-testid*="tab"]').all();
    console.log('Tabs found:', tabs.length);

    for (let i = 0; i < tabs.length; i++) {
      const tab = tabs[i];
      const text = await tab.textContent();
      const isSelected = await tab.getAttribute('aria-selected');
      console.log(`Tab ${i}: "${text}" (selected: ${isSelected})`);
    }

    // Look for specific discovery-related elements
    const dataImportElements = await page.locator('text=/data import|import|upload|cmdb/i').all();
    console.log('Data import related elements:', dataImportElements.length);

    for (let i = 0; i < Math.min(dataImportElements.length, 10); i++) {
      const element = dataImportElements[i];
      const text = await element.textContent();
      const tagName = await element.evaluate(el => el.tagName);
      console.log(`Import element ${i}: "${text}" (${tagName})`);
    }

    // Look for upload areas with different selectors
    const uploadSelectors = [
      '.border-dashed',
      '[data-testid="upload-area"]',
      '.upload-zone',
      '.upload-area',
      '.dropzone',
      'input[type="file"]',
      '[accept*="csv"]',
      'text=/upload|drop/i'
    ];

    for (const selector of uploadSelectors) {
      const elements = await page.locator(selector).count();
      if (elements > 0) {
        console.log(`✅ Found ${elements} elements with selector: ${selector}`);

        // Get details about these elements
        const foundElements = await page.locator(selector).all();
        for (let i = 0; i < foundElements.length; i++) {
          const element = foundElements[i];
          const text = await element.textContent();
          const isVisible = await element.isVisible();
          console.log(`  Element ${i}: "${text?.slice(0, 50)}..." (visible: ${isVisible})`);
        }
      } else {
        console.log(`❌ No elements found with selector: ${selector}`);
      }
    }

    // Check for any buttons that might lead to upload
    const buttons = await page.locator('button').all();
    console.log('Buttons found:', buttons.length);

    const uploadButtons = [];
    for (let i = 0; i < Math.min(buttons.length, 20); i++) {
      const button = buttons[i];
      const text = await button.textContent();
      if (text && (
        text.toLowerCase().includes('upload') ||
        text.toLowerCase().includes('import') ||
        text.toLowerCase().includes('add') ||
        text.toLowerCase().includes('create')
      )) {
        uploadButtons.push(text.trim());
      }
    }

    console.log('Upload-related buttons:', uploadButtons);

    // Look for any links that might lead to upload pages
    const links = await page.locator('a').all();
    console.log('Links found:', links.length);

    const uploadLinks = [];
    for (let i = 0; i < Math.min(links.length, 20); i++) {
      const link = links[i];
      const text = await link.textContent();
      const href = await link.getAttribute('href');
      if ((text && text.toLowerCase().includes('import')) ||
          (href && href.includes('import'))) {
        uploadLinks.push({ text: text?.trim(), href });
      }
    }

    console.log('Import-related links:', uploadLinks);

    // Check if we need to navigate to a specific tab or section
    const importTab = page.locator('button:has-text("Data Import"), button:has-text("Import"), a[href*="import"]').first();
    if (await importTab.isVisible()) {
      console.log('🔍 Found import tab/link, clicking...');
      await importTab.click();
      await page.waitForTimeout(2000);

      console.log('📄 After clicking import, URL:', page.url());
      await page.screenshot({ path: 'test-results/discovery-import-page.png', fullPage: true });

      // Re-check for upload areas after navigation
      const uploadAreasAfterNav = await page.locator('.border-dashed, [data-testid="upload-area"], .upload-zone, input[type="file"]').count();
      console.log('Upload areas after navigation:', uploadAreasAfterNav);
    }

    // Check for any error messages or loading states
    const errorMessages = await page.locator('text=/error|failed|not found/i').count();
    const loadingElements = await page.locator('text=/loading|spinner/i, .spinner, .loading').count();

    console.log('Error messages:', errorMessages);
    console.log('Loading elements:', loadingElements);

    expect(true).toBe(true); // Always pass, this is for debugging
  });
});
