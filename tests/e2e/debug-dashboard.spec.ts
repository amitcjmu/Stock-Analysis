import { test, expect } from '@playwright/test';

test.describe('Debug Dashboard', () => {
  test('Check dashboard navigation structure', async ({ page }) => {
    test.setTimeout(60000);

    // Login first
    console.log('🔐 Logging in...');
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 30000 });

    console.log('✅ Logged in, now on dashboard');
    console.log('Current URL:', page.url());

    // Wait for page to fully load
    await page.waitForTimeout(3000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/dashboard-debug.png', fullPage: true });

    // Check for navigation elements
    const navElements = await page.locator('nav a, nav button, [role="navigation"] a, [role="navigation"] button').all();
    console.log('Navigation elements found:', navElements.length);

    for (let i = 0; i < navElements.length; i++) {
      const element = navElements[i];
      const text = await element.textContent();
      const href = await element.getAttribute('href');
      console.log(`Nav ${i}: "${text}" href="${href}"`);
    }

    // Look for text containing "discovery"
    const discoveryElements = await page.locator('text=/discovery/i').all();
    console.log('Discovery elements found:', discoveryElements.length);

    for (let i = 0; i < discoveryElements.length; i++) {
      const element = discoveryElements[i];
      const text = await element.textContent();
      const tagName = await element.evaluate(el => el.tagName);
      console.log(`Discovery ${i}: "${text}" (${tagName})`);
    }

    // Look for any clickable elements
    const clickableElements = await page.locator('a, button').all();
    console.log('Clickable elements found:', clickableElements.length);

    const discoveryRelated = [];
    for (let i = 0; i < Math.min(clickableElements.length, 50); i++) { // Limit to first 50
      const element = clickableElements[i];
      const text = await element.textContent();
      if (text && text.toLowerCase().includes('discover')) {
        discoveryRelated.push(text.trim());
      }
    }

    console.log('Discovery-related clickable elements:', discoveryRelated);

    // Check for sidebar or menu
    const sidebar = await page.locator('aside, .sidebar, [role="complementary"]').count();
    const menu = await page.locator('.menu, [role="menu"]').count();

    console.log('Sidebar elements:', sidebar);
    console.log('Menu elements:', menu);

    expect(true).toBe(true); // Always pass, this is for debugging
  });
});
