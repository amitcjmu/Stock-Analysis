import { test, expect } from '@playwright/test';

test('Manual Admin Dashboard Verification', async ({ page }) => {
  console.log('🎯 Starting manual admin dashboard verification...');

  // Navigate to the application
  await page.goto('http://localhost:8081');

  // Wait for the page to load
  await page.waitForLoadState('networkidle', { timeout: 30000 });

  // Take initial screenshot
  await page.screenshot({ path: 'tests/e2e/test-results/manual-admin-initial.png', fullPage: true });

  console.log('📍 Current URL:', page.url());
  console.log('📄 Page title:', await page.title());

  // Check if we're on login page or redirected somewhere else
  const currentUrl = page.url();

  if (currentUrl.includes('/login')) {
    console.log('🔐 Found login page, attempting to log in...');

    // Wait for login form
    await page.waitForSelector('input[type="email"], input[name="email"]', { timeout: 10000 });

    // Fill login form
    await page.fill('input[type="email"], input[name="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"], input[name="password"]', 'Password123!');

    // Submit login
    await page.click('button[type="submit"]');

    // Wait for navigation after login
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    console.log('✅ Login attempted, current URL:', page.url());
  }

  // Take post-login screenshot
  await page.screenshot({ path: 'tests/e2e/test-results/manual-admin-post-login.png', fullPage: true });

  // Try to navigate to admin dashboard
  console.log('🎯 Attempting to navigate to admin dashboard...');
  await page.goto('http://localhost:8081/admin/dashboard');
  await page.waitForLoadState('networkidle', { timeout: 30000 });

  // Take admin dashboard screenshot
  await page.screenshot({ path: 'tests/e2e/test-results/manual-admin-dashboard.png', fullPage: true });

  console.log('📍 Admin dashboard URL:', page.url());
  console.log('📄 Admin dashboard title:', await page.title());

  // Count elements on the page
  const headings = await page.locator('h1, h2, h3').count();
  const cards = await page.locator('[class*="card"]').count();
  const tables = await page.locator('table').count();

  console.log(`📊 Elements found - Headings: ${headings}, Cards: ${cards}, Tables: ${tables}`);

  // Check for specific text content
  const pageText = await page.textContent('body');
  const hasClientText = pageText?.toLowerCase().includes('client');
  const hasEngagementText = pageText?.toLowerCase().includes('engagement');
  const hasAdminText = pageText?.toLowerCase().includes('admin');

  console.log(`📝 Content check - Client: ${hasClientText}, Engagement: ${hasEngagementText}, Admin: ${hasAdminText}`);

  // Try to navigate to client management
  console.log('🎯 Testing client management page...');
  await page.goto('http://localhost:8081/admin/clients');
  await page.waitForLoadState('networkidle', { timeout: 30000 });
  await page.screenshot({ path: 'tests/e2e/test-results/manual-admin-clients.png', fullPage: true });

  console.log('📍 Client management URL:', page.url());

  // Try to navigate to engagement management
  console.log('🎯 Testing engagement management page...');
  await page.goto('http://localhost:8081/admin/engagements');
  await page.waitForLoadState('networkidle', { timeout: 30000 });
  await page.screenshot({ path: 'tests/e2e/test-results/manual-admin-engagements.png', fullPage: true });

  console.log('📍 Engagement management URL:', page.url());

  // Check network requests for API calls
  const networkRequests: string[] = [];
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      networkRequests.push(`${response.status()} ${response.url()}`);
    }
  });

  // Reload the dashboard to capture network requests
  await page.goto('http://localhost:8081/admin/dashboard');
  await page.waitForLoadState('networkidle', { timeout: 30000 });

  console.log('🌐 API requests made:');
  networkRequests.forEach(request => console.log(`  - ${request}`));

  console.log('✅ Manual verification completed successfully');
});
