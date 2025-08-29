import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:8081';
const ADMIN_CREDENTIALS = {
  email: 'chocka@gmail.com',
  password: 'Password123!'
};

// Test data expectations
const EXPECTED_DEMO_DATA = {
  clients: { total: 12, active: 10 },
  engagements: { total: 25, active: 18 },
  users: { total: 45, pending: 8, approved: 37 }
};

// Utility functions
async function loginAsAdmin(page: Page) {
  console.log('🔐 Attempting admin login...');
  await page.goto('/login');

  await page.waitForSelector('input[name="email"], input[type="email"]', { timeout: 10000 });
  await page.fill('input[name="email"], input[type="email"]', ADMIN_CREDENTIALS.email);
  await page.fill('input[name="password"], input[type="password"]', ADMIN_CREDENTIALS.password);

  await page.click('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")');
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 15000 });

  console.log(`✅ Login successful, current URL: ${page.url()}`);
  return page.url();
}

async function captureConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(`Console Error: ${msg.text()}`);
    }
  });
  page.on('pageerror', error => {
    errors.push(`Page Error: ${error.message}`);
  });
  return errors;
}

async function captureNetworkFailures(page: Page): Promise<string[]> {
  const failures: string[] = [];
  page.on('response', response => {
    if (!response.ok() && response.status() >= 400) {
      failures.push(`Network Failure: ${response.status()} ${response.url()}`);
    }
  });
  return failures;
}

async function takeScreenshotWithContext(page: Page, name: string): Promise<void> {
  await page.screenshot({
    path: `test-results/admin-dashboard-${name}-${Date.now()}.png`,
    fullPage: true
  });
  console.log(`📸 Screenshot captured: admin-dashboard-${name}`);
}

// Main test suite
test.describe('Admin Dashboard Comprehensive Testing', () => {
  let consoleErrors: string[] = [];
  let networkFailures: string[] = [];

  test.beforeEach(async ({ page }) => {
    consoleErrors = await captureConsoleErrors(page);
    networkFailures = await captureNetworkFailures(page);
  });

  test('Admin Dashboard - Login and Authentication', async ({ page }) => {
    console.log('\n🎯 TEST: Admin Dashboard Login');
    console.log('=====================================');

    await takeScreenshotWithContext(page, 'login-page');

    const redirectUrl = await loginAsAdmin(page);
    await takeScreenshotWithContext(page, 'post-login');

    // Verify admin was redirected to admin dashboard or appropriate admin area
    expect(redirectUrl).toMatch(/\/(admin|dashboard)/);
    console.log('✅ Admin login successful and redirected correctly');
  });

  test('Admin Dashboard - Main Dashboard Data Loading', async ({ page }) => {
    console.log('\n🎯 TEST: Admin Dashboard Main Page');
    console.log('=====================================');

    await loginAsAdmin(page);

    // Navigate to admin dashboard
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');
    await takeScreenshotWithContext(page, 'main-dashboard');

    // Check if the page loaded successfully
    const title = await page.title();
    console.log(`📄 Page title: ${title}`);

    // Look for dashboard elements
    const dashboardExists = await page.locator('h1, h2, h3').count() > 0;
    console.log(`📊 Dashboard elements found: ${dashboardExists}`);

    // Check for statistics/metrics cards
    const statsCards = await page.locator('[class*="card"], [class*="stat"], [class*="metric"]').count();
    console.log(`📈 Statistics cards found: ${statsCards}`);

    // Look for demo data indicators or warnings
    const demoWarnings = await page.locator('text=/demo/i, text=/sample/i, [class*="warning"], [class*="demo"]').count();
    console.log(`⚠️  Demo data warnings found: ${demoWarnings}`);

    // Check for loading states
    const loadingIndicators = await page.locator('[class*="loading"], [class*="spinner"], text=/loading/i').count();
    console.log(`⏳ Loading indicators: ${loadingIndicators}`);

    // Test specific data points if visible
    const clientTotalText = await page.locator('text=/client/i').first().textContent();
    const engagementTotalText = await page.locator('text=/engagement/i').first().textContent();
    const userTotalText = await page.locator('text=/user/i').first().textContent();

    console.log(`👥 Client data: ${clientTotalText || 'Not found'}`);
    console.log(`🏢 Engagement data: ${engagementTotalText || 'Not found'}`);
    console.log(`👤 User data: ${userTotalText || 'Not found'}`);

    // Check if data looks like demo data
    const pageText = await page.textContent('body');
    const hasDemoNumbers = pageText?.includes('12') && pageText?.includes('25') && pageText?.includes('45');
    console.log(`🎭 Potentially using demo data: ${hasDemoNumbers}`);

    // Verify critical dashboard elements exist
    expect(dashboardExists).toBeTruthy();
    console.log('✅ Main dashboard loaded successfully');
  });

  test('Admin Dashboard - Client Management Page', async ({ page }) => {
    console.log('\n🎯 TEST: Client Management Page');
    console.log('=====================================');

    await loginAsAdmin(page);

    // Try different potential client management routes
    const clientRoutes = ['/admin/clients', '/admin/client-management', '/admin/dashboard/clients'];
    let clientPageFound = false;

    for (const route of clientRoutes) {
      try {
        await page.goto(route);
        await page.waitForLoadState('networkidle');
        const pageText = await page.textContent('body');

        if (pageText?.toLowerCase().includes('client') && !pageText?.includes('404')) {
          console.log(`✅ Client management page found at: ${route}`);
          clientPageFound = true;
          break;
        }
      } catch (error) {
        console.log(`❌ Route ${route} not accessible: ${error}`);
      }
    }

    if (!clientPageFound) {
      // Check if clients are managed within the main dashboard
      await page.goto('/admin/dashboard');
      await page.waitForLoadState('networkidle');

      const clientSection = await page.locator('text=/client/i, [data-testid*="client"], [class*="client"]').count();
      console.log(`👥 Client sections in main dashboard: ${clientSection}`);
    }

    await takeScreenshotWithContext(page, 'client-management');

    // Look for client data
    const hasClientTable = await page.locator('table, [role="table"]').count() > 0;
    const hasClientCards = await page.locator('[class*="card"], [class*="client"]').count() > 0;
    const hasClientList = await page.locator('ul, ol, [role="list"]').count() > 0;

    console.log(`📋 Client table found: ${hasClientTable}`);
    console.log(`🃏 Client cards found: ${hasClientCards}`);
    console.log(`📝 Client list found: ${hasClientList}`);

    // Check for empty state or no data messages
    const emptyStateMessages = await page.locator('text=/no.*client/i, text=/empty/i, text=/no.*data/i').count();
    console.log(`📭 Empty state messages: ${emptyStateMessages}`);

    const hasClientData = hasClientTable || hasClientCards || hasClientList;
    console.log(`✅ Client management functionality found: ${hasClientData || clientPageFound}`);
  });

  test('Admin Dashboard - Engagement Management Page', async ({ page }) => {
    console.log('\n🎯 TEST: Engagement Management Page');
    console.log('=====================================');

    await loginAsAdmin(page);

    // Try different potential engagement management routes
    const engagementRoutes = ['/admin/engagements', '/admin/engagement-management', '/admin/dashboard/engagements'];
    let engagementPageFound = false;

    for (const route of engagementRoutes) {
      try {
        await page.goto(route);
        await page.waitForLoadState('networkidle');
        const pageText = await page.textContent('body');

        if (pageText?.toLowerCase().includes('engagement') && !pageText?.includes('404')) {
          console.log(`✅ Engagement management page found at: ${route}`);
          engagementPageFound = true;
          break;
        }
      } catch (error) {
        console.log(`❌ Route ${route} not accessible: ${error}`);
      }
    }

    if (!engagementPageFound) {
      // Check if engagements are managed within the main dashboard
      await page.goto('/admin/dashboard');
      await page.waitForLoadState('networkidle');

      const engagementSection = await page.locator('text=/engagement/i, [data-testid*="engagement"], [class*="engagement"]').count();
      console.log(`🏢 Engagement sections in main dashboard: ${engagementSection}`);
    }

    await takeScreenshotWithContext(page, 'engagement-management');

    // Look for engagement data
    const hasEngagementTable = await page.locator('table, [role="table"]').count() > 0;
    const hasEngagementCards = await page.locator('[class*="card"], [class*="engagement"]').count() > 0;
    const hasEngagementList = await page.locator('ul, ol, [role="list"]').count() > 0;

    console.log(`📋 Engagement table found: ${hasEngagementTable}`);
    console.log(`🃏 Engagement cards found: ${hasEngagementCards}`);
    console.log(`📝 Engagement list found: ${hasEngagementList}`);

    // Check for empty state or no data messages
    const emptyStateMessages = await page.locator('text=/no.*engagement/i, text=/empty/i, text=/no.*data/i').count();
    console.log(`📭 Empty state messages: ${emptyStateMessages}`);

    // Look for engagement statistics
    const statsText = await page.textContent('body');
    const hasEngagementStats = statsText?.includes('25') || statsText?.includes('18'); // Demo data numbers
    console.log(`📊 Has engagement statistics: ${hasEngagementStats}`);

    const hasEngagementData = hasEngagementTable || hasEngagementCards || hasEngagementList;
    console.log(`✅ Engagement management functionality found: ${hasEngagementData || engagementPageFound}`);
  });

  test('Admin Dashboard - Navigation and Routing', async ({ page }) => {
    console.log('\n🎯 TEST: Admin Navigation and Routing');
    console.log('=====================================');

    await loginAsAdmin(page);
    await page.goto('/admin/dashboard');

    // Test admin navigation menu
    const navLinks = await page.locator('nav a, [role="navigation"] a, .nav a, .sidebar a').count();
    console.log(`🧭 Navigation links found: ${navLinks}`);

    // Test common admin routes
    const adminRoutes = [
      '/admin',
      '/admin/dashboard',
      '/admin/users',
      '/admin/clients',
      '/admin/engagements',
      '/admin/settings'
    ];

    let workingRoutes = 0;
    let brokenRoutes: string[] = [];

    for (const route of adminRoutes) {
      try {
        await page.goto(route);
        await page.waitForLoadState('networkidle');

        const pageText = await page.textContent('body');
        const is404 = pageText?.includes('404') || pageText?.includes('Not Found') || pageText?.includes('Page not found');

        if (!is404) {
          workingRoutes++;
          console.log(`✅ Route working: ${route}`);
        } else {
          brokenRoutes.push(route);
          console.log(`❌ Route broken: ${route}`);
        }
      } catch (error) {
        brokenRoutes.push(route);
        console.log(`❌ Route error: ${route} - ${error}`);
      }
    }

    await takeScreenshotWithContext(page, 'navigation-test');

    console.log(`🛣️  Working routes: ${workingRoutes}/${adminRoutes.length}`);
    console.log(`💔 Broken routes: ${brokenRoutes.join(', ')}`);

    expect(workingRoutes).toBeGreaterThan(0);
    console.log('✅ Navigation testing completed');
  });

  test('Admin Dashboard - Error Detection and Console Issues', async ({ page }) => {
    console.log('\n🎯 TEST: Error Detection and Console Issues');
    console.log('=====================================');

    await loginAsAdmin(page);

    // Test multiple admin pages to catch errors
    const testPages = ['/admin', '/admin/dashboard'];

    for (const testPage of testPages) {
      console.log(`🔍 Testing page: ${testPage}`);

      const pageErrors: string[] = [];
      const consoleMessages: string[] = [];

      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleMessages.push(`${testPage} - Console Error: ${msg.text()}`);
        }
        if (msg.type() === 'warn') {
          consoleMessages.push(`${testPage} - Console Warning: ${msg.text()}`);
        }
      });

      page.on('pageerror', error => {
        pageErrors.push(`${testPage} - Page Error: ${error.message}`);
      });

      await page.goto(testPage);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000); // Wait for any async operations

      console.log(`📝 Page errors for ${testPage}: ${pageErrors.length}`);
      console.log(`📝 Console messages for ${testPage}: ${consoleMessages.length}`);

      if (pageErrors.length > 0) {
        console.log('🚨 Page Errors:');
        pageErrors.forEach(error => console.log(`  - ${error}`));
      }

      if (consoleMessages.length > 0) {
        console.log('🚨 Console Messages:');
        consoleMessages.forEach(msg => console.log(`  - ${msg}`));
      }
    }

    await takeScreenshotWithContext(page, 'error-detection');
    console.log('✅ Error detection completed');
  });

  test('Admin Dashboard - Data Validation and Demo Data Detection', async ({ page }) => {
    console.log('\n🎯 TEST: Data Validation and Demo Data Detection');
    console.log('=====================================');

    await loginAsAdmin(page);
    await page.goto('/admin/dashboard');
    await page.waitForLoadState('networkidle');

    // Extract all numbers from the page
    const pageText = await page.textContent('body');
    const numbers = pageText?.match(/\b\d+\b/g) || [];
    console.log(`🔢 Numbers found on page: ${numbers.slice(0, 20).join(', ')}${numbers.length > 20 ? '...' : ''}`);

    // Check for demo data patterns
    const hasDemoClientCount = numbers.includes('12');
    const hasDemoEngagementCount = numbers.includes('25');
    const hasDemoUserCount = numbers.includes('45');

    console.log(`🎭 Demo client count (12) detected: ${hasDemoClientCount}`);
    console.log(`🎭 Demo engagement count (25) detected: ${hasDemoEngagementCount}`);
    console.log(`🎭 Demo user count (45) detected: ${hasDemoUserCount}`);

    // Look for demo data warnings or indicators
    const demoIndicators = await page.locator('text=/demo/i, text=/sample/i, text=/test/i, [class*="demo"], [class*="warning"]').count();
    console.log(`⚠️  Demo/warning indicators: ${demoIndicators}`);

    // Check for toast notifications or alerts about demo data
    const toastMessages = await page.locator('[class*="toast"], [class*="alert"], [class*="notification"]').count();
    console.log(`🍞 Toast/alert messages: ${toastMessages}`);

    // Look for loading states that might indicate API failures
    const loadingStates = await page.locator('[class*="loading"], [class*="spinner"], text=/loading/i').count();
    console.log(`⏳ Active loading states: ${loadingStates}`);

    const potentiallyUsingDemoData = hasDemoClientCount && hasDemoEngagementCount && hasDemoUserCount;
    console.log(`🎪 Likely using demo data: ${potentiallyUsingDemoData}`);

    await takeScreenshotWithContext(page, 'data-validation');
    console.log('✅ Data validation completed');
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Report any errors found during the test
    if (consoleErrors.length > 0 || networkFailures.length > 0) {
      console.log('\n🚨 ISSUES DETECTED:');
      console.log('==================');

      if (consoleErrors.length > 0) {
        console.log('Console Errors:');
        consoleErrors.forEach(error => console.log(`  - ${error}`));
      }

      if (networkFailures.length > 0) {
        console.log('Network Failures:');
        networkFailures.forEach(failure => console.log(`  - ${failure}`));
      }
    }

    // Always take a final screenshot
    await takeScreenshotWithContext(page, `final-${testInfo.title.replace(/\s+/g, '-')}`);
  });
});

// Generate final report
test.afterAll(async () => {
  console.log('\n📊 ADMIN DASHBOARD TEST SUMMARY');
  console.log('================================');
  console.log('All admin dashboard tests completed.');
  console.log('Check test-results/ directory for detailed screenshots.');
  console.log('Review the console output above for detailed findings.');
  console.log('\n📋 Key areas tested:');
  console.log('- Admin authentication and login');
  console.log('- Main dashboard data loading');
  console.log('- Client management functionality');
  console.log('- Engagement management functionality');
  console.log('- Navigation and routing');
  console.log('- Console errors and network issues');
  console.log('- Demo data detection and validation');
});
