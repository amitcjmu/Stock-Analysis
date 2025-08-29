import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:8081';
const ADMIN_CREDENTIALS = {
  email: 'chocka@gmail.com',
  password: 'Password123!'
};

// Utility functions
async function loginAsAdmin(page: Page) {
  console.log('🔐 Attempting admin login...');
  await page.goto(`${BASE_URL}/login`);

  // Wait for the page to load completely
  await page.waitForLoadState('networkidle');

  // Check if already logged in by looking for redirect
  if (!page.url().includes('/login')) {
    console.log('✅ Already logged in, redirected to: ' + page.url());
    return page.url();
  }

  await page.waitForSelector('input[name="email"], input[type="email"]', { timeout: 10000 });
  await page.fill('input[name="email"], input[type="email"]', ADMIN_CREDENTIALS.email);
  await page.fill('input[name="password"], input[type="password"]', ADMIN_CREDENTIALS.password);

  await page.click('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")');
  await page.waitForURL(url => !url.includes('/login'), { timeout: 15000 });

  console.log(`✅ Login successful, current URL: ${page.url()}`);
  return page.url();
}

async function captureConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];
  const networkErrors: string[] = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(`Console Error: ${msg.text()}`);
    }
  });

  page.on('pageerror', error => {
    errors.push(`Page Error: ${error.message}`);
  });

  page.on('response', response => {
    if (!response.ok() && response.status() >= 400) {
      networkErrors.push(`Network ${response.status()}: ${response.url()}`);
    }
  });

  // Return combined errors
  return [...errors, ...networkErrors];
}

async function takeScreenshotWithContext(page: Page, name: string): Promise<void> {
  await page.screenshot({
    path: `tests/e2e/test-results/admin-post-fixes-${name}-${Date.now()}.png`,
    fullPage: true
  });
  console.log(`📸 Screenshot captured: admin-post-fixes-${name}`);
}

// Main test suite
test.describe('Admin Dashboard Post-Fix Verification', () => {
  let allErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    allErrors = await captureConsoleErrors(page);
  });

  test('Verify Login and Authentication Works', async ({ page }) => {
    console.log('\n🎯 TEST: Login and Authentication');
    console.log('==================================');

    await takeScreenshotWithContext(page, 'login-page');

    const redirectUrl = await loginAsAdmin(page);
    await takeScreenshotWithContext(page, 'post-login');

    // Verify admin was redirected correctly
    expect(redirectUrl).toMatch(/\/(admin|dashboard)/);
    console.log('✅ Login and redirect successful');
  });

  test('Check Admin Dashboard Main Data Loading', async ({ page }) => {
    console.log('\n🎯 TEST: Admin Dashboard Main Data Loading');
    console.log('==========================================');

    await loginAsAdmin(page);

    // Navigate to admin dashboard
    await page.goto(`${BASE_URL}/admin/dashboard`);
    await page.waitForLoadState('networkidle');
    await takeScreenshotWithContext(page, 'dashboard-main');

    // Check page title and basic loading
    const title = await page.title();
    console.log(`📄 Page title: ${title}`);

    // Look for dashboard elements
    const hasHeaders = await page.locator('h1, h2, h3').count();
    console.log(`📊 Headers found: ${hasHeaders}`);

    const hasStatsCards = await page.locator('[class*="card"], [class*="stat"], [class*="metric"]').count();
    console.log(`📈 Statistics cards found: ${hasStatsCards}`);

    // Check for demo data warnings
    const demoWarnings = await page.locator('text=/demo/i, text=/sample/i, text=/placeholder/i').count();
    console.log(`⚠️ Demo/sample data indicators: ${demoWarnings}`);

    // Extract page text to look for specific numbers
    const pageText = await page.textContent('body');
    const numbers = pageText?.match(/\b\d+\b/g) || [];
    console.log(`🔢 Numbers found: ${numbers.slice(0, 10).join(', ')}${numbers.length > 10 ? '...' : ''}`);

    // Check for specific demo data patterns
    const hasDemoData = numbers.includes('12') && numbers.includes('25') && numbers.includes('45');
    console.log(`🎭 Using demo data patterns: ${hasDemoData}`);

    expect(hasHeaders).toBeGreaterThan(0);
    console.log('✅ Dashboard main page loaded');
  });

  test('Test Client Management API Endpoints', async ({ page }) => {
    console.log('\n🎯 TEST: Client Management API Endpoints');
    console.log('========================================');

    await loginAsAdmin(page);

    // Navigate to client management
    await page.goto(`${BASE_URL}/admin/clients`);
    await page.waitForLoadState('networkidle');
    await takeScreenshotWithContext(page, 'clients-page');

    // Check for client data loading
    const hasClientData = await page.locator('table, [role="table"], [class*="client"], [class*="card"]').count() > 0;
    console.log(`👥 Client data elements found: ${hasClientData}`);

    // Check for empty states
    const emptyStateMessages = await page.locator('text=/no.*client/i, text=/empty/i, text=/no.*data/i').count();
    console.log(`📭 Empty state messages: ${emptyStateMessages}`);

    // Wait a bit for async data loading
    await page.waitForTimeout(3000);
    await takeScreenshotWithContext(page, 'clients-after-loading');

    console.log('✅ Client management page tested');
  });

  test('Test Engagement Management API Endpoints', async ({ page }) => {
    console.log('\n🎯 TEST: Engagement Management API Endpoints');
    console.log('===========================================');

    await loginAsAdmin(page);

    // Navigate to engagement management
    await page.goto(`${BASE_URL}/admin/engagements`);
    await page.waitForLoadState('networkidle');
    await takeScreenshotWithContext(page, 'engagements-page');

    // Check for engagement data loading
    const hasEngagementData = await page.locator('table, [role="table"], [class*="engagement"], [class*="card"]').count() > 0;
    console.log(`🏢 Engagement data elements found: ${hasEngagementData}`);

    // Check for empty states
    const emptyStateMessages = await page.locator('text=/no.*engagement/i, text=/empty/i, text=/no.*data/i').count();
    console.log(`📭 Empty state messages: ${emptyStateMessages}`);

    // Wait for async data loading
    await page.waitForTimeout(3000);
    await takeScreenshotWithContext(page, 'engagements-after-loading');

    console.log('✅ Engagement management page tested');
  });

  test('Network and Console Error Detection', async ({ page }) => {
    console.log('\n🎯 TEST: Network and Console Error Detection');
    console.log('============================================');

    const allNetworkRequests: { url: string; status: number; method: string }[] = [];
    const apiErrors: string[] = [];

    // Track all network requests
    page.on('response', response => {
      allNetworkRequests.push({
        url: response.url(),
        status: response.status(),
        method: response.request().method()
      });

      // Focus on API errors
      if (response.url().includes('/api/') && !response.ok()) {
        apiErrors.push(`${response.status()} ${response.method} ${response.url()}`);
      }
    });

    await loginAsAdmin(page);

    // Test multiple admin pages
    const testPages = [
      `${BASE_URL}/admin/dashboard`,
      `${BASE_URL}/admin/clients`,
      `${BASE_URL}/admin/engagements`
    ];

    for (const testPage of testPages) {
      console.log(`🔍 Testing: ${testPage}`);

      await page.goto(testPage);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000); // Wait for async operations
    }

    await takeScreenshotWithContext(page, 'error-detection-final');

    // Report findings
    console.log(`📊 Total network requests: ${allNetworkRequests.length}`);
    console.log(`❌ API errors found: ${apiErrors.length}`);

    if (apiErrors.length > 0) {
      console.log('🚨 API Errors:');
      apiErrors.forEach(error => console.log(`  - ${error}`));
    }

    // Filter for admin API calls specifically
    const adminApiRequests = allNetworkRequests.filter(req =>
      req.url.includes('/api/v1/admin/') ||
      req.url.includes('/admin/') && req.url.includes('/api/')
    );

    console.log(`👑 Admin API requests made: ${adminApiRequests.length}`);
    if (adminApiRequests.length > 0) {
      console.log('Admin API calls:');
      adminApiRequests.forEach(req =>
        console.log(`  - ${req.status} ${req.method} ${req.url}`)
      );
    }

    console.log('✅ Error detection completed');
  });

  test('Backend API Endpoint Verification', async ({ page }) => {
    console.log('\n🎯 TEST: Backend API Endpoint Verification');
    console.log('==========================================');

    // Test direct API calls to check if endpoints exist
    const apiEndpoints = [
      '/api/v1/admin/clients/',
      '/api/v1/admin/engagements/',
      '/api/v1/admin/clients/dashboard/stats',
      '/api/v1/admin/engagements/dashboard/stats',
      '/api/v1/auth/admin/dashboard-stats'
    ];

    const endpointResults: { endpoint: string; status: number; exists: boolean }[] = [];

    for (const endpoint of apiEndpoints) {
      try {
        const response = await page.request.get(`${BASE_URL.replace('8081', '8000')}${endpoint}`);
        endpointResults.push({
          endpoint,
          status: response.status(),
          exists: response.status() !== 404
        });
        console.log(`${response.status() === 404 ? '❌' : '✅'} ${endpoint} -> ${response.status()}`);
      } catch (error) {
        endpointResults.push({
          endpoint,
          status: 500,
          exists: false
        });
        console.log(`❌ ${endpoint} -> ERROR: ${error}`);
      }
    }

    const workingEndpoints = endpointResults.filter(r => r.exists).length;
    const totalEndpoints = endpointResults.length;

    console.log(`📊 Admin endpoints working: ${workingEndpoints}/${totalEndpoints}`);
    console.log('✅ Backend API verification completed');
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Final screenshot
    await takeScreenshotWithContext(page, `final-${testInfo.title.replace(/\s+/g, '-')}`);

    // Report any accumulated errors
    if (allErrors.length > 0) {
      console.log('\n🚨 ISSUES DETECTED IN THIS TEST:');
      console.log('=================================');
      allErrors.forEach(error => console.log(`  - ${error}`));
    }
  });
});

// Generate final report
test.afterAll(async () => {
  console.log('\n📊 ADMIN DASHBOARD POST-FIX TEST SUMMARY');
  console.log('========================================');
  console.log('Tests completed to verify admin dashboard fixes.');
  console.log('Check test-results/ directory for screenshots.');
  console.log('Review console output for detailed findings.');
});
