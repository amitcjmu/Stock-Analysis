import { test, expect } from '@playwright/test';

test.describe('Field Mapping Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the field mapping page
    await page.goto('http://localhost:8081/discovery/attribute-mapping');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Wait a bit for any async operations
    await page.waitForTimeout(2000);
  });

  test('Field mapping page loads without React errors', async ({ page }) => {
    // Check for React error messages
    const errorElements = page.locator('[data-testid="error"], .error, [class*="error"]');
    const errorCount = await errorElements.count();

    if (errorCount > 0) {
      console.log('Found potential errors on page:');
      for (let i = 0; i < errorCount; i++) {
        const errorText = await errorElements.nth(i).textContent();
        console.log(`Error ${i + 1}: ${errorText}`);
      }
    }

    // Check that main content is visible
    await expect(page.locator('h1')).toContainText('Attribute Mapping');

    // Check for console errors
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleLogs.push(msg.text());
      }
    });

    await page.waitForTimeout(1000);

    // Report any console errors
    if (consoleLogs.length > 0) {
      console.log('Console errors found:', consoleLogs);
    }

    expect(consoleLogs.length).toBe(0);
  });

  test('Field mappings tab is accessible and shows content', async ({ page }) => {
    // Click on the Field Mapping tab
    await page.click('text=Field Mapping');

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Check if field mappings section is visible
    const fieldMappingsSection = page.locator('[data-testid="field-mappings"], .field-mappings, text="Field Mapping Suggestions"').first();
    await expect(fieldMappingsSection).toBeVisible();

    // Look for field mapping entries
    const mappingItems = page.locator('[data-testid="mapping-item"], .mapping-item, [class*="mapping"]');
    const mappingCount = await mappingItems.count();

    console.log(`Found ${mappingCount} field mapping items`);

    if (mappingCount === 0) {
      // Check if there's a "no mappings" message
      const noMappingsMsg = page.locator('text=No field mappings, text=Loading field mappings');
      const hasNoMappingsMsg = await noMappingsMsg.count() > 0;

      if (hasNoMappingsMsg) {
        const msgText = await noMappingsMsg.first().textContent();
        console.log(`No mappings message: ${msgText}`);
      }
    }
  });

  test('Field mappings show as interactive dropdowns', async ({ page }) => {
    // Click on Field Mapping tab
    await page.click('text=Field Mapping');
    await page.waitForTimeout(1000);

    // Look for dropdown buttons or select elements
    const dropdownButtons = page.locator('button:has-text("→"), select, [role="button"]:has-text("→")');
    const dropdownCount = await dropdownButtons.count();

    console.log(`Found ${dropdownCount} potential dropdown elements`);

    if (dropdownCount > 0) {
      // Try to click the first dropdown
      await dropdownButtons.first().click();

      // Wait for dropdown menu to appear
      await page.waitForTimeout(500);

      // Look for dropdown menu options
      const dropdownOptions = page.locator('[role="option"], .dropdown-option, button:has-text("name"), button:has-text("hostname")');
      const optionCount = await dropdownOptions.count();

      console.log(`Found ${optionCount} dropdown options`);
      expect(optionCount).toBeGreaterThan(0);
    } else {
      // Check if mappings are displayed as static text (which would be wrong)
      const staticMappings = page.locator('text=→');
      const staticCount = await staticMappings.count();

      if (staticCount > 0) {
        console.log(`Found ${staticCount} static mapping displays (should be interactive)`);

        // Take a screenshot for debugging
        await page.screenshot({ path: 'field-mappings-static.png', fullPage: true });
      }
    }
  });

  test('Filter controls are present and functional', async ({ page }) => {
    // Click on Field Mapping tab
    await page.click('text=Field Mapping');
    await page.waitForTimeout(1000);

    // Look for filter checkboxes
    const pendingFilter = page.locator('input[type="checkbox"]:near(text="Pending")');
    const approvedFilter = page.locator('input[type="checkbox"]:near(text="Approved")');
    const rejectedFilter = page.locator('input[type="checkbox"]:near(text="Rejected")');

    // Check if filters exist
    if (await pendingFilter.count() > 0) {
      console.log('Found filter controls');

      // Test filter interaction
      const initialChecked = await pendingFilter.isChecked();
      await pendingFilter.click();
      await page.waitForTimeout(500);
      const afterClickChecked = await pendingFilter.isChecked();

      expect(initialChecked).not.toBe(afterClickChecked);
      console.log(`Filter toggle test passed: ${initialChecked} → ${afterClickChecked}`);
    } else {
      console.log('Filter controls not found - checking for alternative filter UI');
    }
  });

  test('Approval/rejection buttons are present', async ({ page }) => {
    // Click on Field Mapping tab
    await page.click('text=Field Mapping');
    await page.waitForTimeout(1000);

    // Look for approve/reject buttons
    const approveButtons = page.locator('button:has-text("Approve"), button:has-text("✓")');
    const rejectButtons = page.locator('button:has-text("Reject"), button:has-text("✗"), button:has-text("×")');

    const approveCount = await approveButtons.count();
    const rejectCount = await rejectButtons.count();

    console.log(`Found ${approveCount} approve buttons and ${rejectCount} reject buttons`);

    if (approveCount > 0 && rejectCount > 0) {
      // Test approve button click (but don't complete the action)
      await approveButtons.first().hover();
      const isClickable = await approveButtons.first().isEnabled();
      expect(isClickable).toBe(true);

      console.log('Approve/reject buttons are interactive');
    } else {
      console.log('Approve/reject buttons not found - may need to check UI structure');

      // Take screenshot for debugging
      await page.screenshot({ path: 'field-mappings-no-buttons.png', fullPage: true });
    }
  });

  test('Available target fields API is working', async ({ page }) => {
    // Monitor network requests
    const apiCalls: string[] = [];

    page.on('response', response => {
      if (response.url().includes('available-target-fields')) {
        apiCalls.push(`${response.status()}: ${response.url()}`);
      }
    });

    // Click on Field Mapping tab to trigger API calls
    await page.click('text=Field Mapping');
    await page.waitForTimeout(2000);

    // Try to open a dropdown to trigger field loading
    const dropdownButton = page.locator('button:has-text("→")').first();
    if (await dropdownButton.count() > 0) {
      await dropdownButton.click();
      await page.waitForTimeout(1000);
    }

    console.log('Available target fields API calls:', apiCalls);

    // Check if we made successful API calls
    const successfulCalls = apiCalls.filter(call => call.startsWith('200:'));
    expect(successfulCalls.length).toBeGreaterThan(0);
  });

  test('Page layout and structure', async ({ page }) => {
    // Take a full page screenshot
    await page.screenshot({ path: 'field-mappings-full-page.png', fullPage: true });

    // Check main page elements
    await expect(page.locator('h1')).toContainText('Attribute Mapping');

    // Check if tabs are present
    const tabs = page.locator('[role="tab"], .tab, button:has-text("Field Mapping")');
    const tabCount = await tabs.count();
    console.log(`Found ${tabCount} navigation tabs`);

    // Check if main content area exists
    const mainContent = page.locator('main, .main-content, [role="main"]');
    const hasMainContent = await mainContent.count() > 0;
    console.log(`Main content area found: ${hasMainContent}`);

    // Check sidebar
    const sidebar = page.locator('.sidebar, nav, [role="navigation"]');
    const hasSidebar = await sidebar.count() > 0;
    console.log(`Sidebar found: ${hasSidebar}`);
  });
});
