import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  try {
    console.log('1. Navigating to login page...');
    await page.goto('http://localhost:8081/login', { timeout: 30000 });
    await page.waitForTimeout(2000);

    console.log('2. Logging in...');
    await page.fill('input[type="email"], input[name="email"], input[id="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"], input[name="password"], input[id="password"]', 'Password123!');
    await page.click('button:has-text("Login"), button[type="submit"]');
    await page.waitForTimeout(3000);

    console.log('3. Navigating to discovery inventory to see standard layout...');
    await page.goto('http://localhost:8081/discovery/inventory', { timeout: 10000 });
    await page.waitForTimeout(3000);

    console.log('4. Taking screenshot of standard layout...');
    await page.screenshot({ path: 'discovery-layout-example.png', fullPage: true });
    console.log('Screenshot saved as discovery-layout-example.png');

    console.log('5. Analyzing layout structure...');
    
    // Check for sidebar
    const sidebar = await page.$('[data-sidebar="sidebar"], nav, .sidebar').catch(() => null);
    console.log('Sidebar found:', !!sidebar);
    
    // Check for breadcrumbs
    const breadcrumbs = await page.$('[role="navigation"], .breadcrumb, .breadcrumbs').catch(() => null);
    console.log('Breadcrumbs found:', !!breadcrumbs);
    
    // Check for agent monitor panel
    const agentPanel = await page.$('.agent-monitor, .agent-panel, [data-testid="agent-monitor"]').catch(() => null);
    console.log('Agent monitor panel found:', !!agentPanel);

    // Get main layout structure
    const layoutInfo = await page.evaluate(() => {
      const body = document.body;
      const mainLayout = body.querySelector('main, .main, .app-layout, .page-layout');
      const sidebars = document.querySelectorAll('nav, .sidebar, [data-sidebar]');
      const headers = document.querySelectorAll('header, .header, .breadcrumb');
      
      return {
        hasMainLayout: !!mainLayout,
        sidebarCount: sidebars.length,
        headerCount: headers.length,
        bodyClasses: body.className,
        mainLayoutClasses: mainLayout?.className || 'none'
      };
    });
    
    console.log('Layout analysis:', layoutInfo);

  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }
})();