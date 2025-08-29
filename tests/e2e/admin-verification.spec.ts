import { test, expect, Page } from '@playwright/test';

const ADMIN_CREDENTIALS = {
  email: 'chocka@gmail.com',
  password: 'Password123!'
};

async function loginAsAdmin(page: Page) {
  await page.goto('/login');
  await page.fill('input[name="email"], input[type="email"]', ADMIN_CREDENTIALS.email);
  await page.fill('input[name="password"], input[type="password"]', ADMIN_CREDENTIALS.password);
  await page.click('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")');
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 15000 });
  return page.url();
}

test('Quick Admin Dashboard Verification', async ({ page }) => {
  console.log('\n🎯 QUICK ADMIN DASHBOARD VERIFICATION');
  console.log('====================================');

  // Login
  const redirectUrl = await loginAsAdmin(page);
  console.log(`✅ Login successful, redirected to: ${redirectUrl}`);

  // Take screenshot of post-login
  await page.screenshot({
    path: `admin-post-login-${Date.now()}.png`,
    fullPage: true
  });

  // Navigate to admin dashboard
  await page.goto('/admin/dashboard');
  await page.waitForLoadState('networkidle');

  // Capture page title
  const title = await page.title();
  console.log(`📄 Page title: ${title}`);

  // Check for key elements
  const h1Count = await page.locator('h1').count();
  const h2Count = await page.locator('h2').count();
  const h3Count = await page.locator('h3').count();
  console.log(`📊 Headers: H1=${h1Count}, H2=${h2Count}, H3=${h3Count}`);

  // Get all text content
  const bodyText = await page.textContent('body');
  const hasDemo12 = bodyText?.includes('12');
  const hasDemo25 = bodyText?.includes('25');
  const hasDemo45 = bodyText?.includes('45');
  console.log(`🎭 Demo numbers present: 12=${hasDemo12}, 25=${hasDemo25}, 45=${hasDemo45}`);

  // Check for error/warning messages
  const errorMessages = await page.locator('[class*="error"], [class*="danger"], .text-red-500, .text-red-600').count();
  const warningMessages = await page.locator('[class*="warning"], [class*="alert"], .text-yellow-500, .text-amber-500').count();
  console.log(`⚠️  Error messages: ${errorMessages}, Warning messages: ${warningMessages}`);

  // Look for data sections
  const clientSections = bodyText?.toLowerCase().includes('client') ? 1 : 0;
  const engagementSections = bodyText?.toLowerCase().includes('engagement') ? 1 : 0;
  const userSections = bodyText?.toLowerCase().includes('user') ? 1 : 0;
  console.log(`📊 Data sections: Clients=${clientSections}, Engagements=${engagementSections}, Users=${userSections}`);

  // Take screenshot of admin dashboard
  await page.screenshot({
    path: `admin-dashboard-main-${Date.now()}.png`,
    fullPage: true
  });

  // Test /admin/clients route
  try {
    await page.goto('/admin/clients');
    await page.waitForLoadState('networkidle');
    const clientsPageText = await page.textContent('body');
    const isClientsPageValid = !clientsPageText?.includes('404') && clientsPageText?.toLowerCase().includes('client');
    console.log(`👥 /admin/clients page valid: ${isClientsPageValid}`);

    await page.screenshot({
      path: `admin-clients-page-${Date.now()}.png`,
      fullPage: true
    });
  } catch (error) {
    console.log(`❌ /admin/clients error: ${error}`);
  }

  // Test /admin/engagements route
  try {
    await page.goto('/admin/engagements');
    await page.waitForLoadState('networkidle');
    const engagementsPageText = await page.textContent('body');
    const isEngagementsPageValid = !engagementsPageText?.includes('404') && engagementsPageText?.toLowerCase().includes('engagement');
    console.log(`🏢 /admin/engagements page valid: ${isEngagementsPageValid}`);

    await page.screenshot({
      path: `admin-engagements-page-${Date.now()}.png`,
      fullPage: true
    });
  } catch (error) {
    console.log(`❌ /admin/engagements error: ${error}`);
  }

  console.log('\n✅ Quick verification completed');
});
