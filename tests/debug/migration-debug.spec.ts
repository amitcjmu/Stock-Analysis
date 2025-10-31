import { test, expect } from '@playwright/test';

test.describe('Debug - Check Page Structure', () => {
  test('inspect page elements', async ({ page }) => {
    await page.goto('http://localhost:8081');
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot
    await page.screenshot({ path: 'test-results/homepage.png', fullPage: true });
    
    // Log the page title
    const title = await page.title();
    console.log('Page title:', title);
    
    // Check what elements exist
    const hasNav = await page.locator('nav').count();
    const hasHeader = await page.locator('header').count();
    const hasMain = await page.locator('main').count();
    const hasDiv = await page.locator('div').count();
    
    console.log('Found elements:');
    console.log('- nav tags:', hasNav);
    console.log('- header tags:', hasHeader);
    console.log('- main tags:', hasMain);
    console.log('- div tags:', hasDiv);
    
    // Get some text content
    const bodyText = await page.textContent('body');
    console.log('Page contains text:', bodyText?.substring(0, 200));
  });
});
