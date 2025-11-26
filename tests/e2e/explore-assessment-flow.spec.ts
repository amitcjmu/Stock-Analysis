/**
 * Exploration script - Navigate through Assessment Flow to understand workflow
 *
 * Purpose: Manually explore the flow to understand:
 * 1. How to get to Canada Life context
 * 2. How Assessment Overview page works
 * 3. How to start a new assessment
 * 4. How asset selection works for collection flow
 */
import { test, expect } from '@playwright/test';

test('Explore Assessment Flow in Canada Life context', async ({ page }) => {
  // Set slow motion to observe what's happening
  test.setTimeout(300000); // 5 minutes for exploration

  console.log('=== STEP 1: Navigate to app ===');
  await page.goto('http://localhost:8081');
  await page.waitForLoadState('networkidle');

  // Take screenshot to see current state
  await page.screenshot({ path: '/tmp/explore-1-landing.png', fullPage: true });
  console.log('Screenshot saved: /tmp/explore-1-landing.png');

  // Wait to see what's on the page
  await page.waitForTimeout(2000);

  console.log('=== STEP 2: Look for navigation elements ===');
  // Log all navigation links
  const navLinks = await page.locator('nav a, [role="navigation"] a, aside a').all();
  console.log('Found ' + navLinks.length + ' nav links:');
  for (const link of navLinks.slice(0, 10)) {
    const text = await link.textContent();
    const href = await link.getAttribute('href');
    console.log('  - "' + (text?.trim() || '') + '" -> ' + href);
  }

  console.log('=== STEP 3: Look for client/engagement selectors ===');
  // Look for dropdowns that might select Canada Life
  const selects = await page.locator('select, [role="combobox"], [role="listbox"]').all();
  console.log('Found ' + selects.length + ' select elements');

  // Look for buttons
  const buttons = await page.locator('button').all();
  console.log('Found ' + buttons.length + ' buttons:');
  for (const btn of buttons.slice(0, 15)) {
    const text = await btn.textContent();
    console.log('  - Button: "' + (text?.trim().substring(0, 50) || '') + '"');
  }

  console.log('=== STEP 4: Check page URL and title ===');
  const currentUrl = page.url();
  const pageTitle = await page.title();
  console.log('Current URL: ' + currentUrl);
  console.log('Page title: ' + pageTitle);

  // Look for Assessment-related text
  const assessmentText = await page.locator('text=/assessment/i').all();
  console.log('Found ' + assessmentText.length + ' elements with "assessment" text');

  // Look for Canada Life text
  const canadaLifeText = await page.locator('text=/canada life/i').all();
  console.log('Found ' + canadaLifeText.length + ' elements with "Canada Life" text');

  await page.screenshot({ path: '/tmp/explore-2-analysis.png', fullPage: true });

  console.log('=== STEP 5: Try to find and click Assessment link ===');
  // Try different ways to find Assessment
  const assessmentLink = page.locator('a:has-text("Assessment"), button:has-text("Assessment")').first();
  if (await assessmentLink.isVisible()) {
    console.log('Found Assessment link, clicking...');
    await assessmentLink.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/explore-3-after-assessment-click.png', fullPage: true });
  } else {
    console.log('Assessment link not immediately visible');
    // Try sidebar navigation
    const sidebarItems = await page.locator('[class*="sidebar"], [class*="nav"], aside').locator('a, button').all();
    console.log('Sidebar items found: ' + sidebarItems.length);
    for (const item of sidebarItems.slice(0, 10)) {
      const text = await item.textContent();
      console.log('  - Sidebar: "' + (text?.trim().substring(0, 50) || '') + '"');
    }
  }

  // Final screenshot
  await page.screenshot({ path: '/tmp/explore-final.png', fullPage: true });
  console.log('=== Exploration complete ===');
  console.log('Check screenshots at /tmp/explore-*.png');
});
