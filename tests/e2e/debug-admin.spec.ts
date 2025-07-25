import { test, expect } from '@playwright/test';

test('Debug Admin User Approvals Page', async ({ page }) => {
  // Clear localStorage and login
  await page.goto('http://localhost:8081/');
  await page.evaluate(() => localStorage.clear());
  await page.goto('http://localhost:8081/login');
  await page.waitForLoadState('networkidle');

  // Login
  await page.fill('input[type="email"]', 'admin@aiforce.com');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('http://localhost:8081/');

  // Navigate to admin
  await page.goto('http://localhost:8081/admin');
  await page.waitForLoadState('networkidle');

  // Take screenshot of admin dashboard
  await page.screenshot({ path: 'admin-dashboard-debug.png', fullPage: true });

  console.log('Current URL:', page.url());

  // Try to navigate to user approvals
  console.log('Looking for User Approvals link...');
  const userApprovalsLink = page.locator('a[href="/admin/users/approvals"]').first();
  if (await userApprovalsLink.isVisible()) {
    console.log('✅ Found User Approvals link');
    await userApprovalsLink.click();
    await page.waitForLoadState('networkidle');

    console.log('After click URL:', page.url());

    // Take screenshot of user approvals page
    await page.screenshot({ path: 'user-approvals-debug.png', fullPage: true });

    // Look for all h1 elements
    const allH1s = await page.locator('h1').all();
    console.log(`Found ${allH1s.length} h1 elements:`);

    for (let i = 0; i < allH1s.length; i++) {
      const text = await allH1s[i].textContent();
      console.log(`H1 ${i}: "${text}"`);
    }

    // Look for Active Users tab (the button)
    const activeUsersTab = page.locator('button:has-text("Active Users")');
    if (await activeUsersTab.isVisible()) {
      console.log('✅ Found Active Users tab');
      await activeUsersTab.click();
      await page.waitForLoadState('networkidle');

      // Take screenshot after clicking Active Users
      await page.screenshot({ path: 'active-users-debug.png', fullPage: true });

      // Look for user rows
      const userRows = await page.locator('tr, .user-row, [data-testid*="user"]').all();
      console.log(`Found ${userRows.length} potential user row elements`);

      // Look for any tables
      const tables = await page.locator('table').all();
      console.log(`Found ${tables.length} table elements`);

      if (tables.length > 0) {
        const tableRows = await page.locator('table tr').all();
        console.log(`Found ${tableRows.length} table rows`);
      }

    } else {
      console.log('❌ Active Users tab not found');
    }

  } else {
    console.log('❌ User Approvals link not found');

    // Look for all navigation links
    const allLinks = await page.locator('a').all();
    console.log(`Found ${allLinks.length} links total`);

    for (let i = 0; i < Math.min(allLinks.length, 10); i++) {
      const href = await allLinks[i].getAttribute('href');
      const text = await allLinks[i].textContent();
      console.log(`Link ${i}: href="${href}", text="${text}"`);
    }
  }
});
