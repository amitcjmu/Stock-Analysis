import { test, expect, Page } from '@playwright/test';

// Test data
const TEST_USER = {
  email: 'chocka@gmail.com',
  password: 'Password123!'
};

test.describe('Data Import Page', () => {
  let page: Page;

  test.beforeEach(async ({ page: newPage }) => {
    page = newPage;
    
    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    
    // Wait for redirect after login
    await page.waitForURL('**/discovery/**');
  });

  test('should load without console errors', async () => {
    const consoleErrors: string[] = [];
    const apiErrors: Array<{ url: string; status: number; error?: string }> = [];
    
    // Listen for console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.error('Console Error:', msg.text());
      }
    });
    
    // Listen for failed requests
    page.on('requestfailed', (request) => {
      console.error('Request failed:', request.url(), request.failure()?.errorText);
    });
    
    // Listen for responses
    page.on('response', async (response) => {
      if (response.status() >= 400) {
        const error = {
          url: response.url(),
          status: response.status(),
          error: await response.text().catch(() => '')
        };
        apiErrors.push(error);
        console.error('API Error:', error);
      }
    });

    // Navigate to Data Import page
    await page.goto('/discovery/cmdb-import');
    
    // Wait for page to fully load and API calls to complete
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Extra wait for any delayed API calls
    
    // Take screenshot if there are errors
    if (consoleErrors.length > 0 || apiErrors.length > 0) {
      await page.screenshot({ 
        path: 'test-results/data-import-errors.png', 
        fullPage: true 
      });
    }
    
    // Check for any console errors
    if (consoleErrors.length > 0) {
      console.error('Console errors found:', consoleErrors);
    }
    expect(consoleErrors).toHaveLength(0);
    
    // Check for API errors
    if (apiErrors.length > 0) {
      console.error('API errors found:', apiErrors);
    }
    expect(apiErrors).toHaveLength(0);
  });

  test('should load flows without API errors', async () => {
    const apiErrors: string[] = [];
    
    // Intercept API responses
    page.on('response', (response) => {
      if (response.url().includes('/api/v1/') && response.status() >= 400) {
        apiErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    // Navigate to Data Import page
    await page.goto('/discovery/cmdb-import');
    
    // Wait for the flows API call
    await page.waitForResponse(
      response => response.url().includes('/api/v1/flows/') && response.status() === 200,
      { timeout: 10000 }
    ).catch(() => {
      // If timeout, it means the API call failed
    });
    
    // Check no API errors occurred
    expect(apiErrors).toHaveLength(0);
  });

  test('should display page elements correctly', async () => {
    await page.goto('/discovery/cmdb-import');
    
    // Wait for main content
    await page.waitForSelector('h1', { timeout: 10000 });
    
    // Check page title
    const title = await page.locator('h1').first().textContent();
    expect(title).toContain('Data Import');
    
    // Check upload areas are visible
    await expect(page.locator('[data-testid="upload-area"]').first()).toBeVisible();
  });

  test('should handle file upload flow', async () => {
    await page.goto('/discovery/cmdb-import');
    
    // Create a test CSV file
    const csvContent = 'Name,Type,Status\nServer1,VM,Active\nServer2,Physical,Active';
    const buffer = Buffer.from(csvContent);
    
    // Wait for upload area
    const uploadArea = page.locator('[data-testid="upload-area"]').first();
    await expect(uploadArea).toBeVisible();
    
    // Upload file
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles({
      name: 'test-servers.csv',
      mimeType: 'text/csv',
      buffer: buffer
    });
    
    // Check for upload success (no errors)
    await page.waitForTimeout(2000); // Give time for upload
    
    // Should not have error messages
    const errorMessages = page.locator('.text-destructive');
    const errorCount = await errorMessages.count();
    expect(errorCount).toBe(0);
  });

  test('should poll for flow status after upload', async () => {
    let statusPollCount = 0;
    
    // Count status polling requests
    page.on('request', (request) => {
      if (request.url().includes('/flows/') && request.url().includes('/status')) {
        statusPollCount++;
      }
    });
    
    await page.goto('/discovery/cmdb-import');
    
    // Upload a file to trigger polling
    const csvContent = 'Name,Type\nTest1,Server';
    const buffer = Buffer.from(csvContent);
    
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles({
      name: 'test.csv',
      mimeType: 'text/csv',
      buffer: buffer
    });
    
    // Wait for polling to start
    await page.waitForTimeout(5000);
    
    // Should have made status requests
    expect(statusPollCount).toBeGreaterThan(0);
  });

  test('admin user should work with demo context', async () => {
    // Logout first
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Login as admin (assuming we have admin test user)
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'AdminPass123!');
    await page.click('button[type="submit"]');
    
    // Admin might not have client/engagement, should still work
    await page.goto('/discovery/cmdb-import');
    
    // Wait for page load
    await page.waitForLoadState('networkidle');
    
    // Check no errors
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.waitForTimeout(2000);
    expect(consoleErrors).toHaveLength(0);
  });
});

test.describe('Data Import Page - Error Scenarios', () => {
  test('should handle API failures gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('**/api/v1/flows/**', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    // Login
    await page.goto('/login');
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    
    // Navigate to page
    await page.goto('/discovery/cmdb-import');
    
    // Should show page without crashing
    await expect(page.locator('h1')).toContainText('Data Import');
    
    // Should not show error modal (graceful degradation)
    const errorModal = page.locator('[role="alertdialog"]');
    const modalCount = await errorModal.count();
    expect(modalCount).toBe(0);
  });
});